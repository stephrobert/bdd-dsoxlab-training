# L'instance dont personne ne voulait

Le collègue qui tenait `db1.lab` est parti vendredi. L'instance MySQL qui sert
la base `appli` tourne, et c'est à peu près tout ce qu'on peut en dire de bien.

Elle écoute sur **toutes** les interfaces. Un seul compte sert l'application,
`app_tout`, déclaré `@'%'` avec `GRANT ALL PRIVILEGES ON *.*` : il peut lire
les empreintes de mots de passe et supprimer n'importe quelle base, depuis
n'importe où. Aucun réglage n'a jamais été touché, le journal des requêtes
lentes est éteint, et personne ne sait ce que la base fait de ses journées.

Et il n'y a **aucune sauvegarde**. Pas une vieille, pas une incomplète : aucune.

Tu reprends l'astreinte lundi. On te demande de ramener cette instance à un
état que tu accepterais de défendre, et de le **prouver**, parce que la parole
ne vaut rien à trois heures du matin.

C'est une **épreuve**. Rien ne te sera réexpliqué : les cinq labs du niveau
l'ont enseigné, celle-ci le mesure. Dix tâches notées, 70 points pour réussir,
et tout est noté sur l'**état réel du serveur**, après un redémarrage. Deux
indices existent, et ils coûtent cher.

Les identifiants : le compte d'administration `labadmin`, mot de passe
`Adm1n!Lab2026`. Le mot de passe du compte de service à créer est imposé par
l'énoncé, parce qu'un test doit pouvoir s'en servir.

Le guide du niveau : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/)
