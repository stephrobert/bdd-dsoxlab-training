# An application account that can do everything, over a cleartext channel

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

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/)
