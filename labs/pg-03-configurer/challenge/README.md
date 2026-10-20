# What is asked

On `db1.lab`. The log collector is **already on**: it is postmaster-context, so
turning it on would have required a restart, and this lab forbids that.

## 1. Make the logs usable

Three parameters, all reloadable, which must be **effective** on the running
server:

- a slow-query threshold of **250 ms** (`log_min_duration_statement`);
- connection logging, enabled (`log_connections`);
- a line prefix (`log_line_prefix`) carrying at least the timestamp (`%m`), the
  process id (`%p`), and the user and database (`%u` and `%d`).

"Effective" means read from `pg_settings`, not written in a file. A parameter
present in `postgresql.auto.conf` but never reloaded does not count.

## 2. Prepare the `max_connections` raise

`max_connections` must be **200** in the configuration, and the server must
still be running **with 100**, pending its next start.

That is the normal state of a postmaster-context parameter just changed, and it
is what the lab asks for: the restart window is scheduled for tonight, not now.

## 3. Cut nobody

The server **must not have restarted**. A session opened by the setup carries
the application name `temoin-pg-03`: it must still be there. A restart kills it,
and the test sees that.

A `systemctl restart`, a `pg_ctl restart` or a `reboot` therefore fail the lab,
even if every parameter is right.

## 4. Fill in the report

The `~/rapport-config.txt` file holds three values to complete, all read from
the server:

- `max_connections_effectif`: the value it runs with;
- `max_connections_en_attente`: the one the files declare. It is not read in the
  same place as the previous one;
- `nb_parametres_en_attente`: how many parameters are waiting for a restart.

**Edit the file in place.** Its header must survive: it disappears if you
recreate the file with a `>` redirection, and the test refuses that.

## Check

```bash
dsoxlab check pg-03-configurer
```
