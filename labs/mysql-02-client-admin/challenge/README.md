# What is asked

On `db1.lab`, from the `student` account. The instance is running, the
`labadmin` account exists with password `Adm1n!Lab2026`.

## 1. Store the credentials in a login path

Register a profile named `lab` for the `student` account, so that a script
connects **without a password on the command line**.

The expected proof, from `student`, with no `MYSQL_PWD` variable and no
terminal:

```bash
mysql --login-path=lab -N -B -e 'select current_user()' < /dev/null
```

It must answer `labadmin@localhost`.

Mind the host. In MySQL, `@localhost` means the **Unix socket**: a profile
declaring `--host=127.0.0.1` looks for a `@127.0.0.1` account, which is a
different account, and the connection is refused.

## 2. Create the application's objects

A `labdb` database, and in it a `clients` table carrying at least the `id` and
`nom` columns, with **at least three rows**, on the **InnoDB** engine.

## 3. Make the server observable

The **Performance Schema** must be on.

It is not a variable a `SET` turns back on: it is read-only once the server is
up. A `SET GLOBAL` answers an error, and a `SET PERSIST` writes it without
applying it.

## 4. Install MySQL Shell

The `mysqlsh` client must be installed and able to reach the instance.

It lives in the same component of Oracle's repository as the server: no
repository to add.

## 5. Fill in the report

The `~/rapport-client.txt` file holds three values to complete:

- `performance_schema_actif`: what `@@performance_schema` answers;
- `nb_tables_labdb`: the number of tables in the `labdb` database;
- `moteur_de_la_table_clients`: the storage engine of `labdb.clients`.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-02-client-admin
```
