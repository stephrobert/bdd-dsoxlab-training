"""pg-09-repliquer : le flux entre deux machines, et ce qui le rend sûr.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc un
primaire sans rôle de réplication, sans slot et sans règle d'accès, et un
secondaire qui est en réalité un primaire autonome tout neuf. Il efface à
chaque passage le slot, le rôle, la règle `pg_hba`, et refait une grappe neuve
sur la seconde machine si la précédente avait été transformée en secondaire.

LE TEST QUI COMPTE

Celui qui ÉCRIT sur le primaire et LIT sur le secondaire. Tous les autres
décrivent une configuration, et une configuration juste peut ne rien faire
couler : un slot créé mais inutilisé, un `primary_conninfo` qui désigne une
machine injoignable, une règle `pg_hba` dont la colonne base vaut `all` et qui
n'autorise donc pas la réplication. Ce test est le seul qui ne puisse pas se
tromper.

IL ÉCRIT, ET C'EST ASSUMÉ

Il insère une ligne dans une table `appli.sonde` que le setup pose vide à cette
seule fin. Aucun autre test ne compte les lignes de cette table, et le
nettoyage la retire. On ne prouve pas un flux en regardant des réglages.

CE QUE LES TESTS NE NOTENT PAS

La méthode employée pour copier la grappe, ni le contenu de
`postgresql.auto.conf`. `pg_basebackup -R` écrit ces lignes tout seul, mais un
apprenant qui les pose à la main obtient le même résultat, et le même service.
"""

from __future__ import annotations

import time

import pytest

from conftest import lab_host, lab_target_host, message

PRIMAIRE = lab_target_host("db1.lab")
SECONDAIRE = "db2.lab"
MAJEURE = "18"
RAPPORT = "/home/student/rapport-replication.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de replication."

BASE = "facturation"
SCHEMA = "appli"
ROLE_REPLICATION = "replicator"
SLOT = "standby_slot"
DELAI_FLUX_S = 20

# ── Pourquoi ces deux requêtes écrivent `case when` au lieu de lire le booléen
#
# psql AFFICHE une colonne booléenne en `t`, mais un booléen CONCATÉNÉ passe
# par la conversion en texte et vaut `true`. Mesuré sur PostgreSQL 18 :
#
#     select true              -> t
#     select true::text        -> true
#     select true || ',' || false -> true,false
#
# Les deux tests comparaient donc `"t"` à `"true"` et échouaient sur un serveur
# parfaitement configuré. Un `case when` ne dépend d'aucune de ces deux
# conventions : il dit ce qu'il produit.

_ATTRIBUTS_DU_ROLE = (
    "select coalesce(string_agg("
    "  case when rolcanlogin then 't' else 'f' end || ',' ||"
    "  case when rolreplication then 't' else 'f' end || ',' ||"
    "  case when rolsuper then 't' else 'f' end || ',' ||"
    "  case when rolcreatedb then 't' else 'f' end, ''), '') "
    f"from pg_roles where rolname = '{ROLE_REPLICATION}'"
)

_ETAT_DU_SLOT = (
    "select coalesce(string_agg("
    "  slot_type || ',' || case when active then 't' else 'f' end, ''), '') "
    f"from pg_replication_slots where slot_name = '{SLOT}'"
)


@pytest.fixture(scope="module")
def db1():
    return lab_host(PRIMAIRE)


@pytest.fixture(scope="module")
def db2():
    """Le secondaire, joint par l'inventaire et non par une adresse codée."""
    return lab_host(SECONDAIRE)


def _psql(hote, sql: str, base: str = "postgres") -> str:
    r = hote.run("sudo -u postgres psql -X -At -d %s -c %s", base, sql)
    assert r.rc == 0, message(
        en=f"psql failed on {base}: {r.stderr.strip() or r.stdout.strip()}",
        fr=f"psql a échoué sur {base} : {r.stderr.strip() or r.stdout.strip()}",
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing on the primary. `dsoxlab reset pg-09-repliquer` gives it back.",
        fr=f"{RAPPORT} est absent du primaire. `dsoxlab reset pg-09-repliquer` te le rend.",
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


# ── Le primaire : qui a le droit, et ce qu'il retient ───────────────────────


def test_le_role_de_replication_est_dedie_et_restreint(db1) -> None:
    """Son mot de passe va vivre sur l'autre machine : il ne doit rien ouvrir
    de plus que la réplication.

    Employer `postgres` pour cette connexion stockerait un mot de passe de
    superutilisateur sur le secondaire, et ouvrirait un accès total au primaire
    si celui-ci était compromis. C'est pour cela que le test refuse un rôle
    superutilisateur, et pas seulement un rôle absent.
    """
    attributs = _psql(db1, _ATTRIBUTS_DU_ROLE)
    assert attributs, message(
        en=(
            f"The `{ROLE_REPLICATION}` role does not exist. The standby must "
            "authenticate against the primary, and it needs a dedicated role for "
            "that: `create role replicator with login replication password '...'`."
        ),
        fr=(
            f"Le rôle `{ROLE_REPLICATION}` n'existe pas. Le secondaire doit "
            "s'authentifier auprès du primaire, et il lui faut un rôle dédié pour "
            "cela : `create role replicator with login replication password '...'`."
        ),
    )
    peut_entrer, peut_repliquer, est_super, cree_bases = attributs.split(",")
    assert peut_entrer == "t" and peut_repliquer == "t", message(
        en=(
            f"`{ROLE_REPLICATION}` lacks LOGIN or REPLICATION (login={peut_entrer}, "
            f"replication={peut_repliquer}). Both are needed, and they are enough."
        ),
        fr=(
            f"`{ROLE_REPLICATION}` n'a pas LOGIN ou REPLICATION (login="
            f"{peut_entrer}, replication={peut_repliquer}). Les deux sont "
            "nécessaires, et ils suffisent."
        ),
    )
    assert est_super == "f" and cree_bases == "f", message(
        en=(
            f"`{ROLE_REPLICATION}` is a superuser or can create databases "
            f"(super={est_super}, createdb={cree_bases}). Its password will be stored "
            "on the standby: it must open replication and nothing else."
        ),
        fr=(
            f"`{ROLE_REPLICATION}` est superutilisateur ou peut créer des bases "
            f"(super={est_super}, createdb={cree_bases}). Son mot de passe sera "
            "stocké sur le secondaire : il ne doit ouvrir que la réplication."
        ),
    )


def test_un_slot_physique_retient_les_journaux(db1) -> None:
    """Sans slot, un secondaire déconnecté peut ne jamais revenir.

    Le primaire recycle ses journaux. S'il recycle ceux dont le secondaire a
    besoin, la synchronisation est perdue et il faut refaire la copie de base.
    Le slot est ce qui lui dit de les retenir.
    """
    etat = _psql(db1, _ETAT_DU_SLOT)
    assert etat, message(
        en=(
            f"No replication slot named `{SLOT}`. Without it the primary recycles the "
            "logs the standby needs, and a standby disconnected for a few hours never "
            f"comes back. `select pg_create_physical_replication_slot('{SLOT}')`."
        ),
        fr=(
            f"Aucun slot de réplication nommé `{SLOT}`. Sans lui, le primaire recycle "
            "les journaux dont le secondaire a besoin, et un secondaire déconnecté "
            "quelques heures ne revient jamais. `select "
            f"pg_create_physical_replication_slot('{SLOT}')`."
        ),
    )
    nature, actif = etat.split(",")
    assert nature == "physical", message(
        en=f"`{SLOT}` is a {nature!r} slot: physical replication needs a physical one.",
        fr=f"`{SLOT}` est un slot {nature!r} : la réplication physique en demande un physique.",
    )
    assert actif == "t", message(
        en=(
            f"The `{SLOT}` slot exists but is INACTIVE: nobody is consuming it. The "
            "standby must be told to use it, with `--slot` at copy time or "
            "`primary_slot_name` in its configuration."
        ),
        fr=(
            f"Le slot `{SLOT}` existe mais est INACTIF : personne ne le consomme. Le "
            "secondaire doit se voir dire de l'employer, par `--slot` au moment de la "
            "copie ou par `primary_slot_name` dans sa configuration."
        ),
    )


def test_pg_hba_autorise_la_replication_depuis_le_reseau(db1) -> None:
    """La réplication est une base VIRTUELLE : `all` ne la couvre pas.

    C'est la faute la plus fréquente sur ce sujet, et le message d'erreur du
    serveur parle alors d'une base qui n'existe pas, ce qui envoie chercher
    ailleurs.
    """
    f = db1.file(f"/etc/postgresql/{MAJEURE}/main/pg_hba.conf")
    assert f.exists, message(
        en="pg_hba.conf is missing: is the cluster really installed?",
        fr="pg_hba.conf est absent : le cluster est-il bien installé ?",
    )
    colonnes = [
        ligne.split()
        for ligne in f.content_string.splitlines()
        if ligne.strip() and not ligne.strip().startswith("#")
    ]
    reseau = [
        c
        for c in colonnes
        if c[0] in ("host", "hostssl") and len(c) > 3 and c[1] == "replication"
    ]
    locales = ("127.0.0.1", "::1", "localhost", "samehost")
    distantes = [c for c in reseau if not c[3].startswith(locales)]
    assert distantes, message(
        en=(
            "pg_hba.conf has no `host replication` line for an address other than the "
            "loopback. Replication is a VIRTUAL database: a line whose database column "
            "reads `all` does not allow it, and the server then reports a database "
            "that does not exist."
        ),
        fr=(
            "pg_hba.conf n'a aucune ligne `host replication` pour une adresse autre "
            "que la boucle locale. La réplication est une base VIRTUELLE : une ligne "
            "dont la colonne base vaut `all` ne l'autorise pas, et le serveur signale "
            "alors une base qui n'existe pas."
        ),
    )
    fautives = [" ".join(c) for c in distantes if c[-1] in ("trust", "password")]
    assert not fautives, message(
        en=(
            "A replication line uses `trust` or `password`, which lets anyone in or "
            f"sends the password in clear:\n  {chr(10).join(fautives)}\nUse "
            "`scram-sha-256`."
        ),
        fr=(
            "Une ligne de réplication emploie `trust` ou `password`, qui laisse entrer "
            f"n'importe qui ou envoie le mot de passe en clair :\n  "
            f"{chr(10).join(fautives)}\nEmploie `scram-sha-256`."
        ),
    )


# ── Le secondaire, et le lien entre les deux ────────────────────────────────


def test_le_secondaire_est_en_restauration_permanente(db2) -> None:
    """Un secondaire n'est pas un primaire vide : il reste en restauration."""
    en_recovery = _psql(db2, "select pg_is_in_recovery()")
    assert en_recovery == "t", message(
        en=(
            f"{SECONDAIRE} is not in standby mode: it answers pg_is_in_recovery() = "
            f"{en_recovery!r}. It is still the autonomous cluster the Debian "
            "installation left. The `standby.signal` file in its data directory is "
            "what puts it in standby mode, and `pg_basebackup -R` writes it."
        ),
        fr=(
            f"{SECONDAIRE} n'est pas en mode secondaire : il répond "
            f"pg_is_in_recovery() = {en_recovery!r}. C'est encore la grappe autonome "
            "que l'installation Debian a laissée. Le fichier `standby.signal` dans "
            "son répertoire de données est ce qui le met en mode secondaire, et "
            "`pg_basebackup -R` l'écrit."
        ),
    )


def test_le_primaire_voit_un_secondaire_en_flux(db1) -> None:
    etats = _psql(
        db1,
        "select coalesce(string_agg(state, ',' order by state), '') from pg_stat_replication",
    )
    assert etats, message(
        en=(
            "pg_stat_replication is empty on the primary: no standby is connected. "
            "Look at the standby's log, it names what it cannot do."
        ),
        fr=(
            "pg_stat_replication est vide sur le primaire : aucun secondaire n'est "
            "connecté. Regarde le journal du secondaire, il nomme ce qu'il n'arrive "
            "pas à faire."
        ),
    )
    assert "streaming" in etats, message(
        en=(
            f"A standby is connected but its state is {etats!r}, not `streaming`. A "
            "`catchup` state means the base copy is still being replayed: wait, then "
            "look again."
        ),
        fr=(
            f"Un secondaire est connecté mais son état est {etats!r}, et non "
            "« streaming ». Un état `catchup` veut dire que la copie de base est "
            "encore en cours de rejeu : attends, puis regarde à nouveau."
        ),
    )


def test_une_ligne_ecrite_sur_le_primaire_arrive_sur_le_secondaire(db1, db2) -> None:
    """LE test du lab. Il écrit, et c'est assumé.

    Tous les autres décrivent une configuration, et une configuration juste
    peut ne rien faire couler. Celui-ci écrit une marque unique sur le primaire
    et la cherche sur le secondaire, en laissant au flux le temps de la porter.

    La table `appli.sonde` est posée vide par le setup à cette seule fin :
    aucun autre test ne compte ses lignes, et le nettoyage la retire.
    """
    marque = f"flux-{int(time.time())}"
    ecriture = db1.run(
        "sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d %s -c %s",
        BASE,
        f"insert into {SCHEMA}.sonde (marque) values ('{marque}')",
    )
    assert ecriture.rc == 0, message(
        en=(
            "Writing to the primary failed:\n"
            f"{(ecriture.stderr or ecriture.stdout).strip()[:300]}\n"
            f"The {SCHEMA}.sonde table is laid down by the setup: "
            "`dsoxlab reset pg-09-repliquer` gives it back."
        ),
        fr=(
            "L'écriture sur le primaire a échoué :\n"
            f"{(ecriture.stderr or ecriture.stdout).strip()[:300]}\n"
            f"La table {SCHEMA}.sonde est posée par le setup : "
            "`dsoxlab reset pg-09-repliquer` te la rend."
        ),
    )

    requete = f"select count(*) from {SCHEMA}.sonde where marque = '{marque}'"
    for _ in range(DELAI_FLUX_S):
        lu = db2.run("sudo -u postgres psql -X -At -d %s -c %s", BASE, requete)
        if lu.rc == 0 and lu.stdout.strip() == "1":
            return
        time.sleep(1)

    raise AssertionError(
        message(
            en=(
                f"The row written on the primary never reached {SECONDAIRE} within "
                f"{DELAI_FLUX_S} seconds. The configuration may look right and nothing "
                "flow: a slot nobody consumes, a `primary_conninfo` pointing at an "
                "unreachable host, a `pg_hba` line whose database column reads `all` "
                "instead of `replication`. Only this check tells."
            ),
            fr=(
                f"La ligne écrite sur le primaire n'est jamais arrivée sur "
                f"{SECONDAIRE} en {DELAI_FLUX_S} secondes. La configuration peut "
                "sembler juste et rien ne couler : un slot que personne ne consomme, "
                "un `primary_conninfo` qui désigne une machine injoignable, une ligne "
                "`pg_hba` dont la colonne base vaut `all` au lieu de `replication`. "
                "Seul ce contrôle le dit."
            ),
        )
    )


# ── Le rapport : édité, et confronté au primaire ────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-09-repliquer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-09-repliquer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_compte_les_secondaires_en_flux(db1) -> None:
    attendu = _psql(
        db1, "select count(*) from pg_stat_replication where state = 'streaming'"
    )
    ecrit = _valeur(db1, "nb_secondaires_en_flux")
    assert ecrit == attendu, message(
        en=(
            f"nb_secondaires_en_flux = {ecrit!r} in the report, but the primary counts "
            f"{attendu!r} in the `streaming` state."
        ),
        fr=(
            f"nb_secondaires_en_flux = {ecrit!r} dans le rapport, alors que le "
            f"primaire en compte {attendu!r} à l'état « streaming »."
        ),
    )


def test_le_rapport_dit_l_etat_du_slot(db1) -> None:
    attendu = _psql(
        db1, f"select active from pg_replication_slots where slot_name = '{SLOT}'"
    )
    ecrit = _valeur(db1, "slot_actif").lower()
    assert ecrit == attendu, message(
        en=(
            f"slot_actif = {ecrit!r} in the report, but the slot answers {attendu!r}. "
            "`select slot_name, active from pg_replication_slots` gives it."
        ),
        fr=(
            f"slot_actif = {ecrit!r} dans le rapport, alors que le slot répond "
            f"{attendu!r}. `select slot_name, active from pg_replication_slots` le "
            "donne."
        ),
    )


def test_le_rapport_dit_que_le_role_n_est_pas_superuser(db1) -> None:
    """Une question dont la bonne réponse est « non », et c'est voulu.

    Elle oblige à regarder un attribut qu'on croit connaître, et dont la
    valeur est précisément ce qui rend le dispositif sûr.
    """
    attendu = _psql(
        db1, f"select rolsuper from pg_roles where rolname = '{ROLE_REPLICATION}'"
    )
    ecrit = _valeur(db1, "replicator_est_superuser").lower()
    assert ecrit == attendu, message(
        en=(
            f"replicator_est_superuser = {ecrit!r} in the report, but the catalog "
            f"answers {attendu!r}. `select rolsuper from pg_roles where rolname = "
            f"'{ROLE_REPLICATION}'` gives it, and the expected value is what makes the "
            "setup safe."
        ),
        fr=(
            f"replicator_est_superuser = {ecrit!r} dans le rapport, alors que le "
            f"catalogue répond {attendu!r}. `select rolsuper from pg_roles where "
            f"rolname = '{ROLE_REPLICATION}'` le donne, et la valeur attendue est ce "
            "qui rend le dispositif sûr."
        ),
    )
