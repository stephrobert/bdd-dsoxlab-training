# Un serveur de base de données que personne n'a installé exprès

L'équipe tient son inventaire dans un tableur et veut une vraie base de
données pour le remplacer. Quelqu'un a lancé `apt install postgresql` sur une
machine de test le mois dernier, et personne ne se souvient de la version
obtenue, d'où elle vient, ni si elle revient après un redémarrage.

La décision est prise : PostgreSQL 18, depuis le dépôt de paquets du projet
(PGDG), sur une machine Debian 13 neuve. Vous héritez de `db1.lab`. Elle est
vierge : aucun PostgreSQL, aucun dépôt pour lui.

## Mission

Mettre en service une instance que vous pourriez laisser en production.

Trois points comptent plus que de voir `psql` répondre.

Le premier est **l'origine des paquets**. Debian livre son propre PostgreSQL,
d'une version majeure plus ancienne. La version voulue vit dans un autre dépôt,
et vous ne lui faites confiance que si vous savez dire au système quelle clé le
signe.

Le deuxième est **ce qui survit à un redémarrage**. Un serveur lancé à la main
répond aujourd'hui et a disparu demain.

Le troisième est **ce que le serveur expose**. Une instance neuve ne doit pas
écouter le réseau : vous l'ouvrirez volontairement plus tard, quand vous saurez
à qui.
