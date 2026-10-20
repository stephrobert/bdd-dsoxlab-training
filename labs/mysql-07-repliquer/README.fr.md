# mysql-07 : une ligne qui voyage, et deux fils qu'on confond

## Ce que ce lab éprouve

La réplication GTID source-réplica, mise en service entre deux machines, et la
seule preuve qui compte : une ligne écrite sur la source, retrouvée sur le
réplica. Il ouvre le **niveau 3 MySQL** et c'est le **deuxième lab à deux
machines** du catalogue, après `pg-09-repliquer`.

Il est noté sur les **tables d'état du Performance Schema** et sur une ligne
qui voyage. Aucun test ne lit `SHOW REPLICA STATUS` : c'est un affichage de
quarante colonnes dont la forme change entre versions, là où
`replication_connection_status` et `replication_applier_status` sont des
données.

## Les trois faits mesurés qui ont décidé de sa forme

Pris le 2026-10-20 sur deux serveurs MySQL 8.4 placés sur un réseau commun,
avant d'écrire une ligne de test.

**`gtid_mode` refuse de monter d'un coup.** Le serveur répond, mot pour mot :

```text
ERROR 1788 (HY000): The value of @@GLOBAL.GTID_MODE can only be changed one
step at a time: OFF <-> OFF_PERMISSIVE <-> ON_PERMISSIVE <-> ON. Also note
that this value must be stepped up or down simultaneously on all servers.
```

C'est un bon message, et il est rare : il nomme le chemin **et** la contrainte
de simultanéité. L'énoncé le cite donc plutôt que de le paraphraser.

**Le greffon par défaut bloque le canal.** Avec `caching_sha2_password`, le
défaut de 8.4, un canal sans TLS ni clé publique reste en `CONNECTING` avec
l'erreur **2061**, « Authentication requires secure connection », et il
réessaie **toutes les 60 secondes**. Ni le mot de passe ni les privilèges ne
sont en cause, et c'est la même erreur que `mysql-04` fait rencontrer sur une
connexion applicative : la cohérence est heureuse, le greffon est le même.

**`super_read_only` n'empêche pas l'application.** C'est la mesure qui a rendu
l'énoncé soluble. Exiger à la fois un réplica en lecture seule et une ligne qui
arrive aurait pu être contradictoire ; mesuré, la ligne arrive en **1 seconde**,
l'applicateur reste `ON` et son erreur vaut `0`. Le fil d'application contourne
`super_read_only` par conception.

| Ce qu'on tente | Résultat mesuré |
|---|---|
| `INSERT` direct sur le réplica, en `labadmin` | refusé, `ERROR 1290`, « running with the --super-read-only option » |
| la même tentative avec `read_only` seul | passerait : il ne retient pas les comptes tout-puissants |
| délai d'arrivée d'une ligne, cinq mesures | 48, 49, 50, 50 et 67 millisecondes |

Le seuil des tests est à **30 secondes**. Il laisse de la marge à une machine
virtuelle chargée, et il ne sauve pas une réplication arrêtée.

## Pourquoi deux tests pour les deux fils

Le fil d'**entrée** reçoit les événements, le fil d'**application** les joue.
Un réplica connecté dont l'applicateur est arrêté prend du retard
indéfiniment, et rien ne le dit à l'écran. Les confondre est l'erreur de
diagnostic la plus fréquente, d'où deux tests et deux messages distincts.

## Un réplica part d'une copie, jamais de rien

C'est le défaut qui a fait échouer la première version du lab, et il est de ma
main : ma mesure en conteneur activait GTID AVANT de créer la base, donc sa
création portait un GTID et se répliquait. Le setup du lab la crée AVANT
d'activer GTID, donc ses transactions sont **anonymes**, et un réplica en
position automatique ne demande que des GTID.

Mesuré sur l'infrastructure du lab, sans amorçage du réplica :

    appli sur db1 : 1      appli sur db2 : 0
    applicateur   : OFF, erreur 1049
                    « Error executing row event: Unknown database 'appli' »

Le setup **sème** donc le réplica avec la même base et les mêmes lignes, comme
une restauration l'aurait fait, et les documents de l'apprenant l'annoncent. Ce
lab n'enseigne pas l'amorçage, qui demande un dump et `gtid_purged` et relève
de `mysql-05` : il le pose comme un acquis, en le disant.

La leçon de méthode vaut plus que le correctif : une mesure prise dans des
conditions qui ne sont pas celles du lab ne prouve pas que le lab marche. Les
deux diffèrent toujours d'un détail, et c'est celui-là qui casse.

## Le nom de la source ne résout pas où l'on croit

Mesuré le 2026-10-20 sur l'infrastructure du catalogue, et c'est le défaut qui
aurait rendu le lab injouable :

    depuis db2 :  getent hosts db1.lab  ->  10.10.20.14
    sur db1    :  adresse reelle        ->  10.10.100.11

Le nom ne résout donc pas « mal », il résout vers une machine d'un **autre
réseau de lab** : ce catalogue déclare `10.10.100.0/24`, et `10.10.20` est pris
par un autre dépôt. Un apprenant qui écrirait `source_host='db1.lab'`
obtiendrait une erreur de connexion dont la cause n'est ni le mot de passe, ni
les privilèges, ni le greffon.

L'énoncé demande donc de **relever l'adresse sur la source**, et dit pourquoi.
`pg-09-repliquer` contournait déjà le problème sans le nommer : sa solution
relaie l'adresse du primaire par un fait Ansible plutôt que son nom.

## Ce que ce lab ouvre délibérément, et qui surprendra

Son setup pose `bind-address = 0.0.0.0` sur les deux serveurs, là où tous les
autres labs MySQL referment l'écoute sur `127.0.0.1`. Le réplica doit joindre
la source par le réseau : c'est le contraire du sujet de `mysql-01`, et le
réseau du lab est isolé. Le README de l'apprenant ne s'en cache pas.

## Ce qu'il ne couvre pas

La **persistance des réglages** après redémarrage, qui est le sujet de
`mysql-03` : un `gtid_mode` posé pour la session suffit ici, et le README le
dit. La **promotion** du réplica et le basculement, qui demandent un point
d'entrée stable. **Group Replication** et **InnoDB Cluster**, qui sont une
autre architecture. Le **retard de réplication** sous charge, qui demande un
générateur de charge.

## Durée

50 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/)
