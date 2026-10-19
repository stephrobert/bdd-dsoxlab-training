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

`~/.pgpass` is **silently ignored** by psql when its permissions are too
broad. No error, no warning in a script: only a password prompt that hangs. A
file in the right format but in mode 0644 is useless, and that is the most
common mistake on this subject.

## What it does not cover

Transport encryption (`pg_stat_ssl`), which belongs to the access lab, and the
`~/.pg_service.conf` service file, which the guide does not teach.

## Duration

30 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/prise-en-main-psql/)
