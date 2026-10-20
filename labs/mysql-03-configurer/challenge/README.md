# What is asked

On `db1.lab`. MySQL 8.4 is running, the `labadmin` account exists with password
`Adm1n!Lab2026`, and a `lab` login path is already in place for `student`.

## 1. Raise memory and connections

- `innodb_buffer_pool_size` must be **at least 512 MB**;
- `max_connections` must be **at least 300**.

## 2. Turn the slow query log on

- `slow_query_log` on;
- `long_query_time` at **1** second;
- output to a **file**, not a table.

It is not enough for the variables to be set: a slow query must **actually**
appear in the file. The test will run one.

## 3. Make all of it survive a restart

This is the heart of the lab. The test **will stop and start** the server, then
reread the three settings.

Mind this, and it is measured: `performance_schema.variables_info` reports the
**same** source after a `SET GLOBAL` and after a `SET PERSIST`, so it does not
say whether a value will survive. Do not rely on it to conclude.

`performance_schema.persisted_variables` does tell the two apart, and it will
help you. But it reflects memory rather than the file: it proves the server
**meant** to persist, not that it will reread. Only the restart proves that.

And before restarting, make sure your configuration is valid: MySQL ships a way
to check it without starting the server. A refused configuration leaves the
instance down.

## 4. Fill in the report

The `~/rapport-configuration.txt` file holds three values to complete, all read
from the server **after** its restart:

- `buffer_pool_mo`: the buffer pool's size, in megabytes;
- `long_query_time`: the threshold in service;
- `source_du_buffer_pool`: what `variables_info` reports as the source of
  `innodb_buffer_pool_size`. The answer depends on how you set it, and that is
  the whole point of the question.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-03-configurer
```
