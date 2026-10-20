# An instance that says nothing about what it does

`db1.lab` has been running a PostgreSQL 18 instance in production for a week.
The application writes to it, backups go through, nobody complains.

This morning the application team reports intermittent slowness. You are asked
which of its queries are slow. You open the logs: there is nothing. Not one
query, not one connection, and the few lines present say neither when, nor who,
nor on which database. The instance runs with factory logging settings, which
trace almost nothing.

`max_connections` also needs raising, as the application will saturate it at
the next tier.

One constraint, and it is the whole subject: **the application must not lose a
single session.** A restart is out of the question. Yet among the parameters you
must set, some take effect as soon as the server rereads its files, and one
waits for nothing less than its next start. Nothing will tell you: a reload
always succeeds, even when it leaves a parameter without effect.

So you must know which apply, which wait, and prove it.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/)
