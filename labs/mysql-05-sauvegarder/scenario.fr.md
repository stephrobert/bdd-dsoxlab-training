# Une sauvegarde qui réussit, et une restauration qui manque quelque chose

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
