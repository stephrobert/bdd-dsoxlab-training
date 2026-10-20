# Une instance qui ne dit rien de ce qu'elle fait

`db1.lab` porte une instance PostgreSQL 18 en production depuis une semaine.
L'application y écrit, les sauvegardes passent, personne ne s'en plaint.

Ce matin, l'équipe applicative signale des lenteurs intermittentes. On te
demande lesquelles de ses requêtes sont lentes. Tu ouvres les journaux : il n'y
a rien. Pas une requête, pas une connexion, et les quelques lignes présentes ne
disent ni quand, ni qui, ni sur quelle base. L'instance tourne avec les réglages
de journalisation d'usine, qui ne tracent presque rien.

Il faut aussi relever `max_connections`, que l'application saturera au prochain
palier.

Une contrainte, et c'est tout le sujet : **l'application ne doit pas perdre une
seule session.** Un redémarrage est exclu. Or parmi les paramètres que tu dois
poser, certains prennent effet dès que le serveur relit ses fichiers, et un
n'attend rien de moins que son prochain démarrage. Rien ne te le dira : un
rechargement réussit toujours, même quand il laisse un paramètre sans effet.

Tu dois donc savoir lesquels s'appliquent, lesquels attendent, et le prouver.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/)
