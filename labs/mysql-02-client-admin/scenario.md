# A password lying around, and a server that says nothing

The MySQL instance on `db1.lab` is running, closed on its loopback, and the
`labadmin` administration account exists. Three things are missing before anyone
can work with it.

The first shows up in the shell history. The team's scripts call
`mysql -ulabadmin -p'...'`, so the password is on the command line: it can be
read in `ps`, in the history, and in audit logs. MySQL ships a way to avoid
that.

The second is that the application has no objects at all: no database, no
table.

The third is invisible, and it is the most interesting. Someone turned the
**Performance Schema** off to save a few megabytes, and never turned it back
on. The whole family of `sys` views used to diagnose a slowdown is therefore
silent. It is not a variable a `SET` turns back on: it is read at startup.

Finally, you are asked to install **MySQL Shell**, the client the team wants to
use for its scripts.

The credentials: the `labadmin` account, password `Adm1n!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/)
