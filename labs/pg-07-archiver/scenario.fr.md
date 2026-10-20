# Sauvegarder la nuit ne suffit plus

La base `facturation` est sauvegardée chaque nuit par un `pg_dump`. L'équipe
qui l'exploite vient de chiffrer ce que cela coûte : si l'incident arrive à
17 h, on perd la journée.

On te demande de préparer ce qu'il faut pour ne plus perdre qu'un segment de
journal : une **sauvegarde physique** de la grappe, et l'**archivage continu
des WAL** qui la prolonge jusqu'à l'instant de l'incident.

Deux choses à savoir avant de commencer, et elles coûtent cher à qui les
découvre en production.

`archive_mode` exige un **redémarrage complet**. Un `reload` réussit et ne
l'applique pas, sans un mot.

Et l'archivage ne se déclenche **qu'à segment complet**. Sur une base peu
active, tu peux tout avoir réglé correctement et ne voir aucun fichier arriver
pendant des heures. Celui qui en conclut que c'est en panne cherche au mauvais
endroit ; celui qui s'arrête à `SHOW archive_mode` croit son archivage en place
alors que rien n'est encore parti.

On te demande donc d'en apporter la preuve, pas la configuration.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
