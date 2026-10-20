"""pg-02-psql-admin : ce que la machine et le serveur répondent vraiment.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Si oui, ce n'est pas un
test, c'est une hypothèse du setup. Le setup laisse donc une instance qui
tourne mais fermée : écoute sur la seule boucle locale, aucun `.pgpass`,
aucun objet applicatif, rapport non rempli.

LE PIÈGE QUE CE LAB FAIT RENCONTRER

`.pgpass` est **ignoré en silence** par psql si ses permissions sont trop
larges : pas d'erreur, pas d'avertissement visible dans un script, juste une
demande de mot de passe qui bloque. Un apprenant qui écrit le fichier sans le
passer en 0600 croit avoir fini. Le test contrôle donc les deux : le contenu
ET le mode, puis la seule chose qui prouve que psql l'honore, une connexion
réseau qui aboutit sans qu'aucun mot de passe soit fourni.

CE QUE LES TESTS N'INTERROGENT JAMAIS

L'historique des commandes, ni la façon dont l'apprenant a lu les valeurs. Le
rapport est confronté à ce que le serveur déclare : une valeur plausible mais
fausse ne passe pas, et une valeur juste obtenue autrement passe.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
MAJEURE = "18"
RAPPORT = "/home/student/rapport-psql.txt"
PLACEHOLDER = "VOTRE_REPONSE_ICI"
SENTINELLE = "# Rapport d'administration de l'instance."
ROLE = "appli"
BASE = "facturation"
SCHEMA = "appli"
TABLE = "clients"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str, base: str = "postgres") -> str:
    """Une valeur lue sur le serveur en marche, par la socket et le peer."""
    r = db1.run("sudo -u postgres psql -X -At -d %s -c %s", base, sql)
    assert r.rc == 0, message(
        en=f"psql failed: {r.stderr.strip() or r.stdout.strip()}. Is the server running?",
        fr=f"psql a échoué : {r.stderr.strip() or r.stdout.strip()}. Le serveur tourne-t-il ?",
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-02-psql-admin` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-02-psql-admin` te le rend.",
    )
    return f.content_string


def _valeur(db1, cle: str) -> str:
    """La valeur que l'apprenant a écrite pour une clé du rapport."""
    for ligne in _rapport(db1).splitlines():
        if ligne.strip().startswith("#") or "=" not in ligne:
            continue
        nom, _, valeur = ligne.partition("=")
        if nom.strip() == cle:
            return valeur.strip()
    return ""


# ── Le rapport : édité, et non recréé ────────────────────────────────────────

def test_le_rapport_est_rempli_et_non_recree(db1) -> None:
    """Les deux moitiés : plus de placeholder, et l'en-tête survit.

    Exiger seulement la survie de l'en-tête rendrait ce test vert avant tout
    travail, puisque le fichier de départ le porte.
    """
    contenu = _rapport(db1)
    # Les lignes de VALEURS, pas les commentaires : l'en-tête cite le nom du
    # placeholder pour expliquer quoi remplacer, et un test qui lirait tout le
    # fichier le trouverait donc toujours. C'est la faute que `start.conf` a
    # value au lab pg-01 : lire la valeur, jamais le fichier entier.
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"The report still holds '{PLACEHOLDER}'. Fill in the four values "
        "with what the server really answers.",
        fr=f"Le rapport porte encore '{PLACEHOLDER}'. Renseigne les quatre "
        "valeurs avec ce que le serveur répond vraiment.",
    )
    assert SENTINELLE in contenu, message(
        en="The provided header is gone. It only disappears when the file is "
        "RECREATED, typically with a `>` redirection. Edit it in place: "
        "`dsoxlab reset pg-02-psql-admin` gives the starting file back.",
        fr="L'en-tête fourni a disparu. Il ne disparaît que si le fichier a été "
        "RECRÉÉ, typiquement avec une redirection « > ». Édite-le sur place : "
        "`dsoxlab reset pg-02-psql-admin` te rend le fichier de départ.",
    )


# ── L'écoute réseau : la porte, puis qui entre ───────────────────────────────

def test_le_serveur_ecoute_au_dela_de_la_boucle_locale(db1) -> None:
    """Un écouteur doit exister, et au moins un hors de la boucle locale.

    L'ordre des deux assertions compte : « rien n'écoute que localhost » est
    vrai d'une machine où rien n'écoute du tout.
    """
    r = db1.run("ss -H -ltn sport = :5432")
    adresses = [
        ligne.split()[3].rsplit(":", 1)[0] for ligne in r.stdout.splitlines() if ligne.split()
    ]
    assert adresses, message(
        en="Nothing listens on port 5432: the server is not running.",
        fr="Rien n'écoute sur le port 5432 : le serveur ne tourne pas.",
    )
    locales = {"127.0.0.1", "[::1]", "::1", "localhost"}
    assert any(a not in locales for a in adresses), message(
        en=f"PostgreSQL only listens on {', '.join(adresses)}: a remote client "
        "cannot reach it. `listen_addresses` opens the door.",
        fr=f"PostgreSQL n'écoute que sur {', '.join(adresses)} : un client "
        "distant ne peut pas l'atteindre. `listen_addresses` ouvre la porte.",
    )


def test_pg_hba_autorise_une_connexion_reseau_chiffree_en_mot_de_passe(db1) -> None:
    """Ouvrir la porte ne suffit pas : `pg_hba.conf` dit qui entre, et comment.

    `trust` sur une ligne `host` est refusé : il laisse entrer sans rien
    demander, ce qui est pire que l'état de départ.
    """
    f = db1.file(f"/etc/postgresql/{MAJEURE}/main/pg_hba.conf")
    assert f.exists, message(
        en="pg_hba.conf is missing: is the cluster really installed?",
        fr="pg_hba.conf est absent : le cluster est-il bien installé ?",
    )
    lignes = [
        ligne.split()
        for ligne in f.content_string.splitlines()
        if ligne.strip() and not ligne.strip().startswith("#")
    ]
    reseau = [c for c in lignes if c[0] in ("host", "hostssl")]
    # Debian livre déjà `host all all 127.0.0.1/32` : exiger « une ligne host »
    # serait donc vrai avant tout travail. Ce qui manque est une ligne qui vise
    # une adresse AUTRE que la boucle locale.
    locales = ("127.0.0.1", "::1", "localhost", "samehost", "samenet")
    distantes = [c for c in reseau if len(c) > 3 and not c[3].startswith(locales)]
    assert distantes, message(
        en="pg_hba.conf has no `host` line for an address other than the "
        "loopback: the server accepts no connection from the network, whatever "
        "`listen_addresses` says. The loopback line Debian ships does not count.",
        fr="pg_hba.conf n'a aucune ligne `host` pour une adresse autre que la "
        "boucle locale : le serveur n'accepte aucune connexion venue du réseau, "
        "quoi que dise `listen_addresses`. La ligne de boucle locale livrée par "
        "Debian ne compte pas.",
    )
    fautives = [" ".join(c) for c in distantes if c[-1] in ("trust", "password")]
    assert not fautives, message(
        en="A network line uses `trust` or `password`, which lets anyone in or "
        f"sends the password in clear:\n  {chr(10).join(fautives)}\nUse "
        "`scram-sha-256`.",
        fr="Une ligne réseau emploie `trust` ou `password`, qui laisse entrer "
        f"n'importe qui ou envoie le mot de passe en clair :\n  "
        f"{chr(10).join(fautives)}\nEmploie `scram-sha-256`.",
    )


# ── `.pgpass` : le contenu, le mode, puis la preuve ──────────────────────────

def test_pgpass_existe_avec_le_mode_que_psql_exige(db1) -> None:
    """0600, sinon psql l'ignore SANS RIEN DIRE.

    C'est le piège de ce lab : le fichier est là, son contenu est juste, et
    rien ne marche. psql refuse un fichier de mots de passe que d'autres
    comptes pourraient lire, et ne le signale que sur un terminal.
    """
    f = db1.file("/home/student/.pgpass")
    assert f.exists, message(
        en="/home/student/.pgpass is missing: psql will keep asking for the "
        "password, and no script can connect.",
        fr="/home/student/.pgpass est absent : psql continuera de demander le "
        "mot de passe, et aucun script ne pourra se connecter.",
    )
    assert f.mode == 0o600, message(
        en=f".pgpass is in mode {oct(f.mode)[-3:]}. psql IGNORES a password "
        "file that is group- or world-readable, and says so only on a "
        "terminal. `chmod 600` is the fix.",
        fr=f".pgpass est en mode {oct(f.mode)[-3:]}. psql IGNORE un fichier de "
        "mots de passe lisible par le groupe ou tous, et ne le dit que sur un "
        "terminal. `chmod 600` est le correctif.",
    )
    assert f.user == "student", message(
        en=f".pgpass belongs to {f.user}, not student: psql reads the one in "
        "the HOME of the user who runs it.",
        fr=f".pgpass appartient à {f.user}, pas à student : psql lit celui du "
        "HOME de l'utilisateur qui le lance.",
    )
    assert ROLE in f.content_string, message(
        en=f".pgpass holds no line for the `{ROLE}` role.",
        fr=f".pgpass ne porte aucune ligne pour le rôle `{ROLE}`.",
    )


def test_une_connexion_reseau_aboutit_sans_mot_de_passe_fourni(db1) -> None:
    """La seule preuve que la chaîne entière tient.

    Lancée en tant que `student`, sans `PGPASSWORD` et avec l'entrée standard
    fermée : si quelque chose manque, psql demande le mot de passe et la
    commande meurt au lieu de l'inventer.
    """
    ip = db1.run("hostname -I").stdout.split()[0]
    r = db1.run(
        "sudo -u student -H env -u PGPASSWORD psql "
        "-h %s -U %s -d %s -At -c 'select 1' < /dev/null",
        ip,
        ROLE,
        BASE,
    )
    assert r.rc == 0 and r.stdout.strip() == "1", message(
        en=f"A TCP connection as `{ROLE}` on {ip} did not work without a "
        f"password being supplied:\n{(r.stderr or r.stdout).strip()[:300]}\n"
        "The three pieces must all hold: listen_addresses, pg_hba.conf, "
        ".pgpass in 0600.",
        fr=f"Une connexion TCP en `{ROLE}` sur {ip} n'a pas abouti sans qu'un "
        f"mot de passe soit fourni :\n{(r.stderr or r.stdout).strip()[:300]}\n"
        "Les trois pièces doivent tenir ensemble : listen_addresses, "
        "pg_hba.conf, .pgpass en 0600.",
    )


# ── Les objets : ce que le catalogue contient vraiment ───────────────────────

def test_le_schema_et_la_table_demandes_existent(db1) -> None:
    """Lus dans le catalogue, pas dans un fichier .sql laissé sur le disque."""
    schemas = _psql(
        db1, f"select 1 from pg_namespace where nspname = '{SCHEMA}'", BASE
    )
    assert schemas == "1", message(
        en=f"No `{SCHEMA}` schema in the `{BASE}` database.",
        fr=f"Aucun schéma `{SCHEMA}` dans la base `{BASE}`.",
    )
    colonnes = _psql(
        db1,
        "select string_agg(column_name, ',' order by ordinal_position) "
        f"from information_schema.columns where table_schema = '{SCHEMA}' "
        f"and table_name = '{TABLE}'",
        BASE,
    )
    assert colonnes, message(
        en=f"No `{SCHEMA}.{TABLE}` table in the `{BASE}` database.",
        fr=f"Aucune table `{SCHEMA}.{TABLE}` dans la base `{BASE}`.",
    )
    attendues = {"id", "nom"}
    manquantes = attendues - set(colonnes.split(","))
    assert not manquantes, message(
        en=f"`{SCHEMA}.{TABLE}` lacks the column(s): {', '.join(sorted(manquantes))}. "
        f"It has: {colonnes}.",
        fr=f"`{SCHEMA}.{TABLE}` n'a pas la ou les colonnes : "
        f"{', '.join(sorted(manquantes))}. Elle porte : {colonnes}.",
    )


def test_la_table_porte_les_lignes_demandees(db1) -> None:
    """Créer la table ne suffit pas : le lab demande d'y écrire."""
    n = _psql(db1, f"select count(*) from {SCHEMA}.{TABLE}", BASE)
    assert int(n or 0) >= 2, message(
        en=f"`{SCHEMA}.{TABLE}` holds {n or 0} row(s); the lab asks for at least two.",
        fr=f"`{SCHEMA}.{TABLE}` porte {n or 0} ligne(s) ; le lab en demande deux au moins.",
    )
    proprietaire = _psql(
        db1,
        f"select tableowner from pg_tables where schemaname = '{SCHEMA}' "
        f"and tablename = '{TABLE}'",
        BASE,
    )
    assert proprietaire == ROLE, message(
        en=f"`{SCHEMA}.{TABLE}` belongs to `{proprietaire}`, not `{ROLE}`: the "
        "objects of a service belong to its role, not to a superuser.",
        fr=f"`{SCHEMA}.{TABLE}` appartient à `{proprietaire}`, pas à `{ROLE}` : "
        "les objets d'un service appartiennent à son rôle, pas à un superutilisateur.",
    )


# ── Le rapport confronté au serveur ──────────────────────────────────────────

def test_les_valeurs_du_rapport_sont_celles_du_serveur(db1) -> None:
    """Chaque valeur écrite est comparée à ce que le serveur déclare.

    Aucune valeur attendue n'est écrite en dur ici : le test interroge
    `pg_settings` et le catalogue, puis compare. Une réponse plausible mais
    fausse échoue, une réponse juste obtenue autrement passe.
    """
    version = _psql(db1, "show server_version")
    ecoute = _psql(db1, "show listen_addresses")
    checksums = _psql(db1, "show data_checksums")
    tables = _psql(
        db1,
        f"select count(*) from pg_tables where schemaname = '{SCHEMA}'",
        BASE,
    )

    attendu = {
        "server_version": version.split()[0],
        "listen_addresses": ecoute,
        "data_checksums": checksums,
        "nb_tables_schema_appli": tables,
    }
    for cle, vraie in attendu.items():
        ecrite = _valeur(db1, cle)
        assert ecrite, message(
            en=f"The report has no value for `{cle}`.",
            fr=f"Le rapport ne porte aucune valeur pour `{cle}`.",
        )
        # La version majeure suffit : « 18.6 » comme « 18 » sont acceptés, le
        # lab n'enseigne pas à recopier un numéro de correctif.
        if cle == "server_version":
            juste = vraie.startswith(ecrite.strip("'\"")) or ecrite.strip(
                "'\""
            ).startswith(vraie.split(".")[0])
        else:
            juste = ecrite.strip("'\"") == vraie
        assert juste, message(
            en=f"The report says `{cle} = {ecrite}`, the server answers "
            f"`{vraie}`. Read the value, do not guess it.",
            fr=f"Le rapport dit `{cle} = {ecrite}`, le serveur répond "
            f"`{vraie}`. Lis la valeur, ne la devine pas.",
        )
