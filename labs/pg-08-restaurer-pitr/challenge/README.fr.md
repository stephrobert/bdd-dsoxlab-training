# Ce qui est demandé

Sur `db1.lab`. La table `appli.clients` de la base `facturation` a été
supprimée. Tu disposes de :

- une sauvegarde physique de la grappe dans `/var/lib/postgresql/backups/base` ;
- les WAL archivés dans `/var/lib/postgresql/wal_archive` ;
- l'instant qui précède l'incident, dans `/home/student/instant-de-securite.txt`.

## 1. Ramener la base à l'instant noté

À la fin du travail, `appli.clients` doit exister et porter **six** lignes,
dont celle au nom `PITR Test`, insérée juste avant l'incident.

Six, et pas cinq : la sauvegarde physique seule en rendrait cinq, parce que
cette ligne n'existe que dans les journaux. Et pas zéro : rejouer tous les WAL
rejoue le `DROP TABLE`.

## 2. Terminer la restauration

Le serveur ne doit **plus** être en mode restauration : la base doit accepter
les écritures.

Par défaut, le serveur se met **en pause** une fois la cible atteinte, et la
base reste en lecture seule. Deux façons d'en sortir, et le guide donne les
deux.

## 3. La timeline doit en porter la trace

La grappe doit être sur une timeline **supérieure à 1**.

Ce n'est pas une contrainte arbitraire : une restauration menée à son terme
promeut la grappe, et une promotion incrémente la timeline. C'est ce qui
distingue une base restaurée d'une table recréée à la main.

## 4. Remplir le rapport

Le fichier `~/rapport-restauration.txt` porte trois valeurs à compléter :

- `lignes_restaurees` : le nombre de lignes de `appli.clients` ;
- `timeline_apres_restauration` : l'identifiant de timeline de la grappe ;
- `serveur_en_recovery` : ce que `pg_is_in_recovery()` répond, en une lettre.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check pg-08-restaurer-pitr
```
