# A database server that nobody installed on purpose

## The situation

The team keeps its inventory in a spreadsheet and wants a real database for
it. Someone ran `apt install postgresql` on a test machine last month and
nobody remembers which version it gave, where it comes from, or whether it
comes back after a reboot.

The decision is made: PostgreSQL 18, from the project's own package
repository (PGDG), on a fresh Debian 13 machine. You inherit `db1.lab`. It is
bare: no PostgreSQL, no repository for it.

## Mission

Put an instance into service that you could leave in production.

Three things matter more than seeing `psql` answer.

The first is **where the packages come from**. Debian ships its own
PostgreSQL, an older major version. The version you want lives in another
repository, and you only trust it if you can tell the system which key signs
it.

The second is **what survives a reboot**. A server started by hand answers
today and is gone tomorrow.

The third is **what the server exposes**. A fresh instance must not listen to
the network: you will open it deliberately, later, when you know to whom.

## A PostgreSQL 18 you can leave in production

You work on `db1.lab`, a bare Debian 13 machine. You have `sudo`.

### What is expected

1. a **PGDG source** for Debian 13 (`trixie-pgdg`) is declared in APT and tied
   to a **signing key** (`Signed-By`); `apt-get update` works without any
   signature complaint;
2. the **`postgresql-18`** package is installed, coming from PGDG, and the
   running server reports the same version;
3. the **`18/main` cluster is online**, its systemd unit is active, and it
   **starts at boot** (the grader reboots the machine);
4. **`pg_isready`** answers that the server accepts connections;
5. **data checksums are on**, both for the running server
   (`SHOW data_checksums`) and on disk (`pg_controldata`);
6. the server **listens on the loopback only**: port 5432 on `127.0.0.1` and
   `::1`, never on an external address.

### What is proven, and how

The tests do not read your shell history. They question the machine: APT, the
package database, systemd, the server through `psql`, and the sockets that
really listen. You can reach the result by any path.

The last test checks that the instance is still there after a reboot.

### Constraints

- Stay on PostgreSQL **18**, from PGDG. The Debian version is not the answer.
- Do not open the server to the network: the default listening address is the
  right one.
- No `trusted=yes` on the repository: a repository without a key is not a
  repository you verified.

```bash
dsoxlab check pg-01-installer   # grade
dsoxlab hint  pg-01-installer   # one hint, at the cost of points
```
