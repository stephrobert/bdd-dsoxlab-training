# What is asked

On `db1.lab`, from the `student` account.

## 1. Make the instance reachable from the network

The server must listen on its loopback **and** on its private address. A
network connection to the `facturation` database with the `appli` role must be
accepted, through a method that does not carry the password in clear.

`trust` and `password` are refused on a network line: the first requires
nothing, the second sends the password as is.

## 2. Let a script connect without a typed password

Lay down the password file for `student` and the `appli` role. It must be
genuinely honoured by psql, which depends as much on its permissions as on its
contents.

The expected proof: from the `student` account, with no `PGPASSWORD` variable
and no terminal, this command must answer `1`.

```bash
psql -h <private-address> -U appli -d facturation -At -c 'select 1' < /dev/null
```

## 3. Create the service's objects

In the `facturation` database: an `appli` schema, and inside it a `clients`
table with at least the `id` and `nom` columns, holding **at least two rows**.

The table must belong to the `appli` role, not to `postgres`.

## 4. Fill in the report

The `~/rapport-psql.txt` file holds four lines to complete. Read the values
from the server, do not guess them: they are compared with what it answers.

- `server_version`
- `listen_addresses`
- `data_checksums`
- `nb_tables_schema_appli`: the number of tables in the `appli` schema

**Edit the file in place.** Its header must survive: it disappears if you
recreate the file with a `>` redirection, and the test refuses that.

## Check

```bash
dsoxlab check pg-02-psql-admin
```
