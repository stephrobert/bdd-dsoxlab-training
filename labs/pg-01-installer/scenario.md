# A database server that nobody installed on purpose

The team keeps its inventory in a spreadsheet and wants a real database for
it. Someone ran `apt install postgresql` on a test machine last month and
nobody remembers which version it gave, where it comes from, or whether it
comes back after a reboot.

The decision is made: PostgreSQL 18, from the project's own package
repository (PGDG), on a fresh Debian 13 machine. You inherit `db1.lab`. It is
bare: no PostgreSQL, no repository for it.

## Mission

Put an instance into service that you could leave in production.

Three things matter more than seeing `psql` answer.

The first is **where the packages come from**. Debian ships its own
PostgreSQL, an older major version. The version you want lives in another
repository, and you only trust it if you can tell the system which key signs
it.

The second is **what survives a reboot**. A server started by hand answers
today and is gone tomorrow.

The third is **what the server exposes**. A fresh instance must not listen to
the network: you will open it deliberately, later, when you know to whom.
