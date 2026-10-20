# pg-05 : sauvegarder en logique, et le prouver

## Ce que ce lab éprouve

Une sauvegarde est un geste en trois temps, et les deux derniers sont ceux
qu'on saute.

**Produire** le dump, au format custom, celui qui permet une restauration
sélective. **Capturer ce que le dump ne contient pas** : les rôles, globaux au
cluster. **Restaurer** dans une base de vérification et comparer son contenu à
l'original, table par table.

Le lab est noté sur le contenu restauré, pas sur l'existence d'un fichier. Un
dump de 5 Ko sur le disque ne prouve rien du tout.

## Les deux pièges qu'il fait rencontrer

`pg_dump` **ne sauvegarde pas les rôles**. Le guide le dit mot pour mot : ils
sont globaux au cluster. Restaurer ce dump sur une machine neuve échoue alors
sur chaque propriétaire et chaque droit, et on le découvre le jour de
l'incident. `pg_dumpall --globals-only` est l'autre moitié de la sauvegarde.

Un dump au format **plain** (`-Fp`) n'est pas lisible par `pg_restore` : c'est
un script SQL, qu'on rejoue par `psql`. Le format décide des outils de
restauration disponibles, donc il se choisit au moment de la sauvegarde, pas au
moment de l'incident.

## Ce qu'il ne couvre pas

La sauvegarde physique (`pg_basebackup`), l'archivage des WAL et la
restauration à un instant donné, qui demandent une continuité d'archives et
appartiennent au niveau 2.

## Durée

35 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
