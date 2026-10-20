# Deux serveurs qui s'ignorent, et une sauvegarde qui ne suffit plus

`db1.lab` sert la base `appli` en production. `db2.lab` existe, MySQL y tourne,
et les deux serveurs ne se connaissent pas.

Le réplica a déjà reçu une **copie** de la base, restaurée depuis la sauvegarde
de la veille : il porte les mêmes tables et les mêmes lignes. C'est un acquis
de ce lab, et ce n'est pas un détail : un réplica ne part jamais de rien. Sans
cette copie, son fil d'application s'arrête à la première transaction sur une
erreur `1049`, « Unknown database », mesuré.

La sauvegarde quotidienne protège d'une suppression accidentelle, elle ne
protège pas d'une panne matérielle : le temps de restaurer, le service est à
terre. On te demande donc un **réplica**, qui suit la source en continu et que
l'on peut promouvoir.

Trois choses à savoir avant de commencer, et les deux premières vont te coûter
une erreur si tu les ignores.

**`gtid_mode` refuse de passer de OFF à ON d'un coup.** Le serveur répond alors
une erreur `1788` qui nomme le chemin, et il précise que la valeur doit monter
**simultanément sur tous les serveurs**. Lis le message, il dit tout.

**Le greffon d'authentification par défaut bloque la connexion du réplica.**
Avec `caching_sha2_password`, le réplica reste en `CONNECTING` sur une erreur
`2061` qui parle de « secure connection », et il réessaie toutes les 60
secondes. Ce n'est ni le mot de passe ni les privilèges.

**`SHOW REPLICA STATUS` est un affichage, pas une preuve.** La vérification lit
les **tables d'état** du Performance Schema, et surtout elle écrit une ligne
sur la source puis la cherche sur le réplica. Une réplication qui annonce
`ON` sans rien transporter existe, et c'est la panne qu'on ne voit pas.

**Et ne configure pas le canal sur le nom `db1.lab`.** Mesuré sur cette
infrastructure : depuis `db2`, ce nom résout vers une machine d'un **autre
réseau de lab**, pas vers la source. Relève l'adresse de la source **sur la
source**, par exemple avec `ip -4 addr show`, et emploie-la. On ne configure
pas une réplication sur un nom qu'on n'a pas vérifié.

Les identifiants : le compte d'administration `labadmin` sur les **deux**
serveurs, mot de passe `Adm1n!Lab2026`. Le compte de réplication à créer
s'appellera `repl`, avec le mot de passe `R3pl!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/)
