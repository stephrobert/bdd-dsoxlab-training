"""pg-01-installer : ce que la machine exécute vraiment.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Si oui, ce n'est pas un
test, c'est une hypothèse du setup.

Le piège net est l'écoute réseau. « Le serveur n'écoute que sur la boucle
locale » est VRAI sur une machine où PostgreSQL n'est pas installé : aucun
écouteur n'existe. Le test exige donc d'abord qu'un écouteur existe sur 5432,
puis que tous soient locaux.

CE QUE LES TESTS N'INTERROGENT JAMAIS

L'historique de commandes, ni le nom du fichier de dépôt choisi par
l'apprenant : le dépôt est lu tel qu'APT le connaît (sources.list.d, quel que
soit le format), et la clé est jugée à son effet (`apt-get update` sans plainte
de signature), pas à son nom.
"""

from __future__ import annotations

import re

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
MAJEURE = "18"
PGBIN = f"/usr/lib/postgresql/{MAJEURE}/bin"
PGDATA = f"/var/lib/postgresql/{MAJEURE}/main"
LOOPBACK = {"127.0.0.1", "::1"}


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str) -> str:
    """Une valeur lue sur le serveur en marche, par la socket Unix (peer)."""
    r = db1.run("sudo -u postgres psql -X -At -c %s", sql)
    assert r.rc == 0, message(
        en=f"psql failed: {r.stderr.strip() or r.stdout.strip()}. Is the server running?",
        fr=f"psql a échoué : {r.stderr.strip() or r.stdout.strip()}. Le serveur tourne-t-il ?",
    )
    return r.stdout.strip()


def _sources(db1) -> str:
    """Tout ce qu'APT lit comme déclaration de dépôt, tous formats confondus."""
    r = db1.run("cat /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null")
    return r.stdout


def test_depot_pgdg_declare_avec_sa_cle(db1) -> None:
    """Le dépôt PGDG existe, est lié à une clé qui existe, et n'est pas « trusted »."""
    src = _sources(db1)
    assert "apt.postgresql.org" in src, message(
        en="No APT source points to apt.postgresql.org (the PGDG repository).",
        fr="Aucune source APT ne pointe vers apt.postgresql.org (le dépôt PGDG).",
    )
    assert "trixie-pgdg" in src, message(
        en="The PGDG suite for Debian 13 is `trixie-pgdg`.",
        fr="La suite PGDG de Debian 13 est `trixie-pgdg`.",
    )
    assert not re.search(r"trusted\s*[=:]\s*yes", src, re.I), message(
        en="`trusted=yes` switches signature checking off: tie the repository to a key.",
        fr="`trusted=yes` coupe le contrôle de signature : liez le dépôt à une clé.",
    )
    cles = re.findall(r"signed-by\s*[=:]\s*\[?\s*(/[^\s\]]+)", src, re.I)
    assert cles, message(
        en="The PGDG source has no `Signed-By`: APT does not know which key signs it.",
        fr="La source PGDG n'a pas de `Signed-By` : APT ne sait pas quelle clé la signe.",
    )
    for cle in cles:
        f = db1.file(cle)
        assert f.exists and f.size > 0, message(
            en=f"`Signed-By` points to {cle}, which is missing or empty.",
            fr=f"`Signed-By` pointe vers {cle}, absent ou vide.",
        )


def test_apt_update_sans_plainte_de_signature(db1) -> None:
    """La clé déclarée est la bonne : APT accepte l'index sans réserve."""
    r = db1.run("apt-get update 2>&1")
    sortie = r.stdout
    assert r.rc == 0, message(
        en=f"apt-get update fails: {sortie[-300:]}",
        fr=f"apt-get update échoue : {sortie[-300:]}",
    )
    assert not re.search(r"NO_PUBKEY|not signed|signatures couldn|EXPKEYSIG|Warning: .*pgdg", sortie, re.I), message(
        en="apt-get update complains about the signature of the PGDG repository.",
        fr="apt-get update se plaint de la signature du dépôt PGDG.",
    )
    assert "apt.postgresql.org" in sortie, message(
        en="apt-get update does not even read the PGDG repository.",
        fr="apt-get update ne lit même pas le dépôt PGDG.",
    )


def test_postgresql_18_installe_depuis_pgdg(db1) -> None:
    """Le paquet est en 18 et vient de PGDG, pas de Debian (qui livre la 17)."""
    r = db1.run("dpkg-query -W -f='${Status} ${Version}' postgresql-%s", MAJEURE)
    assert r.rc == 0 and "install ok installed" in r.stdout, message(
        en=f"The package postgresql-{MAJEURE} is not installed.",
        fr=f"Le paquet postgresql-{MAJEURE} n'est pas installé.",
    )
    version = r.stdout.rsplit(" ", 1)[-1]
    assert version.startswith(f"{MAJEURE}.") and "pgdg" in version, message(
        en=f"Installed version {version} does not come from PGDG.",
        fr=f"La version installée {version} ne vient pas de PGDG.",
    )
    serveur = _psql(db1, "SHOW server_version_num")
    assert serveur.startswith(MAJEURE), message(
        en=f"The running server is {serveur}, not a {MAJEURE}.x. Is an older instance still serving?",
        fr=f"Le serveur en marche est {serveur}, pas une {MAJEURE}.x. Une ancienne instance sert-elle encore ?",
    )


def test_cluster_en_ligne_et_active_au_demarrage(db1) -> None:
    """Le cluster 18/main est en ligne, et il démarre au boot."""
    r = db1.run("pg_lsclusters --no-header")
    ligne = next((x for x in r.stdout.splitlines() if x.split()[:2] == [MAJEURE, "main"]), "")
    assert ligne, message(
        en=f"No {MAJEURE}/main cluster in pg_lsclusters.",
        fr=f"Aucun cluster {MAJEURE}/main dans pg_lsclusters.",
    )
    assert ligne.split()[3] == "online", message(
        en=f"The {MAJEURE}/main cluster is {ligne.split()[3]}, not online.",
        fr=f"Le cluster {MAJEURE}/main est {ligne.split()[3]}, pas online.",
    )
    assert db1.service(f"postgresql@{MAJEURE}-main").is_running, message(
        en=f"The unit postgresql@{MAJEURE}-main is not active.",
        fr=f"L'unité postgresql@{MAJEURE}-main n'est pas active.",
    )
    # Deux conditions pour revenir au boot : l'unité parapluie est activée,
    # et le cluster est en démarrage automatique (start.conf).
    assert db1.service("postgresql").is_enabled, message(
        en="The postgresql unit is not enabled: the instance will not return at boot.",
        fr="L'unité postgresql n'est pas activée : l'instance ne reviendra pas au boot.",
    )
    start = db1.file(f"/etc/postgresql/{MAJEURE}/main/start.conf")
    assert start.exists, message(
        en=f"start.conf is missing for the {MAJEURE}/main cluster.",
        fr=f"start.conf est absent pour le cluster {MAJEURE}/main.",
    )
    # La VALEUR, pas le premier octet du fichier : `start.conf` livré par
    # postgresql-common commence par dix lignes de commentaires qui décrivent
    # les trois modes, et la valeur effective vient après. Un
    # `content_string.strip().startswith("auto")` est donc toujours faux, même
    # sur un cluster correctement réglé : le test exigeait l'impossible, et ce
    # lab ne pouvait pas être attesté.
    mode = next(
        (
            ligne.strip()
            for ligne in start.content_string.splitlines()
            if ligne.strip() and not ligne.strip().startswith("#")
        ),
        "",
    )
    assert mode == "auto", message(
        en=f"start.conf declares `{mode or 'nothing'}`, not `auto`: the cluster "
        "will not come back at boot.",
        fr=f"start.conf déclare `{mode or 'rien'}`, pas `auto` : le cluster ne "
        "reviendra pas au boot.",
    )


def test_pg_isready_repond(db1) -> None:
    """Le serveur accepte les connexions, par la socket et par TCP local."""
    for cible in ("", "-h 127.0.0.1"):
        r = db1.run(f"{PGBIN}/pg_isready {cible}".strip())
        assert r.rc == 0, message(
            en=f"pg_isready {cible}: {r.stdout.strip()}",
            fr=f"pg_isready {cible} : {r.stdout.strip()}",
        )


def test_sommes_de_controle_actives(db1) -> None:
    """Les checksums sont actifs côté serveur ET inscrits sur le disque."""
    assert _psql(db1, "SHOW data_checksums") == "on", message(
        en="SHOW data_checksums is not `on`.",
        fr="SHOW data_checksums n'est pas `on`.",
    )
    r = db1.run("sudo -u postgres %s/pg_controldata %s", PGBIN, PGDATA)
    ligne = next((x for x in r.stdout.splitlines() if "checksum version" in x), "")
    assert ligne.split(":")[-1].strip() not in ("", "0"), message(
        en=f"pg_controldata reports no checksums on disk: '{ligne}'.",
        fr=f"pg_controldata n'indique aucune somme de contrôle sur le disque : '{ligne}'.",
    )


def test_ecoute_sur_la_boucle_locale_seulement(db1) -> None:
    """Un écouteur existe sur 5432, et chacun est local."""
    r = db1.run("ss -H -ltn")
    ecouteurs = []
    for ligne in r.stdout.splitlines():
        local = ligne.split()[3]
        adresse, _, port = local.rpartition(":")
        if port == "5432":
            ecouteurs.append(adresse.strip("[]"))
    assert ecouteurs, message(
        en="Nothing listens on port 5432: the server is not running.",
        fr="Rien n'écoute sur le port 5432 : le serveur ne tourne pas.",
    )
    exposes = [a for a in ecouteurs if a not in LOOPBACK]
    assert not exposes, message(
        en=f"PostgreSQL listens on {exposes}: restore the default `listen_addresses = 'localhost'`.",
        fr=f"PostgreSQL écoute sur {exposes} : rétablissez `listen_addresses = 'localhost'` par défaut.",
    )
    assert _psql(db1, "SHOW listen_addresses") == "localhost", message(
        en="listen_addresses is not `localhost`.",
        fr="listen_addresses n'est pas `localhost`.",
    )
