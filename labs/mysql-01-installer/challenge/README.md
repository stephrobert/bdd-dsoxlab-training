# What is asked

On `db1.lab`, a fresh Debian 13.

## 1. Install MySQL 8.4 LTS from Oracle's repository

The server must be version **8.4**, come from **Oracle's** repository and not
Debian's, and its signing key must be Oracle's.

The service must be running **and** enabled at boot: a database that does not
come back after a reboot is not in service.

The `root` account's password must be `R00t!Lab2026`.

## 2. Establish the real listening state, then close it

At the end, `mysqld` must listen on the **loopback only**, on **both** its
ports.

First read the real state: `sudo ss -tlnp | grep mysqld` must show two `LISTEN`
lines. If their address is `*`, `0.0.0.0` or `[::]`, the server is open to
every interface.

Mind the second port. `bind-address` does **not** restrict 33060: the X
protocol has its own variable. Both must read `127.0.0.1`, and these variables
do not change at runtime.

## 3. Create a dedicated administration account

An account `labadmin@localhost`, with password `Adm1n!Lab2026`, and all privileges
including the right to grant them.

You do not work day to day as `root`: a dedicated account can be revoked
without touching the fallback one.

## 4. Fill in the report

The `~/rapport-installation.txt` file holds three values to complete, all read
from the server:

- `version_du_serveur`: the full version the server announces;
- `bind_address_en_service`: the value of `@@bind_address`;
- `mysqlx_bind_address_en_service`: that of `@@mysqlx_bind_address`. It is not
  the same variable, and that is the whole point of the question.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-01-installer
```
