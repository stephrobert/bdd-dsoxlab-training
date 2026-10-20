"""mysql-epreuve-n1 : dix tâches notées, et l'état du serveur pour seul juge.

LE BARÈME EST CONTRACTUEL

dsoxlab note PAR TEST. Dix tests, donc dix points chacun, et l'énoncé annonce
exactement dix tâches à dix points. Ajouter un test ici sans ajouter une tâche
à l'énoncé décalerait tout le barème sans que personne le voie : le validateur
de contenu de dsoxlab refuse justement cet écart.

L'ORDRE DES TESTS N'EST PAS LIBRE

Le test des réglages REDÉMARRE le serveur, et celui de l'écoute lit l'état
d'après ce redémarrage. Ils sont donc écrits dans cet ordre. Le second reste
juste joué seul, `bind_address` n'étant pas dynamique : il ne peut pas avoir
changé depuis.

AUCUN TEST NE DÉTRUIT CE QUE LES AUTRES MESURENT

La preuve du moindre privilège était le piège de ce fichier. Vérifier qu'un
compte ne peut pas `DROP TABLE` en essayant un `DROP TABLE` détruit la base
quand le candidat a trop donné : le test passerait au rouge, et les deux
suivants aussi, pour une raison que personne ne rattacherait à la bonne cause.
Les sondes sont donc toutes inoffensives en cas de succès : lire `mysql.user`,
créer une base qu'on retire ensuite.

CE QUE L'ÉPREUVE NE RÉEXPLIQUE PAS

Les pièges du niveau. Un rôle accordé n'est pas actif, un compte `@localhost`
refuse une connexion TCP, `mysqldump` omet les procédures stockées, et
`bind_address` ne se persiste pas avec `SET PERSIST`. Les cinq labs les ont
enseignés ; les messages d'échec d'ici les rappellent sans les détailler, parce
qu'une épreuve qui redonne la leçon ne mesure plus rien.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-epreuve.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de l'epreuve du niveau 1 MySQL."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BASE = "appli"
RESTAUREE = "appli_restauree"
DUMP = "/home/student/sauvegardes/appli.sql"
TABLES = ("clients", "commandes")
PROCEDURE = "chiffre_affaires"

LAXISTE = "app_tout"
ROLE = "role_appli"
SERVICE = "appli_svc"
MDP_SERVICE = "Svc!Appli2026"
HOTE_SERVICE = "127.0.0.1"

DROITS_ATTENDUS = "DELETE,INSERT,SELECT,UPDATE"
MAX_CONNEXIONS = "200"
LONG_QUERY_TIME = "1"

# Les marqueurs des sondes, hors de portée des données de l'épreuve.
CLIENT_SONDE = "sonde-epreuve"
BASE_SONDE = "epreuve_intrus"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _sql(db1, sql: str) -> str:
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _sql_brut(db1, sql: str):
    return db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)


def _service(db1, sql: str, mode_tls: str = "REQUIRED"):
    """Une commande jouée AVEC le compte de service, par le réseau.

    Par le réseau et non par la socket : l'épreuve exige un compte joignable
    depuis `127.0.0.1`, et c'est là que se joue le piège de l'hôte.
    """
    return db1.run(
        "env MYSQL_PWD=%s mysql -h %s -u %s --ssl-mode=%s -N -B -e %s",
        MDP_SERVICE,
        HOTE_SERVICE,
        SERVICE,
        mode_tls,
        sql,
    )


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-epreuve-n1` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-epreuve-n1` te le rend.",
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


def _meme_nombre(ecrit: str, attendu: str) -> bool:
    try:
        return abs(float(ecrit.replace(",", ".")) - float(attendu)) < 1e-9
    except (TypeError, ValueError):
        return ecrit.strip() == attendu.strip()


# ── 1. Le compte tout-puissant n'existe plus ────────────────────────────────


def test_le_compte_tout_puissant_a_disparu(db1) -> None:
    restants = _sql(
        db1, f"select concat(user, '@', host) from mysql.user where user = '{LAXISTE}'"
    )
    assert not restants, message(
        en=(
            f"The `{LAXISTE}` account still exists ({restants!r}). An account declared "
            "`@'%'` with `GRANT ALL PRIVILEGES ON *.*` makes every other task of this "
            "exam pointless: it can read the password hashes and drop any database, "
            "from anywhere."
        ),
        fr=(
            f"Le compte `{LAXISTE}` existe encore ({restants!r}). Un compte déclaré "
            "`@'%'` avec `GRANT ALL PRIVILEGES ON *.*` rend toutes les autres tâches "
            "de cette épreuve inutiles : il peut lire les empreintes de mots de passe "
            "et supprimer n'importe quelle base, depuis n'importe où."
        ),
    )


# ── 2. Un rôle porte les droits, et rien de plus ───────────────────────────


def test_le_role_existe_et_porte_exactement_les_quatre_droits(db1) -> None:
    etat = _sql(db1, f"select account_locked from mysql.user where user = '{ROLE}'")
    assert etat, message(
        en=f"The `{ROLE}` role does not exist.",
        fr=f"Le rôle `{ROLE}` n'existe pas.",
    )
    assert etat == "Y", message(
        en=(
            f"`{ROLE}` exists but is not locked: it is an ACCOUNT, not a role. In "
            "MySQL both live in `mysql.user`, and `account_locked` is what tells them "
            "apart."
        ),
        fr=(
            f"`{ROLE}` existe mais n'est pas verrouillé : c'est un COMPTE, pas un "
            "rôle. En MySQL les deux vivent dans `mysql.user`, et c'est "
            "`account_locked` qui les distingue."
        ),
    )
    droits = _sql(
        db1,
        "select coalesce(group_concat(privilege_type order by privilege_type), '') "
        "from information_schema.schema_privileges "
        f"where grantee = \"'{ROLE}'@'%'\" and table_schema = '{BASE}'",
    )
    assert droits == DROITS_ATTENDUS, message(
        en=(
            f"`{ROLE}` holds {droits!r} on `{BASE}`, expected exactly "
            f"{DROITS_ATTENDUS}. A `GRANT ALL` would hand the surplus to every account "
            "receiving the role, and a global grant does not show up here at all."
        ),
        fr=(
            f"`{ROLE}` détient {droits!r} sur `{BASE}`, attendu exactement "
            f"{DROITS_ATTENDUS}. Un `GRANT ALL` donnerait le surplus à tout compte qui "
            "reçoit le rôle, et un privilège global n'apparaît pas ici du tout."
        ),
    )


# ── 3. Le compte de service se connecte, et son rôle est actif ─────────────


def test_le_compte_de_service_se_connecte_avec_son_role_actif(db1) -> None:
    r = _service(db1, "select current_role()")
    assert r.rc == 0, message(
        en=(
            f"The `{SERVICE}` account cannot connect over the network from "
            f"{HOTE_SERVICE}:\n{(r.stderr or r.stdout).strip()[:300]}\n"
            "Mind the declared host, and mind the password: the brief imposes it "
            "because a test has to use it."
        ),
        fr=(
            f"Le compte `{SERVICE}` ne peut pas se connecter par le réseau depuis "
            f"{HOTE_SERVICE} :\n{(r.stderr or r.stdout).strip()[:300]}\n"
            "Attention à l'hôte déclaré, et au mot de passe : l'énoncé l'impose parce "
            "qu'un test doit s'en servir."
        ),
    )
    actif = r.stdout.strip()
    assert actif and actif.upper() != "NONE", message(
        en=(
            f"The account connects but `CURRENT_ROLE()` answers {actif!r}: the role is "
            "granted and not active, so the account holds no right at all despite the "
            "`GRANT`."
        ),
        fr=(
            f"Le compte se connecte mais `CURRENT_ROLE()` répond {actif!r} : le rôle "
            "est accordé et non actif, donc le compte n'a aucun droit malgré le "
            "`GRANT`."
        ),
    )
    assert ROLE in actif, message(
        en=f"`CURRENT_ROLE()` answers {actif!r}: the active role is not `{ROLE}`.",
        fr=f"`CURRENT_ROLE()` répond {actif!r} : le rôle actif n'est pas `{ROLE}`.",
    )


# ── 4. Le clair est refusé, le chiffré aboutit ─────────────────────────────


def test_le_clair_est_refuse_et_le_chiffre_aboutit(db1) -> None:
    """Un seul test, parce que c'est un seul comportement.

    « Le chiffré aboutit » serait vert sans aucune exigence de TLS, MySQL
    chiffrant par défaut quand le client le demande. Et « le clair est refusé »
    serait vert sur un compte qui n'existe pas. Les deux membres se gardent
    donc l'un l'autre.

    Le CODE d'erreur n'est pas comparé : mesuré, il dépend du greffon du
    compte. L'exiger reviendrait à noter un greffon.
    """
    clair = _service(db1, "select 1", mode_tls="DISABLED")
    assert clair.rc != 0, message(
        en=(
            f"An UNENCRYPTED connection as `{SERVICE}` was accepted. MySQL sets that "
            "requirement on the ACCOUNT, not in a file."
        ),
        fr=(
            f"Une connexion NON CHIFFRÉE en `{SERVICE}` a été acceptée. MySQL pose "
            "cette exigence sur le COMPTE et non dans un fichier."
        ),
    )
    chiffre = _service(db1, "select 1", mode_tls="REQUIRED")
    assert chiffre.rc == 0 and chiffre.stdout.strip() == "1", message(
        en=(
            f"An ENCRYPTED connection as `{SERVICE}` does not work either:\n"
            f"{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refusing cleartext must not refuse everything."
        ),
        fr=(
            f"Une connexion CHIFFRÉE en `{SERVICE}` ne fonctionne pas non plus :\n"
            f"{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refuser le clair ne doit pas tout refuser."
        ),
    )


# ── 5. Le moindre privilège, prouvé par des sondes inoffensives ────────────


def test_le_compte_de_service_lit_ecrit_et_rien_de_plus(db1) -> None:
    """Les sondes de refus sont inoffensives SI elles réussissent.

    Un `DROP TABLE` d'essai détruirait la base que deux autres tests
    comparent, et leur échec ne se rattacherait plus à sa cause. On lit donc
    `mysql.user`, et on tente de créer une base qu'on retire ensuite.
    """
    lecture = _service(db1, f"select count(*) from {BASE}.clients")
    assert lecture.rc == 0, message(
        en=(
            f"`{SERVICE}` cannot read `{BASE}.clients`:\n"
            f"{(lecture.stderr or lecture.stdout).strip()[:300]}"
        ),
        fr=(
            f"`{SERVICE}` ne peut pas lire `{BASE}.clients` :\n"
            f"{(lecture.stderr or lecture.stdout).strip()[:300]}"
        ),
    )

    try:
        ecriture = _service(
            db1, f"insert into {BASE}.clients (nom) values ('{CLIENT_SONDE}')"
        )
        assert ecriture.rc == 0, message(
            en=(
                f"`{SERVICE}` cannot write into `{BASE}.clients`, and the application "
                f"needs to: the role must hold {DROITS_ATTENDUS}.\n"
                f"{(ecriture.stderr or ecriture.stdout).strip()[:300]}"
            ),
            fr=(
                f"`{SERVICE}` ne peut pas écrire dans `{BASE}.clients`, et "
                f"l'application en a besoin : le rôle doit détenir "
                f"{DROITS_ATTENDUS}.\n"
                f"{(ecriture.stderr or ecriture.stdout).strip()[:300]}"
            ),
        )
    finally:
        _sql_brut(db1, f"delete from {BASE}.clients where nom = '{CLIENT_SONDE}'")

    mots_de_passe = _service(db1, "select count(*) from mysql.user")
    assert mots_de_passe.rc != 0, message(
        en=(
            f"`{SERVICE}` was able to read `mysql.user`, which holds the password "
            "hashes. That is what a global `GRANT ... ON *.*` gives."
        ),
        fr=(
            f"`{SERVICE}` a pu lire `mysql.user`, qui porte les empreintes des mots "
            "de passe. C'est ce que donne un `GRANT ... ON *.*` global."
        ),
    )

    try:
        creation = _service(db1, f"create database {BASE_SONDE}")
        assert creation.rc != 0, message(
            en=(
                f"`{SERVICE}` was able to CREATE a database. A service account scoped "
                f"to `{BASE}` must not be able to: it was granted more than the role, "
                "or the role holds a global privilege."
            ),
            fr=(
                f"`{SERVICE}` a pu CRÉER une base. Un compte de service borné à "
                f"`{BASE}` ne doit pas le pouvoir : il a reçu plus que le rôle, ou le "
                "rôle porte un privilège global."
            ),
        )
    finally:
        _sql_brut(db1, f"drop database if exists {BASE_SONDE}")


# ── 6. Les réglages survivent à un redémarrage ─────────────────────────────


def test_les_reglages_demandes_survivent_a_un_redemarrage(db1) -> None:
    """Le test qui redémarre, et il exige les valeurs DEMANDÉES.

    Pas « rien n'a changé » : les valeurs par défaut survivent très bien à un
    redémarrage, donc une égalité avant/après ne mesurerait qu'une tautologie.
    La capture d'avant sert au MESSAGE, « 200 avant, 151 après » diagnostiquant
    mieux que « 151 est faux ».
    """
    avant = {
        "max_connections": _sql(db1, "select @@max_connections"),
        "slow_query_log": _sql(db1, "select @@slow_query_log"),
        "long_query_time": _sql(db1, "select @@long_query_time"),
    }

    # Contrôlé AVANT le redémarrage : une configuration refusée laisserait
    # l'instance éteinte, et le message parlerait alors d'un serveur
    # injoignable plutôt que de sa cause.
    valide = db1.run("mysqld --validate-config")
    assert valide.rc == 0, message(
        en=(
            "`mysqld --validate-config` refuses the configuration:\n"
            f"{(valide.stderr or valide.stdout).strip()[:400]}\n"
            "Restarting now would leave the instance down."
        ),
        fr=(
            "`mysqld --validate-config` refuse la configuration :\n"
            f"{(valide.stderr or valide.stdout).strip()[:400]}\n"
            "Redémarrer maintenant laisserait l'instance éteinte."
        ),
    )

    relance = db1.run("systemctl restart mysql")
    assert relance.rc == 0, message(
        en=(
            "The server refused to restart:\n"
            f"{(relance.stderr or relance.stdout).strip()[:300]}\n"
            "`journalctl -u mysql` names the reason."
        ),
        fr=(
            "Le serveur a refusé de redémarrer :\n"
            f"{(relance.stderr or relance.stdout).strip()[:300]}\n"
            "`journalctl -u mysql` en nomme la raison."
        ),
    )

    apres = {
        "max_connections": _sql(db1, "select @@max_connections"),
        "slow_query_log": _sql(db1, "select @@slow_query_log"),
        "long_query_time": _sql(db1, "select @@long_query_time"),
    }

    assert apres["max_connections"] == MAX_CONNEXIONS, message(
        en=(
            f"After the restart, `max_connections` is {apres['max_connections']!r} "
            f"where {MAX_CONNEXIONS} was asked (it was "
            f"{avant['max_connections']!r} before). A `SET GLOBAL` is lost at restart."
        ),
        fr=(
            f"Après le redémarrage, `max_connections` vaut "
            f"{apres['max_connections']!r} là où {MAX_CONNEXIONS} était demandé (il "
            f"valait {avant['max_connections']!r} avant). Un `SET GLOBAL` est perdu au "
            "redémarrage."
        ),
    )
    assert apres["slow_query_log"] == "1", message(
        en=(
            f"After the restart, the slow query log is off "
            f"({apres['slow_query_log']!r}, it was {avant['slow_query_log']!r} "
            "before)."
        ),
        fr=(
            f"Après le redémarrage, le journal des requêtes lentes est éteint "
            f"({apres['slow_query_log']!r}, il valait {avant['slow_query_log']!r} "
            "avant)."
        ),
    )
    assert _meme_nombre(apres["long_query_time"], LONG_QUERY_TIME), message(
        en=(
            f"After the restart, `long_query_time` is {apres['long_query_time']!r} "
            f"where {LONG_QUERY_TIME} was asked (it was "
            f"{avant['long_query_time']!r} before)."
        ),
        fr=(
            f"Après le redémarrage, `long_query_time` vaut "
            f"{apres['long_query_time']!r} là où {LONG_QUERY_TIME} était demandé (il "
            f"valait {avant['long_query_time']!r} avant)."
        ),
    )


# ── 7. L'instance n'écoute que sa boucle locale ────────────────────────────


def test_l_instance_n_ecoute_que_sa_boucle_locale(db1) -> None:
    """Lu après le redémarrage du test précédent, et ce n'est pas fragile.

    `bind_address` n'est pas une variable dynamique : elle ne peut pas avoir
    changé depuis, et ce test reste juste joué seul.
    """
    for variable in ("bind_address", "mysqlx_bind_address"):
        valeur = _sql(db1, f"select @@{variable}")
        assert valeur == "127.0.0.1", message(
            en=(
                f"`{variable}` is {valeur!r}: the instance still accepts connections "
                "from elsewhere. That setting is NOT dynamic, so `SET PERSIST` cannot "
                "place it: it lives in a configuration file read at startup."
            ),
            fr=(
                f"`{variable}` vaut {valeur!r} : l'instance accepte encore des "
                "connexions venues d'ailleurs. Ce réglage n'est PAS dynamique, donc "
                "`SET PERSIST` ne peut pas le poser : il vit dans un fichier de "
                "configuration lu au démarrage."
            ),
        )


# ── 8. La sauvegarde est complète ──────────────────────────────────────────


def test_la_sauvegarde_porte_la_procedure_stockee(db1) -> None:
    f = db1.file(DUMP)
    assert f.exists, message(
        en=f"{DUMP} does not exist: there is still no backup of `{BASE}`.",
        fr=f"{DUMP} n'existe pas : il n'y a toujours aucune sauvegarde de `{BASE}`.",
    )
    contenu = f.content_string
    haut = contenu.upper()
    assert "CREATE TABLE" in haut and "INSERT INTO" in haut, message(
        en=(
            f"{DUMP} does not carry both the schema and the rows: a backup missing "
            "either of them restores into something unusable."
        ),
        fr=(
            f"{DUMP} ne porte pas à la fois le schéma et les lignes : une sauvegarde "
            "à qui l'un des deux manque se restaure en quelque chose d'inutilisable."
        ),
    )
    porte_la_procedure = any(
        "PROCEDURE" in ligne.upper() and PROCEDURE in ligne
        for ligne in contenu.splitlines()
    )
    assert porte_la_procedure, message(
        en=(
            f"{DUMP} does not carry the `{PROCEDURE}` stored procedure. The dump "
            "succeeded, the restore will succeed with exit code 0, and the "
            "application will fail on an `ERROR 1305` weeks later. One option fixes "
            "it, and `mysqldump --help` says which."
        ),
        fr=(
            f"{DUMP} ne porte pas la procédure stockée `{PROCEDURE}`. Le dump a "
            "réussi, la restauration réussira avec un code 0, et c'est l'application "
            "qui échouera sur un « ERROR 1305 » des semaines plus tard. Une option y "
            "remédie, et `mysqldump --help` dit laquelle."
        ),
    )


# ── 9. La restauration est utilisable ──────────────────────────────────────


def test_la_base_restauree_est_utilisable(db1) -> None:
    existe = _sql(
        db1,
        "select count(*) from information_schema.schemata "
        f"where schema_name = '{RESTAUREE}'",
    )
    assert existe == "1", message(
        en=(
            f"The `{RESTAUREE}` database does not exist. A backup that has never been "
            "restored is not a backup, it is a file."
        ),
        fr=(
            f"La base `{RESTAUREE}` n'existe pas. Une sauvegarde qu'on n'a jamais "
            "restaurée n'est pas une sauvegarde : c'est un fichier."
        ),
    )
    for table in TABLES:
        origine = _sql(db1, f"select count(*) from {BASE}.{table}")
        copie = _sql_brut(db1, f"select count(*) from {RESTAUREE}.{table}")
        assert copie.rc == 0, message(
            en=(
                f"`{RESTAUREE}.{table}` cannot be read:\n"
                f"{(copie.stderr or copie.stdout).strip()[:300]}"
            ),
            fr=(
                f"`{RESTAUREE}.{table}` ne peut pas être lue :\n"
                f"{(copie.stderr or copie.stdout).strip()[:300]}"
            ),
        )
        assert copie.stdout.strip() == origine, message(
            en=(
                f"`{RESTAUREE}.{table}` holds {copie.stdout.strip()} rows where "
                f"`{BASE}.{table}` holds {origine}."
            ),
            fr=(
                f"`{RESTAUREE}.{table}` porte {copie.stdout.strip()} lignes là où "
                f"`{BASE}.{table}` en porte {origine}."
            ),
        )

    appel = _sql_brut(db1, f"call {RESTAUREE}.{PROCEDURE}()")
    assert appel.rc == 0 and appel.stdout.strip(), message(
        en=(
            f"Calling `{RESTAUREE}.{PROCEDURE}()` fails:\n"
            f"{(appel.stderr or appel.stdout).strip()[:300]}\n"
            "The rows are all there and the procedure is not: that is the failure of "
            "an incomplete dump, and it is graded here because it is the one that "
            "reaches production."
        ),
        fr=(
            f"L'appel de `{RESTAUREE}.{PROCEDURE}()` échoue :\n"
            f"{(appel.stderr or appel.stdout).strip()[:300]}\n"
            "Les lignes sont toutes là et la procédure non : c'est la panne d'un dump "
            "incomplet, et elle est notée ici parce que c'est elle qui arrive en "
            "production."
        ),
    )


# ── 10. Le rapport dit l'état réel ─────────────────────────────────────────


def test_le_rapport_dit_l_etat_reel(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-epreuve-n1` gives it back, and loses your "
            "work on the instance."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-epreuve-n1` te le rend, et perd ton "
            "travail sur l'instance."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )

    attendu_max = _sql(db1, "select @@max_connections")
    ecrit_max = _valeur(db1, "connexions_max_apres_redemarrage")
    assert _meme_nombre(ecrit_max, attendu_max), message(
        en=(
            f"connexions_max_apres_redemarrage = {ecrit_max!r} in the report, but the "
            f"server answers {attendu_max!r}."
        ),
        fr=(
            f"connexions_max_apres_redemarrage = {ecrit_max!r} dans le rapport, alors "
            f"que le serveur répond {attendu_max!r}."
        ),
    )

    session = _service(db1, "select current_role()")
    assert session.rc == 0, message(
        en="The service account cannot connect, so the report cannot be checked.",
        fr="Le compte de service ne peut pas se connecter, donc le rapport n'est pas contrôlable.",
    )
    attendu_role = session.stdout.strip()
    ecrit_role = _valeur(db1, "role_actif_du_compte_de_service")
    assert ecrit_role == attendu_role, message(
        en=(
            f"role_actif_du_compte_de_service = {ecrit_role!r} in the report, but a "
            f"session answers {attendu_role!r}. Copy it as is, backquotes included."
        ),
        fr=(
            f"role_actif_du_compte_de_service = {ecrit_role!r} dans le rapport, alors "
            f"qu'une session répond {attendu_role!r}. Recopie-le tel quel, apostrophes "
            "inverses comprises."
        ),
    )

    attendu_routines = _sql(
        db1,
        "select count(*) from information_schema.routines "
        f"where routine_schema = '{RESTAUREE}'",
    )
    ecrit_routines = _valeur(db1, "procedures_dans_la_base_restauree")
    assert _meme_nombre(ecrit_routines, attendu_routines), message(
        en=(
            f"procedures_dans_la_base_restauree = {ecrit_routines!r} in the report, "
            f"but the catalog counts {attendu_routines!r} for `{RESTAUREE}`."
        ),
        fr=(
            f"procedures_dans_la_base_restauree = {ecrit_routines!r} dans le rapport, "
            f"alors que le catalogue en compte {attendu_routines!r} pour "
            f"`{RESTAUREE}`."
        ),
    )
