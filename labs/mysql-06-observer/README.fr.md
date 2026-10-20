# mysql-06 : le plan et la taille, deux états que rien ne devine

## Ce que ce lab éprouve

Les trois gestes d'exploitation qu'un guide énumère et que personne ne prouve :
rendre une requête rapide, récupérer l'espace d'une purge, et retrouver la
requête fautive dans les vues de diagnostic. Il ouvre le **niveau 2 MySQL**.

Il est noté sur le **plan d'exécution** que le serveur annonce et sur la
**taille** que la table occupe vraiment. Aucun test ne lit la liste des index
de la table, et c'est le choix central du lab : un index peut exister sans
servir, et le catalogue ne le dira jamais.

## Les trois faits mesurés qui ont décidé de sa forme

Pris sur MySQL 8.4 le 2026-10-20, dans un conteneur jetable, avant d'écrire une
ligne de test.

| Moment | Lignes | Taille | Plan |
|---|---|---|---|
| état de départ, après la purge | 20 000 | **45 Mo** | `type: ALL`, 17 477 lignes examinées |
| après `CREATE INDEX` sur `service` | 20 000 | **45 Mo** | `type: ref`, 412 lignes examinées |
| après `OPTIMIZE TABLE` | 20 000 | **6 Mo** | `type: ref`, inchangé |

**La deuxième ligne est celle qui compte.** Créer un index change le plan et ne
récupère **aucun octet** : les deux tâches sont donc indépendantes, et aucun
des deux tests ne passe grâce à l'autre. C'était la question à trancher avant
d'écrire, parce que deux tests dont l'un se rend vrai par l'autre ne mesurent
plus deux choses.

**`ALTER TABLE ... ENGINE=InnoDB` fait la même chose qu'`OPTIMIZE TABLE`**, et
le lab accepte les deux. InnoDB ne sait pas optimiser en place : le serveur
répond « Table does not support optimize, doing recreate + analyze instead »,
ce qui dit bien que les deux gestes sont le même.

**`data_free` ne dit pas l'espace mort.** Mesuré : 2 Mo avant la purge, 2 Mo
après, 1 Mo après la reconstruction. Un exploitant qui le surveille conclut que
rien ne s'est passé, dans les deux sens.

## Le piège d'exploitation, et il surprend tout le monde

Une requête jouée **sans base par défaut** est enregistrée dans le
Performance Schema avec un `SCHEMA_NAME` **nul**. Elle n'apparaît donc pas dans
`sys.statement_analysis` quand on filtre sur `db`, ce qui est pourtant la
façon de chercher les requêtes coûteuses d'une base.

Mesuré : la même requête jouée deux fois, une fois sans base sélectionnée et
une fois avec, produit **deux empreintes distinctes**, l'une sous `NULL` et
l'autre sous `appli`. La sonde du lab rend 0 puis 1.

## Deux défauts de ma main, corrigés avant livraison

**Mes propres tests rendaient le troisième vert.** Les helpers interrogeaient la
table avec `-D appli`, donc leurs `select count(*)` étaient fichés sous `appli`,
et la sonde passait au vert dès que le premier test tournait. Aucun ordre de ce
fichier n'emploie plus de base par défaut : ils nomment la table en entier et
sont donc fichés sous `NULL`. La sonde exige en plus que l'empreinte porte le
`WHERE` du tableau de bord.

**`EXPLAIN FORMAT=JSON` n'est pas lisible tel quel.** Le client échappe les
sauts de ligne du JSON en `\n` littéraux, et `json.loads` échoue dessus.
L'option `--raw` les désactive. Sans elle, les tests auraient diagnostiqué une
panne de serveur là où il n'y avait qu'un client qui protège sa sortie.

## Ce qu'il ne couvre pas

Le **journal des requêtes lentes**, que `mysql-03` prouve déjà sur une requête
lente qui y atterrit. Les **alertes** et la métrologie dans le temps, qui
demandent un collecteur. La **réplication**, qui est le niveau 3.

## Durée

40 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/)
