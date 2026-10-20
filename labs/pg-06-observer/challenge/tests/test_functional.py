"""pg-06-observer : ce que le PLANIFICATEUR répond, et l'état de la table.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc
`shared_preload_libraries` vide, aucune extension dans la base, aucun index sur
la colonne filtrée, et quarante mille lignes mortes sur une table dont
l'autovacuum est DÉSACTIVÉ. Ce dernier point n'est pas un ornement : sans lui,
l'autovacuum passerait de lui-même dans la minute et le test du nettoyage
serait vert avant tout travail.

CE QU'AUCUN TEST NE FAIT ICI

Vérifier qu'un index existe. Un index présent mais que le planificateur
n'emploie pas ne corrige rien, et c'est le cas le plus fréquent : on crée
l'index, la requête reste lente, et on cherche ailleurs. Le test lit donc le
PLAN de la requête. C'est le planificateur qui dit si la correction a porté, et
il ne choisit un index que s'il sait le filtre sélectif, donc après un
`ANALYZE`.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-observation.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport d'observation de l'instance."

BASE = "facturation"
SCHEMA = "appli"
TABLE = "journal"
EXTENSION = "pg_stat_statements"
REQUETE = f"select count(*) from {SCHEMA}.{TABLE} where client_id = 42"
SEUIL_MORTES_PCT = 1.0


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str, base: str = "postgres") -> str:
    r = db1.run("sudo -u postgres psql -X -At -d %s -c %s", base, sql)
    assert r.rc == 0, message(
        en=f"psql failed on {base}: {r.stderr.strip() or r.stdout.strip()}",
        fr=f"psql a échoué sur {base} : {r.stderr.strip() or r.stdout.strip()}",
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-06-observer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-06-observer` te le rend.",
    )
    return f.content_string


def _valeur(db1, cle: str) -> str:
    for ligne in _rapport(db1).splitlines():
        if ligne.strip().startswith("#") or "=" not in ligne:
            continue
        nom, _, valeur = ligne.partition("=")
        if nom.strip() == cle:
            return valeur.strip()
    return ""


# ── Observer : le serveur doit garder une trace de ce qu'il exécute ─────────


def test_l_extension_de_collecte_est_chargee_et_creee(db1) -> None:
    """Les deux, et pas l'une des deux.

    La bibliothèque se charge au démarrage du serveur, ce qui en fait un
    paramètre de contexte `postmaster` : un `CREATE EXTENSION` sur un serveur
    qui ne l'a pas préchargée échoue. Et une bibliothèque chargée sans
    extension créée ne donne aucune vue à interroger. Les deux moitiés sont
    donc contrôlées séparément, pour que le message dise laquelle manque.
    """
    chargees = _psql(db1, "show shared_preload_libraries")
    assert EXTENSION in chargees, message(
        en=(
            f"shared_preload_libraries = {chargees!r}: the server does not preload "
            f"{EXTENSION}, so it keeps no record of the queries it runs. This is a "
            "postmaster-context parameter: writing it is not enough, the server must "
            "be RESTARTED."
        ),
        fr=(
            f"shared_preload_libraries = {chargees!r} : le serveur ne précharge pas "
            f"{EXTENSION}, donc il ne garde aucune trace des requêtes qu'il exécute. "
            "C'est un paramètre de contexte postmaster : l'écrire ne suffit pas, le "
            "serveur doit être REDÉMARRÉ."
        ),
    )

    creee = _psql(
        db1, f"select count(*) from pg_extension where extname = '{EXTENSION}'", BASE
    )
    assert creee == "1", message(
        en=(
            f"The library is preloaded but the {EXTENSION} extension is not created "
            f"in {BASE}: there is no view to query. `create extension {EXTENSION}` "
            "in that database."
        ),
        fr=(
            f"La bibliothèque est préchargée mais l'extension {EXTENSION} n'est pas "
            f"créée dans {BASE} : il n'y a aucune vue à interroger. "
            f"`create extension {EXTENSION}` dans cette base."
        ),
    )


# ── Corriger : c'est le planificateur qui tranche ───────────────────────────


def test_la_requete_n_est_plus_lue_sequentiellement(db1) -> None:
    """Le plan, et non le catalogue.

    Un index présent que le planificateur ignore ne corrige rien. Il ne le
    choisit que s'il sait le filtre sélectif, donc après un `ANALYZE` : sans
    statistiques à jour, l'index existe et reste inemployé. C'est précisément
    ce que ce test attrape et qu'un contrôle d'existence laisserait passer.
    """
    plan = _psql(db1, f"explain {REQUETE}", BASE)
    assert "Seq Scan" not in plan, message(
        en=(
            "The planner still reads the whole table:\n"
            f"{plan}\n"
            "An index on the filtered column replaces that scan, BUT only if the "
            "planner knows the filter is selective, hence after an "
            f"`analyze {SCHEMA}.{TABLE}`. An index that exists is not an index in "
            "use."
        ),
        fr=(
            "Le planificateur lit encore la table en entier :\n"
            f"{plan}\n"
            "Un index sur la colonne filtrée remplace ce parcours, MAIS seulement si "
            "le planificateur sait le filtre sélectif, donc après un "
            f"`analyze {SCHEMA}.{TABLE}`. Un index qui existe n'est pas un index "
            "employé."
        ),
    )


# ── Maintenir : l'espace que la purge n'a pas rendu ─────────────────────────


def test_les_lignes_mortes_ont_ete_recuperees(db1) -> None:
    mortes = int(_psql(
        db1,
        f"select n_dead_tup from pg_stat_user_tables "
        f"where schemaname = '{SCHEMA}' and relname = '{TABLE}'",
        BASE,
    ))
    vivantes = int(_psql(
        db1,
        f"select n_live_tup from pg_stat_user_tables "
        f"where schemaname = '{SCHEMA}' and relname = '{TABLE}'",
        BASE,
    ))
    total = mortes + vivantes
    pourcentage = (100.0 * mortes / total) if total else 0.0
    assert pourcentage < SEUIL_MORTES_PCT, message(
        en=(
            f"{SCHEMA}.{TABLE} still holds {mortes} dead rows against {vivantes} live "
            f"ones, i.e. {pourcentage:.1f}%, where under {SEUIL_MORTES_PCT}% is "
            "expected. A `vacuum` makes that space reusable by the table. Avoid "
            "`vacuum full`: it takes an exclusive lock, so it cuts the service."
        ),
        fr=(
            f"{SCHEMA}.{TABLE} porte encore {mortes} lignes mortes contre {vivantes} "
            f"vivantes, soit {pourcentage:.1f} %, là où on attend moins de "
            f"{SEUIL_MORTES_PCT} %. Un `vacuum` rend cet espace réutilisable par la "
            "table. Évite `vacuum full` : il prend un verrou exclusif, donc il coupe "
            "le service."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-06-observer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-06-observer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_les_lignes_mortes_restantes(db1) -> None:
    attendu = _psql(
        db1,
        f"select n_dead_tup from pg_stat_user_tables "
        f"where schemaname = '{SCHEMA}' and relname = '{TABLE}'",
        BASE,
    )
    ecrit = _valeur(db1, "lignes_mortes_journal")
    assert ecrit == attendu, message(
        en=(
            f"lignes_mortes_journal = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. `select n_dead_tup from pg_stat_user_tables where relname = "
            f"'{TABLE}'` gives it."
        ),
        fr=(
            f"lignes_mortes_journal = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. `select n_dead_tup from pg_stat_user_tables where "
            f"relname = '{TABLE}'` le donne."
        ),
    )


def test_le_rapport_compte_les_index(db1) -> None:
    attendu = _psql(
        db1,
        f"select count(*) from pg_indexes "
        f"where schemaname = '{SCHEMA}' and tablename = '{TABLE}'",
        BASE,
    )
    ecrit = _valeur(db1, "nb_index_sur_journal")
    assert ecrit == attendu, message(
        en=(
            f"nb_index_sur_journal = {ecrit!r} in the report, but the catalog counts "
            f"{attendu!r}. The primary key carries one of its own: do not forget it."
        ),
        fr=(
            f"nb_index_sur_journal = {ecrit!r} dans le rapport, alors que le catalogue "
            f"en compte {attendu!r}. La clé primaire en porte un à elle seule : ne "
            "l'oublie pas."
        ),
    )


def test_le_rapport_dit_la_bibliotheque_chargee(db1) -> None:
    attendu = _psql(db1, "show shared_preload_libraries")
    ecrit = _valeur(db1, "bibliotheque_chargee")
    assert ecrit == attendu, message(
        en=(
            f"bibliotheque_chargee = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. `show shared_preload_libraries` gives it, and it is the "
            "value IN SERVICE, not the one written in a file."
        ),
        fr=(
            f"bibliotheque_chargee = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. `show shared_preload_libraries` le donne, et c'est "
            "la valeur EN SERVICE, non celle écrite dans un fichier."
        ),
    )
