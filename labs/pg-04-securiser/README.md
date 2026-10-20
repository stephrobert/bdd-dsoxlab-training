# pg-04: refuse cleartext, and separate the rights

## What this lab exercises

Two hardening steps that are believed done when they are not.

**Encryption.** `ssl = on` on a server whose `pg_hba.conf` line is a `host`
protects nothing: the session is encrypted if the client asks, and in clear if
it does not. The lab is graded on behaviour, not on the setting: an
`sslmode=disable` connection must **fail**, and an encrypted one must succeed
and declare itself encrypted in `pg_stat_ssl`.

**Least privilege.** The guide's pattern, three group roles with no login
right: who creates, who writes, who reads. The privileges are read from the
catalog, not from a `.sql` file left on disk.

## The two traps it makes you meet

`hostssl` without `ssl = on` is **silently ignored**, with only a warning in the
log. And the converse holds too: `ssl = on` without `hostssl` forces nothing.
The two settings are worth something only together, and that is exactly the kind
of pair a file audit declares compliant.

Without `DEFAULT PRIVILEGES`, every **future** table created by the owner will
carry no rights for the other two roles. Everything is right the day it is set
up, and wrong at the first migration.

## What it does not cover

A PKI: the certificate is self-signed, so `verify-full` fails by construction,
and that is said. Row-Level Security and OAuth, which the guide files under
advanced cases.

And two checks the guide gives as **already true** on this cluster, hence out of
the grade: `ssl = on`, set by Debian, and the revocation of `CREATE` on the
`public` schema, done by default since PostgreSQL 15.

## Duration

40 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/)
