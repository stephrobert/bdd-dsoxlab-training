# mysql-02: drive the instance, without leaving the password lying around

## What this lab exercises

The four moves that make an instance usable day to day: connecting without
exposing your password, creating the application's objects, making the server
observable, and giving yourself the client you mean to use.

It is graded on a connection that **really works**, run with no password in the
environment and with standard input closed: if anything is missing, the client
asks for the password and the command dies rather than inventing one. It is the
same proof `pg-02` uses for `.pgpass`.

## The three traps it makes you meet

**`performance_schema` does not turn back on at runtime.** It is a startup
variable, read-only once the server is up: a `SET GLOBAL` answers an error, and
a `SET PERSIST` writes the value without applying it. You must restart, and
that is the kind of detail that makes people wrongly conclude the variable is
useless.

**The connection profile hinges on a host detail.** In MySQL, `@localhost`
means the **Unix socket**, and a TCP connection to `127.0.0.1` looks for a
`@127.0.0.1` account, which is a DIFFERENT account. A login path that declares
a host while the account is `localhost` fails on an "Access denied" that does
not say why.

**The two clients disagree about the socket.** `mysqlsh` uses a compiled-in
path, `/var/lib/mysql/mysql.sock`, which is not Debian's and whose directory it
may not enter: the message is an `Error 2002 ... (13)`, a permission refusal
and not a missing file. The `mysql` client, meanwhile, connects without a word
through the same login path. Declaring the socket in the profile makes both
agree, and it is the only way not to have to repeat it on every command.

## What it does not cover

Memory and log tuning, which belongs to the configuration lab. Roles and TLS,
which belong to the hardening lab. A detailed exploration of the Performance
Schema, which the monitoring guide covers: here we turn it on, we do not
explore it.

## Duration

35 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/prise-en-main-mysql-cli/)
