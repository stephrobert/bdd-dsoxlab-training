"""pg-07-archiver : des journaux réellement partis, et une copie vérifiée.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup efface donc, à
chaque passage, le répertoire d'archive ET la sauvegarde physique, et remet
`archive_mode` à `off` dans le fichier comme dans `postgresql.auto.conf`. Sans
cela, ce qu'un passage précédent a produit rendrait trois tests verts sans
travail.

CE QUI EST NOTÉ, ET POURQUOI CE N'EST PAS LA CONFIGURATION

Parce que la configuration peut être juste et l'archivage ne rien produire.
PostgreSQL n'archive un segment que lorsqu'il est COMPLET : sur une base peu
active, `archive_mode = on`, une `archive_command` correcte et un répertoire
accessible donnent zéro fichier pendant des heures. Celui qui s'arrête à
`SHOW archive_mode` croit son archivage en place alors que rien n'est parti.

Les tests exigent donc le résultat : des fichiers présents, un compteur qui a
bougé, et aucun échec enregistré. Le dernier point compte autant que les deux
autres, car un échec d'archivage ne remonte nulle part ailleurs que dans
`pg_stat_archiver` et le journal du serveur.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
MAJEURE = "18"
RAPPORT = "/home/student/rapport-archivage.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport d'archivage et de sauvegarde physique."

ARCHIVES = "/var/lib/postgresql/wal_archive"
BASEBACKUP = "/var/lib/postgresql/backups/base"
VERIFYBACKUP = f"/usr/lib/postgresql/{MAJEURE}/bin/pg_verifybackup"
VERDICT_ATTENDU = "backup successfully verified"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str) -> str:
    r = db1.run("sudo -u postgres psql -X -At -d postgres -c %s", sql)
    assert r.rc == 0, message(
        en=f"psql failed: {r.stderr.strip() or r.stdout.strip()}",
        fr=f"psql a échoué : {r.stderr.strip() or r.stdout.strip()}",
    )
    return r.stdout.strip()


@pytest.fixture(scope="module")
def verification(db1):
    """Le verdict de `pg_verifybackup` sur la sauvegarde, pris une fois.

    Partagé entre le test de la sauvegarde et celui du rapport : l'outil lit
    toute la copie, et le jouer deux fois doublerait la durée du lab sans rien
    prouver de plus.
    """
    return db1.run("sudo -u postgres %s %s", VERIFYBACKUP, BASEBACKUP)


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-07-archiver` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-07-archiver` te le rend.",
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


# ── L'archivage : réglé, et sûr ─────────────────────────────────────────────


def test_le_repertoire_d_archive_est_pose_et_accessible(db1) -> None:
    """Un répertoire que postgres ne peut pas écrire fait échouer chaque
    archivage, et l'échec ne remonte que dans `pg_stat_archiver`."""
    d = db1.file(ARCHIVES)
    assert d.exists and d.is_directory, message(
        en=f"{ARCHIVES} does not exist: archiving has nowhere to write.",
        fr=f"{ARCHIVES} n'existe pas : l'archivage n'a nulle part où écrire.",
    )
    assert d.user == "postgres", message(
        en=(
            f"{ARCHIVES} belongs to {d.user}, expected postgres. The archive command "
            "runs as the server's account: every archiving attempt would fail, and "
            "the failure shows up nowhere but in pg_stat_archiver."
        ),
        fr=(
            f"{ARCHIVES} appartient à {d.user}, attendu postgres. La commande "
            "d'archivage s'exécute sous le compte du serveur : chaque tentative "
            "échouerait, et l'échec ne se voit nulle part ailleurs que dans "
            "pg_stat_archiver."
        ),
    )


def test_l_archivage_est_en_service_et_sa_commande_est_sure(db1) -> None:
    """Deux faits distincts : il tourne, et il n'écrase rien.

    `archive_mode` est de contexte `postmaster` : un rechargement réussit sans
    l'appliquer. On lit donc la valeur EN SERVICE, pas un fichier.
    """
    mode = _psql(db1, "show archive_mode")
    assert mode in ("on", "always"), message(
        en=(
            f"The running server answers archive_mode = {mode!r}: nothing is being "
            "archived. This is a postmaster-context parameter, so writing it is not "
            "enough: the server must be RESTARTED. A reload succeeds without applying "
            "it, and says nothing."
        ),
        fr=(
            f"Le serveur en marche répond archive_mode = {mode!r} : rien n'est "
            "archivé. C'est un paramètre de contexte postmaster, donc l'écrire ne "
            "suffit pas : le serveur doit être REDÉMARRÉ. Un rechargement réussit "
            "sans l'appliquer, et ne dit rien."
        ),
    )

    commande = _psql(db1, "show archive_command")
    manquants = [jeton for jeton in ("%p", "%f") if jeton not in commande]
    assert not manquants, message(
        en=(
            f"archive_command = {commande!r}, missing {', '.join(manquants)}. `%p` is "
            "the source segment's full path and `%f` its file name: without both, the "
            "command cannot know what to copy where."
        ),
        fr=(
            f"archive_command = {commande!r}, il manque {', '.join(manquants)}. `%p` "
            "est le chemin complet du segment source et `%f` son nom de fichier : "
            "sans les deux, la commande ne peut pas savoir quoi copier où."
        ),
    )
    # Deux formes acceptées, parce que les deux refusent d'ecraser : le
    # `test ! -f` que recommande la documentation, et le `cp -n` qui fait la
    # meme chose en un mot.
    protege = ("test ! -f" in commande) or ("cp -n" in commande) or ("--no-clobber" in commande)
    assert protege, message(
        en=(
            f"archive_command = {commande!r} would OVERWRITE an already archived "
            "segment. That silently breaks the chain a recovery walks back through. "
            "Guard the copy with `test ! -f <archive>/%f &&`, as the official "
            "documentation recommends, or use `cp -n`."
        ),
        fr=(
            f"archive_command = {commande!r} ÉCRASERAIT un segment déjà archivé. Cela "
            "casse en silence la chaîne qu'une restauration remonte. Protège la copie "
            "par `test ! -f <archive>/%f &&`, comme le recommande la documentation "
            "officielle, ou emploie `cp -n`."
        ),
    )


def test_des_journaux_sont_reellement_partis(db1) -> None:
    """Le seul test qui prouve que l'archivage fonctionne.

    L'archivage ne se déclenche qu'à segment COMPLET : une configuration juste
    sur une base peu active ne produit rien. `pg_switch_wal()` clôt le segment
    courant et le livre à l'archivage, et c'est le geste qui manque à tous ceux
    qui croient leur archivage en panne.
    """
    archives = db1.run("find %s -type f -name '0*'", ARCHIVES)
    fichiers = [x for x in archives.stdout.split() if x]
    compteur = _psql(db1, "select archived_count from pg_stat_archiver")
    echec = _psql(db1, "select coalesce(last_failed_wal, '') from pg_stat_archiver")

    assert not echec, message(
        en=(
            f"pg_stat_archiver reports a failure on {echec}. The archive command did "
            "not work: run it by hand as postgres to see why. It is almost always the "
            "directory's permissions."
        ),
        fr=(
            f"pg_stat_archiver signale un échec sur {echec}. La commande d'archivage "
            "n'a pas fonctionné : joue-la à la main en postgres pour voir pourquoi. "
            "C'est presque toujours les droits du répertoire."
        ),
    )
    assert compteur != "0", message(
        en=(
            "pg_stat_archiver counts 0 archived segments. Archiving only fires when a "
            "segment is COMPLETE: on a quiet database, a correct configuration "
            "produces nothing. `select pg_switch_wal()` closes the current segment and "
            "hands it to archiving."
        ),
        fr=(
            "pg_stat_archiver compte 0 segment archivé. L'archivage ne se déclenche "
            "qu'à segment COMPLET : sur une base peu active, une configuration juste "
            "ne produit rien. `select pg_switch_wal()` clôt le segment courant et le "
            "livre à l'archivage."
        ),
    )
    assert fichiers, message(
        en=(
            f"The counter says {compteur} segments archived, yet {ARCHIVES} holds no "
            "segment file. The command reports success without writing where it "
            "should: check the destination path it uses."
        ),
        fr=(
            f"Le compteur annonce {compteur} segments archivés, et pourtant {ARCHIVES} "
            "ne contient aucun fichier de segment. La commande rend un succès sans "
            "écrire où il faut : contrôle le chemin de destination qu'elle emploie."
        ),
    )


# ── La sauvegarde physique : prise, et vérifiée ─────────────────────────────


def test_la_sauvegarde_physique_est_valide(db1, verification) -> None:
    """Une sauvegarde physique non vérifiée ne vaut pas mieux qu'un dump non
    restauré. `pg_verifybackup` compare le manifeste aux fichiers réels."""
    d = db1.file(BASEBACKUP)
    assert d.exists and d.is_directory, message(
        en=(
            f"{BASEBACKUP} does not exist. `sudo -u postgres pg_basebackup -D "
            f"{BASEBACKUP} -Fp` takes it over the local socket, which pg_hba.conf "
            "already allows for replication."
        ),
        fr=(
            f"{BASEBACKUP} n'existe pas. `sudo -u postgres pg_basebackup -D "
            f"{BASEBACKUP} -Fp` la prend par la socket locale, que pg_hba.conf "
            "autorise déjà en replication."
        ),
    )
    assert verification.rc == 0, message(
        en=(
            "pg_verifybackup refuses the backup:\n"
            f"{(verification.stderr or verification.stdout).strip()[:400]}\n"
            "It detects missing, corrupted or modified files. A backup it refuses "
            "will not restore."
        ),
        fr=(
            "pg_verifybackup refuse la sauvegarde :\n"
            f"{(verification.stderr or verification.stdout).strip()[:400]}\n"
            "Il détecte les fichiers manquants, corrompus ou modifiés. Une sauvegarde "
            "qu'il refuse ne se restaurera pas."
        ),
    )


# ── Le rapport : édité, et confronté aux outils ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-07-archiver` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-07-archiver` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_le_mode_en_service(db1) -> None:
    attendu = _psql(db1, "show archive_mode")
    ecrit = _valeur(db1, "archive_mode_en_service")
    assert ecrit == attendu, message(
        en=(
            f"archive_mode_en_service = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. `show archive_mode` gives the value IN SERVICE, not a "
            "file's."
        ),
        fr=(
            f"archive_mode_en_service = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. `show archive_mode` donne la valeur EN SERVICE, non "
            "celle d'un fichier."
        ),
    )


def test_le_rapport_compte_les_segments_archives(db1) -> None:
    attendu = _psql(db1, "select archived_count from pg_stat_archiver")
    ecrit = _valeur(db1, "nb_wal_archives")
    assert ecrit == attendu, message(
        en=(
            f"nb_wal_archives = {ecrit!r} in the report, but pg_stat_archiver counts "
            f"{attendu!r}. The counter keeps moving: read it at the end of your work."
        ),
        fr=(
            f"nb_wal_archives = {ecrit!r} dans le rapport, alors que pg_stat_archiver "
            f"en compte {attendu!r}. Le compteur continue d'avancer : lis-le à la fin "
            "de ton travail."
        ),
    )


def test_le_rapport_recopie_le_verdict_de_l_outil(db1, verification) -> None:
    """Recopié, et non deviné : il faut avoir lancé l'outil."""
    ecrit = _valeur(db1, "verdict_verifybackup").strip().strip('"').lower()
    assert ecrit == VERDICT_ATTENDU, message(
        en=(
            f"verdict_verifybackup = {ecrit!r} in the report, expected "
            f"{VERDICT_ATTENDU!r}. That is what the tool prints, and it must be run to "
            f"be known: {VERIFYBACKUP} {BASEBACKUP}"
        ),
        fr=(
            f"verdict_verifybackup = {ecrit!r} dans le rapport, attendu "
            f"« {VERDICT_ATTENDU} ». C'est ce que l'outil affiche, et il faut l'avoir "
            f"lancé pour le savoir : {VERIFYBACKUP} {BASEBACKUP}"
        ),
    )
