# Une requête lente, et rien pour le dire

L'application se plaint d'une page qui met plusieurs secondes à répondre. Elle
interroge la table `appli.journal`, qui porte cent mille lignes.

Tu te connectes sur `db1.lab` pour voir quelles requêtes coûtent cher. Il n'y a
rien à voir : l'extension qui collecte ces statistiques n'est pas chargée. Le
serveur travaille, et ne garde aucune trace de ce qu'il a fait.

Tu finis par trouver la requête dans le code de l'application :

```sql
select count(*) from appli.journal where client_id = 42
```

Il reste un second problème, que personne n'a signalé parce qu'il ne se voit
pas depuis l'application : une purge a supprimé des dizaines de milliers de
lignes de cette table, et l'espace qu'elles occupaient n'a jamais été rendu.
L'autovacuum a été désactivé sur cette table lors d'une opération, et jamais
réactivé.

Trois gestes, dans cet ordre : rendre le serveur observable, corriger la
requête, récupérer l'espace.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/)
