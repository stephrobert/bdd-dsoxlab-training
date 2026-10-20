# pg-07: physical backup and continuous archiving

## What this lab exercises

What extends a backup to the moment of the incident: a physical copy of the
cluster, and the chain of logs that follows it.

It is graded on the **result**: files actually present in the archive, an
archiving counter that moved, no failure recorded, and a physical backup that
`pg_verifybackup` declares valid. Configuration is never graded for itself.

## The three traps it makes you meet

**`archive_mode` requires a restart.** A `reload` succeeds without applying it,
and does not say so. It is the same trap as the configuration lab, on a
parameter whose breakage only shows at incident time.

**Archiving only fires when a segment is complete.** A quiet server archives
nothing, and `archived_count` stays at zero although everything is set right.
That is why looking at the directory is not enough to conclude.

**`pg_verifybackup` is not in the `PATH`.** The PGDG packages put it in
`/usr/lib/postgresql/18/bin/`. A tool you cannot find is a tool you do not use,
and an unverified physical backup is no better than an unrestored dump.

## What it does not cover

Point-in-time recovery itself (`recovery_target_time`, `recovery.signal`),
which requires stopping the cluster and starting it on the copy: that is the
next lab. Here we build what makes it possible, and prove it.

The retention policy for archived WAL, which the guide covers and belongs to
day-to-day operations more than to the move itself.

## Duration

45 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
