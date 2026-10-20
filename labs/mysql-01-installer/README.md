# mysql-01: install, and close what the install opens

## What this lab exercises

Installing a server is not putting it into service. This lab walks through the
two steps the packages leave to the administrator: proving the software really
comes from the source you think, and closing the listening the installation
opens by default.

It is graded on the **real listening state**, read with `ss`, and on what the
running server declares. Never on the contents of a configuration file: a
correct file and an open port coexist perfectly well.

## The three traps it makes you meet

**Debian's repository does not ship MySQL.** `apt install mysql-server` on a
Debian without Oracle's repository installs MariaDB, which carries similar
package names and a `mariadb` service. So the lab checks provenance, not merely
presence.

**Oracle's packages lay down no `bind-address` line.** Not even a commented
one. Since the variable defaults to `*`, the server listens on every interface
at the end of the installation. Nothing reports it.

**`bind-address` does not restrict port 33060.** The X protocol has its own
variable, `mysqlx-bind-address`. That is the two-storey trap: the first setting
is visible and reassuring, the second is invisible and forgotten. Someone who
stops at the first sees `SELECT @@bind_address` answer `127.0.0.1` and leaves a
door open.

## What it does not cover

Memory and connection tuning, which belongs to the configuration lab. Roles,
TLS and partial revokes, which belong to the hardening lab. The system
firewall, which is the second move the guide recommends and is not MySQL's
business.

## Duration

35 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/)
