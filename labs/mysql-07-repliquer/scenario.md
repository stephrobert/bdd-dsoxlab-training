# Two servers ignoring each other, and a backup that is no longer enough

`db1.lab` serves the `appli` database in production. `db2.lab` exists, MySQL
runs on it, and the two servers do not know each other.

The replica has already received a **copy** of the database, restored from
yesterday's backup: it holds the same tables and the same rows. That is a given
of this lab, and it is no detail: a replica never starts from nothing. Without
that copy, its applier thread stops on the first transaction with an error
`1049`, "Unknown database", measured.

The nightly backup protects against an accidental deletion, it does not protect
against a hardware failure: by the time you restore, the service is down. So
you are asked for a **replica**, which follows the source continuously and can
be promoted.

Three things to know before you start, and the first two will cost you an error
if you ignore them.

**`gtid_mode` refuses to go from OFF to ON in one step.** The server answers an
error `1788` that names the path, and it adds that the value must be stepped up
**simultaneously on all servers**. Read the message, it says everything.

**The default authentication plugin blocks the replica's connection.** With
`caching_sha2_password`, the replica stays in `CONNECTING` on an error `2061`
mentioning "secure connection", and it retries every 60 seconds. It is neither
the password nor the privileges.

**`SHOW REPLICA STATUS` is a display, not a proof.** The check reads the
Performance Schema **state tables**, and above all it writes a row on the
source then looks for it on the replica. A replication that reports `ON`
without carrying anything exists, and that is the failure you do not see.

**And do not configure the channel on the `db1.lab` name.** Measured on this
infrastructure: from `db2`, that name resolves to a machine on **another lab
network**, not to the source. Read the source's address **on the source**, for
instance with `ip -4 addr show`, and use that. You do not configure a
replication on a name you have not checked.

Credentials: the `labadmin` administration account on **both** servers,
password `Adm1n!Lab2026`. The replication account to create will be called
`replicator`, with password `R3pl!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/)
