# mysql-04 : accorder par rôles, et exiger le chiffrement

## Ce que ce lab éprouve

Le moindre privilège, en MySQL, avec ses mécanismes propres : des **rôles** qui
portent les privilèges, et une exigence de TLS posée **sur le compte** et non
dans un fichier.

Il est noté sur le **comportement**, comme son équivalent PostgreSQL : une
connexion non chiffrée doit être **refusée**, une connexion chiffrée doit
aboutir, et le compte doit lire ce qu'il a le droit de lire et rien de plus.
Aucun test ne lit un `GRANT` dans le catalogue : un droit accordé et inactif
existe, et ne sert à rien.

## Les trois pièges qu'il fait rencontrer

**Un rôle accordé n'est pas un rôle actif.** C'est le piège central, et le
guide le nomme. Mesuré sur MySQL 8.4 : après un `GRANT role_reader TO
compte`, `CURRENT_ROLE()` répond `NONE` et le moindre `select` échoue sur
« Access denied ... to database ». Le `GRANT` figure pourtant bien dans le
catalogue. Il faut `SET DEFAULT ROLE ALL TO compte@hote`, et alors
`CURRENT_ROLE()` répond le rôle.

**`@localhost` ne désigne que la socket.** Mesuré : un compte `@localhost`
REFUSE une connexion TCP vers `127.0.0.1`, avec un « Access denied for
'compte'@'127.0.0.1' » qui nomme un hôte que personne n'a déclaré. MySQL
apparie l'hôte tel que la connexion le présente. Un compte qui doit se
connecter par le réseau se déclare donc avec l'adresse, pas avec `localhost`.

**Le refus d'une connexion en clair ne vient pas toujours du même endroit.**
Mesuré sur un compte `REQUIRE SSL` joint avec `--ssl-mode=DISABLED`, et le
greffon d'authentification change l'erreur :

| Greffon du compte | Erreur rendue |
|---|---|
| `caching_sha2_password`, le défaut de 8.4 | `ERROR 2061` : « Authentication requires secure connection » |
| `mysql_native_password`, le défaut d'avant 8.0 | `ERROR 1045` : « Access denied » |

Dans le premier cas, c'est le **greffon** qui refuse d'envoyer le mot de passe
sur un canal en clair, avant même que `REQUIRE SSL` soit consulté. Dans le
second, c'est `REQUIRE SSL` lui-même. Les deux refusent bien la connexion, mais
seul le premier dit pourquoi : beaucoup de documentations citent le `1045`,
qui était l'erreur attendue quand le greffon natif était le défaut.

## Ce qu'il ne couvre pas

Les *partial revokes*, qui révoquent un privilège global sur un schéma précis :
le lab n'emploie aucun privilège global, donc il n'y a rien à révoquer. La
vérification d'identité par certificat client (`REQUIRE X509`), qui demande une
PKI. La politique de complexité des mots de passe, que le guide traite.

## Durée

40 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/)
