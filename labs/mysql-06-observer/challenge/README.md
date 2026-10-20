# What is asked

On `db1.lab`. The `appli` database holds an `evenements` table of 20,000 rows,
what is left of a purge that deleted 180,000. The `labadmin` account exists
with password `Adm1n!Lab2026`.

The dashboard query, the one to make fast:

```sql
SELECT COUNT(*) FROM evenements WHERE service = 'svc-7';
```

## 1. Make the plan stop reading the table whole

`EXPLAIN` must report something other than `ALL` for this query, and examine
far fewer rows than the table holds.

Mind this: **an index already exists** on that table. It does not serve this
query, and `SHOW INDEX` does not say so. The plan decides, not the catalog.

## 2. Reclaim the space the purge did not give back

The table still occupies what it occupied with its 200,000 rows. It must come
back under **20 MB**, without losing a single one of the 20,000 remaining rows.

Two measured details that save time:

- a `DELETE` returns **nothing** to the disk, InnoDB keeps the pages for reuse;
- watching `data_free` will show nothing, it barely moves.

```sql
-- the real size, in megabytes
SELECT ROUND((data_length + index_length) / 1024 / 1024) AS mo
  FROM information_schema.tables
 WHERE table_schema = 'appli' AND table_name = 'evenements';
```

## 3. Make the query findable under its database

A `SELECT` citing `evenements`, with its filter, must appear in
`sys.statement_analysis` for `db = 'appli'`.

This is the lab's operational trap: a query run **without a database
selected** is recorded with a **null** schema, and so never shows up when you
look for "the costly queries of this database".

## 4. Fill in the report

The `~/rapport-observation.txt` file holds three values to fill in:

- `type_d_acces_du_plan`: what the plan reports for the query, copied as is;
- `megaoctets_de_la_table`: the real size, in whole megabytes;
- `lignes_restantes`: how many rows the table holds.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-06-observer
```
