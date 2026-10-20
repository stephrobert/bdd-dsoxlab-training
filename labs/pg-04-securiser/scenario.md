# Encrypted "when the client feels like it"

The internal audit went through `db1.lab`. Two findings, and they are more
alike than they look.

The first: the application's connections **can** be encrypted, but nothing
requires it. The network line in `pg_hba.conf` is a `host`, which accepts an
encrypted and a cleartext session alike. So the client decides, and a
misconfigured client never notices. The certificate presented is the one Debian
laid down at install time, the same one on every machine in the estate.

The second: the `appli` role **owns** its schema and its tables. It can
therefore drop them, and the application runs with that right at all times. A
reporting tool that only reads connects with the same role, for want of another.

You are asked to close both. The server must refuse an unencrypted connection,
and the rights must be separated: who creates, who writes, who reads.

Mind a detail the guide points out: on Debian, `ssl = on` is already set.
Turning SSL on will therefore change nothing, and it is not what is asked.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/)
