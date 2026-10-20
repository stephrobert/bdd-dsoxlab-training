# Ce qui est demandé

Sur `db1.lab`. La base `facturation` porte un schéma `appli` avec ses tables
remplies. Le répertoire `/var/backups/postgresql/` existe et appartient à
`postgres`.

## 1. Sauvegarder la base

Dépose dans `/var/backups/postgresql/` un dump de `facturation` au **format
custom**, celui qui autorise une restauration sélective.

Le fichier doit être réellement lisible par `pg_restore`, et porter les deux
tables du schéma `appli`. Un dump au format `plain` ne passe pas : ce n'est pas
un dump, c'est un script SQL.

## 2. Sauvegarder ce que le dump ne contient pas

Les rôles sont **globaux au cluster** : `pg_dump` ne les sauvegarde pas.
Capture-les dans `/var/backups/postgresql/globals.sql`.

Sans eux, une restauration sur une machine neuve échoue sur chaque
propriétaire et chaque droit.

## 3. Prouver que la sauvegarde se restaure

Restaure le dump dans une base **neuve** nommée `facturation_verif`, distincte
de l'originale, qui doit en sortir avec le même contenu : les mêmes tables, et
le même nombre de lignes dans chacune.

C'est la seule des trois étapes qui prouve quelque chose. Les deux premières
produisent des fichiers ; celle-ci dit s'ils valent quelque chose.

## 4. Remplir le rapport

Le fichier `~/rapport-sauvegarde.txt` porte trois valeurs à compléter :

- `format_du_dump` : le format que `pg_restore` annonce pour ton dump, en un
  mot et en minuscules ;
- `nb_lignes_clients_restaurees` : le nombre de lignes de `appli.clients` dans
  la base de vérification ;
- `nb_roles_sauvegardes` : le nombre de rôles que porte `globals.sql`.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check pg-05-sauvegarder
```
