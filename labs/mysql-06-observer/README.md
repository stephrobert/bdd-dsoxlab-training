# mysql-06: the plan and the size, two states nothing guesses

## What this lab exercises

The three operational moves a guide lists and nobody proves: make a query fast,
reclaim the space of a purge, and find the offending query in the diagnostic
views. It opens **MySQL level 2**.

It is graded on the **execution plan** the server reports and on the **size**
the table really occupies. No test reads the table's index list, and that is
the lab's central choice: an index can exist without serving, and the catalog
will never say so.

## The three measured facts that decided its shape

Taken on MySQL 8.4 on 2026-10-20, in a disposable container, before a single
line of test was written.

| Moment | Rows | Size | Plan |
|---|---|---|---|
| starting state, after the purge | 20,000 | **45 MB** | `type: ALL`, 17,477 rows examined |
| after `CREATE INDEX` on `service` | 20,000 | **45 MB** | `type: ref`, 412 rows examined |
| after `OPTIMIZE TABLE` | 20,000 | **6 MB** | `type: ref`, unchanged |

**The second row is the one that counts.** Creating an index changes the plan
and reclaims **not a single byte**: the two tasks are therefore independent,
and neither test passes thanks to the other. That was the question to settle
before writing, because two tests where one makes the other true no longer
measure two things.

**`ALTER TABLE ... ENGINE=InnoDB` does the same as `OPTIMIZE TABLE`**, and the
lab accepts both. InnoDB cannot optimise in place: the server answers "Table
does not support optimize, doing recreate + analyze instead", which says plainly
that the two moves are one.

**`data_free` does not report dead space.** Measured: 2 MB before the purge,
2 MB after, 1 MB after the rebuild. An operator watching it concludes nothing
happened, in both directions.

## The operational trap, and it surprises everyone

A query run **without a default database** is recorded in the Performance
Schema with a **null** `SCHEMA_NAME`. So it does not appear in
`sys.statement_analysis` when you filter on `db`, which is nonetheless how one
looks for the costly queries of a database.

Measured: the same query run twice, once without a database selected and once
with, produces **two distinct digests**, one under `NULL` and one under
`appli`. The lab's probe returns 0 then 1.

## Two defects of my own, fixed before delivery

**My own tests made the third one green.** The helpers queried the table with
`-D appli`, so their `select count(*)` was filed under `appli`, and the probe
turned green as soon as the first test ran. No statement in that file uses a
default database any more: they name the table in full and are therefore filed
under `NULL`. The probe additionally requires the digest to carry the
dashboard's `WHERE`.

**`EXPLAIN FORMAT=JSON` is not readable as is.** The client escapes the JSON's
newlines as literal `\n`, and `json.loads` fails on it. The `--raw` option
disables that. Without it, the tests would have diagnosed a server failure
where there was only a client protecting its output.

## What it does not cover

The **slow query log**, which `mysql-03` already proves on a slow query landing
in it. **Alerting** and metrology over time, which need a collector.
**Replication**, which is level 3.

## Duration

40 minutes. Hints cost from 5 to 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/)
