# An application account that can do everything, over a cleartext channel

## The situation

The instance on `db1.lab` serves the `appli` database. The internal audit
found two things, and the second is sneakier than the first.

The account the application uses holds **all** privileges on **all** databases,
because someone set it up "just to get the application working" and never came
back to it. So it can read the passwords in the `mysql` database, and drop any
table.

And nothing requires it to connect over an encrypted channel. MySQL does not
control that in a file as PostgreSQL does: the requirement is set **on the
account**.

You are asked to rebuild the arrangement properly: **roles** carrying the
privileges, an application account receiving only one of them, and TLS
required.

One warning, because it costs dearly to whoever ignores it. In MySQL, a granted
role is **not active** at connection time. The account then sees its rights
refused, `CURRENT_ROLE()` answers `NONE`, and no catalog table says the role is
asleep: the `GRANT` is there, and it does nothing.

The credentials: the `labadmin` administration account, password `Adm1n!Lab2026`.
The application account to create is `app_lecture`, with password
`L3cture!2026`.

The guide: [https://www.stephane-robert.info/en/docs/databases/relational/mysql/security/](https://www.stephane-robert.info/en/docs/databases/relational/mysql/security/)

## What is asked

On `db1.lab`. The `appli` database holds its tables, the `labadmin` account
exists with password `Adm1n!Lab2026`, and the server listens on its loopback.

### 1. Create two privilege roles

- `role_reader`: `SELECT` on `appli.*`, and nothing else;
- `role_writer`: `SELECT`, `INSERT`, `UPDATE`, `DELETE` on `appli.*`.

These are **roles**, not accounts: they must not be able to log in.

### 2. Create the application account, and ACTIVATE its role

An account `app_lecture` with password `L3cture!2026`, receiving `role_reader` and
**only** that.

It must be able to connect **over the network**, so from `127.0.0.1`. Mind
this: an account declared `@localhost` refuses a TCP connection, and the error
names a host you never declared.

And above all: **granting a role does not activate it**. At connection time,
`CURRENT_ROLE()` must answer the role and not `NONE`, otherwise the account has
no rights despite the `GRANT`.

### 3. Require encryption on that account

A connection by `app_lecture` **without TLS** must be **refused**, and an
encrypted one must work.

MySQL sets that requirement on the **account**, not in a file. The two expected
proofs:

```bash
# must FAIL
MYSQL_PWD='L3cture!2026' mysql -h 127.0.0.1 -u app_lecture --ssl-mode=DISABLED -e 'select 1'

# must SUCCEED
MYSQL_PWD='L3cture!2026' mysql -h 127.0.0.1 -u app_lecture --ssl-mode=REQUIRED -e 'select 1'
```

### 4. And nothing beyond reading

The `app_lecture` account must be able to read the tables of `appli`, but
**neither write to them** nor **read** the `mysql` database, which holds the
passwords.

### 5. Fill in the report

The `~/rapport-securite.txt` file holds three values to complete:

- `role_actif_a_la_connexion`: what `CURRENT_ROLE()` answers in a `app_lecture`
  session, copied as is;
- `exigence_tls_du_compte`: what the `ssl_type` column of `mysql.user` reports
  for that account;
- `nb_roles_sans_connexion`: how many roles on this server cannot log in.

**Edit the file in place.** Its header must survive.

### Check

```bash
dsoxlab check mysql-04-securiser
```
