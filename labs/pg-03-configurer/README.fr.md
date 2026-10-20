# pg-03 : configurer une instance, et savoir ce qui se recharge

## Ce que ce lab éprouve

Poser un paramètre PostgreSQL, ce n'est pas l'écrire dans un fichier. C'est
l'écrire **et** le faire prendre en compte, ce qui se fait de deux façons selon
le paramètre : un rechargement, qui ne coupe personne, ou un redémarrage, qui
coupe tout le monde.

Le lab demande les deux comportements dans la même manipulation. Des paramètres
rechargeables doivent être **effectifs**, c'est-à-dire lus dans `pg_settings` et
pas seulement présents dans un fichier. Un paramètre de contexte `postmaster`
doit être écrit et rester **en attente**. Et le serveur ne doit pas avoir
redémarré, ce qu'une session laissée ouverte par le setup prouve mieux que
n'importe quelle déclaration.

## Le piège qu'il fait rencontrer

**Un rechargement réussit toujours.** `pg_reload_conf()` rend `t`, `systemctl
reload` sort en 0, et aucun des deux ne signale qu'un paramètre est resté sans
effet parce qu'il exigeait un redémarrage. L'erreur se voit des semaines plus
tard, quand on découvre que le réglage posé n'a jamais servi.

La seule chose qui le dit est `pending_restart`, dans `pg_settings`. Et la
valeur en attente, elle, ne s'y lit pas : `pg_settings.setting` garde la valeur
**en service**. Il faut `pg_file_settings`, la vue qui montre ce que les
fichiers déclarent.

## Ce qu'il ne couvre pas

Le dimensionnement de la mémoire par rapport à la charge réelle, qui demande de
mesurer avant de régler, et l'archivage WAL, qui appartient au lab de
sauvegarde.

## Durée

35 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/)
