# Une base posée sur le réseau sans que personne l'ait voulu

`db1.lab` est une machine Debian 13 neuve. On te demande d'y mettre MySQL
8.4 LTS, la version au support long, depuis le dépôt d'Oracle et non depuis
celui de Debian, qui livre MariaDB sous des noms voisins.

Jusque-là, rien de remarquable. Ce qui l'est davantage, c'est ce que
l'installation laisse derrière elle.

Les paquets d'Oracle ne posent **aucune** ligne `bind-address`, pas même
commentée. Or la valeur par défaut de cette variable est `*`, soit toutes les
interfaces. À la fin d'un `apt install`, `mysqld` écoute donc sur le réseau,
sur **deux** ports : 3306 pour le protocole classique, 33060 pour le protocole
X.

Et il y a un second niveau à ce piège. `bind-address` ne restreint **pas** le
port 33060 : le protocole X a sa propre variable. Tu peux donc poser
`bind-address = 127.0.0.1`, voir `SELECT @@bind_address` te répondre
`127.0.0.1`, et laisser le 33060 grand ouvert.

On te demande donc de constater l'état réel plutôt que de le supposer, et de
fermer les deux portes. Un compte `root@localhost` protège les **comptes**, pas
le **réseau**.

Le mot de passe `root` à poser est `R00t!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/)
