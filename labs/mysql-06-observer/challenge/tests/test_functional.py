"""mysql-06-observer : le plan et la taille, deux états que rien ne devine.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc une
table DÉGRADÉE et la refait à l'identique à chaque passage : il la supprime,
la recrée, la remplit de 200 000 lignes, pose un index LEURRE et purge neuf
lignes sur dix. Sans ce `drop table`, un deuxième passage trouverait la table
déjà reconstruite par le travail du premier.

LES QUATRE MESURES QUI ONT DÉCIDÉ DE CES TESTS, prises sur MySQL 8.4 le
2026-10-20 dans un conteneur jetable

    etat de depart              20 000 lignes, 45 Mo, type=ALL, key=NULL,
                                17 477 lignes examinees, index idx_niveau present
    apres CREATE INDEX          type=ref, key=idx_service, 412 lignes examinees
                                et TOUJOURS 45 Mo
    apres OPTIMIZE TABLE        6 Mo, 20 000 lignes, index toujours employe
    apres ALTER ... ENGINE      meme effet, c'est l'autre geste admis

La deuxième ligne est celle qui compte : **créer un index ne récupère aucun
octet**. Les deux tâches du lab sont donc indépendantes, et aucun de ces deux
tests ne passe grâce à l'autre. C'est ce qu'il fallait vérifier avant d'écrire.

POURQUOI UN INDEX LEURRE DANS LE SETUP

Pour que « un index existe » soit DÉJÀ VRAI au départ. `SHOW INDEX` affiche
alors un index sur la table, et le plan continue de tout lire. Un test qui
porterait sur l'existence d'un index serait vert sans travail ; celui-ci porte
sur le PLAN, qui est le seul état qui dise si l'index sert.

AUCUN ORDRE DE CE FICHIER N'EMPLOIE DE BASE PAR DÉFAUT

Première version de ce fichier : les helpers interrogeaient la table avec
`-D appli`, donc leurs propres `select count(*)` étaient fichés sous `appli`,
et le test « la requête est fichée sous sa base » passait au vert dès que le
premier test tournait. Un test qui se rend vrai lui-même est pire qu'absent.

Tous les ordres nomment donc la table en entier, `appli.evenements`, et sont
enregistrés sous un `SCHEMA_NAME` NUL. La sonde exige en plus que l'empreinte
porte le `WHERE` du tableau de bord : deux couches, parce qu'un test qui
s'auto-valide coûte bien plus qu'une ligne de filtre.

UN PIÈGE DE HARNAIS, MESURÉ ET CONTOURNÉ

`EXPLAIN FORMAT=JSON` lu par le client en mode batch rend un JSON dont les
sauts de ligne sont échappés en `\\n` littéraux, et `json.loads` échoue dessus.
L'option **`--raw`** désactive cet échappement. Sans elle, ce fichier
diagnostiquerait une panne de serveur là où il n'y a qu'un client qui protège
sa sortie.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-observation.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport d'observation de la table appli.evenements."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BASE = "appli"
TABLE = "evenements"
COLONNE = "service"
REQUETE = (
    f"select count(*) from {BASE}.{TABLE} where {COLONNE} = 'svc-7'"
)

# Ce que le setup laisse : 200 000 lignes insérées, 9 sur 10 supprimées.
LIGNES_ATTENDUES = 20000
# Mesuré : 45 Mo au départ, 6 Mo après reconstruction. Le seuil est haut pour
# laisser à l'apprenant la liberté d'ajouter plus d'un index, et reste
# inatteignable sans reconstruire.
SEUIL_MEGAOCTETS = 20


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _sql(db1, sql: str) -> str:
    """Une valeur lue SANS base par défaut, et c'est délibéré.

    Si ce helper employait `-D appli`, ses propres ordres seraient enregistrés
    sous la base `appli` dans le digest, et le test « la requête est fichée
    sous sa base » passerait au vert à cause de lui. Tous les ordres de ce
    fichier nomment donc la table en entier et sont fichés sous `NULL`.
    """
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _plan(db1) -> dict:
    """Le plan de la requête du tableau de bord, en données et non en rendu.

    `--raw` est indispensable : sans lui le client échappe les sauts de ligne
    du JSON et `json.loads` échoue. Mesuré.
    """
    r = db1.run(
        "env MYSQL_PWD=%s mysql -u %s -N -B --raw -e %s",
        MDP_ADMIN,
        ADMIN,
        f"explain format=json {REQUETE}",
    )
    assert r.rc == 0, message(
        en=f"`EXPLAIN FORMAT=JSON` failed: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"`EXPLAIN FORMAT=JSON` a échoué : {(r.stderr or r.stdout).strip()[:300]}",
    )
    try:
        charge = json.loads(r.stdout)
    except ValueError as erreur:  # pragma: no cover - diagnostic
        raise AssertionError(
            message(
                en=(
                    f"The plan is not readable as JSON ({erreur}). First characters: "
                    f"{r.stdout[:200]!r}"
                ),
                fr=(
                    f"Le plan n'est pas lisible en JSON ({erreur}). Premiers "
                    f"caractères : {r.stdout[:200]!r}"
                ),
            )
        ) from erreur
    bloc = charge.get("query_block", {})
    return bloc.get("table") or {}


def _exiger_les_lignes_intactes(db1) -> None:
    """La contrainte qui garde les deux mesures, et elle ne vaut pas un test.

    Un apprenant qui supprimerait la table pour la recréer vide obtiendrait un
    plan rapide et une taille minuscule, donc deux tests verts pour la pire
    des raisons. Les lignes doivent être là.
    """
    lignes = _sql(db1, f"select count(*) from {BASE}.{TABLE}")
    assert lignes == str(LIGNES_ATTENDUES), message(
        en=(
            f"`{BASE}.{TABLE}` holds {lignes} rows where {LIGNES_ATTENDUES} are "
            "expected. The lab asks to reclaim the space of a purge, not to lose "
            "the rows that survived it: a table emptied or recreated would make the "
            "plan fast and the size small for the worst of reasons."
        ),
        fr=(
            f"`{BASE}.{TABLE}` porte {lignes} lignes là où {LIGNES_ATTENDUES} sont "
            "attendues. Le lab demande de récupérer l'espace d'une purge, pas de "
            "perdre les lignes qui y ont survécu : une table vidée ou recréée "
            "rendrait le plan rapide et la taille petite pour la pire des raisons."
        ),
    )


def _megaoctets(db1) -> int:
    """La taille que la table occupe vraiment, rafraîchie avant lecture.

    `information_schema` sert des statistiques, et `ANALYZE TABLE` les
    rafraîchit : les lire sans cela peut rendre la valeur d'avant la
    reconstruction, et accuser un travail qui a été fait.
    """
    _sql(db1, f"analyze table {BASE}.{TABLE}")
    valeur = _sql(
        db1,
        "select round((data_length + index_length) / 1024 / 1024) "
        "from information_schema.tables "
        f"where table_schema = '{BASE}' and table_name = '{TABLE}'",
    )
    return int(valeur or 0)


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-06-observer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-06-observer` te le rend.",
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


# ── Le plan : ce que le serveur fait, et non ce que le catalogue contient ───


def test_le_plan_cesse_de_lire_la_table_entiere(db1) -> None:
    """LE test du lab, et il ne lit aucun catalogue d'index.

    Mesuré au départ : `type: ALL`, `key: NULL`, 17 477 lignes examinées, alors
    qu'un index EXISTE sur la table. Rien dans `SHOW INDEX` ne dit qu'il ne
    sert pas cette requête.
    """
    _exiger_les_lignes_intactes(db1)
    plan = _plan(db1)
    acces = plan.get("access_type")
    assert acces and acces != "ALL", message(
        en=(
            f"The plan still reads the table whole (`access_type: {acces}`), and it "
            f"examines {plan.get('rows_examined_per_scan')} rows for a query that "
            "returns a count. An index already exists on this table and does not "
            "serve this query: the catalog cannot say that, only the plan can. "
            f"Index the column the query filters on, `{COLONNE}`."
        ),
        fr=(
            f"Le plan lit encore la table entière (`access_type: {acces}`), et il "
            f"examine {plan.get('rows_examined_per_scan')} lignes pour une requête "
            "qui rend un décompte. Un index existe déjà sur cette table et ne sert "
            "pas cette requête : le catalogue ne peut pas le dire, seul le plan le "
            f"dit. Indexe la colonne que la requête filtre, `{COLONNE}`."
        ),
    )
    examinees = plan.get("rows_examined_per_scan")
    assert isinstance(examinees, int) and examinees < LIGNES_ATTENDUES / 2, message(
        en=(
            f"The plan announces `access_type: {acces}` but still examines "
            f"{examinees} rows out of {LIGNES_ATTENDUES}. An index that narrows "
            "nothing is not a fix."
        ),
        fr=(
            f"Le plan annonce `access_type: {acces}` mais examine encore "
            f"{examinees} lignes sur {LIGNES_ATTENDUES}. Un index qui ne restreint "
            "rien n'est pas une correction."
        ),
    )


def test_l_index_employe_porte_sur_la_colonne_filtree(db1) -> None:
    """Le bon index, et pas n'importe lequel.

    Un index composite dont la première colonne est autre chose ne sert pas un
    filtre d'égalité sur `service`. Le test lit donc la colonne de rang 1 de
    l'index que le PLAN emploie, pas la liste des index de la table.
    """
    plan = _plan(db1)
    employe = plan.get("key")
    assert employe, message(
        en="The plan uses no index, so there is nothing to check here yet.",
        fr="Le plan n'emploie aucun index, il n'y a donc rien à contrôler ici.",
    )
    premiere = _sql(
        db1,
        "select column_name from information_schema.statistics "
        f"where table_schema = '{BASE}' and table_name = '{TABLE}' "
        f"and index_name = '{employe}' and seq_in_index = 1",
    )
    assert premiere == COLONNE, message(
        en=(
            f"The plan uses the `{employe}` index, whose first column is "
            f"{premiere!r} and not `{COLONNE}`. An equality filter is served by an "
            "index whose FIRST column is the filtered one."
        ),
        fr=(
            f"Le plan emploie l'index `{employe}`, dont la première colonne est "
            f"{premiere!r} et non `{COLONNE}`. Un filtre d'égalité est servi par un "
            "index dont la PREMIÈRE colonne est celle qu'on filtre."
        ),
    )


# ── La taille : l'espace qu'une purge n'a pas rendu ────────────────────────


def test_la_table_a_rendu_son_espace(db1) -> None:
    """Mesuré, et c'est le fait que le lab existe pour faire rencontrer.

    Au départ : 20 000 lignes et 45 Mo, parce qu'un `DELETE` ne rend rien au
    disque. Après une reconstruction : 6 Mo. Et `data_free` ne bouge presque
    pas dans l'intervalle, donc ce n'est pas lui qui le dit.

    Ce test ne passe PAS grâce au précédent : mesuré, `CREATE INDEX` laisse la
    table à 45 Mo.
    """
    _exiger_les_lignes_intactes(db1)
    mo = _megaoctets(db1)
    assert mo < SEUIL_MEGAOCTETS, message(
        en=(
            f"`{BASE}.{TABLE}` still occupies {mo} MB for {LIGNES_ATTENDUES} rows, "
            f"where less than {SEUIL_MEGAOCTETS} MB is expected. A `DELETE` returns "
            "nothing to the disk: InnoDB keeps the pages for later reuse. The space "
            "comes back when the table is REBUILT, by `OPTIMIZE TABLE` or by "
            "`ALTER TABLE ... ENGINE=InnoDB`, which do the same thing here. Watching "
            "`data_free` will not show it: measured, it barely moves."
        ),
        fr=(
            f"`{BASE}.{TABLE}` occupe encore {mo} Mo pour {LIGNES_ATTENDUES} lignes, "
            f"là où moins de {SEUIL_MEGAOCTETS} Mo sont attendus. Un `DELETE` ne rend "
            "rien au disque : InnoDB garde les pages pour les réemployer. L'espace "
            "revient quand la table est RECONSTRUITE, par `OPTIMIZE TABLE` ou par "
            "`ALTER TABLE ... ENGINE=InnoDB`, qui font ici la même chose. Surveiller "
            "`data_free` ne le montrera pas : mesuré, il bouge à peine."
        ),
    )


# ── Le diagnostic : retrouver la requête, sous le nom de sa base ───────────


def test_la_requete_est_fichee_sous_sa_base(db1) -> None:
    """Le piège d'exploitation, mesuré, et il surprend tout le monde.

    Une requête jouée SANS base par défaut est enregistrée avec un
    `SCHEMA_NAME` NUL. Elle n'apparaît donc pas quand on interroge
    `sys.statement_analysis` en filtrant sur `db`, qui est exactement la façon
    dont on cherche « les requêtes coûteuses de cette base ».

    Mesuré : la même requête jouée deux fois, une fois sans base par défaut et
    une fois avec, produit DEUX empreintes distinctes, l'une sous `NULL` et
    l'autre sous `appli`. La sonde rend 0 puis 1.
    """
    combien = _sql(
        db1,
        "select count(*) from sys.statement_analysis "
        f"where db = '{BASE}' and query like 'SELECT%' "
        f"and query like '%{TABLE}%' and query like '%WHERE%{COLONNE}%'",
    )
    assert combien.isdigit() and int(combien) > 0, message(
        en=(
            f"No SELECT citing `{TABLE}` is filed under the `{BASE}` database in "
            "`sys.statement_analysis`. Measured: a statement run WITHOUT a default "
            "database is recorded with a NULL `SCHEMA_NAME`, so it never shows up "
            "when you filter on `db`, which is how one looks for the costly queries "
            "of a database. Run the dashboard query with its database selected, by "
            f"`mysql -D {BASE}` or after a `USE {BASE}`."
        ),
        fr=(
            f"Aucun SELECT citant `{TABLE}` n'est fiché sous la base `{BASE}` dans "
            "`sys.statement_analysis`. Mesuré : une requête jouée SANS base par "
            "défaut est enregistrée avec un `SCHEMA_NAME` NUL, donc elle "
            "n'apparaît jamais quand on filtre sur `db`, ce qui est pourtant la "
            "façon de chercher les requêtes coûteuses d'une base. Joue la requête "
            f"du tableau de bord avec sa base sélectionnée, par `mysql -D {BASE}` "
            f"ou après un `USE {BASE}`."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-06-observer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-06-observer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_l_etat_reel(db1) -> None:
    plan = _plan(db1)
    attendu_acces = str(plan.get("access_type", ""))
    ecrit_acces = _valeur(db1, "type_d_acces_du_plan")
    assert ecrit_acces.lower() == attendu_acces.lower(), message(
        en=(
            f"type_d_acces_du_plan = {ecrit_acces!r} in the report, but the plan "
            f"announces {attendu_acces!r}. `EXPLAIN FORMAT=JSON` gives it as "
            "`access_type`, and the tabular `EXPLAIN` as the `type` column."
        ),
        fr=(
            f"type_d_acces_du_plan = {ecrit_acces!r} dans le rapport, alors que le "
            f"plan annonce {attendu_acces!r}. `EXPLAIN FORMAT=JSON` le donne sous "
            "`access_type`, et l'`EXPLAIN` en tableau dans la colonne `type`."
        ),
    )

    attendu_mo = _megaoctets(db1)
    ecrit_mo = _valeur(db1, "megaoctets_de_la_table")
    assert ecrit_mo.isdigit() and int(ecrit_mo) == attendu_mo, message(
        en=(
            f"megaoctets_de_la_table = {ecrit_mo!r} in the report, but the server "
            f"answers {attendu_mo}. It is `data_length + index_length` of "
            "`information_schema.tables`, in megabytes, and `ANALYZE TABLE` "
            "refreshes it."
        ),
        fr=(
            f"megaoctets_de_la_table = {ecrit_mo!r} dans le rapport, alors que le "
            f"serveur répond {attendu_mo}. C'est `data_length + index_length` de "
            "`information_schema.tables`, en mégaoctets, et `ANALYZE TABLE` le "
            "rafraîchit."
        ),
    )

    attendu_lignes = _sql(db1, f"select count(*) from {BASE}.{TABLE}")
    ecrit_lignes = _valeur(db1, "lignes_restantes")
    assert ecrit_lignes == attendu_lignes, message(
        en=(
            f"lignes_restantes = {ecrit_lignes!r} in the report, but the table holds "
            f"{attendu_lignes}."
        ),
        fr=(
            f"lignes_restantes = {ecrit_lignes!r} dans le rapport, alors que la table "
            f"en porte {attendu_lignes}."
        ),
    )
