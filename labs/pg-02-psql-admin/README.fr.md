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

`~/.pgpass` est **ignoré en silence** par psql si ses permissions sont trop
larges. Pas d'erreur, pas d'avertissement dans un script : seulement une
demande de mot de passe qui bloque. Un fichier au bon format mais en mode 0644
ne sert à rien, et c'est la faute la plus fréquente sur ce sujet.

## Ce qu'il ne couvre pas

Le chiffrement du transport (`pg_stat_ssl`), qui appartient au lab d'accès, et
le fichier de service `~/.pg_service.conf`, que le guide n'enseigne pas.

## Durée

30 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
