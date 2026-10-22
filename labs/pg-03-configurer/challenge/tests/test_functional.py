"""pg-03-configurer : ce que le serveur en marche répond vraiment.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc une
instance dont le collecteur de journaux est actif et dont RIEN d'autre n'est
réglé : pas de seuil de requête lente, pas de trace de connexion, un préfixe
muet, `max_connections` à sa valeur d'usine, et un rapport non rempli.

LE PIÈGE QUE CE LAB FAIT RENCONTRER

Un rechargement réussit TOUJOURS. `pg_reload_conf()` rend `t`, `systemctl
reload` sort en 0, et aucun des deux ne signale qu'un paramètre est resté sans
effet parce qu'il exigeait un redémarrage. Les tests ne lisent donc jamais un
fichier de configuration pour les paramètres rechargeables : ils lisent
`pg_settings`, c'est-à-dire ce avec quoi le serveur TOURNE. Écrire la bonne
valeur au bon endroit sans recharger ne passe pas, et c'est le sujet du lab.

Pour `max_connections`, à l'inverse, l'état demandé est « écrit mais pas
appliqué » : le test contrôle les deux faces, la valeur que les FICHIERS
déclarent (`pg_file_settings`) et celle en SERVICE (`pg_settings`), plus le
drapeau `pending_restart` qui est la seule chose qui dise qu'un paramètre
attend.

CE QUE LES TESTS N'INTERROGENT JAMAIS

Par quel chemin l'apprenant a posé les paramètres. `ALTER SYSTEM`, une édition
de `postgresql.conf` ou un fichier inclus donnent le même résultat, et les
trois passent. On note l'état du serveur, pas la méthode.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-configuration.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de configuration de l'instance."
TEMOIN = "temoin-pg-03"

SEUIL_LENT_MS = "250"
MAX_CONN_ATTENDU = "200"
MAX_CONN_EN_SERVICE = "100"
JETONS_PREFIXE = ("%m", "%p", "%u", "%d")


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str) -> str:
    """Une valeur lue sur le serveur EN MARCHE, par la socket et le peer."""
    r = db1.run("sudo -u postgres psql -X -At -d postgres -c %s", sql)
    assert r.rc == 0, message(
        en=f"psql failed: {r.stderr.strip() or r.stdout.strip()}. Is the server running?",
        fr=f"psql a échoué : {r.stderr.strip() or r.stdout.strip()}. Le serveur tourne-t-il ?",
    )
    return r.stdout.strip()


def _en_service(db1, nom: str) -> str:
    """La valeur avec laquelle le serveur tourne, et non celle d'un fichier."""
    return _psql(db1, f"select setting from pg_settings where name = '{nom}'")


def _dans_les_fichiers(db1, nom: str) -> str:
    """Ce que les fichiers DÉCLARENT, dernière occurrence gagnante.

    `pg_settings` ne sert à rien ici : pour un paramètre en attente, il garde
    la valeur en service. Et quand un paramètre est écrit deux fois (dans
    `postgresql.conf` puis dans `postgresql.auto.conf`), c'est la dernière lue
    qui s'applique, d'où le tri sur `seqno`.
    """
    return _psql(
        db1,
        "select setting from pg_file_settings "
        f"where name = '{nom}' order by seqno desc limit 1",
    )


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-03-configurer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-03-configurer` te le rend.",
    )
    return f.content_string


def _valeur(db1, cle: str) -> str:
    """La valeur que l'apprenant a écrite pour une clé du rapport.

    Les lignes de commentaire sont écartées : l'en-tête du rapport cite le
    marqueur à remplacer, et un test qui lirait le fichier entier le trouverait
    là, donc conclurait que rien n'a été rempli.
    """
    for ligne in _rapport(db1).splitlines():
        if ligne.strip().startswith("#") or "=" not in ligne:
            continue
        nom, _, valeur = ligne.partition("=")
        if nom.strip() == cle:
            return valeur.strip()
    return ""


# ── Personne n'a été coupé ───────────────────────────────────────────────────


def _exiger_aucun_redemarrage(db1) -> None:
    """La session témoin du setup doit avoir survécu.

    C'est la seule preuve côté serveur qu'aucun redémarrage n'a eu lieu : un
    `systemctl restart` la tue, et tous les paramètres seraient alors justes
    pour la mauvaise raison.

    POURQUOI CE N'EST PAS UN TEST À PART

    Il le fut, et il était VERT sur l'état de départ : c'est le setup qui ouvre
    la session témoin, donc elle est là avant que l'apprenant touche à quoi que
    ce soit. Un test vert avant tout travail ne mesure rien, il énonce une
    hypothèse du setup, et le pilote du catalogue l'a refusé. Ne pas redémarrer
    n'est pas un travail à accomplir : c'est une CONTRAINTE sur le travail. Sa
    place est donc dans l'assertion qu'elle garde, et non dans un test à elle.
    """
    vivantes = _psql(
        db1,
        "select count(*) from pg_stat_activity "
        f"where application_name = '{TEMOIN}'",
    )
    assert vivantes != "0", message(
        en=(
            f"The witness session '{TEMOIN}' is gone: the server was restarted. "
            "This lab asks for the parameters to be applied WITHOUT cutting a "
            "single session. `dsoxlab reset pg-03-configurer` puts the starting "
            "state back, witness session included."
        ),
        fr=(
            f"La session témoin « {TEMOIN} » a disparu : le serveur a été "
            "redémarré. Ce lab demande d'appliquer les paramètres SANS couper "
            "une seule session. `dsoxlab reset pg-03-configurer` remet l'état "
            "de départ, session témoin comprise."
        ),
    )


# ── Les paramètres rechargeables : effectifs, pas seulement écrits ───────────


def test_seuil_de_requete_lente_effectif(db1):
    valeur = _en_service(db1, "log_min_duration_statement")
    assert valeur == SEUIL_LENT_MS, message(
        en=(
            f"The running server answers log_min_duration_statement = {valeur!r}, "
            f"expected {SEUIL_LENT_MS!r} (milliseconds). Writing the value into a "
            "file is not enough: the server must have reread it "
            "(`select pg_reload_conf()`). A reload never says a parameter stayed "
            "without effect."
        ),
        fr=(
            f"Le serveur en marche répond log_min_duration_statement = {valeur!r}, "
            f"attendu {SEUIL_LENT_MS!r} (en millisecondes). Écrire la valeur dans "
            "un fichier ne suffit pas : le serveur doit l'avoir relue "
            "(`select pg_reload_conf()`). Un rechargement ne dit jamais qu'un "
            "paramètre est resté sans effet."
        ),
    )


def test_journalisation_des_connexions_effective(db1):
    """Toute valeur qui trace quelque chose est acceptée.

    PostgreSQL 18 a transformé `log_connections` d'un booléen en une liste
    d'aspects à journaliser (`receipt`, `authentication`, `all`…). Exiger
    littéralement « on » reviendrait à noter une version du serveur plutôt
    qu'une capacité : le test refuse donc ce qui ne trace RIEN, et rien
    d'autre.
    """
    valeur = _en_service(db1, "log_connections")
    inactif = valeur.strip().lower() in ("", "off", "false", "no", "0")
    assert not inactif, message(
        en=(
            f"The running server answers log_connections = {valeur!r}: nothing is "
            "logged on connection. Enable it, then reload. Any value that logs "
            "something is accepted (PostgreSQL 18 takes a list of aspects)."
        ),
        fr=(
            f"Le serveur en marche répond log_connections = {valeur!r} : rien "
            "n'est journalisé à la connexion. Active-le, puis recharge. Toute "
            "valeur qui journalise quelque chose est acceptée (PostgreSQL 18 "
            "accepte une liste d'aspects)."
        ),
    )


def test_prefixe_de_ligne_identifie_la_trace(db1):
    """Un journal sans quand, ni qui, ni où ne sert à personne."""
    prefixe = _en_service(db1, "log_line_prefix")
    manquants = [jeton for jeton in JETONS_PREFIXE if jeton not in prefixe]
    assert not manquants, message(
        en=(
            f"log_line_prefix = {prefixe!r} on the running server, missing "
            f"{', '.join(manquants)}. A log line must say when (%m), which process "
            "(%p), and who on which database (%u, %d), otherwise two incidents "
            "cannot be told apart."
        ),
        fr=(
            f"log_line_prefix = {prefixe!r} sur le serveur en marche, il manque "
            f"{', '.join(manquants)}. Une ligne de journal doit dire quand (%m), "
            "quel processus (%p), et qui sur quelle base (%u, %d), sinon deux "
            "incidents ne se distinguent pas."
        ),
    )


# ── Le paramètre qui attend, et qui doit attendre ───────────────────────────


def test_max_connections_est_ecrit_dans_les_fichiers(db1):
    declare = _dans_les_fichiers(db1, "max_connections")
    assert declare == MAX_CONN_ATTENDU, message(
        en=(
            f"The configuration files declare max_connections = {declare!r}, "
            f"expected {MAX_CONN_ATTENDU!r}. `ALTER SYSTEM SET max_connections = "
            f"{MAX_CONN_ATTENDU}` writes it; editing postgresql.conf works too. "
            "`pg_file_settings` is the view that shows what the FILES say."
        ),
        fr=(
            f"Les fichiers de configuration déclarent max_connections = {declare!r}, "
            f"attendu {MAX_CONN_ATTENDU!r}. `ALTER SYSTEM SET max_connections = "
            f"{MAX_CONN_ATTENDU}` l'écrit ; éditer postgresql.conf marche aussi. "
            "`pg_file_settings` est la vue qui montre ce que les FICHIERS disent."
        ),
    )


def test_max_connections_attend_encore_son_redemarrage(db1):
    """Écrit, pas appliqué : l'état normal d'un paramètre `postmaster`.

    Deux faces à contrôler, et aucune ne suffit seule. La valeur en service
    doit être l'ancienne, ce qui prouve que le serveur n'a pas redémarré ; et
    `pending_restart` doit être vrai, ce qui prouve que le serveur a bien RELU
    les fichiers. Un apprenant qui écrit la valeur sans recharger échoue au
    second contrôle, et c'est exactement ce qu'aucun message de rechargement
    ne lui aurait dit.
    """
    _exiger_aucun_redemarrage(db1)

    en_service = _en_service(db1, "max_connections")
    assert en_service == MAX_CONN_EN_SERVICE, message(
        en=(
            f"The server runs with max_connections = {en_service!r}, expected it to "
            f"still be {MAX_CONN_EN_SERVICE!r}. This parameter only takes effect at "
            "the next start, and the lab forbids restarting: the restart window is "
            "tonight."
        ),
        fr=(
            f"Le serveur tourne avec max_connections = {en_service!r}, on attendait "
            f"qu'il soit encore à {MAX_CONN_EN_SERVICE!r}. Ce paramètre ne prend "
            "effet qu'au prochain démarrage, et le lab interdit de redémarrer : la "
            "fenêtre est prévue cette nuit."
        ),
    )

    en_attente = _psql(
        db1,
        "select pending_restart from pg_settings where name = 'max_connections'",
    )
    assert en_attente == "t", message(
        en=(
            "pg_settings says max_connections is NOT pending a restart. The value is "
            "in a file but the server has not reread it: reload "
            "(`select pg_reload_conf()`), then check with `select name from "
            "pg_settings where pending_restart`."
        ),
        fr=(
            "`pg_settings` dit que max_connections n'est PAS en attente de "
            "redémarrage. La valeur est dans un fichier mais le serveur ne l'a pas "
            "relue : recharge (`select pg_reload_conf()`), puis contrôle avec "
            "`select name from pg_settings where pending_restart`."
        ),
    )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1):
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-03-configurer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-03-configurer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_la_valeur_en_service(db1):
    attendu = _en_service(db1, "max_connections")
    ecrit = _valeur(db1, "max_connections_effectif")
    assert ecrit == attendu, message(
        en=(
            f"max_connections_effectif = {ecrit!r} in the report, but the server "
            f"answers {attendu!r}. Read it with `show max_connections`."
        ),
        fr=(
            f"max_connections_effectif = {ecrit!r} dans le rapport, alors que le "
            f"serveur répond {attendu!r}. Lis-la avec `show max_connections`."
        ),
    )


def test_le_rapport_dit_la_valeur_en_attente(db1):
    """Elle ne se lit pas où l'on croit, et c'est le sujet de la question.

    `pg_settings.setting` garde la valeur en service pour un paramètre en
    attente : un apprenant qui la lit là écrira 100 aux deux lignes du rapport,
    et découvrira qu'il existe une autre vue.
    """
    attendu = _dans_les_fichiers(db1, "max_connections")
    ecrit = _valeur(db1, "max_connections_en_attente")
    assert ecrit == attendu, message(
        en=(
            f"max_connections_en_attente = {ecrit!r} in the report, but the files "
            f"declare {attendu!r}. `pg_settings` will not tell you: for a pending "
            "parameter it keeps the value in service. `pg_file_settings` shows what "
            "the files say."
        ),
        fr=(
            f"max_connections_en_attente = {ecrit!r} dans le rapport, alors que les "
            f"fichiers déclarent {attendu!r}. `pg_settings` ne te le dira pas : pour "
            "un paramètre en attente, il garde la valeur en service. "
            "`pg_file_settings` montre ce que les fichiers disent."
        ),
    )


def test_le_rapport_compte_ce_qui_attend(db1):
    attendu = _psql(db1, "select count(*) from pg_settings where pending_restart")
    ecrit = _valeur(db1, "nb_parametres_en_attente")
    assert ecrit == attendu, message(
        en=(
            f"nb_parametres_en_attente = {ecrit!r} in the report, but the server "
            f"counts {attendu!r}. Read it with `select count(*) from pg_settings "
            "where pending_restart`."
        ),
        fr=(
            f"nb_parametres_en_attente = {ecrit!r} dans le rapport, alors que le "
            f"serveur en compte {attendu!r}. Lis-le avec `select count(*) from "
            "pg_settings where pending_restart`."
        ),
    )
