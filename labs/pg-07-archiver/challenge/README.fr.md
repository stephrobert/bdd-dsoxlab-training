# Sauvegarder la nuit ne suffit plus

## La situation

La base `facturation` est sauvegardée chaque nuit par un `pg_dump`. L'équipe
qui l'exploite vient de chiffrer ce que cela coûte : si l'incident arrive à
17 h, on perd la journée.

On te demande de préparer ce qu'il faut pour ne plus perdre qu'un segment de
journal : une **sauvegarde physique** de la grappe, et l'**archivage continu
des WAL** qui la prolonge jusqu'à l'instant de l'incident.

Deux choses à savoir avant de commencer, et elles coûtent cher à qui les
découvre en production.

`archive_mode` exige un **redémarrage complet**. Un `reload` réussit et ne
l'applique pas, sans un mot.

Et l'archivage ne se déclenche **qu'à segment complet**. Sur une base peu
active, tu peux tout avoir réglé correctement et ne voir aucun fichier arriver
pendant des heures. Celui qui en conclut que c'est en panne cherche au mauvais
endroit ; celui qui s'arrête à `SHOW archive_mode` croit son archivage en place
alors que rien n'est encore parti.

On te demande donc d'en apporter la preuve, pas la configuration.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)

## Ce qui est demandé

Sur `db1.lab`. La base `facturation` tourne, `wal_level` est à sa valeur par
défaut.

### 1. Archiver les journaux en continu

Le répertoire d'archive est `/var/lib/postgresql/wal_archive`. Il doit exister et appartenir à
`postgres`.

L'archivage doit être **en service** sur le serveur en marche, et sa commande
doit porter le chemin source (`%p`) et le nom du fichier (`%f`), et **refuser
d'écraser** un journal déjà archivé. Deux formes sont acceptées pour ce refus :
un `test ! -f` devant la copie, ou un `cp -n`.

Attention : `archive_mode` est de contexte `postmaster`. Un rechargement
réussit sans l'appliquer.

### 2. Prouver que des journaux partent vraiment

Le répertoire d'archive doit contenir **au moins un** segment, le compteur
`archived_count` de `pg_stat_archiver` doit être supérieur à zéro, et
`last_failed_wal` doit être vide.

C'est ici que le lab se joue. L'archivage ne se déclenche qu'à segment
complet : une base peu active n'archive rien, et la configuration la plus juste
du monde ne produit aucun fichier.

### 3. Prendre une sauvegarde physique

Dépose dans `/var/lib/postgresql/backups/base` une sauvegarde physique de la grappe au **format
plain**, celle qui sert de point de départ à une restauration à un instant
donné.

Elle doit être déclarée valide par `pg_verifybackup`, que les paquets PGDG
posent dans `/usr/lib/postgresql/18/bin/` et non dans le `PATH`.

### 4. Remplir le rapport

Le fichier `~/rapport-archivage.txt` porte trois valeurs à compléter :

- `archive_mode_en_service` : la valeur avec laquelle le serveur tourne ;
- `nb_wal_archives` : le compteur `archived_count` de `pg_stat_archiver` ;
- `verdict_verifybackup` : la phrase que `pg_verifybackup` rend sur ta
  sauvegarde, recopiée telle quelle.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check pg-07-archiver
```
