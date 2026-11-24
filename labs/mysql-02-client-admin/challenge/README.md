# A password lying around, and a server that says nothing

## The situation

The MySQL instance on `db1.lab` is running, closed on its loopback, and the
`labadmin` administration account exists. Three things are missing before anyone
can work with it.

The first shows up in the shell history. The team's scripts call
`mysql -ulabadmin -p'...'`, so the password is on the command line: it can be
read in `ps`, in the history, and in audit logs. MySQL ships a way to avoid
that.

The second is that the application has no objects at all: no database, no
table.

The third is invisible, and it is the most interesting. Someone turned the
**Performance Schema** off to save a few megabytes, and never turned it back
on. The whole family of `sys` views used to diagnose a slowdown is therefore
silent. It is not a variable a `SET` turns back on: it is read at startup.

Finally, you are asked to install **MySQL Shell**, the client the team wants to
use for its scripts.

The credentials: the `labadmin` account, password `Adm1n!Lab2026`.

The guide: [https://www.stephane-robert.info/en/docs/databases/relational/mysql/mysql-cli/](https://www.stephane-robert.info/en/docs/databases/relational/mysql/mysql-cli/)

## What is asked

On `db1.lab`, from the `student` account. The instance is running, the
`labadmin` account exists with password `Adm1n!Lab2026`.

### 1. Store the credentials in a login path

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

### 2. Create the application's objects

A `appli` database, and in it a `clients` table carrying at least the `id` and
`nom` columns, with **at least three rows**, on the **InnoDB** engine.

### 3. Make the server observable

The **Performance Schema** must be on.

It is not a variable a `SET` turns back on: it is read-only once the server is
up. A `SET GLOBAL` answers an error, and a `SET PERSIST` writes it without
applying it.

### 4. Install MySQL Shell

The `mysqlsh` client must be installed and able to reach the instance.

It lives in the same component of Oracle's repository as the server: no
repository to add.

### 5. Fill in the report

The `~/rapport-client.txt` file holds three values to complete:

- `performance_schema_actif`: what `@@performance_schema` answers;
- `nb_tables_appli`: the number of tables in the `appli` database;
- `moteur_de_la_table_clients`: the storage engine of `appli.clients`.

**Edit the file in place.** Its header must survive.

### Check

```bash
dsoxlab check mysql-02-client-admin
```
