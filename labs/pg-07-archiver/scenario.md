# Backing up at night is no longer enough

The `facturation` database is backed up every night by a `pg_dump`. The team
running it has just put a number on what that costs: if the incident happens at
5 pm, the day is lost.

You are asked to set up what it takes to lose no more than one log segment: a
**physical backup** of the cluster, and the **continuous WAL archiving** that
extends it to the moment of the incident.

Two things to know before you start, and they cost dearly to whoever discovers
them in production.

`archive_mode` requires a **full restart**. A `reload` succeeds and does not
apply it, without a word.

And archiving only fires **when a segment is complete**. On a quiet database you
can have everything set correctly and see no file arrive for hours. Whoever
concludes it is broken looks in the wrong place; whoever stops at `SHOW
archive_mode` believes archiving is in place when nothing has left yet.

So you are asked for the proof, not the configuration.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
