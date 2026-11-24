# The instance is running, and nobody can use it

## The situation

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

The guide: [https://www.stephane-robert.info/en/docs/databases/relational/postgresql/psql-admin/](https://www.stephane-robert.info/en/docs/databases/relational/postgresql/psql-admin/)

## What is asked

On `db1.lab`, from the `student` account.

### 1. Make the instance reachable from the network

The server must listen on its loopback **and** on its private address. A
network connection to the `facturation` database with the `appli` role must be
accepted, through a method that does not carry the password in clear.

`trust` and `password` are refused on a network line: the first requires
nothing, the second sends the password as is.

### 2. Let a script connect without a typed password

Lay down the password file for `student` and the `appli` role. It must be
genuinely honoured by psql, which depends as much on its permissions as on its
contents.

The expected proof: from the `student` account, with no `PGPASSWORD` variable
and no terminal, this command must answer `1`.

```bash
psql -h <private-address> -U appli -d facturation -At -c 'select 1' < /dev/null
```

### 3. Create the service's objects

In the `facturation` database: an `appli` schema, and inside it a `clients`
table with at least the `id` and `nom` columns, holding **at least two rows**.

The table must belong to the `appli` role, not to `postgres`.

### 4. Fill in the report

The `~/rapport-psql.txt` file holds four lines to complete. Read the values
from the server, do not guess them: they are compared with what it answers.

- `server_version`
- `listen_addresses`
- `data_checksums`
- `nb_tables_schema_appli`: the number of tables in the `appli` schema

**Edit the file in place.** Its header must survive: it disappears if you
recreate the file with a `>` redirection, and the test refuses that.

### Check

```bash
dsoxlab check pg-02-psql-admin
```
