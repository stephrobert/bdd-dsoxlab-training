# Ce qui est demandé

Sur `db1.lab`. L'instance tourne, écoute sur le réseau, et une ligne `host`
accepte déjà le rôle `appli` sur la base `facturation`.

## 1. Poser un certificat dédié

Le serveur doit présenter un certificat qui lui est propre, et non celui que
Debian pose à l'installation (`ssl-cert-snakeoil`). Son nom commun (`CN`) doit
être `db1.lab`.

La clé privée doit être lisible **par le seul** compte `postgres` : PostgreSQL
refuse de démarrer si elle est plus ouverte, et c'est la faute la plus fréquente
sur ce sujet.

Le serveur doit ensuite présenter réellement ce certificat, pas seulement
l'avoir sur son disque.

## 2. Refuser les connexions en clair

Une connexion réseau **non chiffrée** vers `facturation` doit être **refusée**,
et une connexion chiffrée doit aboutir.

Les deux preuves attendues, depuis le compte `student` :

```bash
# doit ECHOUER
PGSSLMODE=disable psql -h <adresse-privée> -U appli -d facturation -c 'select 1'

# doit REUSSIR, et se déclarer chiffrée
PGSSLMODE=require psql -h <adresse-privée> -U appli -d facturation \
  -At -c "select ssl from pg_stat_ssl where pid = pg_backend_pid()"
```

Ne touche pas aux lignes `local` : les tests et l'administration passent par la
socket.

## 3. Séparer les droits

Trois rôles-groupes, **sans droit de connexion** : `app_owner`, `app_writer`,
`app_reader`.

- le schéma `appli` et ses tables appartiennent à `app_owner` ;
- `app_reader` peut lire les tables, et **rien d'autre** ;
- `app_writer` peut lire, insérer, modifier et supprimer des lignes ;
- les deux ont l'usage du schéma ;
- le rôle de connexion `appli` est membre de `app_writer`, et n'est plus
  propriétaire de quoi que ce soit.

## 4. Prévoir les tables à venir

Une table créée **plus tard** par `app_owner` dans le schéma `appli` doit
accorder d'elle-même ses droits aux deux autres rôles, sans intervention. Sinon
tout sera juste aujourd'hui et faux à la première migration.

## 5. Remplir le rapport

Le fichier `~/rapport-securite.txt` porte trois valeurs à compléter, toutes
lues sur le serveur :

- `cn_du_certificat` : le nom commun du certificat que le serveur présente ;
- `proprietaire_des_tables` : à qui appartiennent les tables du schéma `appli` ;
- `nb_tables_lisibles_par_reader` : combien de tables de ce schéma `app_reader`
  peut lire.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check pg-04-securiser
```
