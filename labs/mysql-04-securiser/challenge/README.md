# What is asked

On `db1.lab`. The `appli` database holds its tables, the `labadmin` account
exists with password `Adm1n!Lab2026`, and the server listens on its loopback.

## 1. Create two privilege roles

- `role_reader`: `SELECT` on `appli.*`, and nothing else;
- `role_writer`: `SELECT`, `INSERT`, `UPDATE`, `DELETE` on `appli.*`.

These are **roles**, not accounts: they must not be able to log in.

## 2. Create the application account, and ACTIVATE its role

An account `app_lecture` with password `L3cture!2026`, receiving `role_reader` and
**only** that.

It must be able to connect **over the network**, so from `127.0.0.1`. Mind
this: an account declared `@localhost` refuses a TCP connection, and the error
names a host you never declared.

And above all: **granting a role does not activate it**. At connection time,
`CURRENT_ROLE()` must answer the role and not `NONE`, otherwise the account has
no rights despite the `GRANT`.

## 3. Require encryption on that account

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

## 4. And nothing beyond reading

The `app_lecture` account must be able to read the tables of `appli`, but
**neither write to them** nor **read** the `mysql` database, which holds the
passwords.

## 5. Fill in the report

The `~/rapport-securite.txt` file holds three values to complete:

- `role_actif_a_la_connexion`: what `CURRENT_ROLE()` answers in a `app_lecture`
  session, copied as is;
- `exigence_tls_du_compte`: what the `ssl_type` column of `mysql.user` reports
  for that account;
- `nb_roles_sans_connexion`: how many roles on this server cannot log in.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check mysql-04-securiser
```
