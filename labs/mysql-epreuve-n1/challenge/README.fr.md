# L'instance dont personne ne voulait

## La situation

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

## Épreuve du niveau 1

**10 tâches notées, 100 points en tout**, et il en faut 70 pour réussir. Chaque
tâche vaut donc 10 points, et elle est notée sur l'**état du serveur**, jamais
sur les commandes que tu as tapées.

Deux indices existent. Ils coûtent 20 et 30 points : à ce prix, ils servent à
repartir quand on est bloqué, pas à avancer plus vite.

Sur `db1.lab`. Le compte d'administration est `labadmin`, mot de passe
`Adm1n!Lab2026`. La base `appli` porte deux tables, une procédure stockée
`chiffre_affaires()` et un trigger `montant_positif`.

## Ce que l'instance doit devenir

### Le compte tout-puissant n'existe plus (10 points)

`app_tout` doit avoir disparu du serveur. Un compte `@'%'` avec
`GRANT ALL PRIVILEGES ON *.*` n'est pas un compte applicatif, c'est un
contournement de tout ce qui suit.

### Un rôle porte les droits, et rien de plus (10 points)

Un rôle `role_appli` qui détient exactement `SELECT`, `INSERT`, `UPDATE` et
`DELETE` sur `appli.*`. Un rôle, pas un compte : il ne doit pas pouvoir se
connecter.

### Le compte de service se connecte, et son rôle est actif (10 points)

Un compte `appli_svc` joignable depuis `127.0.0.1`, mot de passe
`Svc!Appli2026`, qui reçoit `role_appli` et **lui seul**.

À la connexion, son rôle doit être **actif**.

### Le clair est refusé, le chiffré aboutit (10 points)

Une connexion de `appli_svc` sans chiffrement doit être **refusée**, une
connexion chiffrée doit **aboutir**.

### Le moindre privilège, prouvé (10 points)

`appli_svc` doit pouvoir lire et écrire dans `appli`, et **ne pas** pouvoir
lire la base `mysql` ni supprimer une table.

### Les réglages demandés survivent à un redémarrage (10 points)

Trois valeurs, et elles doivent être là **après** un redémarrage du service :

| Réglage | Valeur attendue |
|---|---|
| `max_connections` | `200` |
| `slow_query_log` | activé |
| `long_query_time` | `1` |

La vérification redémarre le serveur. Un réglage posé pour la session en cours
ne compte pas.

### L'instance n'écoute que sa boucle locale (10 points)

Après ce même redémarrage, le serveur ne doit plus accepter de connexion que
depuis `127.0.0.1`, sur les deux protocoles.

Attention : tous les réglages ne se posent pas au même endroit, et celui-ci
n'est pas dynamique.

### La sauvegarde est complète (10 points)

Un fichier `~/sauvegardes/appli.sql`, sauvegarde logique de `appli`, qui porte
le schéma, les données, le trigger **et la procédure stockée**.

### La restauration est utilisable (10 points)

Une base `appli_restauree`, restaurée depuis ce fichier, avec les mêmes lignes
que `appli` et une procédure `chiffre_affaires()` qui **répond**.

### Le rapport dit l'état réel (10 points)

Le fichier `~/rapport-epreuve.txt` porte trois valeurs à compléter :

- `connexions_max_apres_redemarrage` : ce que `@@max_connections` vaut une fois
  le service redémarré ;
- `role_actif_du_compte_de_service` : ce que `CURRENT_ROLE()` répond dans une
  session de `appli_svc`, recopié tel quel ;
- `procedures_dans_la_base_restauree` : combien de routines
  `information_schema.routines` compte pour `appli_restauree`.

**Édite le fichier sur place.** Son en-tête doit survivre, et un rapport juste
sur une instance fausse ne rapporte rien : cette tâche se note en plus des
autres, pas à leur place.

## Vérifier

```bash
dsoxlab check mysql-epreuve-n1
```

La note s'affiche sur 100, et `dsoxlab submit mysql-epreuve-n1` rend le verdict
de l'épreuve.
