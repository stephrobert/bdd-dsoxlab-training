# Challenge: a PostgreSQL 18 you can leave in production

You work on `db1.lab`, a bare Debian 13 machine. You have `sudo`.

## What is expected

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

## What is proven, and how

The tests do not read your shell history. They question the machine: APT, the
package database, systemd, the server through `psql`, and the sockets that
really listen. You can reach the result by any path.

The last test checks that the instance is still there after a reboot.

## Constraints

- Stay on PostgreSQL **18**, from PGDG. The Debian version is not the answer.
- Do not open the server to the network: the default listening address is the
  right one.
- No `trusted=yes` on the repository: a repository without a key is not a
  repository you verified.

```bash
dsoxlab check pg-01-installer   # grade
dsoxlab hint  pg-01-installer   # one hint, at the cost of points
```
