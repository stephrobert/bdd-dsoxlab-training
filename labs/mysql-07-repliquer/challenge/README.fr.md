# Deux serveurs qui s'ignorent, et une sauvegarde qui ne suffit plus

## La situation

`db1.lab` sert la base `appli` en production. `db2.lab` existe, MySQL y tourne,
et les deux serveurs ne se connaissent pas.

Le réplica a déjà reçu une **copie** de la base, restaurée depuis la sauvegarde
de la veille : il porte les mêmes tables et les mêmes lignes. C'est un acquis
de ce lab, et ce n'est pas un détail : un réplica ne part jamais de rien. Sans
cette copie, son fil d'application s'arrête à la première transaction sur une
erreur `1049`, « Unknown database », mesuré.

La sauvegarde quotidienne protège d'une suppression accidentelle, elle ne
protège pas d'une panne matérielle : le temps de restaurer, le service est à
terre. On te demande donc un **réplica**, qui suit la source en continu et que
l'on peut promouvoir.

Trois choses à savoir avant de commencer, et les deux premières vont te coûter
une erreur si tu les ignores.

**`gtid_mode` refuse de passer de OFF à ON d'un coup.** Le serveur répond alors
une erreur `1788` qui nomme le chemin, et il précise que la valeur doit monter
**simultanément sur tous les serveurs**. Lis le message, il dit tout.

**Le greffon d'authentification par défaut bloque la connexion du réplica.**
Avec `caching_sha2_password`, le réplica reste en `CONNECTING` sur une erreur
`2061` qui parle de « secure connection », et il réessaie toutes les 60
secondes. Ce n'est ni le mot de passe ni les privilèges.

**`SHOW REPLICA STATUS` est un affichage, pas une preuve.** La vérification lit
les **tables d'état** du Performance Schema, et surtout elle écrit une ligne
sur la source puis la cherche sur le réplica. Une réplication qui annonce
`ON` sans rien transporter existe, et c'est la panne qu'on ne voit pas.

**Et ne configure pas le canal sur le nom `db1.lab`.** Mesuré sur cette
infrastructure : depuis `db2`, ce nom résout vers une machine d'un **autre
réseau de lab**, pas vers la source. Relève l'adresse de la source **sur la
source**, par exemple avec `ip -4 addr show`, et emploie-la. On ne configure
pas une réplication sur un nom qu'on n'a pas vérifié.

Les identifiants : le compte d'administration `labadmin` sur les **deux**
serveurs, mot de passe `Adm1n!Lab2026`. Le compte de réplication à créer
s'appellera `replicator`, avec le mot de passe `R3pl!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/)

## Ce qui est demandé

Deux machines. `db1.lab` est la **source**, elle porte la base `appli` et sa
table `clients`. `db2.lab` est le futur **réplica** : MySQL y tourne, il a déjà
reçu une **copie** de la base restaurée depuis une sauvegarde, et il ignore
tout de la source. Le compte `labadmin` existe sur les deux, mot de passe
`Adm1n!Lab2026`.

Cette copie n'est pas un décor. Sans elle, le fil d'application du réplica
s'arrête à la première transaction sur une erreur `1049`, « Unknown
database » : un réplica suit une base, il ne la crée pas.

### 1. Activer GTID sur les deux serveurs

`gtid_mode` doit valoir `ON` et `enforce_gtid_consistency` aussi, **sur la
source et sur le réplica**.

Attention : `gtid_mode` **refuse de passer de OFF à ON d'un coup**. Le serveur
répond une erreur `1788` qui nomme le chemin, et qui précise que la valeur doit
monter simultanément sur tous les serveurs. Lis le message, il dit tout.

### 2. Créer le compte de réplication, et lui seulement ce qu'il faut

Un compte `replicator` avec le mot de passe `R3pl!Lab2026`, joignable depuis le
réplica, qui détient `REPLICATION SLAVE` et **rien de plus**. Un `SELECT`
global lui donnerait la base `mysql` et ses empreintes de mots de passe.

### 3. Brancher le réplica, et le faire tourner

Le canal se crée par `CHANGE REPLICATION SOURCE TO`, avec la position
automatique, puis `START REPLICA`.

**Emploie l'ADRESSE de la source, pas son nom.** Mesuré : depuis `db2`, le nom
`db1.lab` résout vers une machine d'un autre réseau de lab. Relève l'adresse
sur la source :

```bash
# sur db1
ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1
```

Les **deux fils** doivent tourner, et ce sont deux choses distinctes :

```sql
SELECT service_state, last_error_number, last_error_message
  FROM performance_schema.replication_connection_status;   -- le fil d'entrée

SELECT service_state
  FROM performance_schema.replication_applier_status;      -- le fil d'application
```

Attention au second piège : avec le greffon d'authentification par défaut, le
canal reste en `CONNECTING` sur une erreur **2061** qui parle de « secure
connection », et il réessaie toutes les 60 secondes. Ce n'est ni le mot de
passe ni les privilèges. Deux issues existent, l'une donne du TLS au canal,
l'autre lui fait récupérer la clé publique de la source.

### 4. Interdire les écritures directes sur le réplica

`super_read_only` doit être actif, et un `INSERT` depuis `labadmin` doit être
**refusé**. `read_only` seul ne suffit pas : il laisse passer les comptes qui
détiennent tous les privilèges.

Rassure-toi, c'est mesuré : `super_read_only` n'empêche **pas** le fil
d'application de jouer les transactions venues de la source.

### 5. Prouver qu'une ligne voyage

La vérification écrit une ligne sur la source et la cherche sur le réplica.
Aucune table d'état ne remplace cette preuve : une réplication qui annonce `ON`
sans rien transporter existe.

### 6. Remplir le rapport

Le fichier `~/rapport-replication.txt`, sur la source, porte trois valeurs :

- `etat_de_la_connexion` : ce que le fil d'entrée du réplica annonce ;
- `uuid_de_la_source` : l'identifiant du serveur source, que le réplica voit
  aussi ;
- `lignes_sur_le_replica` : combien de lignes la table porte sur le réplica.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check mysql-07-repliquer
```
