# pg-02: drive an instance with psql, over socket and network

## What this lab exercises

A running PostgreSQL instance is not a usable one. This lab walks through the
three obstacles any service hits when it must reach it, then asks you to read
the server's real state rather than assume it.

It is graded on the machine's state: the listening addresses, the access
rules, the permissions of the password file, the objects actually present in
the catalog, and a report whose every value is compared with what the server
declares.

## The trap it makes you meet

**Two different failures produce the same error, and only one warns.**
Measured on PostgreSQL 18 on 2026-10-20:

- a `.pgpass` readable by **group or others** triggers an explicit libpq
  warning, "password file … has group or world access", then psql asks for the
  password again and fails on `fe_sendauth: no password supplied`;
- a `.pgpass` **in 0600 whose host does not match** the `-h` triggers **no**
  warning at all, and fails on exactly the same line.

So the final error is identical and the diagnosis is not. And the first case's
warning goes to standard error: a script that discards it sees only a password
prompt that hangs, which brings both cases back to the same symptom.

## What it does not cover

Transport encryption (`pg_stat_ssl`), which belongs to the access lab, and the
`~/.pg_service.conf` service file: the guide does teach it, but this lab does
not check it. Its three obstacles are already graded, and a fourth would add
nothing.

## Duration

30 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
