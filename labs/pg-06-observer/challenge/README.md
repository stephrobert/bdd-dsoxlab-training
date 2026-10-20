# What is asked

On `db1.lab`. The `facturation` database holds the `appli.journal` table, a
hundred thousand rows, tens of thousands of which are dead.

## 1. Make the server observable

The `pg_stat_statements` extension must be **loaded by the server** and
**created in the** `facturation` **database**.

Both, not one of the two: the library loads at start, so a `CREATE EXTENSION`
alone fails, and a loaded library with no extension created gives no view to
query.

A restart is allowed here, unlike in the configuration lab.

## 2. Fix the query

This query must stop being read sequentially:

```sql
select count(*) from appli.journal where client_id = 42
```

The test reads the **plan** the planner produces, and requires no sequential
scan of `appli.journal` in it. Creating an index the planner does not use
therefore does not count.

Think about what the planner needs in order to choose: up-to-date statistics.

## 3. Reclaim the dead space

The dead rows of `appli.journal` must be reclaimed: fewer than **1%** of the
live rows may remain.

Avoid `VACUUM FULL`: it takes an exclusive lock, so it cuts the service. A plain
`VACUUM` is enough to make the space reusable.

## 4. Fill in the report

The `~/rapport-observation.txt` file holds three values to complete:

- `lignes_mortes_journal`: the number of dead rows left on the table;
- `nb_index_sur_journal`: the number of indexes the table carries;
- `bibliotheque_chargee`: the value the server gives for
  `shared_preload_libraries`.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check pg-06-observer
```
