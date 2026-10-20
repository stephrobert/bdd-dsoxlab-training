# Ce qui est demandé

Sur `db1.lab`. La base `appli` porte deux tables, une procédure stockée
`chiffre_affaires()` et un trigger `montant_positif`. Le compte `labadmin`
existe avec le mot de passe `Adm1n!Lab2026`, et `~/sauvegardes/` est vide.

## 1. Produire une sauvegarde logique COMPLÈTE

Un fichier `~/sauvegardes/appli.sql`, sauvegarde logique de la base `appli`.

**Complète** veut dire : le schéma, les données, le trigger **et la procédure
stockée**. Attention, c'est le piège du lab : les procédures ne sont **pas**
dans un dump par défaut. Regarde ce que `mysqldump --help` annonce pour
`routines`.

## 2. La restaurer dans une base NEUVE

Une base `appli_restauree`, qui reçoit le contenu du fichier. On ne restaure
pas par-dessus la base en service : c'est dans une copie qu'on prouve qu'une
sauvegarde vaut quelque chose.

## 3. Prouver que la copie est UTILISABLE

Trois preuves, et aucune ne se lit dans un catalogue :

- les **mêmes lignes** que `appli`, table par table ;
- la procédure `appli_restauree.chiffre_affaires()` **répond**, et rend la même
  valeur que celle de `appli` ;
- le trigger **déclenche** : insérer un montant négatif dans
  `appli_restauree.commandes` doit le rendre positif.

```bash
# la procedure doit repondre, et non lever un ERROR 1305
MYSQL_PWD='Adm1n!Lab2026' mysql -u labadmin -e 'call appli_restauree.chiffre_affaires()'
```

## 4. Remplir le rapport

Le fichier `~/rapport-sauvegarde.txt` porte trois valeurs à compléter :

- `defaut_de_routines` : ce que `mysqldump --help` annonce pour `routines`,
  recopié tel quel ;
- `lignes_dans_la_base_restauree` : le total des lignes des deux tables de
  `appli_restauree` ;
- `total_rendu_par_la_procedure` : ce que
  `appli_restauree.chiffre_affaires()` répond.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Ce qui n'est pas noté, et pourquoi c'est dit

`--single-transaction` est la bonne pratique, et le guide explique pourquoi.
Aucun test ne l'exige : mesuré sur MySQL 8.4, un dump pris avec et un dump pris
sans sont **indiscernables** une fois le fichier écrit, le `LOCK TABLES` y
figurant dans les deux cas. Un test qui prétendrait le vérifier noterait une
ligne de commande, pas un état. Emploie-le quand même : sur une base en
service, il évite de bloquer les écritures.

## Vérifier

```bash
dsoxlab check mysql-05-sauvegarder
```
