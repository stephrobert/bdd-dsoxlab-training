# Une instance réglée pour un ordinateur portable

## La situation

`db1.lab` porte MySQL 8.4, installé et joignable. Ses réglages, eux, sont
restés ceux du paquet.

Le buffer pool InnoDB vaut **128 Mo**, le défaut compilé. C'est le cache qui
évite les lectures disque, et sur une machine qui en a plusieurs gigaoctets,
c'est absurde. Le plafond de connexions vaut 151, et l'application en
réclamera davantage au prochain palier.

Surtout, le journal des requêtes lentes est **éteint**. On te demandera un jour
quelle requête ralentit l'application, et il n'y aura rien à lire.

On te demande donc de régler les trois, et de faire que cela **survive à un
redémarrage**. Ce dernier point n'est pas une formalité : MySQL offre trois
façons de changer une variable, et deux d'entre elles perdent le réglage au
prochain démarrage sans le dire.

Une table du serveur, `performance_schema.persisted_variables`, dit bien ce
qui a été persisté, et c'est utile. Mais elle reflète ce que le serveur a
**voulu** écrire, et non l'état du fichier : en vidant ce fichier derrière son
dos, elle continue d'annoncer la valeur. Elle prouve donc l'intention, pas
l'aller-retour.

La seule façon de savoir si une valeur reviendra est de redémarrer, donc c'est
ce que la vérification fera.

Les identifiants : le compte `labadmin`, mot de passe `Adm1n!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)

## Ce qui est demandé

Sur `db1.lab`. MySQL 8.4 tourne, le compte `labadmin` existe avec le mot de
passe `Adm1n!Lab2026`, et un login path `lab` est déjà en place pour `student`.

### 1. Relever la mémoire et les connexions

- `innodb_buffer_pool_size` doit valoir **au moins 512 Mo** ;
- `max_connections` doit valoir **au moins 300**.

### 2. Activer le journal des requêtes lentes

- `slow_query_log` actif ;
- `long_query_time` à **1** seconde ;
- la sortie dans un **fichier**, et non dans une table.

Il ne suffit pas que les variables soient posées : une requête lente devra
**réellement** apparaître dans le fichier. Le test en lancera une.

### 3. Faire que tout cela survive à un redémarrage

C'est le cœur du lab. Le test **arrêtera et relancera** le serveur, puis
relira les trois réglages.

Attention, et c'est mesuré : `performance_schema.variables_info` annonce la
**même** source après un `SET GLOBAL` et après un `SET PERSIST`, donc elle ne
dit pas si une valeur survivra. Ne te fie pas à elle pour conclure.

`performance_schema.persisted_variables`, elle, distingue les deux, et elle
t'aidera. Mais elle reflète la mémoire et non le fichier : elle prouve que le
serveur a **voulu** persister, pas qu'il relira. Seul le redémarrage le
prouve.

Et avant de redémarrer, assure-toi que ta configuration est valide : MySQL
fournit de quoi la contrôler sans démarrer le serveur. Une configuration
refusée laisse l'instance éteinte.

### 4. Remplir le rapport

Le fichier `~/rapport-configuration.txt` porte trois valeurs à compléter,
toutes lues sur le serveur **après** son redémarrage :

- `buffer_pool_mo` : la taille du buffer pool, en mégaoctets ;
- `long_query_time` : le seuil en service ;
- `source_du_buffer_pool` : ce que `variables_info` annonce comme source de
  `innodb_buffer_pool_size`. La réponse dépend de la façon dont tu l'as posée,
  et c'est tout l'intérêt de la question.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check mysql-03-configurer
```
