# pg-05: back up logically, and prove it

## What this lab exercises

A backup is a three-step move, and the last two are the ones people skip.

**Produce** the dump, in custom format, the one that allows a selective
restore. **Capture what the dump does not contain**: the roles, global to the
cluster. **Restore** into a verification database and compare its content with
the original, table by table.

The lab is graded on the restored content, not on a file's existence. A 5 KB
dump on disk proves nothing at all.

## The two traps it makes you meet

`pg_dump` **does not back up roles**. The guide says it in so many words: they
are global to the cluster. Restoring that dump onto a fresh machine then fails
on every owner and every privilege, and you find out on the day of the
incident. `pg_dumpall --globals-only` is the other half of the backup.

A **plain** format dump (`-Fp`) is not readable by `pg_restore`: it is an SQL
script, replayed with `psql`. The format decides which restore tools are
available, so it is chosen at backup time, not at incident time.

## What it does not cover

Physical backup (`pg_basebackup`), WAL archiving and point-in-time recovery,
which require a continuity of archives and belong to level 2.

## Duration

35 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
