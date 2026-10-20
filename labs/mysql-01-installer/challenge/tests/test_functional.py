"""mysql-01-installer : ce que la machine écoute vraiment, et d'où vient le serveur.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse une machine
VIERGE de tout serveur de base de données : il purge MySQL et MariaDB, efface
les données, la configuration, le dépôt d'Oracle et sa clé, et oublie les
réponses debconf d'un passage précédent. Aucun test ne peut donc passer sans
travail.

CE QUI EST NOTÉ, ET POURQUOI CE N'EST PAS UN FICHIER

L'écoute RÉELLE, relevée par `ss`, et ce que le serveur EN MARCHE déclare. Un
fichier de configuration juste et un port ouvert coexistent très bien, et c'est
exactement le cas que ce lab fait rencontrer.

LE PIÈGE À DEUX ÉTAGES

Les paquets d'Oracle ne posent AUCUNE ligne `bind-address`, pas même
commentée, et la valeur par défaut de la variable est `*`. À la fin d'un
`apt install`, le serveur écoute donc sur toutes les interfaces, sur deux
ports : 3306 et 33060.

Et `bind-address` NE RESTREINT PAS le 33060 : le protocole X a sa propre
variable, `mysqlx-bind-address`. Un apprenant qui pose la première seule voit
son `SELECT @@bind_address` répondre `127.0.0.1` et laisse la seconde porte
ouverte. Les tests contrôlent donc les deux ports séparément, et leurs messages
nomment celui qui manque.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-installation.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport d'installation de MySQL."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
MAJEURE_ATTENDUE = "8.4"
PORTS = {"3306": "protocole classique", "33060": "protocole X"}
LOCALES = ("127.0.0.1", "::1", "[::1]")


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _mysql(db1, sql: str):
    """Une valeur lue sur le serveur, par la SOCKET Unix.

    Par la socket et non par TCP, et ce n'est pas un détail : en MySQL, le
    compte `labadmin@localhost` désigne la socket. Un `-h 127.0.0.1` viserait
    `labadmin@127.0.0.1`, qui est un AUTRE compte, et que le lab ne demande
    pas de créer.

    Le mot de passe passe par `MYSQL_PWD` et non sur la ligne de commande :
    une ligne de commande se lit dans `ps`.
    """
    return db1.run(
        "env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql
    )


def _valeur_serveur(db1, expression: str) -> str:
    r = _mysql(db1, f"select {expression}")
    assert r.rc == 0, message(
        en=(
            f"Cannot query the server as `{ADMIN}`: "
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "The dedicated account must exist with the password the brief gives."
        ),
        fr=(
            f"Impossible d'interroger le serveur en `{ADMIN}` : "
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "Le compte dédié doit exister avec le mot de passe que la consigne "
            "donne."
        ),
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-01-installer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-01-installer` te le rend.",
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


# ── Le serveur : présent, en service, et de la bonne provenance ─────────────


def test_le_service_tourne_et_revient_au_demarrage(db1) -> None:
    """Une base qui ne revient pas après un redémarrage n'est pas en service."""
    service = db1.service("mysql")
    assert service.is_running, message(
        en=(
            "The `mysql` service is not running. If `systemctl status mysql` says "
            "the unit does not exist, MySQL is not installed; if it failed to start, "
            "its log names the reason (`journalctl -u mysql`)."
        ),
        fr=(
            "Le service `mysql` ne tourne pas. Si `systemctl status mysql` dit que "
            "l'unité n'existe pas, MySQL n'est pas installé ; s'il a échoué au "
            "démarrage, son journal en nomme la raison (`journalctl -u mysql`)."
        ),
    )
    assert service.is_enabled, message(
        en=(
            "The `mysql` service is running but not enabled at boot: the database "
            "would not come back after a reboot. `systemctl enable mysql`."
        ),
        fr=(
            "Le service `mysql` tourne mais n'est pas activé au démarrage : la base "
            "ne reviendrait pas après un redémarrage. `systemctl enable mysql`."
        ),
    )


def test_le_serveur_vient_du_depot_oracle_en_8_4(db1) -> None:
    """MariaDB porte des noms voisins : la présence ne dit pas la provenance.

    `apt install mysql-server` sur une Debian sans le dépôt d'Oracle installe
    MariaDB. Le test contrôle donc le paquet ET la source, pas seulement qu'un
    serveur réponde.
    """
    paquet = db1.run("dpkg-query -W -f '${Status}' mysql-community-server")
    assert "install ok installed" in paquet.stdout, message(
        en=(
            "The `mysql-community-server` package is not installed. If a server "
            "answers anyway, it is MariaDB, which Debian's repository ships under "
            "similar names: that is not what the brief asks for."
        ),
        fr=(
            "Le paquet `mysql-community-server` n'est pas installé. Si un serveur "
            "répond quand même, c'est MariaDB, que le dépôt de Debian livre sous des "
            "noms voisins : ce n'est pas ce que la consigne demande."
        ),
    )

    sources = db1.run("grep -rl repo.mysql.com /etc/apt/sources.list.d/ /etc/apt/sources.list")
    assert sources.rc == 0 and sources.stdout.strip(), message(
        en=(
            "No APT source points at `repo.mysql.com`: the package does not come from "
            "Oracle's repository. Declare it, with Oracle's signing key."
        ),
        fr=(
            "Aucune source APT ne pointe sur `repo.mysql.com` : le paquet ne vient "
            "pas du dépôt d'Oracle. Déclare-le, avec la clé de signature d'Oracle."
        ),
    )

    version = _valeur_serveur(db1, "@@version")
    assert version.startswith(MAJEURE_ATTENDUE), message(
        en=(
            f"The server answers version {version!r}, expected a {MAJEURE_ATTENDUE} "
            "release. That is the long-term support branch, and the one the brief "
            "asks for."
        ),
        fr=(
            f"Le serveur répond la version {version!r}, on attendait une "
            f"{MAJEURE_ATTENDUE}. C'est la branche au support long, et celle que la "
            "consigne demande."
        ),
    )


# ── L'écoute : ce que la machine fait, et non ce qu'un fichier déclare ──────


def test_aucun_des_deux_ports_n_ecoute_sur_le_reseau(db1) -> None:
    """LE test du lab, et il porte sur les DEUX ports séparément.

    Le second est le piège : `bind-address` ne restreint pas le 33060. Un
    message qui dirait seulement « un port écoute sur le réseau » laisserait
    l'apprenant chercher le mauvais réglage, donc chaque port est nommé avec sa
    variable.
    """
    variables = {"3306": "bind-address", "33060": "mysqlx-bind-address"}
    for port, protocole in PORTS.items():
        r = db1.run("ss -H -ltn sport = :%s", port)
        lignes = [ligne.split() for ligne in r.stdout.splitlines() if ligne.split()]
        assert lignes, message(
            en=(
                f"Nothing listens on port {port} ({protocole}). The server must serve "
                "both of its protocols: a missing one is not a closed one, it is a "
                "server that did not start properly."
            ),
            fr=(
                f"Rien n'écoute sur le port {port} ({protocole}). Le serveur doit "
                "servir ses deux protocoles : un port absent n'est pas un port fermé, "
                "c'est un serveur qui n'a pas démarré correctement."
            ),
        )
        adresses = [ligne[3].rsplit(":", 1)[0] for ligne in lignes]
        ouvertes = [a for a in adresses if a not in LOCALES]
        assert not ouvertes, message(
            en=(
                f"Port {port} ({protocole}) listens on {', '.join(ouvertes)}, not on "
                f"the loopback only. Close it with `{variables[port]}`, and mind that "
                "it is NOT the same variable as the other port's: `bind-address` does "
                "not restrict 33060. These variables do not change at runtime, the "
                "service must be restarted."
            ),
            fr=(
                f"Le port {port} ({protocole}) écoute sur {', '.join(ouvertes)}, et "
                f"non sur la seule boucle locale. Ferme-le par `{variables[port]}`, "
                "et retiens que ce n'est PAS la même variable que celle de l'autre "
                "port : `bind-address` ne restreint pas le 33060. Ces variables ne se "
                "changent pas à chaud, le service doit être redémarré."
            ),
        )


def test_le_serveur_declare_les_deux_variables_sur_la_boucle_locale(db1) -> None:
    """Le complément de `ss`, et non son doublon.

    `ss` dit ce que la machine écoute maintenant ; ces variables disent ce que
    le serveur APPLIQUE. Les deux peuvent diverger le temps qu'un redémarrage
    n'a pas eu lieu, et c'est précisément ce que ce test attrape : une
    configuration écrite mais pas appliquée.
    """
    for expression in ("@@bind_address", "@@mysqlx_bind_address"):
        valeur = _valeur_serveur(db1, expression)
        assert valeur in LOCALES, message(
            en=(
                f"The running server answers {expression} = {valeur!r}, expected "
                "127.0.0.1. A value written in a file but not applied is not a "
                "restriction: these variables need a restart, and `ss` and the server "
                "disagree until it happens."
            ),
            fr=(
                f"Le serveur en marche répond {expression} = {valeur!r}, attendu "
                "127.0.0.1. Une valeur écrite dans un fichier mais non appliquée "
                "n'est pas une restriction : ces variables exigent un redémarrage, "
                "et `ss` et le serveur se contredisent jusque-là."
            ),
        )


# ── Le compte dédié ─────────────────────────────────────────────────────────


def test_un_compte_d_administration_dedie_existe(db1) -> None:
    """Ce que les autres tests ne disent pas : le compte peut déléguer.

    L'EXISTENCE du compte est déjà prouvée, et mieux qu'ici : toutes les
    requêtes de ce fichier passent par lui, donc un compte absent ou dont le
    mot de passe ne marche pas fait échouer les autres tests avant celui-ci. Un
    compte déclaré mais injoignable n'est pas un compte, et c'est l'usage qui
    le dit, pas le catalogue.

    Reste ce que l'usage ne dit pas : qu'il a le droit d'ACCORDER des droits,
    ce qui est l'objet d'un compte d'administration, et qu'il n'est pas `root`.
    Ces deux points se lisent, et c'est pour eux que ce test existe.
    """
    # Bilingue bien qu'AUCUN apprenant ne la lise : elle n'échoue que si un
    # auteur met `root` dans la constante. Le garde-fou `instructor audit`, lui,
    # ne sait pas distinguer une invariante d'auteur d'un message d'apprenant,
    # et un compteur qui reste à « 1 reste » apprend à ne plus être lu.
    assert ADMIN != "root", message(
        en=(
            f"The lab asks to work as {ADMIN!r}: it must not ask for root. This is "
            "an authoring invariant, not something you did."
        ),
        fr=(
            f"Le lab demande de travailler en {ADMIN!r} : il ne doit pas demander "
            "root. C'est une invariante d'écriture du lab, pas une faute de ta part."
        ),
    )
    # `mysql.user.Grant_priv` et NON `information_schema.user_privileges`.
    #
    # Mesuré sur MySQL 8.4 dans un conteneur jetable : « GRANT OPTION »
    # n'existe PAS comme `privilege_type` dans cette vue. Un test qui l'y
    # cherche compte toujours zéro, donc il échoue sur un serveur
    # correctement configuré, et c'est ce qu'il faisait.
    #
    # Deux sources discriminent vraiment, vérifiées sur un compte avec et un
    # compte sans : `mysql.user.Grant_priv` rend Y contre N, et
    # `user_privileges.is_grantable` rend YES contre NO. On prend la première :
    # une seule ligne, pas de guillemets à échapper, et un nom de colonne que
    # le message peut citer.
    droit = _valeur_serveur(
        db1,
        f"Grant_priv from mysql.user where user = '{ADMIN}' and host = 'localhost'",
    )
    assert droit == "Y", message(
        en=(
            f"`mysql.user.Grant_priv` answers {droit!r} for `{ADMIN}@localhost`, "
            "expected 'Y'. The account cannot delegate rights, which is what an "
            "administration account is for: add `with grant option` to the GRANT. "
            "An empty answer means the account does not exist under that exact host."
        ),
        fr=(
            f"`mysql.user.Grant_priv` répond {droit!r} pour `{ADMIN}@localhost`, "
            "attendu « Y ». Le compte ne peut pas déléguer de droits, ce qui est "
            "l'objet d'un compte d'administration : ajoute `with grant option` au "
            "GRANT. Une réponse vide veut dire que le compte n'existe pas sous cet "
            "hôte exact."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-01-installer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-01-installer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_la_version_du_serveur(db1) -> None:
    attendu = _valeur_serveur(db1, "@@version")
    ecrit = _valeur(db1, "version_du_serveur")
    assert ecrit == attendu, message(
        en=(
            f"version_du_serveur = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. `select @@version` gives it, in full."
        ),
        fr=(
            f"version_du_serveur = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. `select @@version` la donne, en entier."
        ),
    )


def test_le_rapport_dit_les_deux_adresses_d_ecoute(db1) -> None:
    """Deux clés, deux variables, et c'est tout l'intérêt de la question.

    Un apprenant qui croit `bind-address` suffisante recopie la même valeur aux
    deux lignes. Le test les compare séparément à ce que le serveur répond,
    donc l'écart se voit.
    """
    for cle, expression in (
        ("bind_address_en_service", "@@bind_address"),
        ("mysqlx_bind_address_en_service", "@@mysqlx_bind_address"),
    ):
        attendu = _valeur_serveur(db1, expression)
        ecrit = _valeur(db1, cle)
        assert ecrit == attendu, message(
            en=(
                f"{cle} = {ecrit!r} in the report, but the server answers {attendu!r} "
                f"for {expression}. These are two DIFFERENT variables: read each one."
            ),
            fr=(
                f"{cle} = {ecrit!r} dans le rapport, alors que le serveur répond "
                f"{attendu!r} pour {expression}. Ce sont deux variables DIFFÉRENTES : "
                "lis chacune."
            ),
        )
