# Ce qui est demandé

Sur `db1.lab`. La base `facturation` tourne, `wal_level` est à sa valeur par
défaut.

## 1. Archiver les journaux en continu

Le répertoire d'archive est `/var/lib/postgresql/wal_archive`. Il doit exister et appartenir à
`postgres`.

L'archivage doit être **en service** sur le serveur en marche, et sa commande
doit porter le chemin source (`%p`) et le nom du fichier (`%f`), et **refuser
d'écraser** un journal déjà archivé. Deux formes sont acceptées pour ce refus :
un `test ! -f` devant la copie, ou un `cp -n`.

Attention : `archive_mode` est de contexte `postmaster`. Un rechargement
réussit sans l'appliquer.

## 2. Prouver que des journaux partent vraiment

Le répertoire d'archive doit contenir **au moins un** segment, le compteur
`archived_count` de `pg_stat_archiver` doit être supérieur à zéro, et
`last_failed_wal` doit être vide.

C'est ici que le lab se joue. L'archivage ne se déclenche qu'à segment
complet : une base peu active n'archive rien, et la configuration la plus juste
du monde ne produit aucun fichier.

## 3. Prendre une sauvegarde physique

Dépose dans `/var/lib/postgresql/backups/base` une sauvegarde physique de la grappe au **format
plain**, celle qui sert de point de départ à une restauration à un instant
donné.

Elle doit être déclarée valide par `pg_verifybackup`, que les paquets PGDG
posent dans `/usr/lib/postgresql/18/bin/` et non dans le `PATH`.

## 4. Remplir le rapport

Le fichier `~/rapport-archivage.txt` porte trois valeurs à compléter :

- `archive_mode_en_service` : la valeur avec laquelle le serveur tourne ;
- `nb_wal_archives` : le compteur `archived_count` de `pg_stat_archiver` ;
- `verdict_verifybackup` : la phrase que `pg_verifybackup` rend sur ta
  sauvegarde, recopiée telle quelle.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check pg-07-archiver
```
