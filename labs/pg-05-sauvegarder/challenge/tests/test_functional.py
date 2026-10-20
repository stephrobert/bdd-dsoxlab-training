"""pg-05-sauvegarder : ce que les fichiers contiennent, et ce qui se restaure.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc un
répertoire de sauvegarde VIDE, aucune base de vérification, et un rapport non
rempli. Il vide ce répertoire et détruit la base de vérification à chaque
passage : sans cela, un dump laissé par un passage précédent rendrait le lab
vert sans travail.

CE QUI EST NOTÉ, ET POURQUOI CE N'EST PAS L'EXISTENCE D'UN FICHIER

Le guide titre lui-même la raison : « Une sauvegarde non testée n'est pas une
sauvegarde. » Un dump de 5 Ko sur le disque ne prouve rien. Les tests ouvrent
donc le dump avec `pg_restore --list`, ce qui échoue sur un format qui n'en est
pas un, et surtout ils comparent le contenu RESTAURÉ à l'original, table par
table.

LE PIÈGE QUE CE LAB FAIT RENCONTRER

`pg_dump` ne sauvegarde pas les rôles : ils sont globaux au cluster. Un dump
restauré sur une machine neuve échoue alors sur chaque propriétaire et chaque
droit, et on le découvre le jour de l'incident. Le test exige donc l'autre
moitié de la sauvegarde, et son message dit laquelle.

CE QUE LES TESTS N'IMPOSENT PAS

Le nom du fichier de dump. Les tests cherchent, dans le répertoire, un fichier
que `pg_restore` sait lire : toute convention de nommage passe. Imposer un nom
reviendrait à noter une dictée.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-sauvegarde.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de sauvegarde de la base facturation."

DEPOT = "/var/backups/postgresql"
GLOBALS = f"{DEPOT}/globals.sql"
BASE = "facturation"
BASE_VERIF = "facturation_verif"
SCHEMA = "appli"
TABLES = ("clients", "commandes")
ROLE = "appli"


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


@pytest.fixture(scope="module")
def dump(db1) -> tuple[str, str]:
    """Le dump trouvé dans le dépôt, et sa table des matières.

    Cherché et non imposé : tout fichier que `pg_restore` sait lire fait
    l'affaire, quelle que soit la convention de nommage. `globals.sql` est
    écarté, puisque c'est un script SQL et non un dump.
    """
    liste = db1.run("find %s -maxdepth 1 -type f ! -name globals.sql", DEPOT)
    candidats = [c for c in liste.stdout.split() if c]
    assert candidats, message(
        en=(
            f"{DEPOT} holds no backup file. The nightly job stopped running: "
            "produce the dump yourself (`pg_dump`)."
        ),
        fr=(
            f"{DEPOT} ne contient aucun fichier de sauvegarde. La tâche nocturne a "
            "cessé de tourner : produis le dump toi-même (`pg_dump`)."
        ),
    )
    echecs = []
    for chemin in candidats:
        toc = db1.run("sudo -u postgres pg_restore --list %s", chemin)
        if toc.rc == 0:
            return chemin, toc.stdout
        echecs.append(f"{chemin} : {(toc.stderr or toc.stdout).strip()[:200]}")
    pytest.fail(
        message(
            en=(
                "No file in "
                f"{DEPOT} is readable by pg_restore:\n" + "\n".join(echecs) + "\n"
                "A `plain` format dump (-Fp) is not a dump, it is an SQL script, and "
                "pg_restore refuses it. The custom format (-Fc) is the one that "
                "allows a selective restore."
            ),
            fr=(
                "Aucun fichier de "
                f"{DEPOT} n'est lisible par pg_restore :\n" + "\n".join(echecs) + "\n"
                "Un dump au format `plain` (-Fp) n'est pas un dump, c'est un script "
                "SQL, et pg_restore le refuse. Le format custom (-Fc) est celui qui "
                "autorise une restauration sélective."
            ),
        )
    )


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-05-sauvegarder` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-05-sauvegarder` te le rend.",
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


# ── Le dump : lisible, au bon format, et complet ────────────────────────────


def test_le_dump_est_au_format_custom(db1, dump) -> None:
    """Le format décide des outils de restauration, donc il se choisit avant."""
    chemin, toc = dump
    entete = [
        ligne
        for ligne in toc.splitlines()
        if ligne.lstrip("; \t").startswith("Format:")
    ]
    assert entete, message(
        en=f"pg_restore --list on {chemin} prints no format header.",
        fr=f"pg_restore --list sur {chemin} n'affiche aucun en-tête de format.",
    )
    annonce = entete[0].split(":", 1)[1].strip()
    assert annonce.upper() == "CUSTOM", message(
        en=(
            f"{chemin} is in format {annonce!r}, expected "
            "CUSTOM. Only the custom and directory formats allow a selective restore "
            "with pg_restore."
        ),
        fr=(
            f"{chemin} est au format {annonce!r}, attendu "
            "CUSTOM. Seuls les formats custom et directory autorisent une "
            "restauration sélective par pg_restore."
        ),
    )


def test_le_dump_porte_les_deux_tables(db1, dump) -> None:
    """Un dump sélectif qui aurait oublié une table n'est pas une sauvegarde."""
    chemin, toc = dump
    manquantes = [t for t in TABLES if f"{SCHEMA} {t}" not in toc]
    assert not manquantes, message(
        en=(
            f"{chemin} does not carry {', '.join(manquantes)}. Its table of contents "
            f"holds no TABLE entry for the {SCHEMA} schema: the dump is selective and "
            "left them out, or it does not cover this database."
        ),
        fr=(
            f"{chemin} ne porte pas {', '.join(manquantes)}. Sa table des matières "
            f"n'a aucune entrée TABLE pour le schéma {SCHEMA} : le dump est sélectif "
            "et les a laissées de côté, ou il ne couvre pas cette base."
        ),
    )


def test_les_roles_sont_sauvegardes_a_part(db1) -> None:
    """Ce que `pg_dump` ne peut pas contenir, et qu'on découvre trop tard.

    Les rôles sont globaux au cluster. Une restauration sur une machine neuve
    échoue sur chaque propriétaire et chaque droit, et le message ne parle
    alors ni de sauvegarde ni de rôles.
    """
    f = db1.file(GLOBALS)
    assert f.exists, message(
        en=(
            f"{GLOBALS} does not exist. `pg_dump` does NOT back up roles: they are "
            "global to the cluster. Without them, restoring onto a fresh machine "
            "fails on every owner and every privilege. `pg_dumpall --globals-only` "
            "is the other half of the backup."
        ),
        fr=(
            f"{GLOBALS} n'existe pas. `pg_dump` ne sauvegarde PAS les rôles : ils "
            "sont globaux au cluster. Sans eux, une restauration sur une machine "
            "neuve échoue sur chaque propriétaire et chaque droit. `pg_dumpall "
            "--globals-only` est l'autre moitié de la sauvegarde."
        ),
    )
    contenu = f.content_string
    assert f"CREATE ROLE {ROLE};" in contenu or f"CREATE ROLE {ROLE}\n" in contenu, message(
        en=(
            f"{GLOBALS} exists but does not create the `{ROLE}` role. Is it really the "
            "output of `pg_dumpall --globals-only`?"
        ),
        fr=(
            f"{GLOBALS} existe mais ne crée pas le rôle `{ROLE}`. Est-ce bien la "
            "sortie de `pg_dumpall --globals-only` ?"
        ),
    )


# ── La restauration : la seule étape qui prouve quelque chose ───────────────


def test_la_base_de_verification_existe_et_est_distincte(db1) -> None:
    bases = _psql(db1, "select datname from pg_database order by datname")
    assert BASE_VERIF in bases.split(), message(
        en=(
            f"The {BASE_VERIF} database does not exist. A backup nobody has restored "
            "is not a backup: restore the dump into a NEW database and compare."
        ),
        fr=(
            f"La base {BASE_VERIF} n'existe pas. Une sauvegarde que personne n'a "
            "restaurée n'est pas une sauvegarde : restaure le dump dans une base "
            "NEUVE et compare."
        ),
    )
    assert BASE in bases.split(), message(
        en=(
            f"The original {BASE} database has disappeared. The verification restore "
            "must not replace production: it goes into a separate database."
        ),
        fr=(
            f"La base d'origine {BASE} a disparu. La restauration de vérification ne "
            "doit pas remplacer la production : elle va dans une base distincte."
        ),
    )


def test_le_contenu_restaure_est_identique_a_l_original(db1) -> None:
    """Table par table, et non « la base fait la bonne taille »."""
    for table in TABLES:
        presente = _psql(
            db1,
            f"select count(*) from pg_tables "
            f"where schemaname = '{SCHEMA}' and tablename = '{table}'",
            BASE_VERIF,
        )
        assert presente == "1", message(
            en=(
                f"{SCHEMA}.{table} is absent from {BASE_VERIF}. The restore did not "
                "carry the whole dump: `pg_restore -d <base> <the dump>` restores "
                "everything, and its errors must be read."
            ),
            fr=(
                f"{SCHEMA}.{table} est absente de {BASE_VERIF}. La restauration n'a "
                "pas porté tout le dump : `pg_restore -d <base> <le dump>` restaure "
                "tout, et ses erreurs doivent être lues."
            ),
        )
        origine = _psql(db1, f"select count(*) from {SCHEMA}.{table}", BASE)
        restaure = _psql(db1, f"select count(*) from {SCHEMA}.{table}", BASE_VERIF)
        assert restaure == origine, message(
            en=(
                f"{SCHEMA}.{table} holds {restaure} row(s) in {BASE_VERIF} against "
                f"{origine} in {BASE}. A restore that loses rows is worse than no "
                "restore: it looks like it worked."
            ),
            fr=(
                f"{SCHEMA}.{table} porte {restaure} ligne(s) dans {BASE_VERIF} contre "
                f"{origine} dans {BASE}. Une restauration qui perd des lignes est "
                "pire qu'une absence de restauration : elle a l'air d'avoir marché."
            ),
        )


# ── Le rapport : édité, et confronté aux fichiers ──────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-05-sauvegarder` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-05-sauvegarder` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_le_format_du_dump(db1) -> None:
    ecrit = _valeur(db1, "format_du_dump").lower()
    assert ecrit == "custom", message(
        en=(
            f"format_du_dump = {ecrit!r} in the report, expected 'custom'. "
            "`pg_restore --list <the dump>` prints it in its header."
        ),
        fr=(
            f"format_du_dump = {ecrit!r} dans le rapport, attendu « custom ». "
            "`pg_restore --list <le dump>` l'affiche dans son en-tête."
        ),
    )


def test_le_rapport_compte_les_lignes_restaurees(db1) -> None:
    attendu = _psql(db1, f"select count(*) from {SCHEMA}.clients", BASE_VERIF)
    ecrit = _valeur(db1, "nb_lignes_clients_restaurees")
    assert ecrit == attendu, message(
        en=(
            f"nb_lignes_clients_restaurees = {ecrit!r} in the report, but "
            f"{BASE_VERIF} answers {attendu!r}. Count it in the RESTORED database, "
            "not in the original: that is the point of the check."
        ),
        fr=(
            f"nb_lignes_clients_restaurees = {ecrit!r} dans le rapport, alors que "
            f"{BASE_VERIF} répond {attendu!r}. Compte-les dans la base RESTAURÉE et "
            "non dans l'originale : c'est tout l'objet de la vérification."
        ),
    )


def test_le_rapport_compte_les_roles_sauvegardes(db1) -> None:
    """Compté sur le fichier lui-même : il faut l'avoir ouvert."""
    r = db1.run("grep -c '^CREATE ROLE' %s", GLOBALS)
    attendu = r.stdout.strip()
    assert r.rc == 0 and attendu, message(
        en=f"{GLOBALS} carries no CREATE ROLE line: is it really a globals dump?",
        fr=f"{GLOBALS} ne porte aucune ligne CREATE ROLE : est-ce bien un dump des globaux ?",
    )
    ecrit = _valeur(db1, "nb_roles_sauvegardes")
    assert ecrit == attendu, message(
        en=(
            f"nb_roles_sauvegardes = {ecrit!r} in the report, but {GLOBALS} holds "
            f"{attendu!r}. `grep -c '^CREATE ROLE' {GLOBALS}` counts them."
        ),
        fr=(
            f"nb_roles_sauvegardes = {ecrit!r} dans le rapport, alors que {GLOBALS} "
            f"en porte {attendu!r}. `grep -c '^CREATE ROLE' {GLOBALS}` les compte."
        ),
    )
