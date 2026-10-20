# What is asked

On `db1.lab`. The `facturation` database is running, `wal_level` is at its
default value.

## 1. Archive the logs continuously

The archive directory is `/var/lib/postgresql/wal_archive`. It must exist and belong to `postgres`.

Archiving must be **in service** on the running server, and its command must
carry the source path (`%p`) and the file name (`%f`), and **refuse to
overwrite** an already archived log. Two forms are accepted for that refusal: a
`test ! -f` before the copy, or a `cp -n`.

Mind this: `archive_mode` is postmaster-context. A reload succeeds without
applying it.

## 2. Prove logs really leave

The archive directory must hold **at least one** segment, the `archived_count`
counter of `pg_stat_archiver` must be above zero, and `last_failed_wal` must be
empty.

This is where the lab is won. Archiving only fires when a segment is complete: a
quiet database archives nothing, and the most correct configuration in the world
produces no file.

## 3. Take a physical backup

Drop a **plain format** physical backup of the cluster into `/var/lib/postgresql/backups/base`, the
one that serves as the starting point for a point-in-time recovery.

It must be declared valid by `pg_verifybackup`, which the PGDG packages put in
`/usr/lib/postgresql/18/bin/` and not in the `PATH`.

## 4. Fill in the report

The `~/rapport-archivage.txt` file holds three values to complete:

- `archive_mode_en_service`: the value the server runs with;
- `nb_wal_archives`: the `archived_count` counter of `pg_stat_archiver`;
- `verdict_verifybackup`: the sentence `pg_verifybackup` returns on your
  backup, copied as is.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check pg-07-archiver
```
