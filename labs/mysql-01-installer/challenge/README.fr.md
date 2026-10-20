# Ce qui est demandé

Sur `db1.lab`, une Debian 13 neuve.

## 1. Installer MySQL 8.4 LTS depuis le dépôt d'Oracle

Le serveur doit être en version **8.4**, venir du dépôt **Oracle** et non de
celui de Debian, et sa clé de signature doit être celle d'Oracle.

Le service doit tourner **et** être activé au démarrage : une base qui ne
revient pas après un redémarrage n'est pas en service.

Le mot de passe du compte `root` doit être `R00t!Lab2026`.

## 2. Constater l'écoute réelle, puis la fermer

À la fin, `mysqld` ne doit écouter que sur la **boucle locale**, sur ses
**deux** ports.

Relève d'abord l'état réel : `sudo ss -tlnp | grep mysqld` doit montrer deux
lignes `LISTEN`. Si leur adresse est `*`, `0.0.0.0` ou `[::]`, le serveur est
ouvert à toutes les interfaces.

Attention au second port. `bind-address` ne restreint **pas** le 33060 : le
protocole X a sa propre variable. Les deux doivent valoir `127.0.0.1`, et ces
variables ne se changent pas à chaud.

## 3. Créer un compte d'administration dédié

Un compte `labadmin@localhost`, avec le mot de passe `Adm1n!Lab2026`, et tous les
droits y compris celui d'en accorder.

On ne travaille pas au quotidien avec `root` : un compte dédié se révoque sans
toucher au compte de secours.

## 4. Remplir le rapport

Le fichier `~/rapport-installation.txt` porte trois valeurs à compléter, toutes
lues sur le serveur :

- `version_du_serveur` : la version complète que le serveur annonce ;
- `bind_address_en_service` : la valeur de `@@bind_address` ;
- `mysqlx_bind_address_en_service` : celle de `@@mysqlx_bind_address`. Ce n'est
  pas la même variable, et c'est tout l'intérêt de la question.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check mysql-01-installer
```
