# Ce qui est demandé

Sur `db1.lab`. La base `facturation` porte la table `appli.journal`, cent mille
lignes, dont des dizaines de milliers sont mortes.

## 1. Rendre le serveur observable

L'extension `pg_stat_statements` doit être **chargée par le serveur** et
**créée dans la base** `facturation`.

Les deux, et pas l'une des deux : la bibliothèque se charge au démarrage, donc
un `CREATE EXTENSION` seul échoue, et une bibliothèque chargée sans extension
créée ne donne aucune vue à interroger.

Un redémarrage est autorisé ici, contrairement au lab de configuration.

## 2. Corriger la requête

Cette requête doit cesser d'être lue séquentiellement :

```sql
select count(*) from appli.journal where client_id = 42
```

Le test lit le **plan** que le planificateur produit, et exige qu'aucun
parcours séquentiel de `appli.journal` n'y figure. Créer un index que le
planificateur n'emploie pas ne compte donc pas.

Pense à ce dont le planificateur a besoin pour choisir : des statistiques à
jour.

## 3. Récupérer l'espace mort

Les lignes mortes de `appli.journal` doivent être récupérées : il doit en
rester moins de **1 %** des lignes vivantes.

`VACUUM FULL` est à éviter : il prend un verrou exclusif, donc il coupe le
service. Un `VACUUM` ordinaire suffit à rendre l'espace réutilisable.

## 4. Remplir le rapport

Le fichier `~/rapport-observation.txt` porte trois valeurs à compléter :

- `lignes_mortes_journal` : le nombre de lignes mortes restantes sur la table ;
- `nb_index_sur_journal` : le nombre d'index que porte la table ;
- `bibliotheque_chargee` : la valeur que le serveur donne pour
  `shared_preload_libraries`.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check pg-06-observer
```
