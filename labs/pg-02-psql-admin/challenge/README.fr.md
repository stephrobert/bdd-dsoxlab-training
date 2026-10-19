# Ce qui est demandé

Sur `db1.lab`, depuis le compte `student`.

## 1. Rendre l'instance joignable depuis le réseau

Le serveur doit écouter sur sa boucle locale **et** sur son adresse privée.
Une connexion réseau vers la base `facturation` avec le rôle `appli` doit être
acceptée, par une méthode qui ne transporte pas le mot de passe en clair.

`trust` et `password` sont refusés sur une ligne réseau : le premier n'exige
rien, le second envoie le mot de passe tel quel.

## 2. Permettre à un script de se connecter sans mot de passe tapé

Pose le fichier de mots de passe de `student` pour le rôle `appli`. Il doit
être réellement pris en compte par psql, ce qui dépend autant de ses
permissions que de son contenu.

La preuve attendue : depuis le compte `student`, sans variable
`PGPASSWORD` et sans terminal, cette commande doit répondre `1`.

```bash
psql -h <adresse-privée> -U appli -d facturation -At -c 'select 1' < /dev/null
```

## 3. Créer les objets du service

Dans la base `facturation` : un schéma `appli`, et dedans une table `clients`
portant au moins les colonnes `id` et `nom`, avec **au moins deux lignes**.

La table doit appartenir au rôle `appli`, pas à `postgres`.

## 4. Remplir le rapport

Le fichier `~/rapport-psql.txt` porte quatre lignes à compléter. Lis les
valeurs sur le serveur, ne les devine pas : elles sont comparées à ce qu'il
répond.

- `server_version`
- `listen_addresses`
- `data_checksums`
- `nb_tables_schema_appli` : le nombre de tables du schéma `appli`

**Édite le fichier sur place.** Son en-tête doit survivre : il disparaît si tu
recrées le fichier avec une redirection `>`, et le test le refuse.

## Vérifier

```bash
dsoxlab check pg-02-psql-admin
```
