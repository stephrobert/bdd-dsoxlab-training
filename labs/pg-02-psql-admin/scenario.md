# The instance is running, and nobody can use it

PostgreSQL 18 is installed on `db1.lab` and the service starts at boot. The
`appli` application role exists with its password, and the `facturation`
database belongs to it. On paper, everything is ready.

The team that has to ship the application just told you nothing works. From
their machine, `psql` hangs. From `db1` itself, as `postgres`, all is well.

You have three things to fix, and they live in three different places: the
server only listens on its own loopback, it does not know who to accept from
the network, and no client can authenticate without a human typing a password,
which a script will never do.

Then the application needs its objects: a schema, a table, and enough to check
that it really writes. They must belong to the service's role, not to the
superuser.

Finally, you are asked for a four-line report on the instance's real state.
The values will be compared with what the server answers: a plausible but
wrong value will be rejected.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
