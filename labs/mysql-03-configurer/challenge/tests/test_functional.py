"""mysql-03-configurer : des réglages qui survivent, et un journal qui écrit.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup laisse donc les
réglages du paquet, et deux précautions qui ne sont pas des ornements :

- `mysqld-auto.cnf` est EFFACÉ, parce que c'est là que `SET PERSIST` écrit.
  Sans cela, le travail d'un passage précédent survivrait au nettoyage et
  trois tests seraient verts avant tout travail ;
- le journal lent est éteint par un fichier explicite ET son fichier de sortie
  est retiré, parce qu'un journal laissé par un passage précédent rendrait
  vert le test qui exige qu'une requête y atterrisse.

POURQUOI UN TEST REDÉMARRE LE SERVEUR

Parce que rien d'autre ne prouve l'ALLER-RETOUR. Mesuré sur MySQL 8.4 le
2026-10-20, dans un conteneur jetable, et la première version de ce commentaire
concluait trop vite :

    valeur laissee au defaut   variables_info COMPILED  persisted_variables vide
    apres SET GLOBAL           variables_info DYNAMIC   persisted_variables vide
    apres SET PERSIST          variables_info DYNAMIC   la valeur y figure
    apres RESET PERSIST        -                        vide, valeur en service

`variables_info` répond donc identiquement après un `SET GLOBAL` perdu au
redémarrage et après un `SET PERSIST` qui survivra : un test qui lirait cette
source conclurait au vert sur un réglage volatile.

`persisted_variables`, en revanche, distingue bien les deux. Ce n'est donc pas
vrai que « rien » ne les distingue, et je l'avais écrit.

MAIS elle reflète la MÉMOIRE et non le fichier, et c'est la sonde qui tranche :
en vidant `mysqld-auto.cnf` derrière le dos du serveur, SANS redémarrer, la
table continue d'annoncer la valeur. Elle prouve que le serveur a VOULU
persister, pas que le fichier est intact ni qu'il sera relu.

Le redémarrage reste donc la seule preuve de l'aller-retour, et c'est une
raison plus précise que « faute d'autre preuve ».

CE QUE LE JOURNAL LENT EST NOTÉ SUR

Une requête lente qui y atterrit VRAIMENT. Trois variables doivent tenir
ensemble, et un fichier doit être accessible au compte du serveur : un journal
activé dont rien ne sort ne sert à personne, et c'est le cas le plus fréquent.
"""

from __future__ import annotations

import time

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("db1.lab")
RAPPORT = "/home/student/rapport-configuration.txt"
PLACEHOLDER = "A_COMPLETER"
SENTINELLE = "# Rapport de configuration de l'instance MySQL."

ADMIN = "labadmin"
MDP_ADMIN = "Adm1n!Lab2026"
BUFFER_MO_MINIMUM = 512
MAX_CONN_MINIMUM = 300
SEUIL_LENT = 1.0


@pytest.fixture(scope="module")
def db1():
    return lab_host(CIBLE)


def _mysql(db1, sql: str) -> str:
    r = db1.run("env MYSQL_PWD=%s mysql -u %s -N -B -e %s", MDP_ADMIN, ADMIN, sql)
    assert r.rc == 0, message(
        en=(
            f"Cannot query the server: {(r.stderr or r.stdout).strip()[:300]}\n"
            "If it does not answer at all, a refused configuration may have left it "
            "down: `mysqld --validate-config` says what it refuses."
        ),
        fr=(
            f"Impossible d'interroger le serveur : {(r.stderr or r.stdout).strip()[:300]}\n"
            "S'il ne répond plus du tout, une configuration refusée l'a peut-être "
            "laissé éteint : `mysqld --validate-config` dit ce qu'elle refuse."
        ),
    )
    return r.stdout.strip()


def _rapport(db1) -> str:
    f = db1.file(RAPPORT)
    assert f.exists, message(
        en=f"{RAPPORT} is missing. `dsoxlab reset mysql-03-configurer` gives it back.",
        fr=f"{RAPPORT} est absent. `dsoxlab reset mysql-03-configurer` te le rend.",
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


# ── Les réglages sont effectifs ─────────────────────────────────────────────


def test_la_memoire_et_les_connexions_sont_relevees(db1) -> None:
    octets = int(_mysql(db1, "select @@innodb_buffer_pool_size"))
    mo = octets // (1024 * 1024)
    assert mo >= BUFFER_MO_MINIMUM, message(
        en=(
            f"innodb_buffer_pool_size is {mo} MB, at least {BUFFER_MO_MINIMUM} are "
            "expected. 128 MB is the compiled default: the cache that avoids disk "
            "reads is then absurd on a machine with gigabytes."
        ),
        fr=(
            f"innodb_buffer_pool_size vaut {mo} Mo, on en attend au moins "
            f"{BUFFER_MO_MINIMUM}. 128 Mo est le défaut compilé : le cache qui évite "
            "les lectures disque est alors absurde sur une machine qui a des "
            "gigaoctets."
        ),
    )

    connexions = int(_mysql(db1, "select @@max_connections"))
    assert connexions >= MAX_CONN_MINIMUM, message(
        en=(
            f"max_connections is {connexions}, at least {MAX_CONN_MINIMUM} are "
            "expected."
        ),
        fr=(
            f"max_connections vaut {connexions}, on en attend au moins "
            f"{MAX_CONN_MINIMUM}."
        ),
    )


def test_le_journal_lent_est_arme_et_ecrit_dans_un_fichier(db1) -> None:
    """Trois variables doivent tenir ensemble, pas une.

    `slow_query_log` seule ne suffit pas : sans `long_query_time` au bon
    seuil, rien n'est lent ; et sans `log_output` à FILE, la sortie part dans
    la table `mysql.slow_log` et aucun fichier n'apparaît.
    """
    actif = _mysql(db1, "select @@slow_query_log")
    assert actif == "1", message(
        en=(
            "slow_query_log is off: nobody will be able to say which query is slow. "
            "Turn it on, and make the setting survive a restart."
        ),
        fr=(
            "slow_query_log est éteint : personne ne pourra dire quelle requête est "
            "lente. Active-le, et fais que le réglage survive à un redémarrage."
        ),
    )

    seuil = float(_mysql(db1, "select @@long_query_time"))
    assert seuil == SEUIL_LENT, message(
        en=(
            f"long_query_time is {seuil}, expected {SEUIL_LENT}. The default is 10 "
            "seconds, which logs almost nothing."
        ),
        fr=(
            f"long_query_time vaut {seuil}, attendu {SEUIL_LENT}. Le défaut est de 10 "
            "secondes, ce qui ne journalise presque rien."
        ),
    )

    sortie = _mysql(db1, "select @@log_output")
    assert "FILE" in sortie.upper(), message(
        en=(
            f"log_output is {sortie!r}: the slow log goes to the `mysql.slow_log` "
            "table and no file appears. The brief asks for a file."
        ),
        fr=(
            f"log_output vaut {sortie!r} : le journal lent part dans la table "
            "`mysql.slow_log` et aucun fichier n'apparaît. La consigne demande un "
            "fichier."
        ),
    )


def test_une_requete_lente_atterrit_vraiment_dans_le_journal(db1) -> None:
    """Le seul test qui prouve que le journal SERT.

    Un journal activé dont rien ne sort est le cas le plus fréquent : fichier
    que le compte du serveur ne peut pas écrire, répertoire absent, seuil mal
    compris. Aucune variable ne le dit, seule une requête le prouve.

    La requête dort deux secondes au-dessus du seuil demandé : elle ne mesure
    donc pas la machine, seulement le dépassement.
    """
    fichier = _mysql(db1, "select @@slow_query_log_file")
    assert fichier, message(
        en="slow_query_log_file is empty: the server has no file to write to.",
        fr="slow_query_log_file est vide : le serveur n'a aucun fichier où écrire.",
    )

    marque = f"marque_lab_{int(time.time())}"
    lente = db1.run(
        "env MYSQL_PWD=%s mysql -u %s -N -B -e %s",
        MDP_ADMIN,
        ADMIN,
        f"select sleep(2), '{marque}'",
    )
    assert lente.rc == 0, message(
        en=f"The slow query itself failed: {(lente.stderr or lente.stdout).strip()[:200]}",
        fr=f"La requête lente elle-même a échoué : {(lente.stderr or lente.stdout).strip()[:200]}",
    )

    # Le serveur écrit le journal de façon asynchrone : on laisse le temps, et
    # on relit, plutôt que de conclure sur un premier coup d'oeil.
    for _ in range(10):
        trouve = db1.run("grep -c %s %s", marque, fichier)
        if trouve.rc == 0 and trouve.stdout.strip() not in ("", "0"):
            return
        time.sleep(1)

    raise AssertionError(
        message(
            en=(
                f"The slow query never reached {fichier}. The variables may be set and "
                "nothing written: check that the file's directory exists and belongs "
                "to the `mysql` account. A log that cannot be written is a silent log, "
                "and no variable says so."
            ),
            fr=(
                f"La requête lente n'est jamais arrivée dans {fichier}. Les variables "
                "peuvent être posées et rien écrit : contrôle que le répertoire du "
                "fichier existe et appartient au compte `mysql`. Un journal qui ne "
                "peut pas s'écrire est un journal silencieux, et aucune variable ne le "
                "dit."
            ),
        )
    )


# ── Et tout cela survit au redémarrage ──────────────────────────────────────


def test_les_reglages_demandes_survivent_a_un_redemarrage(db1) -> None:
    """LE test du lab, et il redémarre le serveur à dessein.

    Rien d'autre ne prouve l'ALLER-RETOUR : mesuré sur MySQL 8.4, `SET PERSIST`
    et `SET GLOBAL` annoncent la MÊME source, `DYNAMIC`, sur un serveur en
    marche. La source ne devient `PERSISTED` qu'après le redémarrage.

    Un test qui lirait cette source conclurait donc au vert sur un réglage
    volatile, ce qui est exactement la faute que ce lab existe pour attraper.

    `performance_schema.persisted_variables`, elle, distingue bien les deux, et
    la docstring du module dit ce qu'elle prouve au juste : l'intention de
    persister, et non la relecture du fichier.

    CE QUE CE TEST EXIGE, ET POURQUOI CE N'EST PAS « RIEN N'A CHANGÉ »

    Il l'a été, et il était VERT sur l'état de départ : les valeurs PAR DÉFAUT
    survivent très bien à un redémarrage. Exiger l'égalité avant et après ne
    mesurait donc qu'une tautologie, et le pilote du catalogue l'a refusé.

    Il exige maintenant, APRÈS le redémarrage, les valeurs DEMANDÉES. Un
    apprenant qui a employé `SET GLOBAL` les voit retomber aux défauts : les
    seuils échouent, et la persistance est prouvée par eux. La capture
    avant/après est gardée pour le MESSAGE, parce que « 512 Mo avant, 128 Mo
    après » diagnostique mieux que « 128 Mo est trop peu ».

    Les tests qui suivent lisent le serveur APRÈS ce redémarrage, ce qui est
    voulu : le rapport doit décrire l'état qui tient, pas celui qui passait.
    """
    avant = {
        "innodb_buffer_pool_size": _mysql(db1, "select @@innodb_buffer_pool_size"),
        "max_connections": _mysql(db1, "select @@max_connections"),
        "slow_query_log": _mysql(db1, "select @@slow_query_log"),
        "long_query_time": _mysql(db1, "select @@long_query_time"),
    }

    # La configuration est contrôlée AVANT le redémarrage : une configuration
    # refusée laisserait l'instance éteinte, et le message parlerait alors
    # d'un serveur injoignable plutôt que de sa cause.
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

    for _ in range(30):
        if db1.run("mysqladmin ping --socket=/var/run/mysqld/mysqld.sock").rc == 0:
            break
        time.sleep(2)

    # Les valeurs DEMANDÉES, après le redémarrage. Les mêmes seuils que le
    # premier test, et c'est le point : ce qui comptait avant doit compter
    # encore après, sinon ce n'était pas une configuration.
    apres = {
        variable: _mysql(db1, f"select @@{variable}") for variable in avant
    }
    mo_apres = int(apres["innodb_buffer_pool_size"]) // (1024 * 1024)

    manques = []
    if mo_apres < BUFFER_MO_MINIMUM:
        manques.append(
            f"innodb_buffer_pool_size : {mo_apres} Mo après le redémarrage, "
            f"{int(avant['innodb_buffer_pool_size']) // (1024 * 1024)} Mo avant, "
            f"au moins {BUFFER_MO_MINIMUM} attendus"
        )
    if int(apres["max_connections"]) < MAX_CONN_MINIMUM:
        manques.append(
            f"max_connections : {apres['max_connections']} après, "
            f"{avant['max_connections']} avant, au moins {MAX_CONN_MINIMUM} attendus"
        )
    if apres["slow_query_log"] != "1":
        manques.append(
            f"slow_query_log : {apres['slow_query_log']} après, "
            f"{avant['slow_query_log']} avant, attendu 1"
        )
    if float(apres["long_query_time"]) != SEUIL_LENT:
        manques.append(
            f"long_query_time : {apres['long_query_time']} après, "
            f"{avant['long_query_time']} avant, attendu {SEUIL_LENT}"
        )

    assert not manques, message(
        en=(
            "These settings are NOT in place after the restart:\n  "
            + "\n  ".join(manques)
            + "\nA `SET GLOBAL` changes the running server and is lost at the next "
            "start, without a word: that is why the values before the restart may "
            "have been right. `SET PERSIST` writes them to `mysqld-auto.cnf`, and a "
            "line in a `.cnf` file works too. What does not work is believing the "
            "source reported on a running server: it is the same in both cases."
        ),
        fr=(
            "Ces réglages ne sont PAS en place après le redémarrage :\n  "
            + "\n  ".join(manques)
            + "\nUn `SET GLOBAL` change le serveur en marche et se perd au prochain "
            "démarrage, sans un mot : c'est pourquoi les valeurs d'avant le "
            "redémarrage pouvaient être justes. `SET PERSIST` les écrit dans "
            "`mysqld-auto.cnf`, et une ligne dans un fichier `.cnf` marche aussi. Ce "
            "qui ne marche pas, c'est de croire la source annoncée sur un serveur en "
            "marche : elle est la même dans les deux cas."
        ),
    )


# ── Le rapport : édité, et confronté au serveur redémarré ───────────────────


def test_le_rapport_a_ete_edite_et_non_recree(db1) -> None:
    contenu = _rapport(db1)
    assert SENTINELLE in contenu, message(
        en=(
            f"The header of {RAPPORT} is gone: the file was recreated instead of "
            "edited. `dsoxlab reset mysql-03-configurer` gives it back."
        ),
        fr=(
            f"L'en-tête de {RAPPORT} a disparu : le fichier a été recréé au lieu "
            "d'être édité. `dsoxlab reset mysql-03-configurer` te le rend."
        ),
    )
    valeurs = "\n".join(
        ligne for ligne in contenu.splitlines() if not ligne.strip().startswith("#")
    )
    assert PLACEHOLDER not in valeurs, message(
        en=f"{RAPPORT} still holds {PLACEHOLDER}: at least one value is not filled in.",
        fr=f"{RAPPORT} porte encore {PLACEHOLDER} : au moins une valeur n'est pas remplie.",
    )


def test_le_rapport_dit_la_taille_du_buffer_pool(db1) -> None:
    attendu = str(int(_mysql(db1, "select @@innodb_buffer_pool_size")) // (1024 * 1024))
    ecrit = _valeur(db1, "buffer_pool_mo")
    assert ecrit == attendu, message(
        en=(
            f"buffer_pool_mo = {ecrit!r} in the report, but the server answers "
            f"{attendu!r} MB. `select @@innodb_buffer_pool_size / 1024 / 1024` gives "
            "it."
        ),
        fr=(
            f"buffer_pool_mo = {ecrit!r} dans le rapport, alors que le serveur répond "
            f"{attendu!r} Mo. `select @@innodb_buffer_pool_size / 1024 / 1024` le "
            "donne."
        ),
    )


def test_le_rapport_dit_le_seuil_de_lenteur(db1) -> None:
    attendu = _mysql(db1, "select @@long_query_time")
    ecrit = _valeur(db1, "long_query_time")
    assert ecrit == attendu, message(
        en=(
            f"long_query_time = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. Copy what it says, decimals included."
        ),
        fr=(
            f"long_query_time = {ecrit!r} dans le rapport, alors que le serveur répond "
            f"{attendu!r}. Recopie ce qu'il dit, décimales comprises."
        ),
    )


def test_le_rapport_dit_la_source_du_buffer_pool(db1) -> None:
    """La question dont la réponse dépend de la méthode, et c'est voulu.

    Lue APRÈS le redémarrage, cette source distingue enfin les méthodes : un
    `SET PERSIST` donne `PERSISTED`, une ligne dans un `.cnf` donne une source
    de fichier. Avant le redémarrage, les deux répondaient `DYNAMIC`.
    """
    attendu = _mysql(
        db1,
        "select variable_source from performance_schema.variables_info "
        "where variable_name = 'innodb_buffer_pool_size'",
    )
    ecrit = _valeur(db1, "source_du_buffer_pool")
    assert ecrit.upper() == attendu.upper(), message(
        en=(
            f"source_du_buffer_pool = {ecrit!r} in the report, but the server answers "
            f"{attendu!r}. Read it AFTER the restart: before it, a persisted value and "
            "a volatile one both report `DYNAMIC`."
        ),
        fr=(
            f"source_du_buffer_pool = {ecrit!r} dans le rapport, alors que le serveur "
            f"répond {attendu!r}. Lis-la APRÈS le redémarrage : avant, une valeur "
            "persistée et une valeur volatile répondent toutes deux « DYNAMIC »."
        ),
    )
