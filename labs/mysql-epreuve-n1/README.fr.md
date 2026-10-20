# mysql-epreuve-n1 : l'épreuve du niveau 1

## Ce que cette épreuve éprouve

Les cinq labs du niveau, ensemble, sur une seule instance et depuis un seul
énoncé. Elle ne réexplique rien : elle mesure ce qui reste quand les
instructions pas à pas disparaissent.

C'est le **premier lab évalué** de ce catalogue : `lab_type: challenge` et
`exam_passing_score: 70`, donc `dsoxlab submit` rend un verdict et non
seulement une note.

| Ce qu'elle mesure | Le lab qui l'a enseigné |
|---|---|
| un compte tout-puissant qui disparaît | mysql-04 |
| un rôle aux droits exacts, et son activation | mysql-04 |
| le TLS exigé sur le compte | mysql-04 |
| trois réglages qui survivent à un redémarrage | mysql-03 |
| l'écoute refermée sur la boucle locale | mysql-01 et mysql-03 |
| une sauvegarde complète et sa restauration prouvée | mysql-05 |
| lire le serveur plutôt que le deviner | mysql-02 |

## Le barème est contractuel, et un garde-fou le tient

Dix tâches annoncées à dix points, dix tests dans le fichier. dsoxlab note
**par test** : ajouter un test sans ajouter une tâche décalerait tout le barème
sans que personne le voie, et le validateur de contenu de dsoxlab refuse
justement cet écart. Toute modification de ce lab doit donc toucher l'énoncé
**et** les tests ensemble.

## Les deux décisions de conception qui ont coûté le plus

**Le setup DÉSASSEMBLE l'instance à chaque passage.** Il recrée `app_tout`,
rétablit `bind-address = 0.0.0.0`, efface `mysqld-auto.cnf` et **retire les
fichiers de configuration que le candidat aurait ajoutés**. Sans ce dernier
point, un `z-zz-candidat.cnf` d'un passage précédent l'emporterait sur celui du
setup, l'ordre de lecture étant alphabétique : le deuxième passage noterait
alors le travail du premier.

**Aucune sonde ne détruit ce qu'une autre mesure.** Le premier jet vérifiait le
moindre privilège en tentant un `DROP TABLE`. Sur une copie trop permissive, ce
`DROP` aboutit : la table disparaît, le test passe au rouge, et les deux
suivants aussi, pour une raison que personne ne rattache à la bonne cause. Les
sondes de refus sont donc inoffensives en cas de succès, lire `mysql.user` et
créer une base qu'on retire ensuite.

## Ce qu'elle ne mesure pas

`--single-transaction`, pour la raison expliquée dans mysql-05 : aucune trace
vérifiable dans le fichier produit. Le PITR et la réplication, qui sont des
niveaux suivants. Et le temps : l'épreuve est annoncée à 1h15, rien ne le
chronomètre.

## Les indices coûtent cher, à dessein

20 et 30 points. Un candidat qui prend les deux tombe à 50 et ne peut plus
atteindre 70 : c'est voulu. Ils servent à repartir quand on est bloqué, et
l'épreuve se repasse. Ils nomment les deux pièges du niveau sans donner une
seule commande.

## Durée

1h15.

Le guide du niveau : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/)
