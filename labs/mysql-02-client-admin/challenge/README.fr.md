# Un mot de passe qui traîne, et un serveur qui ne dit rien

## La situation

L'instance MySQL de `db1.lab` tourne, fermée sur sa boucle locale, et le
compte d'administration `labadmin` existe. Trois choses manquent pour qu'on
puisse travailler avec.

La première se voit dans l'historique du shell. Les scripts de l'équipe
appellent `mysql -ulabadmin -p'...'`, donc le mot de passe est sur la ligne de
commande : il se lit dans `ps`, dans l'historique, et dans les journaux
d'audit. MySQL fournit de quoi l'éviter.

La deuxième est que l'application n'a aucun objet : ni base, ni table.

La troisième ne se voit pas du tout, et c'est la plus intéressante. Quelqu'un a
éteint le **Performance Schema** pour gagner quelques mégaoctets, et ne l'a
jamais rallumé. Toute la famille de vues `sys` qui sert à diagnostiquer une
lenteur est donc muette. Ce n'est pas une variable qu'un `SET` rallume : elle
se lit au démarrage.

Enfin, on te demande d'installer **MySQL Shell**, le client que l'équipe veut
employer pour ses scripts.

Les identifiants : le compte `labadmin`, mot de passe `Adm1n!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/)

## Ce qui est demandé

Sur `db1.lab`, depuis le compte `student`. L'instance tourne, le compte
`labadmin` existe avec le mot de passe `Adm1n!Lab2026`.

### 1. Ranger les identifiants dans un login path

Enregistre un profil nommé `lab` pour le compte `student`, de sorte qu'un
script se connecte **sans mot de passe sur la ligne de commande**.

La preuve attendue, depuis `student`, sans variable `MYSQL_PWD` et sans
terminal :

```bash
mysql --login-path=lab -N -B -e 'select current_user()' < /dev/null
```

Elle doit répondre `labadmin@localhost`.

Attention à l'hôte. En MySQL, `@localhost` désigne la **socket Unix** : un
profil qui déclare `--host=127.0.0.1` cherche un compte `@127.0.0.1`, qui est
un autre compte, et la connexion est refusée.

### 2. Créer les objets de l'application

Une base `appli`, et dedans une table `clients` portant au moins les colonnes
`id` et `nom`, avec **au moins trois lignes**, en moteur **InnoDB**.

### 3. Rendre le serveur observable

Le **Performance Schema** doit être actif.

Ce n'est pas une variable qu'un `SET` rallume : elle est en lecture seule une
fois le serveur lancé. Un `SET GLOBAL` répond une erreur, et un `SET PERSIST`
l'écrit sans l'appliquer.

### 4. Installer MySQL Shell

Le client `mysqlsh` doit être installé et joindre l'instance.

Il vit dans le même composant du dépôt d'Oracle que le serveur : aucun dépôt à
ajouter.

### 5. Remplir le rapport

Le fichier `~/rapport-client.txt` porte trois valeurs à compléter :

- `performance_schema_actif` : ce que `@@performance_schema` répond ;
- `nb_tables_appli` : le nombre de tables de la base `appli` ;
- `moteur_de_la_table_clients` : le moteur de stockage de `appli.clients`.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check mysql-02-client-admin
```
