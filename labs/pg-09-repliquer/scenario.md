# A single machine carries production

`db1.lab` carries the `facturation` database, and it carries it alone. Backups
are in place, log archiving too: we know how to come back after an incident.
What we cannot do is carry on during one.

`db2.lab` is available, with PostgreSQL installed and an empty cluster running
for nothing.

You are asked to turn it into a **streaming standby**: a copy that follows the
primary continuously, ready to take over, and which can already be queried for
reads to relieve reporting.

Three precautions, and they are not comfort details.

The standby must authenticate against the primary. Using `postgres` for that
would store a superuser password on the second machine, and would open full
access to the primary if it were compromised.

The primary must **retain** the logs the standby needs. Without that, a standby
disconnected for a few hours wakes up to recycled logs, and everything must be
started over.

Finally, replication is not a backup: a `DROP TABLE` on the primary replicates
in a few milliseconds. It protects against a machine failing, not against human
error.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/)
