"""mysql-07-repliquer : une ligne qui voyage, et deux tables d'état.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc deux
serveurs qui s'ignorent : `gtid_mode` à OFF sur les deux, aucun compte de
réplication, aucun canal, et un réplica inscriptible. Et il DÉFAIT à chaque
passage ce qu'un passage précédent aurait laissé : `reset replica all` efface
le canal ET ses identifiants, les fichiers de configuration ajoutés sont
retirés, et le service redémarre, ce qui ramène `gtid_mode` à son défaut.

CE QUE LES TESTS NE LISENT JAMAIS

`SHOW REPLICA STATUS`. C'est un affichage de quarante colonnes, qu'il faudrait
découper, et dont la forme change entre versions. Les tests lisent les TABLES
du Performance Schema, qui sont des données :

    performance_schema.replication_connection_status   le fil d'entrée
    performance_schema.replication_applier_status      le fil d'application

Les deux comptent, et c'est la panne qu'on ne voit pas : un canal CONNECTÉ qui
n'applique rien laisse le réplica en retard indéfini sans qu'aucune erreur
n'apparaisse à l'écran.

ET SURTOUT, UNE LIGNE QUI VOYAGE

Le test central écrit une ligne sur la source et la cherche sur le réplica.
Aucune table d'état ne remplace cette preuve : une réplication qui annonce
`ON` sans rien transporter existe.

LES TROIS MESURES QUI ONT DÉCIDÉ DE CES TESTS, prises sur MySQL 8.4 le
2026-10-20 avec deux serveurs sur un réseau commun

    gtid_mode OFF -> ON directement   ERROR 1788, et le message nomme le
                                      chemin OFF <-> OFF_PERMISSIVE <->
                                      ON_PERMISSIVE <-> ON, à monter
                                      SIMULTANÉMENT sur tous les serveurs
    canal sans TLS ni cle publique    service_state CONNECTING, erreur 2061,
                                      « Authentication requires secure
                                      connection », reessai toutes les 60 s
    super_read_only = ON              n'empeche PAS l'application : la ligne
                                      arrive en 1 s, applicateur ON, erreur 0

La troisième mesure est celle qui a rendu l'énoncé soluble : sans elle, exiger
à la fois un réplica en lecture seule et une ligne qui arrive aurait pu être
contradictoire. Ce n'est pas le cas, le fil d'application contourne
`super_read_only` par conception.

Le délai d'arrivée a été mesuré cinq fois entre 48 et 67 ms. Le seuil des
tests est à 30 secondes, qui laisse de la marge à une machine virtuelle
chargée sans pour autant complaire à une réplication en panne.
"""

from __future__ import annotations

import time

import pytest

from conftest import lab_host, lab_target_host, message

SOURCE = lab_target_host("db1.lab")
REPLICA = "db2.lab"
RAPPORT = "/home/student/rapport-replication.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de mise en service de la replication."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BASE = "appli"
TABLE = "clients"
COMPTE_REPL = "repl"

# Mesuré entre 48 et 67 ms sur deux conteneurs. Trente secondes laissent de la
# marge à une VM chargée, et ne sauvent pas une réplication arrêtée.
DELAI_ARRIVEE_S = 30


@pytest.fixture(scope="module")
def db1():
    """La source, joue le rôle de `lab_target`."""
    return lab_host(SOURCE)


@pytest.fixture(scope="module")
def db2():
    """Le réplica, joint par l'inventaire et non par une adresse codée."""
    return lab_host(REPLICA)


def _sql(hote, sql: str) -> str:
    r = hote.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _sql_brut(hote, sql: str):
    """Sans exiger le succès : un refus est parfois ce qu'on mesure."""
    return hote.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)


def _etat_connexion(db2) -> tuple[str, str, str]:
    """L'état du fil d'entrée, en données et non en affichage."""
    brut = _sql(
        db2,
        "select service_state, last_error_number, "
        "coalesce(left(last_error_message, 200), '') "
        "from performance_schema.replication_connection_status",
    )
    if not brut:
        return ("", "", "")
    morceaux = brut.split("\t")
    while len(morceaux) < 3:
        morceaux.append("")
    return (morceaux[0], morceaux[1], morceaux[2])


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-07-repliquer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-07-repliquer` te le rend.",
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


# ── GTID : sur les deux serveurs, et pas sur un seul ───────────────────────


def test_gtid_est_actif_sur_les_deux_serveurs(db1, db2) -> None:
    """Les deux, parce que la réplication par position automatique l'exige.

    Mesuré : passer `gtid_mode` de OFF à ON directement rend une `ERROR 1788`
    dont le message nomme le chemin et précise que la valeur doit monter
    SIMULTANÉMENT sur tous les serveurs. Un apprenant qui ne l'active que sur
    la source obtient un canal qui refuse de démarrer.
    """
    for nom, hote in (("source", db1), ("réplica", db2)):
        mode = _sql(hote, "select @@gtid_mode")
        assert mode == "ON", message(
            en=(
                f"`gtid_mode` is {mode!r} on the {nom}, where `ON` is expected. It "
                "cannot be changed in one step: the server answers `ERROR 1788` and "
                "names the path `OFF <-> OFF_PERMISSIVE <-> ON_PERMISSIVE <-> ON`. "
                "And `enforce_gtid_consistency` must be `ON` first, on BOTH servers."
            ),
            fr=(
                f"`gtid_mode` vaut {mode!r} sur le {nom}, là où `ON` est attendu. Il "
                "ne se change pas d'un coup : le serveur répond `ERROR 1788` et "
                "nomme le chemin `OFF <-> OFF_PERMISSIVE <-> ON_PERMISSIVE <-> ON`. "
                "Et `enforce_gtid_consistency` doit valoir `ON` d'abord, sur LES DEUX "
                "serveurs."
            ),
        )
        coherence = _sql(hote, "select @@enforce_gtid_consistency")
        assert coherence in ("ON", "1"), message(
            en=(
                f"`enforce_gtid_consistency` is {coherence!r} on the {nom}. GTID "
                "replication needs it: without it, a statement that cannot be "
                "assigned a single GTID would break the replica silently."
            ),
            fr=(
                f"`enforce_gtid_consistency` vaut {coherence!r} sur le {nom}. La "
                "réplication GTID en a besoin : sans lui, une instruction à laquelle "
                "on ne peut pas attribuer un seul GTID casserait le réplica en "
                "silence."
            ),
        )


# ── Le compte de réplication : ce qu'il peut, et ce qu'il ne doit pas ──────


def test_le_compte_de_replication_ne_peut_que_repliquer(db1) -> None:
    """Le moindre privilège, lu sur le compte lui-même.

    `REPLICATION SLAVE` suffit à un réplica. Un `GRANT ALL` lui donnerait de
    quoi lire les empreintes de mots de passe et supprimer n'importe quelle
    base, depuis le réplica.
    """
    droits = _sql(
        db1,
        "select coalesce(group_concat(privilege_type order by privilege_type), '') "
        "from information_schema.user_privileges "
        f"where grantee like \"'{COMPTE_REPL}'@%\"",
    )
    assert droits, message(
        en=(
            f"The `{COMPTE_REPL}` account holds no global privilege, or does not "
            "exist. A replica connects with an account that holds "
            "`REPLICATION SLAVE`."
        ),
        fr=(
            f"Le compte `{COMPTE_REPL}` n'a aucun privilège global, ou n'existe pas. "
            "Un réplica se connecte avec un compte qui détient "
            "`REPLICATION SLAVE`."
        ),
    )
    assert "REPLICATION SLAVE" in droits, message(
        en=(
            f"`{COMPTE_REPL}` holds {droits!r} and not `REPLICATION SLAVE`, which is "
            "the privilege a replica needs."
        ),
        fr=(
            f"`{COMPTE_REPL}` détient {droits!r} et pas `REPLICATION SLAVE`, qui est "
            "le privilège dont un réplica a besoin."
        ),
    )
    assert "SELECT" not in droits, message(
        en=(
            f"`{COMPTE_REPL}` also holds a GLOBAL `SELECT` ({droits!r}), which "
            "includes the `mysql` database and its password hashes. A replication "
            "account needs `REPLICATION SLAVE` and nothing else."
        ),
        fr=(
            f"`{COMPTE_REPL}` détient aussi un `SELECT` GLOBAL ({droits!r}), qui "
            "inclut la base `mysql` et ses empreintes de mots de passe. Un compte de "
            "réplication a besoin de `REPLICATION SLAVE` et de rien d'autre."
        ),
    )


# ── Les deux fils : celui qui reçoit et celui qui applique ────────────────


def test_le_fil_d_entree_du_replica_est_connecte(db2) -> None:
    """Le piège du greffon, et il ne ressemble pas à ce qu'il est.

    Mesuré : avec `caching_sha2_password`, le défaut de 8.4, un canal sans TLS
    ni clé publique reste en `CONNECTING` avec l'erreur `2061`,
    « Authentication requires secure connection », et il réessaie toutes les 60
    secondes. Ce n'est ni le mot de passe ni les privilèges, et le message ne
    le dit pas clairement.
    """
    etat, erreur, texte = _etat_connexion(db2)
    assert etat, message(
        en=(
            "`performance_schema.replication_connection_status` is empty: no "
            "replication channel exists on the replica. "
            "`CHANGE REPLICATION SOURCE TO ... SOURCE_AUTO_POSITION = 1` creates it, "
            "then `START REPLICA` starts it."
        ),
        fr=(
            "`performance_schema.replication_connection_status` est vide : aucun "
            "canal de réplication n'existe sur le réplica. "
            "`CHANGE REPLICATION SOURCE TO ... SOURCE_AUTO_POSITION = 1` le crée, "
            "puis `START REPLICA` le démarre."
        ),
    )
    assert etat == "ON", message(
        en=(
            f"The replica's input thread reports `{etat}` with error {erreur}: "
            f"{texte}\n"
            "An error 2061 mentioning a secure connection is the default "
            "authentication plugin: `caching_sha2_password` refuses to send the "
            "password over an unencrypted channel. Either give the channel TLS, or "
            "let it fetch the public key with `GET_SOURCE_PUBLIC_KEY = 1`. It is "
            "neither the password nor the privileges."
        ),
        fr=(
            f"Le fil d'entrée du réplica annonce `{etat}` avec l'erreur {erreur} : "
            f"{texte}\n"
            "Une erreur 2061 qui parle de connexion sûre, c'est le greffon "
            "d'authentification par défaut : `caching_sha2_password` refuse "
            "d'envoyer le mot de passe sur un canal en clair. Donne du TLS au canal, "
            "ou laisse-le récupérer la clé publique avec "
            "`GET_SOURCE_PUBLIC_KEY = 1`. Ce n'est ni le mot de passe ni les "
            "privilèges."
        ),
    )
    assert erreur in ("0", ""), message(
        en=f"The channel is connected and still reports error {erreur}: {texte}",
        fr=f"Le canal est connecté et annonce encore l'erreur {erreur} : {texte}",
    )


def test_le_fil_d_application_tourne(db2) -> None:
    """La panne qu'on ne voit pas : connecté, et n'appliquant rien.

    Les deux fils sont distincts. Celui d'entrée reçoit les événements, celui
    d'application les joue. Un réplica connecté dont l'applicateur est arrêté
    prend du retard indéfiniment sans qu'aucune erreur n'apparaisse à l'écran.
    """
    etat = _sql(
        db2,
        "select service_state from performance_schema.replication_applier_status",
    )
    assert etat == "ON", message(
        en=(
            f"The replica's applier thread reports {etat!r}. The input thread and "
            "the applier are two distinct threads: a connected replica whose applier "
            "is stopped falls behind indefinitely, and nothing says so on screen. "
            "`START REPLICA` starts both; "
            "`performance_schema.replication_applier_status_by_worker` names the "
            "error if one is stuck."
        ),
        fr=(
            f"Le fil d'application du réplica annonce {etat!r}. Le fil d'entrée et "
            "l'applicateur sont deux fils distincts : un réplica connecté dont "
            "l'applicateur est arrêté prend du retard indéfiniment, et rien ne le "
            "dit à l'écran. `START REPLICA` démarre les deux ; "
            "`performance_schema.replication_applier_status_by_worker` nomme "
            "l'erreur si l'un est bloqué."
        ),
    )


# ── LA preuve : une ligne qui voyage ──────────────────────────────────────


def test_une_ligne_ecrite_sur_la_source_arrive_sur_le_replica(db1, db2) -> None:
    """Aucune table d'état ne remplace cette preuve.

    Une réplication qui annonce `ON` sans rien transporter existe. Le test
    écrit donc une ligne marquée sur la source, la cherche sur le réplica, puis
    la retire, pour que le compte de lignes que le rapport décrit reste celui
    que l'apprenant a relevé.

    Mesuré : l'arrivée prend entre 48 et 67 ms entre deux conteneurs. Le délai
    accordé est de trente secondes.
    """
    marqueur = f"voyage-{int(time.time())}"
    pose = _sql_brut(
        db1, f"insert into {BASE}.{TABLE} (nom) values ('{marqueur}')"
    )
    assert pose.rc == 0, message(
        en=(
            f"Cannot write to `{BASE}.{TABLE}` on the source:\n"
            f"{(pose.stderr or pose.stdout).strip()[:300]}"
        ),
        fr=(
            f"Impossible d'écrire dans `{BASE}.{TABLE}` sur la source :\n"
            f"{(pose.stderr or pose.stdout).strip()[:300]}"
        ),
    )
    try:
        arrivee = False
        for _ in range(DELAI_ARRIVEE_S):
            trouve = _sql_brut(
                db2,
                f"select count(*) from {BASE}.{TABLE} where nom = '{marqueur}'",
            )
            if trouve.rc == 0 and trouve.stdout.strip() == "1":
                arrivee = True
                break
            time.sleep(1)
        etat, erreur, texte = _etat_connexion(db2)
        assert arrivee, message(
            en=(
                f"A row written on the source has not arrived on the replica after "
                f"{DELAI_ARRIVEE_S} seconds. The channel reports `{etat}` with error "
                f"{erreur}: {texte}\n"
                "Measured between two servers, the trip takes about fifty "
                "milliseconds. If the state tables look fine, check that the replica "
                "replicates the right database and that nothing filters it out."
            ),
            fr=(
                "Une ligne écrite sur la source n'est pas arrivée sur le réplica "
                f"après {DELAI_ARRIVEE_S} secondes. Le canal annonce `{etat}` avec "
                f"l'erreur {erreur} : {texte}\n"
                "Mesuré entre deux serveurs, le trajet prend une cinquantaine de "
                "millisecondes. Si les tables d'état paraissent saines, vérifie que "
                "le réplica réplique bien cette base et que rien ne la filtre."
            ),
        )
    finally:
        _sql_brut(db1, f"delete from {BASE}.{TABLE} where nom = '{marqueur}'")


# ── Le réplica refuse les écritures directes ─────────────────────────────


def test_le_replica_refuse_une_ecriture_directe(db2) -> None:
    """Prouvé en essayant, et avec le compte le plus puissant.

    `super_read_only` refuse l'écriture MÊME aux comptes qui ont tous les
    privilèges, là où `read_only` seul les laisse passer. Mesuré : l'erreur est
    `1290`, « The MySQL server is running with the --super-read-only option ».

    Et mesuré aussi, ce qui rend l'énoncé soluble : `super_read_only` n'empêche
    PAS le fil d'application de jouer les transactions venues de la source.
    """
    actif = _sql(db2, "select @@super_read_only")
    assert actif in ("1", "ON"), message(
        en=(
            f"`super_read_only` is {actif!r} on the replica. A replica that accepts "
            "direct writes diverges from its source without a word, and the "
            "divergence is only discovered at promotion. `read_only` alone is not "
            "enough: it lets through any account holding every privilege."
        ),
        fr=(
            f"`super_read_only` vaut {actif!r} sur le réplica. Un réplica qui accepte "
            "les écritures directes divergera de sa source sans un mot, et la "
            "divergence ne se découvre qu'à la promotion. `read_only` seul ne suffit "
            "pas : il laisse passer tout compte qui détient tous les privilèges."
        ),
    )
    intrus = _sql_brut(db2, f"insert into {BASE}.{TABLE} (nom) values ('intrus')")
    assert intrus.rc != 0, message(
        en=(
            "An administration account was able to INSERT directly into the replica, "
            "although `super_read_only` reports being on. Check which value is really "
            "in service rather than the one a file declares."
        ),
        fr=(
            "Un compte d'administration a pu INSÉRER directement dans le réplica, "
            "alors que `super_read_only` s'annonce actif. Contrôle la valeur "
            "réellement en service plutôt que celle qu'un fichier déclare."
        ),
    )


# ── Le rapport : édité, et confronté aux deux serveurs ───────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-07-repliquer` gives it back, and loses the "
            "replication."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-07-repliquer` te le rend, et perd la "
            "réplication."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_l_etat_des_deux_serveurs(db1, db2) -> None:
    etat, _, _ = _etat_connexion(db2)
    ecrit_etat = _valeur(db1, "etat_de_la_connexion")
    assert ecrit_etat.upper() == etat.upper(), message(
        en=(
            f"etat_de_la_connexion = {ecrit_etat!r} in the report, but "
            f"`replication_connection_status` answers {etat!r}."
        ),
        fr=(
            f"etat_de_la_connexion = {ecrit_etat!r} dans le rapport, alors que "
            f"`replication_connection_status` répond {etat!r}."
        ),
    )

    attendu_uuid = _sql(db1, "select @@server_uuid")
    ecrit_uuid = _valeur(db1, "uuid_de_la_source")
    assert ecrit_uuid.lower() == attendu_uuid.lower(), message(
        en=(
            f"uuid_de_la_source = {ecrit_uuid!r} in the report, but the source "
            f"answers {attendu_uuid!r}. The replica sees the same value in the "
            "`source_uuid` column of `replication_connection_status`, which is a way "
            "to check the two servers agree."
        ),
        fr=(
            f"uuid_de_la_source = {ecrit_uuid!r} dans le rapport, alors que la source "
            f"répond {attendu_uuid!r}. Le réplica voit la même valeur dans la colonne "
            "`source_uuid` de `replication_connection_status`, ce qui est un moyen de "
            "contrôler que les deux serveurs s'accordent."
        ),
    )

    attendu_lignes = _sql(db2, f"select count(*) from {BASE}.{TABLE}")
    ecrit_lignes = _valeur(db1, "lignes_sur_le_replica")
    assert ecrit_lignes == attendu_lignes, message(
        en=(
            f"lignes_sur_le_replica = {ecrit_lignes!r} in the report, but the replica "
            f"holds {attendu_lignes}."
        ),
        fr=(
            f"lignes_sur_le_replica = {ecrit_lignes!r} dans le rapport, alors que le "
            f"réplica en porte {attendu_lignes}."
        ),
    )
