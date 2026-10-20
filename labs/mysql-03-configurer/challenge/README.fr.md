# Ce qui est demandé

Sur `db1.lab`. MySQL 8.4 tourne, le compte `labadmin` existe avec le mot de
passe `Adm1n!Lab2026`, et un login path `lab` est déjà en place pour `student`.

## 1. Relever la mémoire et les connexions

- `innodb_buffer_pool_size` doit valoir **au moins 512 Mo** ;
- `max_connections` doit valoir **au moins 300**.

## 2. Activer le journal des requêtes lentes

- `slow_query_log` actif ;
- `long_query_time` à **1** seconde ;
- la sortie dans un **fichier**, et non dans une table.

Il ne suffit pas que les variables soient posées : une requête lente devra
**réellement** apparaître dans le fichier. Le test en lancera une.

## 3. Faire que tout cela survive à un redémarrage

C'est le cœur du lab. Le test **arrêtera et relancera** le serveur, puis
relira les trois réglages.

Attention, et c'est mesuré : sur un serveur en marche, **rien** ne distingue
une valeur qui survivra d'une valeur qui disparaîtra. Même
`performance_schema.variables_info` annonce la même source après un
`SET GLOBAL` et après un `SET PERSIST`. Ne te fie donc pas à elle pour
conclure.

Et avant de redémarrer, assure-toi que ta configuration est valide : MySQL
fournit de quoi la contrôler sans démarrer le serveur. Une configuration
refusée laisse l'instance éteinte.

## 4. Remplir le rapport

Le fichier `~/rapport-configuration.txt` porte trois valeurs à compléter,
toutes lues sur le serveur **après** son redémarrage :

- `buffer_pool_mo` : la taille du buffer pool, en mégaoctets ;
- `long_query_time` : le seuil en service ;
- `source_du_buffer_pool` : ce que `variables_info` annonce comme source de
  `innodb_buffer_pool_size`. La réponse dépend de la façon dont tu l'as posée,
  et c'est tout l'intérêt de la question.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check mysql-03-configurer
```
