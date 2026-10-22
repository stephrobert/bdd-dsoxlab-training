"""mysql-02-client-admin : une connexion qui aboutit, et un serveur observable.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc une
instance qui tourne mais sans rien de ce que le lab demande : aucun login path
pour `student`, aucune base applicative, aucun MySQL Shell, et le Performance
Schema ÉTEINT.

Ce dernier point est posé EXPLICITEMENT par le setup, et ce n'est pas un
ornement : `performance_schema` est ACTIF par défaut sur MySQL 8.4. Sans ce
réglage, le test correspondant serait vert avant tout travail, et noterait le
paquet Oracle plutôt que l'apprenant.

CE QUI EST NOTÉ POUR LE LOGIN PATH

Une connexion RÉELLE, jouée en `student`, sans `MYSQL_PWD` dans
l'environnement et avec l'entrée standard fermée. Si quelque chose manque, le
client demande le mot de passe et la commande meurt au lieu de l'inventer.
C'est la même preuve que `pg-02` emploie pour `.pgpass`, et elle vaut mieux
qu'un contrôle de présence de fichier : un `~/.mylogin.cnf` au bon format mais
qui désigne le mauvais hôte existe, et ne connecte rien.

LE PIÈGE D'HÔTE

En MySQL, `@localhost` désigne la SOCKET Unix. Une connexion TCP vers
`127.0.0.1` cherche un compte `@127.0.0.1`, qui est un AUTRE compte. Un login
path qui déclare `--host=127.0.0.1` alors que le compte est en `localhost`
échoue sur un « Access denied » qui ne dit pas pourquoi. Le test exige donc que
`current_user()` réponde le compte attendu, ce qui prouve le chemin employé et
pas seulement qu'une connexion a eu lieu.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-client.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de prise en main du client MySQL."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
PROFIL = "lab"
BASE = "appli"
TABLE = "clients"
LIGNES_MINIMUM = 3
MOTEUR = "InnoDB"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _mysql(db1, sql: str) -> str:
    """Une valeur lue par la socket, avec le compte d'administration.

    Ce chemin-ci ne passe PAS par le login path : les tests ne doivent pas
    dépendre du travail qu'ils notent, sinon un login path manquant ferait
    échouer tous les tests au lieu du seul qui le concerne.
    """
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-02-client-admin` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-02-client-admin` te le rend.",
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


# ── Le login path : prouvé en s'en servant ─────────────────────────────────


def test_un_script_se_connecte_sans_mot_de_passe_tape(db1) -> None:
    """LE test du login path, et il ne regarde pas le fichier.

    Lancé en `student`, sans `MYSQL_PWD` et avec l'entrée standard fermée : si
    quelque chose manque, le client demande le mot de passe et la commande
    meurt au lieu de l'inventer.

    Et il exige que `current_user()` réponde le compte attendu, ce qui prouve
    le CHEMIN employé : un login path qui déclare un hôte alors que le compte
    est en `localhost` connecte autre chose, ou rien.
    """
    r = db1.run(
        "sudo -u student -H env -u MYSQL_PWD mysql --login-path=%s -N -B -e %s < /dev/null",
        PROFIL,
        "select current_user()",
    )
    assert r.rc == 0, message(
        en=(
            f"A connection with `--login-path={PROFIL}` did not work from `student` "
            f"without a password being supplied:\n{(r.stderr or r.stdout).strip()[:300]}\n"
            "`mysql_config_editor set --login-path=lab --user=... --password` stores "
            "it in `~/.mylogin.cnf`. Do not declare a host: without `--host` the "
            f"client goes through the Unix socket, which is what `{ADMIN}@localhost` "
            "means."
        ),
        fr=(
            f"Une connexion avec `--login-path={PROFIL}` n'a pas abouti depuis "
            "`student` sans qu'un mot de passe soit fourni :\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "`mysql_config_editor set --login-path=lab --user=... --password` "
            "l'enregistre dans `~/.mylogin.cnf`. Ne déclare pas d'hôte : sans "
            "`--host`, le client passe par la socket Unix, ce qui est précisément ce "
            f"que `{ADMIN}@localhost` désigne."
        ),
    )
    attendu = f"{ADMIN}@localhost"
    assert r.stdout.strip() == attendu, message(
        en=(
            f"The connection works but `current_user()` answers "
            f"{r.stdout.strip()!r}, expected {attendu!r}. The login path reaches "
            "another account than the one the brief names."
        ),
        fr=(
            f"La connexion aboutit mais `current_user()` répond "
            f"{r.stdout.strip()!r}, attendu {attendu!r}. Le login path atteint un "
            "autre compte que celui que la consigne nomme."
        ),
    )


def test_le_login_path_est_ferme_aux_autres_comptes(db1) -> None:
    """Un fichier d'identifiants lisible par d'autres annule son intérêt.

    `mysql_config_editor` le pose en 0600 de lui-même : ce test attrape celui
    qui a écrit le fichier autrement, à la main ou par un script.
    """
    f = db1.file("/home/student/.mylogin.cnf")
    assert f.exists, message(
        en=(
            "`/home/student/.mylogin.cnf` does not exist: the login path is stored "
            "somewhere else, or nowhere. `mysql_config_editor` writes it there."
        ),
        fr=(
            "`/home/student/.mylogin.cnf` n'existe pas : le login path est rangé "
            "ailleurs, ou nulle part. `mysql_config_editor` l'écrit là."
        ),
    )
    assert f.mode == 0o600, message(
        en=(
            f"`.mylogin.cnf` is in {oct(f.mode)}, expected 0600. A credentials file "
            "other accounts can read defeats its own purpose: it is obfuscated, not "
            "encrypted."
        ),
        fr=(
            f"`.mylogin.cnf` est en {oct(f.mode)}, attendu 0600. Un fichier "
            "d'identifiants que d'autres comptes peuvent lire annule son intérêt : il "
            "est obscurci, pas chiffré."
        ),
    )


# ── Les objets de l'application ────────────────────────────────────────────


def test_la_base_et_la_table_demandees_existent(db1) -> None:
    """Lues dans le catalogue, et non dans un fichier .sql laissé sur le disque."""
    bases = _mysql(db1, "show databases")
    assert BASE in bases.split(), message(
        en=f"The `{BASE}` database does not exist. `create database {BASE}`.",
        fr=f"La base `{BASE}` n'existe pas. `create database {BASE}`.",
    )

    colonnes = _mysql(
        db1,
        "select column_name from information_schema.columns "
        f"where table_schema = '{BASE}' and table_name = '{TABLE}'",
    ).split()
    manquantes = [c for c in ("id", "nom") if c not in colonnes]
    assert colonnes, message(
        en=f"The `{BASE}.{TABLE}` table does not exist.",
        fr=f"La table `{BASE}.{TABLE}` n'existe pas.",
    )
    assert not manquantes, message(
        en=(
            f"`{BASE}.{TABLE}` lacks the column(s) {', '.join(manquantes)}. It carries "
            f"{', '.join(colonnes)}."
        ),
        fr=(
            f"`{BASE}.{TABLE}` n'a pas la ou les colonnes {', '.join(manquantes)}. "
            f"Elle porte {', '.join(colonnes)}."
        ),
    )

    lignes = int(_mysql(db1, f"select count(*) from {BASE}.{TABLE}"))
    assert lignes >= LIGNES_MINIMUM, message(
        en=(
            f"`{BASE}.{TABLE}` holds {lignes} row(s), at least {LIGNES_MINIMUM} are "
            "expected. An empty table proves the DDL, not that anything can be "
            "written."
        ),
        fr=(
            f"`{BASE}.{TABLE}` porte {lignes} ligne(s), on en attend au moins "
            f"{LIGNES_MINIMUM}. Une table vide prouve le DDL, pas qu'on peut y "
            "écrire."
        ),
    )

    moteur = _mysql(
        db1,
        "select engine from information_schema.tables "
        f"where table_schema = '{BASE}' and table_name = '{TABLE}'",
    )
    assert moteur == MOTEUR, message(
        en=(
            f"`{BASE}.{TABLE}` uses the {moteur!r} engine, expected {MOTEUR!r}, which "
            "is the only one with transactions and crash recovery."
        ),
        fr=(
            f"`{BASE}.{TABLE}` emploie le moteur {moteur!r}, attendu {MOTEUR!r}, le "
            "seul qui apporte les transactions et la reprise après panne."
        ),
    )


# ── Le serveur observable ──────────────────────────────────────────────────


def test_le_performance_schema_est_actif(db1) -> None:
    """Une variable de DÉMARRAGE, et c'est tout le piège.

    `set global performance_schema = on` répond « read only variable », et un
    `set persist` l'écrit dans `mysqld-auto.cnf` sans l'appliquer. Le test lit
    donc la valeur EN SERVICE : elle ne vaut `1` que si le serveur a redémarré
    avec le réglage.
    """
    actif = _mysql(db1, "select @@performance_schema")
    assert actif == "1", message(
        en=(
            f"`@@performance_schema` answers {actif!r}: the server runs without it, so "
            "the whole `sys` family of views is silent. It is a STARTUP variable, "
            "read-only once the server is up: `set global` answers an error and `set "
            "persist` writes it without applying it. Put it in a file under "
            "`[mysqld]` and restart."
        ),
        fr=(
            f"`@@performance_schema` répond {actif!r} : le serveur tourne sans lui, "
            "donc toute la famille de vues `sys` est muette. C'est une variable de "
            "DÉMARRAGE, en lecture seule une fois le serveur lancé : `set global` "
            "répond une erreur et `set persist` l'écrit sans l'appliquer. Pose-la "
            "dans un fichier de la section `[mysqld]` et redémarre."
        ),
    )

    # Le rallumer sans que `sys` réponde ne servirait à rien : on éprouve une
    # vue, pas seulement la variable.
    r = db1.run(
        "env MYSQL_PWD=%s mysql -u %s -N -B -e %s",
        MDP_ADMIN,
        ADMIN,
        "select count(*) from sys.session",
    )
    assert r.rc == 0, message(
        en=(
            "`performance_schema` is on but `sys.session` cannot be read:\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "The variable alone is not the point: the views built on it must answer."
        ),
        fr=(
            "`performance_schema` est actif mais `sys.session` ne se lit pas :\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "La variable seule n'est pas le but : les vues bâties dessus doivent "
            "répondre."
        ),
    )


def test_mysql_shell_est_installe_et_joint_l_instance(db1) -> None:
    """Un client installé qui ne se connecte pas n'est pas un client."""
    version = db1.run("mysqlsh --version")
    assert version.rc == 0, message(
        en=(
            "`mysqlsh` is not installed. It lives in the same component of Oracle's "
            "repository as the server: `apt install mysql-shell`, no repository to "
            "add."
        ),
        fr=(
            "`mysqlsh` n'est pas installé. Il vit dans le même composant du dépôt "
            "d'Oracle que le serveur : `apt install mysql-shell`, aucun dépôt à "
            "ajouter."
        ),
    )
    r = db1.run(
        "sudo -u student -H env -u MYSQL_PWD mysqlsh --login-path=%s --sql -e %s < /dev/null",
        PROFIL,
        "select 1",
    )
    assert r.rc == 0, message(
        en=(
            "`mysqlsh` is installed but does not reach the instance:\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "It reads the same login path as the `mysql` client."
        ),
        fr=(
            "`mysqlsh` est installé mais ne joint pas l'instance :\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "Il lit le même login path que le client `mysql`."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-02-client-admin` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-02-client-admin` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_l_etat_du_performance_schema(db1) -> None:
    attendu = _mysql(db1, "select @@performance_schema")
    ecrit = _valeur(db1, "performance_schema_actif")
    assert ecrit == attendu, message(
        en=(
            f"performance_schema_actif = {ecrit!r} in the report, but the server "
            f"answers {attendu!r}. `select @@performance_schema` gives it."
        ),
        fr=(
            f"performance_schema_actif = {ecrit!r} dans le rapport, alors que le "
            f"serveur répond {attendu!r}. `select @@performance_schema` le donne."
        ),
    )


def test_le_rapport_compte_les_tables_et_nomme_le_moteur(db1) -> None:
    attendu_tables = _mysql(
        db1,
        "select count(*) from information_schema.tables "
        f"where table_schema = '{BASE}'",
    )
    ecrit_tables = _valeur(db1, "nb_tables_appli")
    assert ecrit_tables == attendu_tables, message(
        en=(
            f"nb_tables_appli = {ecrit_tables!r} in the report, but the catalog counts "
            f"{attendu_tables!r}. `information_schema.tables` answers it."
        ),
        fr=(
            f"nb_tables_appli = {ecrit_tables!r} dans le rapport, alors que le "
            f"catalogue en compte {attendu_tables!r}. `information_schema.tables` le "
            "donne."
        ),
    )

    attendu_moteur = _mysql(
        db1,
        "select engine from information_schema.tables "
        f"where table_schema = '{BASE}' and table_name = '{TABLE}'",
    )
    ecrit_moteur = _valeur(db1, "moteur_de_la_table_clients")
    assert ecrit_moteur == attendu_moteur, message(
        en=(
            f"moteur_de_la_table_clients = {ecrit_moteur!r} in the report, but the "
            f"catalog answers {attendu_moteur!r}. Case included: copy what the server "
            "says."
        ),
        fr=(
            f"moteur_de_la_table_clients = {ecrit_moteur!r} dans le rapport, alors que "
            f"le catalogue répond {attendu_moteur!r}. Casse comprise : recopie ce que "
            "le serveur dit."
        ),
    )
