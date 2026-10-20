# pg-08: restore to a point in time

## What this lab exercises

The move that gives meaning to everything before it. A physical backup alone
brings you back to the backup's hour; the logs alone bring you back nowhere.
Together they bring you back to **the instant you choose**, and it is that
choice the lab grades.

Three landing points are possible, and two are wrong:

- the physical backup alone: the last row inserted before the incident is
  missing;
- the last available WAL: the `DROP TABLE` is replayed, so the incident is
  reproduced;
- the instant noted just before: the only one that makes the database usable.

## The trap it makes you meet

There has been **no `recovery.conf`** since PostgreSQL 12. The recovery
parameters live in `postgresql.conf`, and it is the **`recovery.signal`** file
that triggers recovery mode at start. Someone who learned PostgreSQL before 12,
or who reads a dated post, writes a file the server ignores, and concludes that
PITR does not work.

A second, less known trap: the server stops **paused** once the target is
reached, because `recovery_target_action` defaults to `pause`. The database is
then read-only and looks unfinished. You must either take over
(`pg_wal_replay_resume()`) or have asked for `promote` from the start.

## How it is graded, and why

On the data **and** on the **timeline**. A completed recovery promotes the
cluster, and a promotion increments the timeline: a fresh cluster is at 1, a
restored and promoted one at 2.

That is what makes it possible to grade the move rather than its apparent
result. Without that check, recreating the table by hand would pass all the
others.

## What it does not cover

Recovery targeted by transaction id (`recovery_target_xid`) or by named point
(`recovery_target_name`), which follow the same mechanics. pgBackRest, which
automates all of this and which the guide files elsewhere.

## Duration

50 minutes. Hints cost between 5 and 20 points. This is an assessment: the pass
mark is 80%.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
