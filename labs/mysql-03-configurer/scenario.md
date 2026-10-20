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

And nothing, on a running server, tells a value that will survive from one that
will vanish. Even the table that reports a value's **source** answers the same
thing in both cases. The only way to know is to restart, so that is what the
check will do.

The credentials: the `labadmin` account, password `Adm1n!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/configuration/)
