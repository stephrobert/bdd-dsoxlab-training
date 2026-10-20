"""mysql-05-sauvegarder : une sauvegarde complète, prouvée en la restaurant.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup ne laisse donc
aucun fichier de sauvegarde et aucune base restaurée, et il RETIRE à chaque
passage ceux d'un passage précédent : sans cela, le travail de la fois d'avant
survivrait et six tests seraient verts avant tout travail.

POURQUOI DEUX FAMILLES DE TESTS, ET NON UNE

Trois tests regardent le FICHIER, trois regardent la BASE RESTAURÉE, et ce
n'est pas une redondance. Un apprenant peut très bien produire un dump
incomplet puis recréer la procédure à la main dans la copie : la base
restaurée serait alors juste, et le fichier, lui, resterait inutilisable le
jour de l'incident. Or c'est du fichier qu'on restaure quand la machine a
brûlé. L'inverse se tient aussi : un dump complet ne prouve pas qu'il se
restaure.

LE PIÈGE CENTRAL, MESURÉ SUR MYSQL 8.4 LE 2026-10-20

    mysqldump --help   ->   routines FALSE
                            events   FALSE
                            triggers TRUE

Un dump pris sans `--routines` omet donc les procédures stockées, et GARDE les
triggers. Et sa restauration dans une base neuve :

    code de retour du restore            0        (elle REUSSIT)
    lignes restaurees                    2        (toutes la)
    triggers restaures                   1        (present)
    procedures restaurees                0
    call appli_sans.chiffre_affaires()   ERROR 1305, « does not exist »

L'échec n'arrive donc jamais au moment de la sauvegarde ni à celui de la
restauration : il arrive le jour où l'application appelle la procédure.

CE QU'AUCUN TEST N'EXIGE, ET POURQUOI C'EST DIT AUX APPRENANTS

`--single-transaction`. C'est la bonne pratique, le guide l'explique, et elle
ne laisse AUCUNE trace vérifiable dans le fichier produit : mesuré, un dump
pris avec et un dump pris sans portent tous les deux un `LOCK TABLES`. Un test
qui prétendrait le contrôler noterait une ligne de commande au lieu d'un état,
ce que ce catalogue refuse de faire.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-sauvegarde.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de sauvegarde de la base appli."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BASE = "appli"
RESTAUREE = "appli_restauree"
DUMP = "/home/student/sauvegardes/appli.sql"
TABLES = ("clients", "commandes")
PROCEDURE = "chiffre_affaires"
# Le client_id de la ligne que le test du trigger insère puis retire. Hors de
# portée des données du setup, pour qu'un échec ne la confonde avec rien.
MARQUEUR = 999


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _sql(db1, sql: str) -> str:
    """Une valeur lue avec le compte d'administration, par la socket."""
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}",
        fr=f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}",
    )
    return r.stdout.strip()


def _sql_brut(db1, sql: str):
    """La même chose, mais SANS exiger le succès.

    Nécessaire pour l'appel de la procédure : son échec est précisément ce
    qu'un test doit pouvoir constater et nommer.
    """
    return db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)


def _contenu_du_dump(db1) -> str:
    f = db1.file(DUMP)
    assert f.exists, message(
        en=(
            f"{DUMP} does not exist. The lab asks for a logical backup of the "
            f"`{BASE}` database at exactly that path."
        ),
        fr=(
            f"{DUMP} n'existe pas. Le lab demande une sauvegarde logique de la base "
            f"`{BASE}` à exactement ce chemin."
        ),
    )
    return f.content_string


def _base_existe(db1, nom: str) -> bool:
    return (
        _sql(
            db1,
            "select count(*) from information_schema.schemata "
            f"where schema_name = '{nom}'",
        )
        == "1"
    )


def _exiger_la_base_restauree(db1) -> None:
    assert _base_existe(db1, RESTAUREE), message(
        en=(
            f"The `{RESTAUREE}` database does not exist. The lab asks for the backup "
            "to be restored into a FRESH database, which is where a backup is proven "
            "to be worth something. `create database "
            f"{RESTAUREE}` then `mysql -u {ADMIN} {RESTAUREE} < {DUMP}`."
        ),
        fr=(
            f"La base `{RESTAUREE}` n'existe pas. Le lab demande de restaurer la "
            "sauvegarde dans une base NEUVE, qui est là où l'on prouve qu'une "
            f"sauvegarde vaut quelque chose. `create database {RESTAUREE}` puis "
            f"`mysql -u {ADMIN} {RESTAUREE} < {DUMP}`."
        ),
    )


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-05-sauvegarder` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-05-sauvegarder` te le rend.",
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
    """Compare deux nombres sans se laisser arrêter par leur écriture.

    `55.5` et `55.50` sont la même valeur, et un rapport refusé sur un zéro de
    queue enverrait chercher une faute là où il n'y en a pas. Un faux rouge
    coûte plus cher qu'un verdict manquant.
    """
    try:
        return abs(float(ecrit.replace(",", ".")) - float(attendu)) < 1e-9
    except (TypeError, ValueError):
        return ecrit.strip() == attendu.strip()


# ── Le FICHIER : ce dont on restaure le jour de l'incident ──────────────────


def test_le_fichier_de_sauvegarde_existe_et_est_un_dump(db1) -> None:
    contenu = _contenu_du_dump(db1)
    assert contenu.strip(), message(
        en=f"{DUMP} exists but is empty. The dump produced nothing.",
        fr=f"{DUMP} existe mais il est vide. Le dump n'a rien produit.",
    )
    assert "MySQL dump" in contenu, message(
        en=(
            f"{DUMP} does not look like a mysqldump output: its header does not "
            "carry the `MySQL dump` line that the tool writes. If you redirected "
            "something else into that file, the backup is not one."
        ),
        fr=(
            f"{DUMP} ne ressemble pas à une sortie de mysqldump : son en-tête ne "
            "porte pas la ligne `MySQL dump` que l'outil écrit. Si tu as redirigé "
            "autre chose dans ce fichier, la sauvegarde n'en est pas une."
        ),
    )


def test_le_dump_porte_le_schema_et_les_donnees(db1) -> None:
    contenu = _contenu_du_dump(db1)
    haut = contenu.upper()
    assert "CREATE TABLE" in haut, message(
        en=(
            f"{DUMP} carries no `CREATE TABLE`: the schema is missing. A dump taken "
            "with `--no-create-info` holds only the rows, and restores into nothing."
        ),
        fr=(
            f"{DUMP} ne porte aucun `CREATE TABLE` : le schéma manque. Un dump pris "
            "avec `--no-create-info` ne porte que les lignes, et ne se restaure dans "
            "rien."
        ),
    )
    for table in TABLES:
        assert table in contenu, message(
            en=f"{DUMP} does not mention the `{table}` table: the backup is partial.",
            fr=f"{DUMP} ne mentionne pas la table `{table}` : la sauvegarde est partielle.",
        )
    assert "INSERT INTO" in haut, message(
        en=(
            f"{DUMP} carries no `INSERT INTO`: the rows are missing. A dump taken "
            "with `--no-data` holds only the structure."
        ),
        fr=(
            f"{DUMP} ne porte aucun `INSERT INTO` : les lignes manquent. Un dump pris "
            "avec `--no-data` ne porte que la structure."
        ),
    )


def test_le_dump_porte_la_procedure_stockee(db1) -> None:
    """LE test du lab, et il regarde le fichier et non le serveur.

    Mesuré sur MySQL 8.4 : `mysqldump --help` annonce `routines FALSE`, donc un
    dump pris sans `--routines` omet les procédures stockées tout en gardant
    les triggers, et sa restauration réussit avec un code 0. L'incomplétude ne
    se dit nulle part.
    """
    contenu = _contenu_du_dump(db1)
    porte_la_procedure = any(
        "PROCEDURE" in ligne.upper() and PROCEDURE in ligne
        for ligne in contenu.splitlines()
    )
    assert porte_la_procedure, message(
        en=(
            f"{DUMP} does not carry the `{PROCEDURE}` stored procedure, and it is the "
            "whole point of this lab. Measured on MySQL 8.4, `mysqldump --help` "
            "reports `routines FALSE`: procedures and functions are omitted by "
            "default, while triggers are kept. Nothing says so, the dump succeeds, "
            "the restore succeeds with exit code 0, and the application fails later "
            f"on `ERROR 1305: PROCEDURE {BASE}.{PROCEDURE} does not exist`. Add "
            "`--routines` and take the backup again."
        ),
        fr=(
            f"{DUMP} ne porte pas la procédure stockée `{PROCEDURE}`, et c'est tout "
            "l'objet de ce lab. Mesuré sur MySQL 8.4, `mysqldump --help` annonce "
            "`routines FALSE` : les procédures et les fonctions sont omises par "
            "défaut, là où les triggers sont gardés. Rien ne le dit, le dump "
            "réussit, la restauration réussit avec un code 0, et c'est "
            "l'application qui échoue plus tard sur "
            f"« ERROR 1305: PROCEDURE {BASE}.{PROCEDURE} does not exist ». Ajoute "
            "`--routines` et reprends la sauvegarde."
        ),
    )


# ── La BASE RESTAURÉE : ce qui prouve que le fichier se restaure ────────────


def test_la_base_restauree_porte_les_memes_lignes(db1) -> None:
    _exiger_la_base_restauree(db1)
    for table in TABLES:
        presente = _sql(
            db1,
            "select count(*) from information_schema.tables "
            f"where table_schema = '{RESTAUREE}' and table_name = '{table}'",
        )
        assert presente == "1", message(
            en=(
                f"`{RESTAUREE}` has no `{table}` table. The restore did not bring the "
                "schema in, or it was run against another database."
            ),
            fr=(
                f"`{RESTAUREE}` n'a pas de table `{table}`. La restauration n'a pas "
                "amené le schéma, ou elle a visé une autre base."
            ),
        )
        origine = _sql(db1, f"select count(*) from {BASE}.{table}")
        copie = _sql(db1, f"select count(*) from {RESTAUREE}.{table}")
        assert copie == origine, message(
            en=(
                f"`{RESTAUREE}.{table}` holds {copie} rows where `{BASE}.{table}` "
                f"holds {origine}. If you changed `{BASE}` after taking the dump, "
                "take it again: a backup describes the state it was taken from."
            ),
            fr=(
                f"`{RESTAUREE}.{table}` porte {copie} lignes là où `{BASE}.{table}` en "
                f"porte {origine}. Si tu as modifié `{BASE}` après avoir pris le dump, "
                "reprends-le : une sauvegarde décrit l'état d'où elle a été prise."
            ),
        )


def test_la_procedure_restauree_repond_la_meme_chose(db1) -> None:
    """Prouvé en l'appelant, et non en lisant `information_schema.routines`.

    Une procédure peut figurer au catalogue et refuser de s'exécuter, par
    exemple si son `DEFINER` ne correspond à aucun compte. C'est l'appel qui
    tranche, comme le fera l'application.
    """
    _exiger_la_base_restauree(db1)
    attendu = _sql(db1, f"call {BASE}.{PROCEDURE}()")
    r = _sql_brut(db1, f"call {RESTAUREE}.{PROCEDURE}()")
    assert r.rc == 0, message(
        en=(
            f"Calling `{RESTAUREE}.{PROCEDURE}()` fails:\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "An `ERROR 1305 ... does not exist` means the dump was taken without "
            "`--routines`: the restore succeeded, the rows are all there, the trigger "
            "too, and the procedure is simply absent. That is the failure this lab is "
            "about."
        ),
        fr=(
            f"L'appel de `{RESTAUREE}.{PROCEDURE}()` échoue :\n"
            f"{(r.stderr or r.stdout).strip()[:300]}\n"
            "Un « ERROR 1305 ... does not exist » signifie que le dump a été pris "
            "sans `--routines` : la restauration a réussi, les lignes sont toutes là, "
            "le trigger aussi, et la procédure est simplement absente. C'est la panne "
            "dont ce lab parle."
        ),
    )
    obtenu = r.stdout.strip()
    assert _meme_nombre(obtenu, attendu), message(
        en=(
            f"`{RESTAUREE}.{PROCEDURE}()` answers {obtenu!r} where `{BASE}` answers "
            f"{attendu!r}. The procedure was restored but the data it reads is not "
            "the same."
        ),
        fr=(
            f"`{RESTAUREE}.{PROCEDURE}()` répond {obtenu!r} là où `{BASE}` répond "
            f"{attendu!r}. La procédure a été restaurée mais les données qu'elle lit "
            "ne sont pas les mêmes."
        ),
    )


def test_le_trigger_restaure_declenche_vraiment(db1) -> None:
    """Le trigger est inclus PAR DÉFAUT : ce test ne garde donc pas `--triggers`.

    Il garde autre chose, et c'est pour cela qu'il existe : il distingue une
    base RESTAURÉE d'une base reconstruite à la main. Un apprenant qui
    recréerait les tables et recopierait les lignes aurait les bons comptes, et
    pas de trigger.

    La ligne témoin est retirée dans un `finally` : un test qui laisse une
    ligne derrière lui fait mentir le compte que le rapport doit décrire.
    """
    _exiger_la_base_restauree(db1)
    try:
        pose = _sql_brut(
            db1,
            f"insert into {RESTAUREE}.commandes (client_id, montant) "
            f"values ({MARQUEUR}, -99.00)",
        )
        assert pose.rc == 0, message(
            en=(
                f"Cannot insert into `{RESTAUREE}.commandes`:\n"
                f"{(pose.stderr or pose.stdout).strip()[:300]}"
            ),
            fr=(
                f"Impossible d'insérer dans `{RESTAUREE}.commandes` :\n"
                f"{(pose.stderr or pose.stdout).strip()[:300]}"
            ),
        )
        relu = _sql(
            db1,
            f"select montant from {RESTAUREE}.commandes "
            f"where client_id = {MARQUEUR}",
        )
        assert _meme_nombre(relu, "99.00"), message(
            en=(
                f"A -99.00 amount inserted into `{RESTAUREE}.commandes` reads back as "
                f"{relu!r}, where the `montant_positif` trigger should have made it "
                "99.00. So the trigger is not in the restored database: it was "
                f"probably rebuilt by hand rather than restored from {DUMP}. Triggers "
                "are included in a dump by default, so a real restore brings them in."
            ),
            fr=(
                f"Un montant -99.00 inséré dans `{RESTAUREE}.commandes` se relit "
                f"{relu!r}, là où le trigger `montant_positif` devait le rendre "
                "99.00. Le trigger n'est donc pas dans la base restaurée : elle a "
                f"probablement été reconstruite à la main au lieu d'être restaurée "
                f"depuis {DUMP}. Les triggers sont inclus par défaut dans un dump, "
                "donc une vraie restauration les amène."
            ),
        )
    finally:
        _sql_brut(
            db1, f"delete from {RESTAUREE}.commandes where client_id = {MARQUEUR}"
        )


# ── Le rapport : édité, et confronté aux outils ────────────────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-05-sauvegarder` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-05-sauvegarder` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_le_defaut_de_routines(db1) -> None:
    """La valeur attendue est lue dans le BINAIRE, pas écrite ici.

    Si une version ultérieure de MySQL changeait ce défaut, ce test suivrait et
    le lab ne noterait pas une valeur périmée.
    """
    r = db1.run("mysqldump --help")
    attendu = ""
    for ligne in r.stdout.splitlines():
        if ligne.startswith("routines ") or ligne.startswith("routines\t"):
            morceaux = ligne.split()
            if len(morceaux) >= 2:
                attendu = morceaux[1]
            break
    assert attendu, message(
        en=(
            "`mysqldump --help` does not report a `routines` line on this machine, so "
            "the report cannot be checked. Report this: the lab relies on it."
        ),
        fr=(
            "`mysqldump --help` n'annonce pas de ligne `routines` sur cette machine, "
            "donc le rapport n'est pas contrôlable. Signale-le : le lab s'appuie "
            "dessus."
        ),
    )
    ecrit = _valeur(db1, "defaut_de_routines")
    assert ecrit.upper() == attendu.upper(), message(
        en=(
            f"defaut_de_routines = {ecrit!r} in the report, but `mysqldump --help` "
            f"reports {attendu!r}. The summary of effective values at the end of the "
            "help holds one line per option."
        ),
        fr=(
            f"defaut_de_routines = {ecrit!r} dans le rapport, alors que "
            f"`mysqldump --help` annonce {attendu!r}. Le récapitulatif des valeurs "
            "effectives, à la fin de l'aide, porte une ligne par option."
        ),
    )


def test_le_rapport_compte_les_lignes_restaurees(db1) -> None:
    _exiger_la_base_restauree(db1)
    attendu = _sql(
        db1,
        "select "
        + " + ".join(f"(select count(*) from {RESTAUREE}.{t})" for t in TABLES),
    )
    ecrit = _valeur(db1, "lignes_dans_la_base_restauree")
    assert _meme_nombre(ecrit, attendu), message(
        en=(
            f"lignes_dans_la_base_restauree = {ecrit!r} in the report, but the two "
            f"tables of `{RESTAUREE}` hold {attendu!r} rows in total."
        ),
        fr=(
            f"lignes_dans_la_base_restauree = {ecrit!r} dans le rapport, alors que les "
            f"deux tables de `{RESTAUREE}` portent {attendu!r} lignes au total."
        ),
    )


def test_le_rapport_dit_le_total_de_la_procedure(db1) -> None:
    _exiger_la_base_restauree(db1)
    r = _sql_brut(db1, f"call {RESTAUREE}.{PROCEDURE}()")
    assert r.rc == 0, message(
        en=(
            f"`{RESTAUREE}.{PROCEDURE}()` does not answer, so the report cannot be "
            "checked against it."
        ),
        fr=(
            f"`{RESTAUREE}.{PROCEDURE}()` ne répond pas, donc le rapport n'est pas "
            "contrôlable par cette valeur."
        ),
    )
    attendu = r.stdout.strip()
    ecrit = _valeur(db1, "total_rendu_par_la_procedure")
    assert _meme_nombre(ecrit, attendu), message(
        en=(
            f"total_rendu_par_la_procedure = {ecrit!r} in the report, but "
            f"`call {RESTAUREE}.{PROCEDURE}()` answers {attendu!r}."
        ),
        fr=(
            f"total_rendu_par_la_procedure = {ecrit!r} dans le rapport, alors que "
            f"`call {RESTAUREE}.{PROCEDURE}()` répond {attendu!r}."
        ),
    )
