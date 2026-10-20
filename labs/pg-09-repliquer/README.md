# pg-09: a streaming standby

## What this lab exercises

The catalogue's first **two-machine** lab. `db1.lab` is the primary, `db2.lab`
the standby, and the lab is graded on the **flow** between them: a row written
on the primary must be readable on the standby.

It is the only check that proves anything. A `primary_conninfo` written, a slot
created, a `pg_hba` line laid down: all of that can be right and nothing flow.

## The four traps it makes you meet

**The standby's data directory must be empty** before the copy. On Debian the
installation initialises a cluster: `pg_basebackup` refuses to write into a
non-empty directory, and the message does not say you must empty the one the
package just created.

**An ordinary `pg_hba` line is not enough.** Replication is a virtual database:
you need a line whose database column reads literally `replication`, and `all`
does not cover it. It is the most common mistake on this subject, and the error
message talks about a database that does not exist.

**Without a slot, a disconnected standby may never come back.** The primary
recycles its logs: if it recycles the ones the standby needs, synchronisation is
lost and the base copy must be redone. The slot is what tells it to retain them.

**A command run under another account cannot return where it came from.**
`find` saves its starting directory and returns to it when it finishes: run as
`postgres` from a home directory in 0700, it fails on "Failed to restore
initial working directory", and the message names that directory rather than
the cause. Both accounts on these machines have a 0700 home, measured: the
remedy is to move to `/tmp` first.

## What it does not cover

Manual failover (`pg_ctl promote`) and logical replication by publication and
subscription, which the guide covers and which each deserve their own lab.
Synchronous replication, which changes the primary's behaviour when the standby
fails.

## Duration

50 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/)
