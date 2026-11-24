# Une sauvegarde qui réussit, et une restauration qui manque quelque chose

## La situation

L'instance de `db1.lab` sert la base `appli`. Elle porte deux tables, mais pas
seulement : une **procédure stockée** que l'application appelle pour calculer
son chiffre d'affaires, et un **trigger** qui normalise les montants à
l'insertion.

La sauvegarde quotidienne existe. Elle tourne depuis des mois, elle n'a jamais
rien dit, et le fichier qu'elle produit pèse ce qu'il doit peser. Le mois
dernier, on a restauré cette sauvegarde sur un serveur de recette. La
restauration s'est terminée **sans une erreur**, les tables étaient là, les
lignes aussi. L'application a démarré, puis a échoué à la première page qui
affiche le chiffre d'affaires :

```text
ERROR 1305 (42000): PROCEDURE appli.chiffre_affaires does not exist
```

Le piège n'est donc pas dans la restauration : c'est la **sauvegarde** qui
était incomplète, et rien dans son déroulement ne le disait. Mesuré sur MySQL
8.4, `mysqldump --help` annonce `routines FALSE` : les procédures stockées et
les fonctions sont **omises par défaut**, là où les triggers, eux, sont
inclus. Un fichier incomplet se restaure parfaitement, avec un code de retour
0.

On te demande de refaire le dispositif en prouvant qu'il tient. Produire une
sauvegarde logique **complète** de `appli`, la restaurer dans une base neuve
`appli_restauree`, et vérifier que la copie est **utilisable** : les mêmes
lignes, la procédure qui répond, le trigger qui déclenche.

Une sauvegarde qu'on n'a jamais restaurée n'est pas une sauvegarde : c'est un
fichier.

Les identifiants : le compte d'administration `labadmin`, mot de passe
`Adm1n!Lab2026`. Le répertoire de travail `~/sauvegardes/` t'attend, vide.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/)

## Ce qui est demandé

Sur `db1.lab`. La base `appli` porte deux tables, une procédure stockée
`chiffre_affaires()` et un trigger `montant_positif`. Le compte `labadmin`
existe avec le mot de passe `Adm1n!Lab2026`, et `~/sauvegardes/` est vide.

### 1. Produire une sauvegarde logique COMPLÈTE

Un fichier `~/sauvegardes/appli.sql`, sauvegarde logique de la base `appli`.

**Complète** veut dire : le schéma, les données, le trigger **et la procédure
stockée**. Attention, c'est le piège du lab : les procédures ne sont **pas**
dans un dump par défaut. Regarde ce que `mysqldump --help` annonce pour
`routines`.

### 2. La restaurer dans une base NEUVE

Une base `appli_restauree`, qui reçoit le contenu du fichier. On ne restaure
pas par-dessus la base en service : c'est dans une copie qu'on prouve qu'une
sauvegarde vaut quelque chose.

### 3. Prouver que la copie est UTILISABLE

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

### 4. Remplir le rapport

Le fichier `~/rapport-sauvegarde.txt` porte trois valeurs à compléter :

- `defaut_de_routines` : ce que `mysqldump --help` annonce pour `routines`,
  recopié tel quel ;
- `lignes_dans_la_base_restauree` : le total des lignes des deux tables de
  `appli_restauree` ;
- `total_rendu_par_la_procedure` : ce que
  `appli_restauree.chiffre_affaires()` répond.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Ce qui n'est pas noté, et pourquoi c'est dit

`--single-transaction` est la bonne pratique, et le guide explique pourquoi.
Aucun test ne l'exige : mesuré sur MySQL 8.4, un dump pris avec et un dump pris
sans sont **indiscernables** une fois le fichier écrit, le `LOCK TABLES` y
figurant dans les deux cas. Un test qui prétendrait le vérifier noterait une
ligne de commande, pas un état. Emploie-le quand même : sur une base en
service, il évite de bloquer les écritures.

### Vérifier

```bash
dsoxlab check mysql-05-sauvegarder
```
