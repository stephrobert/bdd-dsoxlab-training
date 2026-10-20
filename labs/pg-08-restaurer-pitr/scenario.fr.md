# Un DROP TABLE en production

Il est 14 h 30. Une migration mal relue vient de jouer un `DROP TABLE` sur
`appli.clients`, dans la base `facturation` de `db1.lab`. La table n'existe
plus, et l'application est à l'arrêt.

Ce qui te sauve, c'est que l'archivage continu des WAL était en place, et
qu'une sauvegarde physique de la grappe existe dans `/var/lib/postgresql/backups/base`.

Quelqu'un a eu le réflexe de noter l'instant qui précède l'incident, avant que
la table disparaisse. Il est dans `/home/student/instant-de-securite.txt`.

On te demande de ramener la base à cet instant-là. Pas au dernier WAL
disponible : rejouer tout, c'est rejouer le `DROP TABLE`. Et pas davantage à la
sauvegarde physique seule : la dernière ligne insérée avant l'incident ne s'y
trouve pas, elle n'existe que dans les journaux.

Il y a donc exactement un point d'arrivée juste, et c'est là tout le sujet.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
