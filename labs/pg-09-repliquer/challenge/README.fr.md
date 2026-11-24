# Une seule machine porte la production

## La situation

`db1.lab` porte la base `facturation`, et elle la porte seule. Les sauvegardes
sont en place, l'archivage des journaux aussi : on sait remonter après un
incident. Ce qu'on ne sait pas faire, c'est continuer pendant.

`db2.lab` est disponible, avec PostgreSQL installé et une grappe vide qui
tourne pour rien.

On te demande d'en faire un **secondaire en flux** : une copie qui suit le
primaire en continu, prête à prendre le relais, et qu'on peut déjà interroger
en lecture pour soulager les rapports.

Trois précautions, et elles ne sont pas des détails de confort.

Le secondaire doit s'authentifier auprès du primaire. Employer `postgres` pour
cela stockerait un mot de passe de superutilisateur sur la seconde machine, et
ouvrirait un accès total au primaire si elle était compromise.

Le primaire doit **retenir** les journaux dont le secondaire a besoin. Sans
cela, un secondaire déconnecté quelques heures se réveille devant des journaux
recyclés, et il faut tout recommencer.

Enfin, la réplication n'est pas une sauvegarde : un `DROP TABLE` sur le
primaire se réplique en quelques millisecondes. Elle protège de la panne d'une
machine, pas de l'erreur humaine.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/)

## Ce qui est demandé

Deux machines. `db1.lab` porte la base `facturation` ; `db2.lab` a PostgreSQL
installé et une grappe vide qui tourne.

### 1. Préparer le primaire

Sur `db1.lab` :

- un rôle de réplication **dédié**, nommé `replicator`, qui peut se connecter
  et répliquer, et qui n'est **ni superutilisateur, ni créateur de bases**. Son
  mot de passe sera stocké sur la seconde machine : il ne doit ouvrir que la
  réplication ;
- un **slot de réplication physique** nommé `standby_slot`, pour que le
  primaire retienne les journaux dont le secondaire a besoin ;
- une règle d'accès qui autorise la réplication **depuis le réseau**, par une
  méthode qui ne transporte pas le mot de passe en clair.

Attention : la réplication est une base virtuelle. Une ligne `pg_hba` dont la
colonne base vaut `all` ne l'autorise **pas**.

### 2. Construire le secondaire

Sur `db2.lab`, remplace la grappe vide par une copie du primaire, et démarre-la
en mode secondaire.

Le répertoire de données doit être **vide** avant la copie : l'installation
Debian en a déjà posé une grappe, et `pg_basebackup` refuse d'écrire par-dessus.

Le secondaire doit employer le slot créé à l'étape 1.

### 3. Prouver que les données coulent

À la fin :

- `db2.lab` doit être en mode restauration permanente, et accepter les lectures ;
- `db1.lab` doit voir **un** secondaire à l'état `streaming` ;
- le slot doit être **actif** ;
- et surtout : une ligne écrite sur le primaire doit apparaître sur le
  secondaire. C'est le seul contrôle qui prouve quelque chose.

### 4. Remplir le rapport

Le fichier `~/rapport-replication.txt`, **sur `db1.lab`**, porte trois valeurs :

- `nb_secondaires_en_flux` : combien de secondaires `pg_stat_replication`
  compte à l'état `streaming` ;
- `slot_actif` : ce que la colonne `active` du slot répond, en une lettre ;
- `replicator_est_superuser` : ce que `rolsuper` répond pour ce rôle, en une
  lettre.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check pg-09-repliquer
```
