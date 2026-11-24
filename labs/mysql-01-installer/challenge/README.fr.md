# Une base posée sur le réseau sans que personne l'ait voulu

## La situation

`db1.lab` est une machine Debian 13 neuve. On te demande d'y mettre MySQL
8.4 LTS, la version au support long, depuis le dépôt d'Oracle et non depuis
celui de Debian, qui livre MariaDB sous des noms voisins.

Jusque-là, rien de remarquable. Ce qui l'est davantage, c'est ce que
l'installation laisse derrière elle.

Les paquets d'Oracle ne posent **aucune** ligne `bind-address`, pas même
commentée. Or la valeur par défaut de cette variable est `*`, soit toutes les
interfaces. À la fin d'un `apt install`, `mysqld` écoute donc sur le réseau,
sur **deux** ports : 3306 pour le protocole classique, 33060 pour le protocole
X.

Et il y a un second niveau à ce piège. `bind-address` ne restreint **pas** le
port 33060 : le protocole X a sa propre variable. Tu peux donc poser
`bind-address = 127.0.0.1`, voir `SELECT @@bind_address` te répondre
`127.0.0.1`, et laisser le 33060 grand ouvert.

On te demande donc de constater l'état réel plutôt que de le supposer, et de
fermer les deux portes. Un compte `root@localhost` protège les **comptes**, pas
le **réseau**.

Le mot de passe `root` à poser est `R00t!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/)

## Ce qui est demandé

Sur `db1.lab`, une Debian 13 neuve.

### 1. Installer MySQL 8.4 LTS depuis le dépôt d'Oracle

Le serveur doit être en version **8.4**, venir du dépôt **Oracle** et non de
celui de Debian, et sa clé de signature doit être celle d'Oracle.

Le service doit tourner **et** être activé au démarrage : une base qui ne
revient pas après un redémarrage n'est pas en service.

Le mot de passe du compte `root` doit être `R00t!Lab2026`.

### 2. Constater l'écoute réelle, puis la fermer

À la fin, `mysqld` ne doit écouter que sur la **boucle locale**, sur ses
**deux** ports.

Relève d'abord l'état réel : `sudo ss -tlnp | grep mysqld` doit montrer deux
lignes `LISTEN`. Si leur adresse est `*`, `0.0.0.0` ou `[::]`, le serveur est
ouvert à toutes les interfaces.

Attention au second port. `bind-address` ne restreint **pas** le 33060 : le
protocole X a sa propre variable. Les deux doivent valoir `127.0.0.1`, et ces
variables ne se changent pas à chaud.

### 3. Créer un compte d'administration dédié

Un compte `labadmin@localhost`, avec le mot de passe `Adm1n!Lab2026`, et tous les
droits y compris celui d'en accorder.

On ne travaille pas au quotidien avec `root` : un compte dédié se révoque sans
toucher au compte de secours.

### 4. Remplir le rapport

Le fichier `~/rapport-installation.txt` porte trois valeurs à compléter, toutes
lues sur le serveur :

- `version_du_serveur` : la version complète que le serveur annonce ;
- `bind_address_en_service` : la valeur de `@@bind_address` ;
- `mysqlx_bind_address_en_service` : celle de `@@mysqlx_bind_address`. Ce n'est
  pas la même variable, et c'est tout l'intérêt de la question.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check mysql-01-installer
```
