# Une seule machine porte la production

`db1.lab` porte la base `facturation`, et elle la porte seule. Les sauvegardes
sont en place, l'archivage des journaux aussi : on sait remonter après un
incident. Ce qu'on ne sait pas faire, c'est continuer pendant.

`db2.lab` est disponible, avec PostgreSQL installé et une grappe vide qui
tourne pour rien.

On te demande d'en faire un **secondaire en flux** : une copie qui suit le
primaire en continu, prête à prendre le relais, et qu'on peut déjà interroger
en lecture pour soulager les rapports.

Trois précautions, et elles ne sont pas des détails de confort.

Le secondaire doit s'authentifier auprès du primaire. Employer `postgres` pour
cela stockerait un mot de passe de superutilisateur sur la seconde machine, et
ouvrirait un accès total au primaire si elle était compromise.

Le primaire doit **retenir** les journaux dont le secondaire a besoin. Sans
cela, un secondaire déconnecté quelques heures se réveille devant des journaux
recyclés, et il faut tout recommencer.

Enfin, la réplication n'est pas une sauvegarde : un `DROP TABLE` sur le
primaire se réplique en quelques millisecondes. Elle protège de la panne d'une
machine, pas de l'erreur humaine.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/)
