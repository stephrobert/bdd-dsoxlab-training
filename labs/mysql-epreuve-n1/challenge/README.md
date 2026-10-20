# Level 1 exam

**10 graded tasks, 100 points in all**, and 70 are needed to pass. So each task
is worth 10 points, and it is graded on the **state of the server**, never on
the commands you typed.

Two hints exist. They cost 20 and 30 points: at that price they are there to
get you going again when you are stuck, not to go faster.

On `db1.lab`. The administration account is `labadmin`, password
`Adm1n!Lab2026`. The `appli` database holds two tables, a `chiffre_affaires()`
stored procedure and a `montant_positif` trigger.

## What the instance must become

### The all-powerful account is gone (10 points)

`app_tout` must have disappeared from the server. An account declared `@'%'`
with `GRANT ALL PRIVILEGES ON *.*` is not an application account, it is a way
around everything that follows.

### A role carries the rights, and nothing more (10 points)

A `role_appli` role holding exactly `SELECT`, `INSERT`, `UPDATE` and `DELETE`
on `appli.*`. A role, not an account: it must not be able to log in.

### The service account connects, and its role is active (10 points)

An `appli_svc` account reachable from `127.0.0.1`, password `Svc!Appli2026`,
which receives `role_appli` and **only** that.

On connection, its role must be **active**.

### Cleartext is refused, encrypted works (10 points)

A connection as `appli_svc` without encryption must be **refused**, an
encrypted one must **succeed**.

### Least privilege, proven (10 points)

`appli_svc` must be able to read and write in `appli`, and **must not** be able
to read the `mysql` database nor drop a table.

### The requested settings survive a restart (10 points)

Three values, and they must be there **after** a restart of the service:

| Setting | Expected value |
|---|---|
| `max_connections` | `200` |
| `slow_query_log` | on |
| `long_query_time` | `1` |

The check restarts the server. A setting applied to the current session only
does not count.

### The instance listens on its loopback alone (10 points)

After that same restart, the server must accept connections from `127.0.0.1`
only, on both protocols.

Mind this: not every setting is applied in the same place, and this one is not
dynamic.

### The backup is complete (10 points)

A `~/sauvegardes/appli.sql` file, a logical backup of `appli`, carrying the
schema, the data, the trigger **and the stored procedure**.

### The restore is usable (10 points)

An `appli_restauree` database, restored from that file, with the same rows as
`appli` and a `chiffre_affaires()` procedure that **answers**.

### The report states the real state (10 points)

The `~/rapport-epreuve.txt` file holds three values to fill in:

- `connexions_max_apres_redemarrage`: what `@@max_connections` is once the
  service has been restarted;
- `role_actif_du_compte_de_service`: what `CURRENT_ROLE()` answers in an
  `appli_svc` session, copied as is;
- `procedures_dans_la_base_restauree`: how many routines
  `information_schema.routines` counts for `appli_restauree`.

**Edit the file in place.** Its header must survive, and a correct report about
a wrong instance earns nothing: this task is graded in addition to the others,
not instead of them.

## Check

```bash
dsoxlab check mysql-epreuve-n1
```

The score shows out of 100, and `dsoxlab submit mysql-epreuve-n1` gives the
exam verdict.
