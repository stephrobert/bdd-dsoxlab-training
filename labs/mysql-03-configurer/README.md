# mysql-03: configure, and survive the restart

## What this lab exercises

Three day-to-day operational settings, and the only thing that proves they
hold: a **restart**.

The central test stops and starts the server, then rereads the three values.
That is not a precaution, it is the only measurement available, and the lab
exists for that reason.

The slow query log is graded on a **slow query actually landing in it**. A log
turned on that nothing comes out of serves nobody, and it happens: a file the
server's account cannot write, a misread threshold, output sent to a table
rather than a file.

## The trap it makes you meet

**Nothing tells a persisted value from a volatile one on a running server.**
Measured on MySQL 8.4:

| How the value was set | Reported source |
|---|---|
| left at the default | `COMPILED` |
| `SET GLOBAL` | `DYNAMIC` |
| `SET PERSIST` | `DYNAMIC` too |

So `performance_schema.variables_info`, the table that reports a value's
source, answers the **same thing** after a `SET GLOBAL` that will be lost at
restart and after a `SET PERSIST` that will survive. The source only becomes
`PERSISTED` **after** the restart, when the value is reread from
`mysqld-auto.cnf`.

A second trap, which the guide names: a **static** variable refuses
`SET GLOBAL` with an `ERROR 1238 ... is a read only variable`. It is not a
matter of authorisation, it is the variable's context.

## What it does not cover

Sizing against real load, which requires measuring before setting. The new
InnoDB defaults of 8.4 and `innodb_dedicated_server`, which the guide covers
and which are a judgement call rather than a move. The binary log, which
belongs to the backup lab.

## Duration

40 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)
