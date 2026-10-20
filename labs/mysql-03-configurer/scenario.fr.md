# Une instance réglée pour un ordinateur portable

`db1.lab` porte MySQL 8.4, installé et joignable. Ses réglages, eux, sont
restés ceux du paquet.

Le buffer pool InnoDB vaut **128 Mo**, le défaut compilé. C'est le cache qui
évite les lectures disque, et sur une machine qui en a plusieurs gigaoctets,
c'est absurde. Le plafond de connexions vaut 151, et l'application en
réclamera davantage au prochain palier.

Surtout, le journal des requêtes lentes est **éteint**. On te demandera un jour
quelle requête ralentit l'application, et il n'y aura rien à lire.

On te demande donc de régler les trois, et de faire que cela **survive à un
redémarrage**. Ce dernier point n'est pas une formalité : MySQL offre trois
façons de changer une variable, et deux d'entre elles perdent le réglage au
prochain démarrage sans le dire.

Et rien, sur un serveur en marche, ne distingue une valeur qui survivra d'une
valeur qui disparaîtra. Même la table qui annonce la **source** d'une valeur
répond la même chose dans les deux cas. La seule façon de savoir est de
redémarrer, donc c'est ce que la vérification fera.

Les identifiants : le compte `labadmin`, mot de passe `Adm1n!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)
