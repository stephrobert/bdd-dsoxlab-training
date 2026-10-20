"""mysql-04-securiser : des rôles qui servent, et un canal qu'on exige.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc une
instance sans aucun rôle, sans compte applicatif et sans exigence de TLS, et
il RETIRE à chaque passage les rôles et le compte d'un passage précédent :
sans cela, le travail de la fois d'avant survivrait et quatre tests seraient
verts avant tout travail.

CE QUE LES TESTS NE LISENT JAMAIS

Un `GRANT` dans le catalogue. C'est le piège central du lab : en MySQL, un
rôle accordé n'est PAS actif à la connexion. Le `GRANT` figure au catalogue,
`CURRENT_ROLE()` répond `NONE`, et le compte n'a aucun droit. Mesuré sur
MySQL 8.4 : le moindre `select` échoue alors sur « Access denied ... to
database ».

Les tests se connectent donc avec le compte et regardent ce qu'il peut faire.
C'est la seule façon de distinguer un droit accordé d'un droit effectif.

LES TROIS MESURES QUI ONT DÉCIDÉ LA FORME DES TESTS, prises le 2026-10-20

    compte @localhost, connexion TCP      REFUSEE, et l'erreur nomme
                                          @127.0.0.1, un hote non declare
    REQUIRE SSL + caching_sha2_password   ERROR 2061, « Authentication
                                          requires secure connection »
    REQUIRE SSL + mysql_native_password   ERROR 1045, « Access denied »

La dernière explique pourquoi les tests ne comparent PAS le code d'erreur : il
dépend du greffon du compte, donc l'exiger reviendrait à noter un greffon. Ce
qui compte est que la connexion soit refusée, et que la chiffrée aboutisse.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-securite.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de securisation de l'instance MySQL."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BASE = "appli"
LECTEUR = "app_lecture"
MDP_LECTEUR = "L3cture!2026"
HOTE_LECTEUR = "127.0.0.1"
ROLES = ("role_reader", "role_writer")


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _admin(db1, sql: str) -> str:
    """Une valeur lue avec le compte d'administration, par la socket."""
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _lecteur(db1, sql: str, mode_tls: str = "REQUIRED"):
    """Une commande jouée AVEC le compte applicatif, par le réseau.

    Par le réseau et non par la socket : le lab exige un compte joignable
    depuis `127.0.0.1`, et c'est là que se joue le piège de l'hôte.
    """
    return db1.run(
        "env MYSQL_PWD=%s mysql -h %s -u %s --ssl-mode=%s -N -B -e %s",
        MDP_LECTEUR,
        HOTE_LECTEUR,
        LECTEUR,
        mode_tls,
        sql,
    )


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-04-securiser` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-04-securiser` te le rend.",
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


# ── Les rôles : des porteurs de droits, pas des comptes ─────────────────────


def test_les_deux_roles_existent_et_ne_se_connectent_pas(db1) -> None:
    """Un rôle porte des droits, il ne se connecte pas.

    En MySQL, un rôle EST une ligne de `mysql.user`, comme un compte : ce qui
    l'en distingue est `account_locked`. Un « rôle » créé par un
    `CREATE USER` serait donc un compte, et le lab demande des rôles.
    """
    for role in ROLES:
        etat = _admin(
            db1, f"select account_locked from mysql.user where user = '{role}'"
        )
        assert etat, message(
            en=(
                f"The `{role}` role does not exist. `create role {role}` creates it, "
                "and it carries privileges without being able to log in."
            ),
            fr=(
                f"Le rôle `{role}` n'existe pas. `create role {role}` le crée, et il "
                "porte des privilèges sans pouvoir se connecter."
            ),
        )
        assert etat == "Y", message(
            en=(
                f"`{role}` exists but is not locked: it is an ACCOUNT, not a role. "
                "`create role` locks it; `create user` does not. In MySQL both live in "
                "`mysql.user`, and `account_locked` is what tells them apart."
            ),
            fr=(
                f"`{role}` existe mais n'est pas verrouillé : c'est un COMPTE, pas un "
                "rôle. `create role` le verrouille, `create user` non. En MySQL les "
                "deux vivent dans `mysql.user`, et c'est `account_locked` qui les "
                "distingue."
            ),
        )


def test_le_role_de_lecture_ne_porte_que_la_lecture(db1) -> None:
    """Le moindre privilège, lu sur le rôle lui-même.

    Un `GRANT ALL` sur le rôle donnerait les droits d'écriture au compte qui
    le reçoit, et le lab serait vert sur les tests de lecture tout en ayant
    manqué son objet.
    """
    droits = _admin(
        db1,
        "select coalesce(group_concat(privilege_type order by privilege_type), '') "
        "from information_schema.schema_privileges "
        f"where grantee = \"'role_reader'@'%'\" and table_schema = '{BASE}'",
    )
    assert droits, message(
        en=(
            f"`role_reader` holds no privilege on `{BASE}`. "
            f"`grant select on {BASE}.* to role_reader`."
        ),
        fr=(
            f"`role_reader` n'a aucun privilège sur `{BASE}`. "
            f"`grant select on {BASE}.* to role_reader`."
        ),
    )
    assert droits == "SELECT", message(
        en=(
            f"`role_reader` holds {droits!r} on `{BASE}`, expected SELECT and nothing "
            "else. A reading role that can also write is not a reading role, and the "
            "account receiving it inherits the surplus."
        ),
        fr=(
            f"`role_reader` détient {droits!r} sur `{BASE}`, attendu SELECT et rien "
            "d'autre. Un rôle de lecture qui peut aussi écrire n'est pas un rôle de "
            "lecture, et le compte qui le reçoit hérite du surplus."
        ),
    )


# ── Le compte : joignable, et son rôle ACTIF ────────────────────────────────


def test_le_compte_se_connecte_et_son_role_est_actif(db1) -> None:
    """LE piège du lab, et il ne se voit qu'en se connectant.

    Accorder un rôle ne l'active pas. Le `GRANT` figure au catalogue,
    `CURRENT_ROLE()` répond `NONE`, et le compte n'a aucun droit. Mesuré sur
    MySQL 8.4, le moindre `select` échoue alors sur « Access denied ... to
    database » : rien dans le catalogue ne dit que le rôle dort.
    """
    r = _lecteur(db1, "select current_role()")
    assert r.rc == 0, message(
        en=(
            f"The `{LECTEUR}` account cannot connect over the network from "
            f"{HOTE_LECTEUR}:\n{(r.stderr or r.stdout).strip()[:300]}\n"
            "Mind the host: an account declared `@localhost` refuses a TCP "
            "connection, and the error then names a host you never declared. MySQL "
            "matches the host as the connection presents it."
        ),
        fr=(
            f"Le compte `{LECTEUR}` ne peut pas se connecter par le réseau depuis "
            f"{HOTE_LECTEUR} :\n{(r.stderr or r.stdout).strip()[:300]}\n"
            "Attention à l'hôte : un compte déclaré en `@localhost` refuse une "
            "connexion TCP, et l'erreur nomme alors un hôte que tu n'as pas déclaré. "
            "MySQL apparie l'hôte tel que la connexion le présente."
        ),
    )
    actif = r.stdout.strip()
    assert actif and actif.upper() != "NONE", message(
        en=(
            f"The account connects but `CURRENT_ROLE()` answers {actif!r}: the role is "
            "granted and NOT active, so the account has no rights despite the `GRANT`. "
            f"`set default role all to '{LECTEUR}'@'{HOTE_LECTEUR}'` wakes it. Nothing "
            "in the catalog says a role is asleep."
        ),
        fr=(
            f"Le compte se connecte mais `CURRENT_ROLE()` répond {actif!r} : le rôle "
            "est accordé et NON actif, donc le compte n'a aucun droit malgré le "
            f"`GRANT`. `set default role all to '{LECTEUR}'@'{HOTE_LECTEUR}'` le "
            "réveille. Rien dans le catalogue ne dit qu'un rôle dort."
        ),
    )
    assert "role_reader" in actif, message(
        en=(
            f"`CURRENT_ROLE()` answers {actif!r}: the active role is not the reading "
            "one. The account must receive `role_reader`, and only that."
        ),
        fr=(
            f"`CURRENT_ROLE()` répond {actif!r} : le rôle actif n'est pas celui de "
            "lecture. Le compte doit recevoir `role_reader`, et lui seul."
        ),
    )


# ── Le canal : le clair refusé, le chiffré debout ───────────────────────────


def test_le_clair_est_refuse_et_le_chiffre_aboutit(db1) -> None:
    """Un seul test, parce que c'est un seul comportement.

    « Le chiffré aboutit » serait vert sans aucune exigence de TLS : MySQL
    chiffre par défaut quand le client le demande. Et « le clair est refusé »
    serait vert sur un compte qui n'existe pas. Les deux membres se gardent
    donc l'un l'autre.

    Le CODE d'erreur n'est pas comparé, et c'est mesuré : il dépend du greffon
    du compte. `caching_sha2_password` rend 2061, « Authentication requires
    secure connection », parce que le greffon refuse d'envoyer le mot de passe
    en clair ; `mysql_native_password` rend 1045, « Access denied », parce que
    c'est `REQUIRE SSL` qui tranche. Exiger un code reviendrait à noter un
    greffon.
    """
    clair = _lecteur(db1, "select 1", mode_tls="DISABLED")
    assert clair.rc != 0, message(
        en=(
            f"An UNENCRYPTED connection as `{LECTEUR}` was accepted. MySQL sets that "
            "requirement on the ACCOUNT, not in a file: "
            f"`alter user '{LECTEUR}'@'{HOTE_LECTEUR}' require ssl`."
        ),
        fr=(
            f"Une connexion NON CHIFFRÉE en `{LECTEUR}` a été acceptée. MySQL pose "
            "cette exigence sur le COMPTE et non dans un fichier : "
            f"`alter user '{LECTEUR}'@'{HOTE_LECTEUR}' require ssl`."
        ),
    )

    chiffre = _lecteur(db1, "select 1", mode_tls="REQUIRED")
    assert chiffre.rc == 0 and chiffre.stdout.strip() == "1", message(
        en=(
            f"An ENCRYPTED connection as `{LECTEUR}` does not work either:\n"
            f"{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refusing cleartext must not refuse everything."
        ),
        fr=(
            f"Une connexion CHIFFRÉE en `{LECTEUR}` ne fonctionne pas non plus :\n"
            f"{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refuser le clair ne doit pas tout refuser."
        ),
    )


def test_le_compte_lit_et_ne_fait_que_lire(db1) -> None:
    """Prouvé en essayant, et non en lisant le catalogue.

    Un droit refusé se constate : le compte doit lire les tables de la base
    applicative, échouer sur une écriture, et ne pas voir la base `mysql`, qui
    porte les mots de passe.
    """
    lecture = _lecteur(db1, f"select count(*) from {BASE}.clients")
    assert lecture.rc == 0, message(
        en=(
            f"`{LECTEUR}` cannot read `{BASE}.clients`:\n"
            f"{(lecture.stderr or lecture.stdout).strip()[:300]}\n"
            "If the connection works, the role is probably granted without being "
            "active."
        ),
        fr=(
            f"`{LECTEUR}` ne peut pas lire `{BASE}.clients` :\n"
            f"{(lecture.stderr or lecture.stdout).strip()[:300]}\n"
            "Si la connexion aboutit, le rôle est probablement accordé sans être "
            "actif."
        ),
    )

    ecriture = _lecteur(db1, f"insert into {BASE}.clients (nom) values ('intrus')")
    assert ecriture.rc != 0, message(
        en=(
            f"`{LECTEUR}` was able to INSERT into `{BASE}.clients`. A reading account "
            "must not write: it probably received `role_writer`, or a `GRANT ALL`."
        ),
        fr=(
            f"`{LECTEUR}` a pu INSÉRER dans `{BASE}.clients`. Un compte de lecture ne "
            "doit pas écrire : il a probablement reçu `role_writer`, ou un "
            "`GRANT ALL`."
        ),
    )

    mots_de_passe = _lecteur(db1, "select count(*) from mysql.user")
    assert mots_de_passe.rc != 0, message(
        en=(
            f"`{LECTEUR}` was able to read `mysql.user`, which holds the password "
            "hashes. That is what `GRANT ALL PRIVILEGES ON *.*` gives, and it is "
            "exactly what the audit asked to remove."
        ),
        fr=(
            f"`{LECTEUR}` a pu lire `mysql.user`, qui porte les empreintes des mots de "
            "passe. C'est ce que donne un `GRANT ALL PRIVILEGES ON *.*`, et c'est "
            "précisément ce que l'audit demandait de retirer."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-04-securiser` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-04-securiser` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_le_role_actif(db1) -> None:
    r = _lecteur(db1, "select current_role()")
    assert r.rc == 0, message(
        en="The account cannot connect, so the report cannot be checked.",
        fr="Le compte ne peut pas se connecter, donc le rapport n'est pas contrôlable.",
    )
    attendu = r.stdout.strip()
    ecrit = _valeur(db1, "role_actif_a_la_connexion")
    assert ecrit == attendu, message(
        en=(
            f"role_actif_a_la_connexion = {ecrit!r} in the report, but a session "
            f"answers {attendu!r}. Copy it as is, backquotes included."
        ),
        fr=(
            f"role_actif_a_la_connexion = {ecrit!r} dans le rapport, alors qu'une "
            f"session répond {attendu!r}. Recopie-le tel quel, apostrophes inverses "
            "comprises."
        ),
    )


def test_le_rapport_dit_l_exigence_de_tls(db1) -> None:
    attendu = _admin(
        db1,
        f"select ssl_type from mysql.user where user = '{LECTEUR}' "
        f"and host = '{HOTE_LECTEUR}'",
    )
    ecrit = _valeur(db1, "exigence_tls_du_compte")
    assert ecrit.upper() == attendu.upper(), message(
        en=(
            f"exigence_tls_du_compte = {ecrit!r} in the report, but `mysql.user` "
            f"answers {attendu!r}. The `ssl_type` column reports the requirement."
        ),
        fr=(
            f"exigence_tls_du_compte = {ecrit!r} dans le rapport, alors que "
            f"`mysql.user` répond {attendu!r}. La colonne `ssl_type` annonce "
            "l'exigence."
        ),
    )


def test_le_rapport_compte_les_roles(db1) -> None:
    """Un rôle est un compte VERROUILLÉ : c'est ce qui les distingue."""
    attendu = _admin(
        db1, "select count(*) from mysql.user where account_locked = 'Y'"
    )
    ecrit = _valeur(db1, "nb_roles_sans_connexion")
    assert ecrit == attendu, message(
        en=(
            f"nb_roles_sans_connexion = {ecrit!r} in the report, but the server counts "
            f"{attendu!r}. In MySQL a role is a LOCKED account: "
            "`select count(*) from mysql.user where account_locked = 'Y'`."
        ),
        fr=(
            f"nb_roles_sans_connexion = {ecrit!r} dans le rapport, alors que le serveur "
            f"en compte {attendu!r}. En MySQL, un rôle est un compte VERROUILLÉ : "
            "`select count(*) from mysql.user where account_locked = 'Y'`."
        ),
    )
