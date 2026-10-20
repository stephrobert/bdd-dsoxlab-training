# What is asked

On `db1.lab`. The instance is running, listens on the network, and a `host`
line already accepts the `appli` role on the `facturation` database.

## 1. Put a dedicated certificate in place

The server must present a certificate of its own, not the one Debian lays down
at install time (`ssl-cert-snakeoil`). Its common name (`CN`) must be `db1.lab`.

The private key must be readable by the `postgres` account **only**: PostgreSQL
refuses to start if it is more open, and that is the most common mistake on this
subject.

The server must then actually present that certificate, not merely hold it on
disk.

## 2. Refuse cleartext connections

An **unencrypted** network connection to `facturation` must be **refused**, and
an encrypted one must succeed.

The two expected proofs, from the `student` account:

```bash
# must FAIL
PGSSLMODE=disable psql -h <private-address> -U appli -d facturation -c 'select 1'

# must SUCCEED, and declare itself encrypted
PGSSLMODE=require psql -h <private-address> -U appli -d facturation \
  -At -c "select ssl from pg_stat_ssl where pid = pg_backend_pid()"
```

Leave the `local` lines alone: the tests and administration go through the
socket.

## 3. Separate the rights

Three group roles, **with no login right**: `app_owner`, `app_writer`,
`app_reader`.

- the `appli` schema and its tables belong to `app_owner`;
- `app_reader` can read the tables, and **nothing else**;
- `app_writer` can read, insert, update and delete rows;
- both have usage of the schema;
- the `appli` login role is a member of `app_writer`, and no longer owns
  anything.

## 4. Provide for future tables

A table created **later** by `app_owner` in the `appli` schema must grant its
rights to the other two roles by itself, with no intervention. Otherwise
everything is right today and wrong at the first migration.

## 5. Fill in the report

The `~/rapport-securite.txt` file holds three values to complete, all read from
the server:

- `cn_du_certificat`: the common name of the certificate the server presents;
- `proprietaire_des_tables`: who owns the tables of the `appli` schema;
- `nb_tables_lisibles_par_reader`: how many tables of that schema `app_reader`
  can read.

**Edit the file in place.** Its header must survive.

## Check

```bash
dsoxlab check pg-04-securiser
```
