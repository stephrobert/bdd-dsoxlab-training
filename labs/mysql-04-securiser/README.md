# mysql-04: grant through roles, and require encryption

## What this lab exercises

Least privilege, in MySQL, with its own mechanisms: **roles** carrying the
privileges, and a TLS requirement set **on the account** rather than in a file.

It is graded on **behaviour**, like its PostgreSQL counterpart: an unencrypted
connection must be **refused**, an encrypted one must work, and the account must
read what it is allowed to and nothing more. No test reads a `GRANT` from the
catalog: a right that is granted and inactive exists, and does nothing.

## The three traps it makes you meet

**A granted role is not an active role.** That is the central trap, and the
guide names it. Measured on MySQL 8.4: after a `GRANT role_reader TO account`,
`CURRENT_ROLE()` answers `NONE` and any `select` fails on "Access denied ... to
database". The `GRANT` is nonetheless there in the catalog. You need `SET
DEFAULT ROLE ALL TO account@host`, and then `CURRENT_ROLE()` answers the role.

**`@localhost` means the socket only.** Measured: a `@localhost` account
REFUSES a TCP connection to `127.0.0.1`, with an "Access denied for
'account'@'127.0.0.1'" that names a host nobody declared. MySQL matches the host
as the connection presents it. An account that must connect over the network is
therefore declared with the address, not with `localhost`.

**Refusing a cleartext connection does not always come from the same place.**
Measured on a `REQUIRE SSL` account reached with `--ssl-mode=DISABLED`, and the
authentication plugin changes the error:

| Account's plugin | Error returned |
|---|---|
| `caching_sha2_password`, the 8.4 default | `ERROR 2061`: "Authentication requires secure connection" |
| `mysql_native_password`, the pre-8.0 default | `ERROR 1045`: "Access denied" |

In the first case it is the **plugin** that refuses to send the password over a
cleartext channel, before `REQUIRE SSL` is even consulted. In the second it is
`REQUIRE SSL` itself. Both refuse the connection, but only the first says why:
many documents quote the `1045`, which was the expected error back when the
native plugin was the default.

## What it does not cover

Partial revokes, which revoke a global privilege on a specific schema: the lab
uses no global privilege, so there is nothing to revoke. Client certificate
verification (`REQUIRE X509`), which needs a PKI. Password complexity policy,
which the guide covers.

## Duration

40 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/)
