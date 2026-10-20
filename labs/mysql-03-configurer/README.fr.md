# mysql-03 : configurer, et survivre au redémarrage

## Ce que ce lab éprouve

Trois réglages d'exploitation courante, et la seule chose qui prouve qu'ils
tiennent : un **redémarrage**.

Le test central arrête et relance le serveur, puis relit les trois valeurs. Ce
n'est pas une précaution, c'est la seule mesure possible, et le lab existe
pour cette raison.

Le journal des requêtes lentes, lui, est noté sur une **requête lente qui y
atterrit vraiment**. Un journal activé dont rien ne sort ne sert à personne, et
cela arrive : fichier non accessible au compte du serveur, seuil mal compris,
sortie dirigée vers une table plutôt qu'un fichier.

## Le piège qu'il fait rencontrer

**La table qui annonce la source d'une valeur ne dit pas si elle survivra.**
Mesuré sur MySQL 8.4 :

| Comment la valeur a été posée | `variables_info` | `persisted_variables` |
|---|---|---|
| laissée au défaut | `COMPILED` | vide |
| `SET GLOBAL` | `DYNAMIC` | vide |
| `SET PERSIST` | `DYNAMIC` aussi | la valeur y figure |

`variables_info` répond donc la **même chose** après un `SET GLOBAL` perdu au
redémarrage et après un `SET PERSIST` qui survivra : sa source ne devient
`PERSISTED` qu'**après** le redémarrage. Un administrateur qui s'y fie pour
vérifier sa persistance croira son `SET PERSIST` en échec, ou vérifiera une
garantie que cette table ne donne pas.

`persisted_variables`, elle, distingue bien les deux. Mais elle reflète la
**mémoire et non le fichier** : en vidant `mysqld-auto.cnf` derrière le dos du
serveur, sans redémarrer, elle continue d'annoncer la valeur. Elle prouve donc
que le serveur a **voulu** persister, pas que le fichier est intact ni qu'il
sera relu. Un fichier corrompu, ou une variable retirée dans une version
ultérieure, ne se verraient qu'au redémarrage.

**Le redémarrage reste donc la seule preuve de l'aller-retour**, et c'est pour
cela que le test central le joue.

Second piège, que le guide nomme : une variable **statique** refuse
`SET GLOBAL` avec un `ERROR 1238 ... is a read only variable`. Ce n'est pas une
question d'autorisation, c'est le contexte de la variable.

## Ce qu'il ne couvre pas

Le dimensionnement par rapport à la charge réelle, qui demande de mesurer
avant de régler. Les nouveaux défauts InnoDB de 8.4 et `innodb_dedicated_server`,
que le guide traite et qui relèvent d'un arbitrage, pas d'un geste. Le binary
log, qui appartient au lab de sauvegarde.

## Durée

40 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)
