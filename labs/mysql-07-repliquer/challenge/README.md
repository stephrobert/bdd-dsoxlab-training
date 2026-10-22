# What is asked

Two machines. `db1.lab` is the **source**, it holds the `appli` database and
its `clients` table. `db2.lab` is the future **replica**: MySQL runs on it, it
has already received a **copy** of the database restored from a backup, and it
knows nothing of the source. The `labadmin` account exists on both, password
`Adm1n!Lab2026`.

That copy is not scenery. Without it, the replica's applier thread stops on the
first transaction with an error `1049`, "Unknown database": a replica follows a
database, it does not create one.

## 1. Turn GTID on, on both servers

`gtid_mode` must be `ON` and so must `enforce_gtid_consistency`, **on the
source and on the replica**.

Mind this: `gtid_mode` **refuses to go from OFF to ON in one step**. The server
answers an error `1788` that names the path, and adds that the value must be
stepped up simultaneously on all servers. Read the message, it says everything.

## 2. Create the replication account, and only what it needs

A `replicator` account with password `R3pl!Lab2026`, reachable from the replica,
holding `REPLICATION SLAVE` and **nothing more**. A global `SELECT` would give
it the `mysql` database and its password hashes.

## 3. Connect the replica, and get it running

The channel is created by `CHANGE REPLICATION SOURCE TO`, with automatic
positioning, then `START REPLICA`.

**Use the source's ADDRESS, not its name.** Measured: from `db2`, the name
`db1.lab` resolves to a machine on another lab network. Read the address on the
source:

```bash
# on db1
ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1
```

**Both threads** must be running, and they are two distinct things:

```sql
SELECT service_state, last_error_number, last_error_message
  FROM performance_schema.replication_connection_status;   -- the input thread

SELECT service_state
  FROM performance_schema.replication_applier_status;      -- the applier thread
```

Mind the second trap: with the default authentication plugin, the channel stays
in `CONNECTING` on an error **2061** mentioning "secure connection", and it
retries every 60 seconds. It is neither the password nor the privileges. Two
ways out exist, one gives the channel TLS, the other makes it fetch the
source's public key.

## 4. Forbid direct writes on the replica

`super_read_only` must be on, and an `INSERT` from `labadmin` must be
**refused**. `read_only` alone is not enough: it lets through accounts holding
every privilege.

Rest assured, it is measured: `super_read_only` does **not** prevent the
applier thread from playing the transactions coming from the source.

## 5. Prove a row travels

The check writes a row on the source and looks for it on the replica. No state
table replaces that proof: a replication that reports `ON` without carrying
anything exists.

## 6. Fill in the report

The `~/rapport-replication.txt` file, on the source, holds three values:

- `etat_de_la_connexion`: what the replica's input thread reports;
- `uuid_de_la_source`: the source server's identifier, which the replica also
  sees;
- `lignes_sur_le_replica`: how many rows the table holds on the replica.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-07-repliquer
```
