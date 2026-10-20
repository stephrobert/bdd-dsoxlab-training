# "We have a backup"

The `facturation` database on `db1.lab` holds the production data. It is backed
up, you are told: a `pg_dump` runs every night and drops its file in
`/var/backups/postgresql/`.

You ask when the restore was last exercised. Nobody knows. The directory is
empty, as it happens: the job stopped running a while ago, and nothing reported
it.

You are asked to take the subject from the top, and to deliver nothing you have
not verified.

Three things, and the third is the only one that proves anything. Produce the
database's backup. Capture what a database backup **does not contain**: roles
are global to the cluster, `pg_dump` ignores them, and a restore onto a fresh
machine then fails on owners and privileges. Then restore for real, into a
verification database, and compare.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
