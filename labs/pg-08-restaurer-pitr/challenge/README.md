# A DROP TABLE in production

## The situation

It is 2:30 pm. A poorly reviewed migration has just run a `DROP TABLE` on
`appli.clients`, in the `facturation` database on `db1.lab`. The table is gone,
and the application is down.

What saves you is that continuous WAL archiving was in place, and that a
physical backup of the cluster exists in `/var/lib/postgresql/backups/base`.

Someone had the presence of mind to note the instant just before the incident,
before the table disappeared. It is in `/home/student/instant-de-securite.txt`.

You are asked to bring the database back to that instant. Not to the last
available WAL: replaying everything means replaying the `DROP TABLE`. And not to
the physical backup alone either: the last row inserted before the incident is
not in it, it exists only in the logs.

So there is exactly one correct landing point, and that is the whole subject.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/ (in French)](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/) (in French)

## What is asked

On `db1.lab`. The `appli.clients` table of the `facturation` database has been
dropped. You have:

- a physical backup of the cluster in `/var/lib/postgresql/backups/base`;
- the archived WAL in `/var/lib/postgresql/wal_archive`;
- the instant preceding the incident, in `/home/student/instant-de-securite.txt`.

### 1. Bring the database back to the noted instant

At the end of the work, `appli.clients` must exist and hold **six** rows,
including the one named `PITR Test`, inserted just before the incident.

Six, not five: the physical backup alone would give five, because that row
exists only in the logs. And not zero: replaying all the WAL replays the `DROP
TABLE`.

### 2. Finish the recovery

The server must **no longer** be in recovery mode: the database must accept
writes.

By default the server **pauses** once the target is reached, and the database
stays read-only. There are two ways out, and the guide gives both.

### 3. The timeline must carry the trace

The cluster must be on a timeline **greater than 1**.

This is not an arbitrary requirement: a completed recovery promotes the cluster,
and a promotion increments the timeline. That is what tells a restored database
from a table recreated by hand.

### 4. Fill in the report

The `~/rapport-restauration.txt` file holds three values to complete:

- `lignes_restaurees`: the number of rows in `appli.clients`;
- `timeline_apres_restauration`: the cluster's timeline id;
- `serveur_en_recovery`: what `pg_is_in_recovery()` answers, in one letter.

**Edit the file in place.** Its header must survive.

### Check

```bash
dsoxlab check pg-08-restaurer-pitr
```
