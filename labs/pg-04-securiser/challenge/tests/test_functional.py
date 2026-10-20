"""pg-04-securiser : le comportement du serveur, et les droits du catalogue.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Elle a écarté un test qui
paraissait évident : « une connexion chiffrée aboutit ». Elle aboutit DÉJÀ sur
l'état de départ, puisque Debian livre `ssl = on` et son certificat snakeoil.
Le comportement noté est donc le COUPLE, dans un seul test : la connexion en
clair doit être REFUSÉE, et la connexion chiffrée doit encore aboutir. Le
second membre n'est pas décoratif, il interdit au premier d'être vert parce que
le serveur est tombé.

LE PIÈGE QUE CE LAB FAIT RENCONTRER

`ssl = on` et `hostssl` ne valent qu'ensemble, et chacun seul donne l'illusion
de l'autre. `hostssl` sans `ssl = on` est silencieusement ignoré, avec un
avertissement qui part dans le journal. `ssl = on` sans `hostssl` chiffre
quand le client le demande, donc n'impose rien. C'est exactement le couple
qu'un audit de fichiers déclare conforme.

CE QUE LES TESTS NE NOTENT PAS

Deux états que le guide donne pour déjà acquis sur cette grappe : `ssl = on`,
posé par Debian, et la révocation de `CREATE` sur le schéma `public`, faite
d'office depuis PostgreSQL 15. Les noter reviendrait à noter le paquet Debian
et le numéro de version, pas le travail de l'apprenant.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
MAJEURE = "18"
RAPPORT = "/home/student/rapport-securite.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de durcissement de l'instance."

ROLE_CONNEXION = "appli"
BASE = "facturation"
SCHEMA = "appli"
TABLES = ("clients", "commandes")
OWNER, WRITER, READER = "app_owner", "app_writer", "app_reader"
GROUPES = (OWNER, WRITER, READER)
CN_ATTENDU = "db1.lab"


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _psql(db1, sql: str, base: str = "postgres") -> str:
    """Une valeur lue sur le serveur, par la socket locale et le peer.

    La socket, et jamais le réseau : le lab ferme justement le réseau au clair,
    et un test qui passerait par là mesurerait sa propre configuration client.
    """
    r = db1.run("sudo -u postgres psql -X -At -d %s -c %s", base, sql)
    assert r.rc == 0, message(
        en=f"psql failed: {r.stderr.strip() or r.stdout.strip()}",
        fr=f"psql a échoué : {r.stderr.strip() or r.stdout.strip()}",
    )
    return r.stdout.strip()


def _exiger_role(db1, nom: str) -> None:
    """Sans ce garde-fou, un rôle absent sort en trace psql illisible."""
    existe = _psql(db1, f"select 1 from pg_roles where rolname = '{nom}'")
    assert existe == "1", message(
        en=f"The `{nom}` role does not exist yet: the rights cannot be checked.",
        fr=f"Le rôle `{nom}` n'existe pas encore : les droits ne peuvent pas être contrôlés.",
    )


def _droit(db1, role: str, table: str, droit: str) -> bool:
    _exiger_role(db1, role)
    reponse = _psql(
        db1,
        f"select has_table_privilege('{role}', '{SCHEMA}.{table}', '{droit}')",
        BASE,
    )
    return reponse == "t"


def _adresse(db1) -> str:
    return db1.run("hostname -I").stdout.split()[0]


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset pg-04-securiser` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset pg-04-securiser` te le rend.",
    )
    return f.content_string


def _valeur(db1, cle: str) -> str:
    """La valeur écrite pour une clé, en écartant les commentaires.

    L'en-tête du rapport cite le marqueur à remplacer : un test qui lirait le
    fichier entier le trouverait là et conclurait que rien n'est rempli.
    """
    for ligne in _rapport(db1).splitlines():
        if ligne.strip().startswith("#") or "=" not in ligne:
            continue
        nom, _, valeur = ligne.partition("=")
        if nom.strip() == cle:
            return valeur.strip()
    return ""


# ── Le certificat : dédié, protégé, et réellement présenté ──────────────────


def test_le_serveur_presente_un_certificat_dedie(db1) -> None:
    """Trois faits, et aucun ne se déduit des autres.

    Le serveur doit DÉCLARER un autre certificat que celui de Debian, ce
    certificat doit porter le bon nom commun, et sa clé privée doit être
    fermée. Un certificat posé sur le disque mais non déclaré ne sert à rien,
    et un certificat déclaré dont la clé est trop ouverte empêche le serveur de
    démarrer.
    """
    chemin = _psql(db1, "show ssl_cert_file")
    assert "snakeoil" not in chemin, message(
        en=(
            f"The server still presents Debian's certificate ({chemin}): the same "
            "one on every machine in the estate. Generate a dedicated one and "
            "point `ssl_cert_file` at it."
        ),
        fr=(
            f"Le serveur présente encore le certificat de Debian ({chemin}) : le "
            "même sur toutes les machines du parc. Génère-en un dédié et fais "
            "pointer `ssl_cert_file` dessus."
        ),
    )

    sujet = db1.run("openssl x509 -noout -subject -in %s", chemin)
    assert sujet.rc == 0, message(
        en=f"{chemin} is not a readable certificate: {sujet.stderr.strip()}",
        fr=f"{chemin} n'est pas un certificat lisible : {sujet.stderr.strip()}",
    )
    assert f"CN={CN_ATTENDU}" in sujet.stdout.replace(" = ", "="), message(
        en=(
            f"The certificate's subject is {sujet.stdout.strip()!r}, expected a "
            f"common name of {CN_ATTENDU}."
        ),
        fr=(
            f"Le sujet du certificat est {sujet.stdout.strip()!r}, on attendait un "
            f"nom commun {CN_ATTENDU}."
        ),
    )

    chemin_cle = _psql(db1, "show ssl_key_file")
    cle = db1.file(chemin_cle)
    assert cle.mode == 0o600, message(
        en=(
            f"The private key {chemin_cle} is in {oct(cle.mode)}, expected 0600. "
            "PostgreSQL refuses to load a key readable by anyone else, and says so "
            "in the log rather than on screen."
        ),
        fr=(
            f"La clé privée {chemin_cle} est en {oct(cle.mode)}, attendu 0600. "
            "PostgreSQL refuse de charger une clé lisible par d'autres, et le dit "
            "dans le journal plutôt qu'à l'écran."
        ),
    )
    assert cle.user == "postgres", message(
        en=f"The private key {chemin_cle} belongs to {cle.user}, expected postgres.",
        fr=f"La clé privée {chemin_cle} appartient à {cle.user}, attendu postgres.",
    )


# ── Le comportement : le clair refusé, le chiffré debout ────────────────────


def test_le_clair_est_refuse_et_le_chiffre_aboutit(db1) -> None:
    """Un seul test, parce que c'est un seul comportement.

    « Le chiffré aboutit » serait vert sur l'état de départ : Debian pose déjà
    `ssl = on`. Et « le clair est refusé » serait vert sur un serveur arrêté.
    Les deux membres se gardent donc l'un l'autre, et c'est ce couple que le
    lab demande.
    """
    ip = _adresse(db1)
    base = "sudo -u student -H env -u PGPASSWORD PGSSLMODE=%s psql -h %s -U %s -d %s -At -c %s"

    clair = db1.run(base, "disable", ip, ROLE_CONNEXION, BASE, "select 1")
    assert clair.rc != 0, message(
        en=(
            f"An UNENCRYPTED connection as `{ROLE_CONNEXION}` on {ip} was accepted. "
            "A `host` line accepts an encrypted and a cleartext session alike, so "
            "the client decides, which imposes nothing. `hostssl` refuses the "
            "cleartext one on the server side."
        ),
        fr=(
            f"Une connexion NON CHIFFRÉE en `{ROLE_CONNEXION}` sur {ip} a été "
            "acceptée. Une ligne `host` accepte indifféremment une session "
            "chiffrée et une session en clair : c'est donc le client qui décide, "
            "ce qui n'impose rien. `hostssl` refuse le clair côté serveur."
        ),
    )

    chiffre = db1.run(
        base,
        "require",
        ip,
        ROLE_CONNEXION,
        BASE,
        "select ssl from pg_stat_ssl where pid = pg_backend_pid()",
    )
    assert chiffre.rc == 0, message(
        en=(
            f"An ENCRYPTED connection as `{ROLE_CONNEXION}` on {ip} no longer "
            f"works:\n{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refusing cleartext must not refuse everything: the `hostssl` line must "
            "still accept this role on this database, and `ssl` must be on."
        ),
        fr=(
            f"Une connexion CHIFFRÉE en `{ROLE_CONNEXION}` sur {ip} ne fonctionne "
            f"plus :\n{(chiffre.stderr or chiffre.stdout).strip()[:300]}\n"
            "Refuser le clair ne doit pas tout refuser : la ligne `hostssl` doit "
            "encore accepter ce rôle sur cette base, et `ssl` doit être actif."
        ),
    )
    assert chiffre.stdout.strip() == "t", message(
        en=(
            f"The session answers ssl = {chiffre.stdout.strip()!r}: it is not "
            "encrypted, although the client asked for it. `pg_stat_ssl` is what the "
            "server says about the session, not what the client believes."
        ),
        fr=(
            f"La session répond ssl = {chiffre.stdout.strip()!r} : elle n'est pas "
            "chiffrée, alors que le client l'a demandé. `pg_stat_ssl` est ce que le "
            "serveur dit de la session, pas ce que le client croit."
        ),
    )


# ── Les rôles : qui crée, qui écrit, qui lit ────────────────────────────────


def test_les_trois_roles_groupes_existent_sans_connexion(db1) -> None:
    """Un rôle-groupe ne se connecte jamais : il se porte, il ne s'emprunte pas."""
    for nom in GROUPES:
        _exiger_role(db1, nom)
        peut_se_connecter = _psql(
            db1, f"select rolcanlogin from pg_roles where rolname = '{nom}'"
        )
        assert peut_se_connecter == "f", message(
            en=(
                f"The `{nom}` role can log in. A group role carries rights, it does "
                "not connect: `nologin`. A login role becomes a member of it."
            ),
            fr=(
                f"Le rôle `{nom}` peut se connecter. Un rôle-groupe porte des "
                "droits, il ne se connecte pas : `nologin`. Un rôle de connexion "
                "en devient membre."
            ),
        )


def test_les_tables_appartiennent_au_proprietaire_et_non_a_l_applicatif(db1) -> None:
    """Le constat de l'audit : `appli` pouvait supprimer ses propres tables."""
    _exiger_role(db1, OWNER)
    for table in TABLES:
        proprietaire = _psql(
            db1,
            f"select tableowner from pg_tables "
            f"where schemaname = '{SCHEMA}' and tablename = '{table}'",
            BASE,
        )
        assert proprietaire == OWNER, message(
            en=(
                f"{SCHEMA}.{table} belongs to {proprietaire!r}, expected {OWNER!r}. "
                "As long as the application's login role owns the table, it can drop "
                "it, and it runs with that right at all times."
            ),
            fr=(
                f"{SCHEMA}.{table} appartient à {proprietaire!r}, attendu {OWNER!r}. "
                "Tant que le rôle de connexion de l'application possède la table, il "
                "peut la supprimer, et il tourne avec ce droit en permanence."
            ),
        )

    proprietaire_schema = _psql(
        db1,
        f"select pg_get_userbyid(nspowner) from pg_namespace where nspname = '{SCHEMA}'",
        BASE,
    )
    assert proprietaire_schema == OWNER, message(
        en=f"The {SCHEMA} schema belongs to {proprietaire_schema!r}, expected {OWNER!r}.",
        fr=f"Le schéma {SCHEMA} appartient à {proprietaire_schema!r}, attendu {OWNER!r}.",
    )


def test_le_lecteur_lit_et_ne_fait_que_lire(db1) -> None:
    for table in TABLES:
        assert _droit(db1, READER, table, "SELECT"), message(
            en=f"{READER} cannot read {SCHEMA}.{table}: grant it SELECT.",
            fr=f"{READER} ne peut pas lire {SCHEMA}.{table} : accorde-lui SELECT.",
        )
        for interdit in ("INSERT", "UPDATE", "DELETE"):
            assert not _droit(db1, READER, table, interdit), message(
                en=(
                    f"{READER} holds {interdit} on {SCHEMA}.{table}. A reporting role "
                    "reads, and nothing else: that is the whole point of separating it."
                ),
                fr=(
                    f"{READER} détient {interdit} sur {SCHEMA}.{table}. Un rôle de "
                    "reporting lit, et rien d'autre : c'est tout l'intérêt de le "
                    "séparer."
                ),
            )
    usage = _psql(
        db1, f"select has_schema_privilege('{READER}', '{SCHEMA}', 'USAGE')", BASE
    )
    assert usage == "t", message(
        en=(
            f"{READER} has no USAGE on the {SCHEMA} schema: the table rights are "
            "unreachable, since the schema gates them."
        ),
        fr=(
            f"{READER} n'a pas l'USAGE du schéma {SCHEMA} : les droits sur les tables "
            "sont inatteignables, le schéma leur faisant barrage."
        ),
    )


def test_l_ecrivain_ecrit_sans_rien_posseder(db1) -> None:
    for table in TABLES:
        for attendu in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            assert _droit(db1, WRITER, table, attendu), message(
                en=f"{WRITER} lacks {attendu} on {SCHEMA}.{table}.",
                fr=f"{WRITER} n'a pas {attendu} sur {SCHEMA}.{table}.",
            )
    possede = _psql(
        db1,
        f"select count(*) from pg_tables "
        f"where schemaname = '{SCHEMA}' and tableowner = '{WRITER}'",
        BASE,
    )
    assert possede == "0", message(
        en=(
            f"{WRITER} owns {possede} table(s) of the {SCHEMA} schema. Writing rows "
            "and owning the table are two different rights: only the owner can drop "
            "it."
        ),
        fr=(
            f"{WRITER} possède {possede} table(s) du schéma {SCHEMA}. Écrire des "
            "lignes et posséder la table sont deux droits distincts : seul le "
            "propriétaire peut la supprimer."
        ),
    )


def test_le_role_de_connexion_passe_par_le_groupe(db1) -> None:
    """Les droits se portent par le groupe, pour pouvoir se retirer d'un geste."""
    _exiger_role(db1, WRITER)
    membre = _psql(
        db1,
        "select count(*) from pg_auth_members m "
        "join pg_roles r on r.oid = m.roleid "
        "join pg_roles e on e.oid = m.member "
        f"where r.rolname = '{WRITER}' and e.rolname = '{ROLE_CONNEXION}'",
    )
    assert membre != "0", message(
        en=(
            f"`{ROLE_CONNEXION}` is not a member of {WRITER}: it holds its rights "
            "directly, or holds none. Going through the group is what lets you revoke "
            "them in one move."
        ),
        fr=(
            f"`{ROLE_CONNEXION}` n'est pas membre de {WRITER} : il porte ses droits "
            "en direct, ou n'en a aucun. Passer par le groupe est ce qui permet de "
            "les retirer d'un seul geste."
        ),
    )


def test_les_tables_a_venir_heriteront_des_droits(db1) -> None:
    """Sans cela, tout est juste aujourd'hui et faux à la première migration.

    Un `grant ... on all tables` ne vise que l'existant : il ne dit rien des
    tables qu'une migration créera. C'est `ALTER DEFAULT PRIVILEGES` qui le
    dit, et le catalogue le garde dans `pg_default_acl`.
    """
    _exiger_role(db1, OWNER)
    acl = _psql(
        db1,
        "select coalesce(string_agg(array_to_string(d.defaclacl, ' '), ' '), '') "
        "from pg_default_acl d "
        "join pg_namespace n on n.oid = d.defaclnamespace "
        f"where n.nspname = '{SCHEMA}' and d.defaclobjtype = 'r'",
        BASE,
    )
    for role in (READER, WRITER):
        assert f"{role}=" in acl, message(
            en=(
                f"No default privilege for {role} on the future tables of {SCHEMA}. "
                "`ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA appli GRANT "
                "... ` is what covers the tables a migration has yet to create."
            ),
            fr=(
                f"Aucun droit par défaut pour {role} sur les futures tables de "
                f"{SCHEMA}. `ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA "
                "appli GRANT ...` est ce qui couvre les tables qu'une migration n'a "
                "pas encore créées."
            ),
        )


# ── Le rapport : édité, et confronté au serveur ─────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset pg-04-securiser` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset pg-04-securiser` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_le_nom_commun_du_certificat(db1) -> None:
    ecrit = _valeur(db1, "cn_du_certificat")
    assert ecrit == CN_ATTENDU, message(
        en=(
            f"cn_du_certificat = {ecrit!r} in the report, expected {CN_ATTENDU!r}. "
            "`openssl x509 -noout -subject -in <the certificate>` gives it."
        ),
        fr=(
            f"cn_du_certificat = {ecrit!r} dans le rapport, attendu {CN_ATTENDU!r}. "
            "`openssl x509 -noout -subject -in <le certificat>` le donne."
        ),
    )


def test_le_rapport_dit_le_proprietaire(db1) -> None:
    attendu = _psql(
        db1,
        f"select tableowner from pg_tables "
        f"where schemaname = '{SCHEMA}' and tablename = 'clients'",
        BASE,
    )
    ecrit = _valeur(db1, "proprietaire_des_tables")
    assert ecrit == attendu, message(
        en=(
            f"proprietaire_des_tables = {ecrit!r} in the report, but the catalog "
            f"answers {attendu!r}. `\\dt {SCHEMA}.*` shows it."
        ),
        fr=(
            f"proprietaire_des_tables = {ecrit!r} dans le rapport, alors que le "
            f"catalogue répond {attendu!r}. `\\dt {SCHEMA}.*` l'affiche."
        ),
    )


def test_le_rapport_compte_ce_que_le_lecteur_peut_lire(db1) -> None:
    _exiger_role(db1, READER)
    attendu = _psql(
        db1,
        "select count(*) from pg_tables "
        f"where schemaname = '{SCHEMA}' "
        f"and has_table_privilege('{READER}', schemaname || '.' || tablename, 'SELECT')",
        BASE,
    )
    ecrit = _valeur(db1, "nb_tables_lisibles_par_reader")
    assert ecrit == attendu, message(
        en=(
            f"nb_tables_lisibles_par_reader = {ecrit!r} in the report, but the server "
            f"counts {attendu!r}. `has_table_privilege` answers per table."
        ),
        fr=(
            f"nb_tables_lisibles_par_reader = {ecrit!r} dans le rapport, alors que le "
            f"serveur en compte {attendu!r}. `has_table_privilege` répond table par "
            "table."
        ),
    )
