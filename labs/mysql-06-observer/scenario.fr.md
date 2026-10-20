# Une table purgée qui n'a rien rendu, et une requête qui lit tout

L'instance de `db1.lab` sert la base `appli`. Sa table `evenements` a reçu
200 000 lignes de journal applicatif, puis la purge mensuelle en a supprimé
neuf sur dix. Il en reste 20 000.

Le disque, lui, n'a rien rendu. La table occupe encore ce qu'elle occupait
avant la purge, et l'exploitant qui a lancé le `DELETE` a cru son travail fait.

Et une requête que le tableau de bord appelle toutes les minutes lit la table
**entière** à chaque fois :

```sql
SELECT COUNT(*) FROM evenements WHERE service = 'svc-7';
```

Un index existe pourtant sur cette table. Il ne sert pas cette requête, et rien
dans le catalogue ne le dit : `SHOW INDEX` affiche un index, l'exploitant
conclut que la table est indexée, et le plan continue de tout lire.

On te demande trois choses, et la troisième est celle qu'on oublie :

1. que la requête du tableau de bord **cesse de lire la table entière** ;
2. que la table **rende l'espace** que la purge n'a pas rendu ;
3. que cette requête soit **retrouvable** dans les outils de diagnostic du
   serveur, sous le nom de sa base.

Tout est noté sur l'état réel : le **plan d'exécution** que le serveur
annonce, la **taille** que la table occupe vraiment, et ce que les vues de
diagnostic contiennent. Aucun test ne regarde une commande que tu aurais tapée.

Les identifiants : le compte d'administration `labadmin`, mot de passe
`Adm1n!Lab2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/)
