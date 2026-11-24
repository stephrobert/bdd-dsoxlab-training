# Backing up at night is no longer enough

## The situation

The `facturation` database is backed up every night by a `pg_dump`. The team
running it has just put a number on what that costs: if the incident happens at
5 pm, the day is lost.

You are asked to set up what it takes to lose no more than one log segment: a
**physical backup** of the cluster, and the **continuous WAL archiving** that
extends it to the moment of the incident.

Two things to know before you start, and they cost dearly to whoever discovers
them in production.

`archive_mode` requires a **full restart**. A `reload` succeeds and does not
apply it, without a word.

And archiving only fires **when a segment is complete**. On a quiet database you
can have everything set correctly and see no file arrive for hours. Whoever
concludes it is broken looks in the wrong place; whoever stops at `SHOW
archive_mode` believes archiving is in place when nothing has left yet.

So you are asked for the proof, not the configuration.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/ (in French)](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/) (in French)

## What is asked

On `db1.lab`. The `facturation` database is running, `wal_level` is at its
default value.

### 1. Archive the logs continuously

The archive directory is `/var/lib/postgresql/wal_archive`. It must exist and belong to `postgres`.

Archiving must be **in service** on the running server, and its command must
carry the source path (`%p`) and the file name (`%f`), and **refuse to
overwrite** an already archived log. Two forms are accepted for that refusal: a
`test ! -f` before the copy, or a `cp -n`.

Mind this: `archive_mode` is postmaster-context. A reload succeeds without
applying it.

### 2. Prove logs really leave

The archive directory must hold **at least one** segment, the `archived_count`
counter of `pg_stat_archiver` must be above zero, and `last_failed_wal` must be
empty.

This is where the lab is won. Archiving only fires when a segment is complete: a
quiet database archives nothing, and the most correct configuration in the world
produces no file.

### 3. Take a physical backup

Drop a **plain format** physical backup of the cluster into `/var/lib/postgresql/backups/base`, the
one that serves as the starting point for a point-in-time recovery.

It must be declared valid by `pg_verifybackup`, which the PGDG packages put in
`/usr/lib/postgresql/18/bin/` and not in the `PATH`.

### 4. Fill in the report

The `~/rapport-archivage.txt` file holds three values to complete:

- `archive_mode_en_service`: the value the server runs with;
- `nb_wal_archives`: the `archived_count` counter of `pg_stat_archiver`;
- `verdict_verifybackup`: the sentence `pg_verifybackup` returns on your
  backup, copied as is.

**Edit the file in place.** Its header must survive.

### Check

```bash
dsoxlab check pg-07-archiver
```
