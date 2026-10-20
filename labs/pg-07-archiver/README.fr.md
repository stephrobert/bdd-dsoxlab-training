# pg-07 : sauvegarde physique et archivage continu

## Ce que ce lab éprouve

Ce qui prolonge une sauvegarde jusqu'à l'instant de l'incident : une copie
physique de la grappe, et la chaîne des journaux qui la suit.

Il est noté sur le **résultat** : des fichiers réellement présents dans
l'archive, un compteur d'archivage qui a bougé, aucun échec enregistré, et une
sauvegarde physique que `pg_verifybackup` déclare valide. La configuration
n'est jamais notée pour elle-même.

## Les trois pièges qu'il fait rencontrer

**`archive_mode` exige un redémarrage.** Un `reload` réussit sans l'appliquer,
et ne le dit pas. C'est le même piège que le lab de configuration, sur un
paramètre dont la panne ne se voit qu'à l'incident.

**L'archivage ne se déclenche qu'à segment complet.** Un serveur peu actif
n'archive rien, et `archived_count` reste à zéro alors que tout est bien réglé.
C'est la raison pour laquelle on ne peut pas se contenter de regarder le
répertoire pour conclure.

**`pg_verifybackup` n'est pas dans le `PATH`.** Les paquets PGDG le posent dans
`/usr/lib/postgresql/18/bin/`. Un outil qu'on ne trouve pas est un outil qu'on
n'emploie pas, et une sauvegarde physique non vérifiée ne vaut pas mieux qu'un
dump non restauré.

## Ce qu'il ne couvre pas

La restauration à un instant donné elle-même (`recovery_target_time`,
`recovery.signal`), qui demande d'arrêter la grappe et de la repartir sur la
copie : c'est le lab suivant. Ici on construit de quoi la rendre possible, et
on le prouve.

La politique de rétention des WAL archivés, que le guide traite et qui relève
de l'exploitation courante plus que du geste.

## Durée

45 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
