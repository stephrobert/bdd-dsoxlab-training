# pg-02 : piloter une instance avec psql, par la socket et par le réseau

## Ce que ce lab éprouve

Une instance PostgreSQL qui tourne n'est pas une instance utilisable. Ce lab
fait franchir les trois obstacles que rencontre tout service qui doit la
joindre, puis demande de lire l'état réel du serveur plutôt que de le supposer.

Il est noté sur l'état de la machine : les adresses écoutées, les règles
d'accès, les permissions du fichier de mots de passe, les objets réellement
présents dans le catalogue, et un rapport dont chaque valeur est comparée à ce
que le serveur déclare.

## Le piège qu'il fait rencontrer

**Deux pannes différentes rendent la même erreur, et une seule avertit.**
Mesuré sur PostgreSQL 18 le 2026-10-20 :

- un `.pgpass` dont le **groupe ou les autres** peuvent lire déclenche un
  avertissement explicite de libpq, « password file … has group or world
  access », puis psql redemande le mot de passe et échoue sur
  `fe_sendauth: no password supplied` ;
- un `.pgpass` **en 0600 dont l'hôte ne correspond pas** au `-h` ne déclenche
  **aucun** avertissement, et échoue sur exactement la même ligne.

L'erreur finale est donc identique et le diagnostic ne l'est pas. Et
l'avertissement du premier cas part sur la sortie d'erreur : un script qui la
jette ne voit qu'une demande de mot de passe qui bloque, ce qui ramène les deux
cas au même symptôme.

## Ce qu'il ne couvre pas

Le chiffrement du transport (`pg_stat_ssl`), qui appartient au lab d'accès, et
le fichier de service `~/.pg_service.conf` : le guide l'enseigne, mais ce lab
ne le vérifie pas. Ses trois obstacles sont déjà évalués, et un quatrième
n'apporterait rien.

## Durée

30 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
