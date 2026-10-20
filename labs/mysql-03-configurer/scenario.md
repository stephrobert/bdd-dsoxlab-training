# An instance tuned for a laptop

`db1.lab` runs MySQL 8.4, installed and reachable. Its settings, though, are
still the package's.

The InnoDB buffer pool is **128 MB**, the compiled default. It is the cache
that avoids disk reads, and on a machine with several gigabytes that is absurd.
The connection ceiling is 151, and the application will ask for more at the
next tier.

Above all, the slow query log is **off**. One day you will be asked which query
is slowing the application down, and there will be nothing to read.

So you are asked to set all three, and to make it **survive a restart**. That
last point is not a formality: MySQL offers three ways to change a variable,
and two of them lose the setting at the next start without saying so.

One server table, `performance_schema.persisted_variables`, does say what has
been persisted, and that is useful. But it reflects what the server **meant**
to write rather than the file's state: empty that file behind its back and the
table keeps reporting the value. So it proves the intent, not the round trip.

The only way to know whether a value will come back is to restart, so that is
what the check will do.

The credentials: the `labadmin` account, password `Adm1n!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)
