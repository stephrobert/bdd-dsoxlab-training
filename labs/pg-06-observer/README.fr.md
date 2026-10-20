# pg-06 : observer, identifier, corriger

## Ce que ce lab éprouve

La démarche du guide, de bout en bout, sur un seul cas : **observer** avec
`pg_stat_statements`, **identifier** avec `EXPLAIN`, **corriger** avec un index,
et **maintenir** avec `VACUUM`.

## Le piège qu'il fait rencontrer

**Un index présent n'est pas un index employé.** C'est le cas le plus fréquent,
et le plus coûteux : on crée l'index, la requête reste lente, et on cherche
ailleurs. Le lab ne note donc jamais l'existence d'un index. Il lit le **plan**
de la requête et exige que le parcours séquentiel ait disparu : c'est le
planificateur qui dit si la correction a porté, pas le catalogue.

Second piège, du même genre : `pg_stat_statements` ne s'installe pas d'un
`CREATE EXTENSION`. La bibliothèque doit être chargée **au démarrage du
serveur**, ce qui en fait un paramètre de contexte `postmaster`. Un
`CREATE EXTENSION` sur un serveur qui ne l'a pas préchargée échoue, et le
message ne dit pas quoi faire.

## Ce qu'il ne couvre pas

Le réglage fin de l'autovacuum table par table, et les métriques Prometheus,
que le guide range en « aller plus loin ». `VACUUM FULL`, qui prend un verrou
exclusif et n'a pas sa place sur une table en service.

## Durée

40 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/)
