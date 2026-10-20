# pg-06: observe, identify, fix

## What this lab exercises

The guide's method, end to end, on a single case: **observe** with
`pg_stat_statements`, **identify** with `EXPLAIN`, **fix** with an index, and
**maintain** with `VACUUM`.

## The trap it makes you meet

**An index that exists is not an index in use.** It is the most common case, and
the most expensive: you create the index, the query stays slow, and you look
elsewhere. So the lab never grades an index's existence. It reads the query's
**plan** and requires the sequential scan to be gone: it is the planner that
says whether the fix landed, not the catalog.

A second trap of the same kind: `pg_stat_statements` does not install with a
`CREATE EXTENSION`. The library must be loaded **at server start**, which makes
it a postmaster-context parameter. A `CREATE EXTENSION` on a server that has not
preloaded it fails, and the message does not say what to do.

## What it does not cover

Fine-tuning autovacuum table by table, and Prometheus metrics, which the guide
files under "going further". `VACUUM FULL`, which takes an exclusive lock and
has no place on a table in service.

## Duration

40 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/)
