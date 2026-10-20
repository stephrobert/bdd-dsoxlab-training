# Un mot de passe qui traîne, et un serveur qui ne dit rien

L'instance MySQL de `db1.lab` tourne, fermée sur sa boucle locale, et le
compte d'administration `labadmin` existe. Trois choses manquent pour qu'on
puisse travailler avec.

La première se voit dans l'historique du shell. Les scripts de l'équipe
appellent `mysql -ulabadmin -p'...'`, donc le mot de passe est sur la ligne de
commande : il se lit dans `ps`, dans l'historique, et dans les journaux
d'audit. MySQL fournit de quoi l'éviter.

La deuxième est que l'application n'a aucun objet : ni base, ni table.

La troisième ne se voit pas du tout, et c'est la plus intéressante. Quelqu'un a
éteint le **Performance Schema** pour gagner quelques mégaoctets, et ne l'a
jamais rallumé. Toute la famille de vues `sys` qui sert à diagnostiquer une
lenteur est donc muette. Ce n'est pas une variable qu'un `SET` rallume : elle
se lit au démarrage.

Enfin, on te demande d'installer **MySQL Shell**, le client que l'équipe veut
employer pour ses scripts.

Les identifiants : le compte `labadmin`, mot de passe `Adm1n!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/)
