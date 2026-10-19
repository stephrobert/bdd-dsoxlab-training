# L'instance tourne, et personne ne peut s'en servir

PostgreSQL 18 est installé sur `db1.lab` et le service démarre au boot. Le rôle
applicatif `appli` existe avec son mot de passe, la base `facturation` lui
appartient. Sur le papier, tout est prêt.

L'équipe qui doit livrer l'application vient de te dire que rien ne marche.
Depuis leur machine, `psql` reste sans réponse. Depuis `db1` elle-même, en
`postgres`, tout va bien.

Tu as trois choses à régler, et elles vivent à trois endroits différents : le
serveur n'écoute que sa propre boucle locale, il ne sait pas qui accepter
depuis le réseau, et aucun client ne peut s'authentifier sans qu'un humain
tape un mot de passe, ce qu'un script ne fera jamais.

Ensuite, l'application a besoin de ses objets : un schéma, une table, et de
quoi vérifier qu'elle écrit bien. Ils doivent appartenir au rôle du service,
pas au superutilisateur.

Enfin, on te demande un rapport de quatre lignes sur l'état réel de
l'instance. Les valeurs seront confrontées à ce que le serveur répond : une
valeur plausible mais fausse sera refusée.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
