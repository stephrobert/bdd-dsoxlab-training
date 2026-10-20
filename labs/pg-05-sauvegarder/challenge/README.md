# What is asked

On `db1.lab`. The `facturation` database holds an `appli` schema with its
tables filled. The `/var/backups/postgresql/` directory exists and belongs to
`postgres`.

## 1. Back up the database

Drop a **custom format** dump of `facturation` into
`/var/backups/postgresql/`, the format that allows a selective restore.

The file must actually be readable by `pg_restore`, and carry both tables of
the `appli` schema. A `plain` format dump does not pass: it is not a dump, it
is an SQL script.

## 2. Back up what the dump does not contain

Roles are **global to the cluster**: `pg_dump` does not back them up. Capture
them into `/var/backups/postgresql/globals.sql`.

Without them, a restore onto a fresh machine fails on every owner and every
privilege.

## 3. Prove the backup restores

Restore the dump into a **new** database named `facturation_verif`, distinct
from the original, which must come out with the same content: the same tables,
and the same number of rows in each.

It is the only one of the three steps that proves anything. The first two
produce files; this one says whether they are worth something.

## 4. Fill in the report

The `~/rapport-sauvegarde.txt` file holds three values to complete:

- `format_du_dump`: the format `pg_restore` reports for your dump, in one
  lowercase word;
- `nb_lignes_clients_restaurees`: the number of rows of `appli.clients` in the
  verification database;
- `nb_roles_sauvegardes`: the number of roles `globals.sql` carries.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check pg-05-sauvegarder
```
