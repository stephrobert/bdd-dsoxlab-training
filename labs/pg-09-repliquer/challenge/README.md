# What is asked

Two machines. `db1.lab` carries the `facturation` database; `db2.lab` has
PostgreSQL installed and an empty cluster running.

## 1. Prepare the primary

On `db1.lab`:

- a **dedicated** replication role named `replicator`, which can log in and
  replicate, and which is **neither a superuser nor a database creator**. Its
  password will be stored on the second machine: it must open replication and
  nothing else;
- a **physical replication slot** named `standby_slot`, so the primary retains
  the logs the standby needs;
- an access rule allowing replication **from the network**, through a method
  that does not carry the password in clear.

Mind this: replication is a virtual database. A `pg_hba` line whose database
column reads `all` does **not** allow it.

## 2. Build the standby

On `db2.lab`, replace the empty cluster with a copy of the primary, and start it
in standby mode.

The data directory must be **empty** before the copy: the Debian installation
has already laid a cluster there, and `pg_basebackup` refuses to write over it.

The standby must use the slot created in step 1.

## 3. Prove the data flows

At the end:

- `db2.lab` must be in permanent recovery mode, and accept reads;
- `db1.lab` must see **one** standby in the `streaming` state;
- the slot must be **active**;
- and above all: a row written on the primary must appear on the standby. It is
  the only check that proves anything.

## 4. Fill in the report

The `~/rapport-replication.txt` file, **on `db1.lab`**, holds three values:

- `nb_secondaires_en_flux`: how many standbys `pg_stat_replication` counts in
  the `streaming` state;
- `slot_actif`: what the slot's `active` column answers, in one letter;
- `replicator_est_superuser`: what `rolsuper` answers for that role, in one
  letter.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check pg-09-repliquer
```
