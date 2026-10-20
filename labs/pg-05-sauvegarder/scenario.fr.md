# « On a une sauvegarde »

La base `facturation` de `db1.lab` porte les données de production. Elle est
sauvegardée, te dit-on : un `pg_dump` tourne chaque nuit et dépose son fichier
dans `/var/backups/postgresql/`.

Tu demandes quand la restauration a été éprouvée pour la dernière fois.
Personne ne sait. Le répertoire est vide, d'ailleurs : la tâche a cessé de
tourner il y a un moment, et rien ne l'a signalé.

On te demande de reprendre le sujet depuis le début, et de ne rien livrer que
tu n'aies vérifié.

Trois choses, et la troisième est la seule qui prouve quelque chose. Produire
la sauvegarde de la base. Capturer ce qu'une sauvegarde de base **ne contient
pas** : les rôles sont globaux au cluster, `pg_dump` les ignore, et une
restauration sur une machine neuve échoue alors sur les propriétaires et les
droits. Puis restaurer pour de vrai, dans une base de vérification, et
comparer.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
