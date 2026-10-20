"""pg-08-restaurer-pitr : les données revenues, et la trace du geste.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc une
base dont la table est SUPPRIMÉE, une grappe en timeline 1, et un rapport non
rempli. Il efface à chaque passage l'archive, la sauvegarde physique, le
répertoire écarté et les paramètres de restauration : sans cela, une grappe
déjà restaurée rendrait trois tests verts sans travail.

LA PREUVE QU'ON NE PEUT PAS CONTOURNER

Recréer la table à la main avec six lignes passerait tous les contrôles portant
sur les données. C'est pourquoi le lab contrôle aussi la TIMELINE : une
restauration menée à son terme promeut la grappe, et une promotion incrémente
la timeline. Une grappe neuve est en 1, une grappe restaurée et promue en 2.
C'est ce contrôle qui note le GESTE plutôt que son résultat apparent.

LES TROIS POINTS D'ARRIVÉE, DONT DEUX SONT FAUX

La sauvegarde physique seule rend CINQ lignes : la sixième n'existe que dans
les journaux. Le dernier WAL disponible rend ZÉRO ligne : le DROP TABLE est
rejoué. Seul l'instant noté rend les six. Le test sur le compte de lignes est
donc le test central, et son message nomme les trois cas.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-restauration.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de restauration a un instant donne."

BASE = "facturation"
SCHEMA = "appli"
TABLE = "clients"
LIGNES_ATTENDUES = 6
TEMOIN = "PITR Test"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str, base: str = "postgres") -> str:
    r = db1.run("sudo -u postgres psql -X -At -d %s -c %s", base, sql)
    assert r.rc == 0, message(
        en=(
            f"psql failed on {base}: {r.stderr.strip() or r.stdout.strip()}. If the "
            "server does not start, read its log: a recovery that cannot find a "
            "segment stops there."
        ),
        fr=(
            f"psql a échoué sur {base} : {r.stderr.strip() or r.stdout.strip()}. Si "
            "le serveur ne démarre pas, lis son journal : une restauration qui ne "
            "trouve pas un segment s'arrête là."
        ),
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-08-restaurer-pitr` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-08-restaurer-pitr` te le rend.",
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


# ── La restauration est allée à son terme ───────────────────────────────────


def _exiger_hors_restauration(db1) -> None:
    """Par défaut, le serveur s'arrête EN PAUSE une fois la cible atteinte.

    `recovery_target_action` vaut `pause` : la base est alors en lecture seule
    et paraît inachevée, sans que rien ne dise que c'est normal.

    POURQUOI CE N'EST PAS UN TEST À PART

    Il le fut, et il était VERT sur l'état de départ : avant tout travail, le
    serveur est un primaire ordinaire, donc hors restauration. Un test vert
    avant tout travail ne mesure rien, et le pilote du catalogue l'a refusé.
    Sortir de la restauration n'est pas un travail à accomplir en soi : c'est
    une CONTRAINTE sur l'état d'arrivée. Son contrôle vit donc en tête de
    l'assertion qu'il garde, celle qui exige que la base accepte à nouveau les
    écritures.
    """
    en_recovery = _psql(db1, "select pg_is_in_recovery()")
    assert en_recovery == "f", message(
        en=(
            "The server is still in recovery mode: the database is read-only. Once "
            "the target is reached it PAUSES, because `recovery_target_action` "
            "defaults to `pause`. Take over with `select pg_wal_replay_resume()`, or "
            "ask for `recovery_target_action = 'promote'` from the start."
        ),
        fr=(
            "Le serveur est encore en mode restauration : la base est en lecture "
            "seule. Une fois la cible atteinte, il se met EN PAUSE, car "
            "`recovery_target_action` vaut `pause` par défaut. Reprends la main avec "
            "`select pg_wal_replay_resume()`, ou demande "
            "`recovery_target_action = 'promote'` dès le départ."
        ),
    )


def test_la_grappe_a_change_de_timeline(db1) -> None:
    """La trace du geste, et non de son résultat.

    Une restauration menée à son terme promeut la grappe, et une promotion
    incrémente la timeline. C'est ce qui distingue une base restaurée d'une
    table recréée à la main, laquelle laisserait la grappe en timeline 1 tout
    en satisfaisant tous les contrôles portant sur les données.
    """
    timeline = int(_psql(db1, "select timeline_id from pg_control_checkpoint()"))
    assert timeline > 1, message(
        en=(
            f"The cluster is on timeline {timeline}: it has never been restored and "
            "promoted. A completed recovery increments the timeline. If the data is "
            "back without the timeline moving, the table was recreated rather than "
            "recovered, and the backup remains unproven."
        ),
        fr=(
            f"La grappe est en timeline {timeline} : elle n'a jamais été restaurée "
            "puis promue. Une restauration menée à son terme incrémente la timeline. "
            "Si les données sont revenues sans que la timeline bouge, la table a été "
            "recréée et non récupérée, et la sauvegarde reste non prouvée."
        ),
    )


# ── Les données sont revenues, et au bon instant ────────────────────────────


def test_la_table_est_revenue_avec_toutes_ses_lignes(db1) -> None:
    """Le test central : le compte de lignes dit où la restauration s'est arrêtée."""
    existe = _psql(
        db1,
        f"select count(*) from pg_tables "
        f"where schemaname = '{SCHEMA}' and tablename = '{TABLE}'",
        BASE,
    )
    assert existe == "1", message(
        en=(
            f"{SCHEMA}.{TABLE} does not exist. Either nothing has been restored, or "
            "the recovery replayed ALL the WAL and therefore replayed the DROP TABLE. "
            "`recovery_target_time` is what stops it before the incident."
        ),
        fr=(
            f"{SCHEMA}.{TABLE} n'existe pas. Soit rien n'a été restauré, soit la "
            "restauration a rejoué TOUS les WAL et donc rejoué le DROP TABLE. "
            "`recovery_target_time` est ce qui l'arrête avant l'incident."
        ),
    )

    lignes = int(_psql(db1, f"select count(*) from {SCHEMA}.{TABLE}", BASE))
    assert lignes == LIGNES_ATTENDUES, message(
        en=(
            f"{SCHEMA}.{TABLE} holds {lignes} rows, expected {LIGNES_ATTENDUES}. The "
            "count says where the recovery stopped: 5 means it stopped at the physical "
            "backup, whose row was inserted afterwards and lives only in the logs; 0 "
            "means it replayed everything, DROP TABLE included. Only the noted instant "
            f"gives {LIGNES_ATTENDUES}."
        ),
        fr=(
            f"{SCHEMA}.{TABLE} porte {lignes} lignes, attendu {LIGNES_ATTENDUES}. Le "
            "compte dit où la restauration s'est arrêtée : 5 veut dire qu'elle s'est "
            "arrêtée à la sauvegarde physique, dont la ligne suivante a été insérée "
            "après et ne vit que dans les journaux ; 0 veut dire qu'elle a tout "
            "rejoué, DROP TABLE compris. Seul l'instant noté en rend "
            f"{LIGNES_ATTENDUES}."
        ),
    )


def test_la_derniere_ligne_avant_l_incident_est_la(db1) -> None:
    """Celle qui n'existe que dans les journaux, nommée et non comptée.

    Un compte juste pourrait venir de six lignes quelconques. Celle-ci a été
    insérée APRÈS la sauvegarde physique : sa présence prouve que les journaux
    ont été rejoués, et pas seulement la copie restaurée.
    """
    presente = _psql(
        db1,
        f"select count(*) from {SCHEMA}.{TABLE} where nom = '{TEMOIN}'",
        BASE,
    )
    assert presente == "1", message(
        en=(
            f"The row named {TEMOIN!r} is missing. It was inserted AFTER the physical "
            "backup, so it exists only in the archived WAL: restoring the copy alone "
            "does not bring it back. Its absence means the logs were not replayed up "
            "to the noted instant."
        ),
        fr=(
            f"La ligne nommée « {TEMOIN} » est absente. Elle a été insérée APRÈS la "
            "sauvegarde physique, donc elle n'existe que dans les WAL archivés : "
            "restaurer la copie seule ne la ramène pas. Son absence veut dire que les "
            "journaux n'ont pas été rejoués jusqu'à l'instant noté."
        ),
    )


def test_la_base_accepte_de_nouveau_les_ecritures(db1) -> None:
    """Une base restaurée mais en lecture seule n'a pas remis le service.

    Contrôlé par une écriture RÉELLE, immédiatement défaite : `pg_is_in_recovery`
    dit l'état du serveur, pas celui de la base, et un `default_transaction_read_only`
    laissé en place passerait le premier test en échouant celui-ci.
    """
    _exiger_hors_restauration(db1)

    r = db1.run(
        "sudo -u postgres psql -X -At -d %s -c %s",
        BASE,
        f"begin; insert into {SCHEMA}.{TABLE} (nom) values ('controle ecriture'); rollback;",
    )
    assert r.rc == 0, message(
        en=(
            "The database refuses a write:\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "The service is not back. A paused recovery, or a read-only transaction "
            "default, keeps the database unusable even though the data is there."
        ),
        fr=(
            "La base refuse une écriture :\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "Le service n'est pas rétabli. Une restauration en pause, ou un défaut de "
            "transaction en lecture seule, laisse la base inutilisable alors que les "
            "données sont là."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-08-restaurer-pitr` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-08-restaurer-pitr` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_compte_les_lignes_restaurees(db1) -> None:
    attendu = _psql(db1, f"select count(*) from {SCHEMA}.{TABLE}", BASE)
    ecrit = _valeur(db1, "lignes_restaurees")
    assert ecrit == attendu, message(
        en=(
            f"lignes_restaurees = {ecrit!r} in the report, but the table holds "
            f"{attendu!r}."
        ),
        fr=(
            f"lignes_restaurees = {ecrit!r} dans le rapport, alors que la table en "
            f"porte {attendu!r}."
        ),
    )


def test_le_rapport_dit_la_timeline(db1) -> None:
    attendu = _psql(db1, "select timeline_id from pg_control_checkpoint()")
    ecrit = _valeur(db1, "timeline_apres_restauration")
    assert ecrit == attendu, message(
        en=(
            f"timeline_apres_restauration = {ecrit!r} in the report, but the cluster "
            f"answers {attendu!r}. `select timeline_id from pg_control_checkpoint()` "
            "gives it."
        ),
        fr=(
            f"timeline_apres_restauration = {ecrit!r} dans le rapport, alors que la "
            f"grappe répond {attendu!r}. `select timeline_id from "
            "pg_control_checkpoint()` le donne."
        ),
    )


def test_le_rapport_dit_l_etat_de_restauration(db1) -> None:
    attendu = _psql(db1, "select pg_is_in_recovery()")
    ecrit = _valeur(db1, "serveur_en_recovery").lower()
    assert ecrit == attendu, message(
        en=(
            f"serveur_en_recovery = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. `select pg_is_in_recovery()` gives it, in one letter."
        ),
        fr=(
            f"serveur_en_recovery = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. `select pg_is_in_recovery()` le donne, en une "
            "lettre."
        ),
    )
