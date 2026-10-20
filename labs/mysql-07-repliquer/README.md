# mysql-07: a row that travels, and two threads people confuse

## What this lab exercises

GTID source-replica replication, put into service between two machines, and the
only proof that counts: a row written on the source, found on the replica. It
opens **MySQL level 3** and it is the catalogue's **second two-machine lab**,
after `pg-09-repliquer`.

It is graded on the **Performance Schema state tables** and on a row that
travels. No test reads `SHOW REPLICA STATUS`: that is a forty-column display
whose shape changes between versions, where
`replication_connection_status` and `replication_applier_status` are data.

## The three measured facts that decided its shape

Taken on 2026-10-20 on two MySQL 8.4 servers placed on a common network, before
a single line of test was written.

**`gtid_mode` refuses to step up at once.** The server answers, word for word:

```text
ERROR 1788 (HY000): The value of @@GLOBAL.GTID_MODE can only be changed one
step at a time: OFF <-> OFF_PERMISSIVE <-> ON_PERMISSIVE <-> ON. Also note
that this value must be stepped up or down simultaneously on all servers.
```

That is a good message, and a rare one: it names the path **and** the
simultaneity constraint. So the brief quotes it rather than paraphrasing it.

**The default plugin blocks the channel.** With `caching_sha2_password`, the 8.4
default, a channel without TLS or a public key stays in `CONNECTING` with error
**2061**, "Authentication requires secure connection", and it retries **every
60 seconds**. Neither the password nor the privileges are at fault, and it is
the same error `mysql-04` makes learners meet on an application connection: the
coherence is welcome, the plugin is the same.

**`super_read_only` does not prevent application.** This is the measurement
that made the brief solvable. Requiring both a read-only replica and a row that
arrives could have been contradictory; measured, the row arrives in **1
second**, the applier stays `ON` and its error is `0`. The applier thread
bypasses `super_read_only` by design.

| What is attempted | Measured result |
|---|---|
| direct `INSERT` on the replica, as `labadmin` | refused, `ERROR 1290`, "running with the --super-read-only option" |
| the same attempt with `read_only` alone | would pass: it does not hold back all-powerful accounts |
| arrival delay of one row, five measurements | 48, 49, 50, 50 and 67 milliseconds |

The tests' threshold is **30 seconds**. It leaves room for a loaded virtual
machine, and it does not save a stopped replication.

## Why two tests for the two threads

The **input** thread receives the events, the **applier** thread plays them. A
connected replica whose applier is stopped falls behind indefinitely, and
nothing says so on screen. Confusing them is the most common diagnostic error,
hence two tests and two distinct messages.

## A replica starts from a copy, never from nothing

This is the defect that made the lab's first version fail, and it is mine: my
container measurement enabled GTID BEFORE creating the database, so its
creation carried a GTID and replicated. The lab's setup creates it BEFORE
enabling GTID, so its transactions are **anonymous**, and a replica using
automatic positioning only asks for GTIDs.

Measured on the lab's infrastructure, without seeding the replica:

    appli on db1 : 1      appli on db2 : 0
    applier      : OFF, error 1049
                   "Error executing row event: Unknown database 'appli'"

So the setup **seeds** the replica with the same database and the same rows, as
a restore would have done, and the learner's documents say so. This lab does
not teach seeding, which needs a dump and `gtid_purged` and belongs to
`mysql-05`: it posits it as a given, and says so.

The method lesson is worth more than the fix: a measurement taken under
conditions that are not the lab's does not prove the lab works. The two always
differ by one detail, and that is the one that breaks.

## The source's name does not resolve where you think

Measured on 2026-10-20 on the catalogue's infrastructure, and it is the defect
that would have made the lab unplayable:

    from db2 :  getent hosts db1.lab  ->  10.10.20.14
    on db1   :  real address          ->  10.10.100.11

So the name does not resolve "badly", it resolves to a machine on **another lab
network**: this catalogue declares `10.10.100.0/24`, and `10.10.20` is taken by
another repository. A learner writing `source_host='db1.lab'` would get a
connection error whose cause is neither the password, nor the privileges, nor
the plugin.

So the brief asks to **read the address on the source**, and says why.
`pg-09-repliquer` already worked around the problem without naming it: its
solution relays the primary's address through an Ansible fact rather than its
name.

## What this lab deliberately opens, and it will surprise

Its setup sets `bind-address = 0.0.0.0` on both servers, where every other
MySQL lab closes the listening down to `127.0.0.1`. The replica must reach the
source over the network: that is the opposite of `mysql-01`'s subject, and the
lab's network is isolated. The learner's brief does not hide it.

## What it does not cover

**Settings persistence** after a restart, which is `mysql-03`'s subject: a
`gtid_mode` set for the session is enough here, and the brief says so. Replica
**promotion** and failover, which need a stable entry point. **Group
Replication** and **InnoDB Cluster**, which are another architecture.
**Replication lag** under load, which needs a load generator.

## Duration

50 minutes. Hints cost from 5 to 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/replication/)
