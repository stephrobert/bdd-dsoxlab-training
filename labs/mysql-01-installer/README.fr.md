# mysql-01 : installer, et fermer ce que l'installation ouvre

## Ce que ce lab éprouve

Installer un serveur n'est pas le mettre en service. Ce lab fait franchir les
deux étapes que les paquets laissent à l'administrateur : prouver que le
logiciel vient bien de la source qu'on croit, et fermer l'écoute que
l'installation ouvre par défaut.

Il est noté sur l'**écoute réelle**, relevée par `ss`, et sur ce que le serveur
en marche déclare. Jamais sur le contenu d'un fichier de configuration : un
fichier juste et un port ouvert coexistent très bien.

## Les trois pièges qu'il fait rencontrer

**Le dépôt de Debian ne livre pas MySQL.** `apt install mysql-server` sur une
Debian sans le dépôt d'Oracle installe MariaDB, qui porte des noms de paquets
voisins et un service `mariadb`. Le lab contrôle donc la provenance, pas
seulement la présence.

**Les paquets Oracle ne posent aucune ligne `bind-address`.** Pas même
commentée. La valeur par défaut de la variable étant `*`, le serveur écoute sur
toutes les interfaces à la fin de l'installation. Rien ne le signale.

**`bind-address` ne restreint pas le port 33060.** Le protocole X a sa propre
variable, `mysqlx-bind-address`. C'est le piège à deux étages : le premier
réglage est visible et rassurant, le second est invisible et oublié. Un
apprenant qui s'arrête au premier voit son `SELECT @@bind_address` répondre
`127.0.0.1` et laisse une porte ouverte.

## Ce qu'il ne couvre pas

Le réglage de la mémoire et des connexions, qui appartient au lab de
configuration. Les rôles, le TLS et les révocations partielles, qui
appartiennent au lab de sécurisation. Le pare-feu système, qui est le second
geste que le guide recommande et qui ne relève pas de MySQL.

## Durée

35 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/)
