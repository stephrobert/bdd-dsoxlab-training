# mysql-02 : piloter l'instance, sans laisser traîner le mot de passe

## Ce que ce lab éprouve

Les quatre gestes qui rendent une instance exploitable au quotidien : se
connecter sans exposer son mot de passe, créer les objets de l'application,
rendre le serveur observable, et se donner le client qu'on veut employer.

Il est noté sur une connexion qui **aboutit vraiment**, jouée sans mot de passe
dans l'environnement et avec l'entrée standard fermée : si quelque chose
manque, le client demande le mot de passe et la commande meurt au lieu de
l'inventer. C'est la même preuve que `pg-02` emploie pour `.pgpass`.

## Les trois pièges qu'il fait rencontrer

**`performance_schema` ne se rallume pas à chaud.** C'est une variable de
démarrage, en lecture seule une fois le serveur lancé : un `SET GLOBAL` répond
une erreur, et un `SET PERSIST` écrit la valeur sans l'appliquer. Il faut
redémarrer, et c'est le genre de détail qui fait conclure à tort que la
variable ne sert à rien.

**Le profil de connexion dépend d'un détail d'hôte.** En MySQL, `@localhost`
désigne la **socket Unix**, et une connexion TCP vers `127.0.0.1` cherche un
compte `@127.0.0.1`, qui est un AUTRE compte. Un login path qui déclare un hôte
alors que le compte est en `localhost` échoue sur un « Access denied » qui ne
dit pas pourquoi.

**Les deux clients ne s'accordent pas sur la socket.** `mysqlsh` emploie un
chemin compilé en dur, `/var/lib/mysql/mysql.sock`, qui n'est pas celui de
Debian, et dont le répertoire lui est interdit : le message est un
« Error 2002 ... (13) », un refus de permission et non un fichier absent. Le
client `mysql`, lui, se connecte sans rien dire par le même login path.
Déclarer la socket dans le profil met les deux d'accord, et c'est la seule
façon de ne pas avoir à le redire à chaque commande.

## Ce qu'il ne couvre pas

Le réglage de la mémoire et des journaux, qui appartient au lab de
configuration. Les rôles et le TLS, qui appartiennent au lab de sécurisation.
L'exploration détaillée du Performance Schema, que le guide de supervision
traite : ici on le rallume, on ne l'explore pas.

## Durée

35 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/)
