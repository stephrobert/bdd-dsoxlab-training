# mysql-05 : une sauvegarde complète, prouvée en la restaurant

## Ce que ce lab éprouve

La sauvegarde logique d'une base MySQL, et surtout la **preuve** qu'elle vaut
quelque chose. L'apprenant produit un dump, le restaure dans une base neuve, et
établit que la copie est **utilisable** : mêmes lignes, procédure stockée qui
répond, trigger qui déclenche.

Il est noté sur **deux objets distincts**, et ce n'est pas une redondance :

- le **fichier** de sauvegarde, parce que c'est de lui qu'on restaure le jour
  où la machine a brûlé ;
- la **base restaurée**, parce qu'un dump complet ne prouve pas qu'il se
  restaure.

Un apprenant peut produire un dump incomplet puis recréer la procédure à la
main dans la copie : la base serait juste, le fichier resterait inutilisable.
L'inverse se tient aussi. Les deux familles de tests se gardent donc l'une
l'autre.

## Le piège central, et il est mesuré

**Une sauvegarde incomplète ne se signale nulle part.** Mesuré sur MySQL 8.4
le 2026-10-20, `mysqldump --help` annonce dans son récapitulatif des valeurs
effectives :

| Option | Valeur par défaut |
|---|---|
| `routines` | `FALSE` |
| `events` | `FALSE` |
| `triggers` | `TRUE` |

Un dump pris sans `--routines` omet donc les **procédures stockées** et les
fonctions, tout en **gardant** les triggers. Et voici ce que sa restauration
dans une base neuve donne, mesuré dans le même conteneur :

| Ce qu'on observe | Résultat |
|---|---|
| code de retour de la restauration | `0`, elle **réussit** |
| lignes restaurées | toutes |
| triggers restaurés | présents |
| procédures restaurées | **aucune** |
| `call base.chiffre_affaires()` | `ERROR 1305 ... does not exist` |

Trois étapes réussissent donc sans un mot : le dump, la restauration, et le
démarrage de l'application. L'échec arrive à la première page qui appelle la
procédure, parfois des semaines plus tard, et le fichier de sauvegarde paraît
hors de cause puisqu'il « s'est restauré sans erreur ».

## Ce que ce lab ne note pas, et pourquoi c'est écrit dans l'énoncé

**`--single-transaction`.** C'est la bonne pratique, le guide l'explique, et
elle ne laisse **aucune trace vérifiable** dans le fichier produit. Mesuré : un
dump pris avec et un dump pris sans portent tous les deux un `LOCK TABLES`, et
sont indiscernables une fois écrits. Un test qui prétendrait le contrôler
noterait une ligne de commande au lieu d'un état, ce que ce catalogue refuse.
L'énoncé le dit à l'apprenant plutôt que de le taire : une option utile dont on
ne peut pas prouver l'emploi reste une option utile.

Ce choix a une conséquence qu'il faut assumer : un apprenant qui oublie
`--single-transaction` obtient 100. Le lab mesure la **complétude** de la
sauvegarde, pas la façon de la prendre sur une base sous charge.

## Ce qu'il ne couvre pas

Le **PITR** et l'archivage des binary logs, qui demandent un lab à eux et une
notion de temps. **MySQL Shell** (`util.dumpSchemas()`), qui produit une
sauvegarde parallèle en plusieurs fichiers : c'est un autre outil pour la même
capacité, et le guide le traite. La sauvegarde **physique** (Percona
XtraBackup), qui suppose un même numéro de version majeure à la restauration.

## Un détail d'implémentation qui a décidé du setup

La procédure et le trigger sont créés **par `labadmin`**, le compte que
l'apprenant emploie. Leur `DEFINER` est donc `labadmin@localhost`, et la
restauration par ce même compte n'exige aucun privilège dynamique : mesuré, un
`GRANT ALL PRIVILEGES` ne donne pas `SET_USER_ID`, qui serait requis pour
restaurer une routine dont le `DEFINER` est un autre compte.

## Durée

35 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/)
