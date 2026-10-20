# The instance nobody wanted

The colleague who looked after `db1.lab` left on Friday. The MySQL instance
serving the `appli` database is running, and that is about the only good thing
to say about it.

It listens on **every** interface. A single account serves the application,
`app_tout`, declared `@'%'` with `GRANT ALL PRIVILEGES ON *.*`: it can read the
password hashes and drop any database, from anywhere. No setting has ever been
touched, the slow query log is off, and nobody knows what the database does all
day.

And there is **no backup**. Not an old one, not an incomplete one: none.

You are on call from Monday. You are asked to bring this instance to a state
you would be willing to defend, and to **prove** it, because your word is worth
nothing at three in the morning.

This is an **exam**. Nothing will be explained again: the level's five labs
taught it, this one measures it. Ten graded tasks, 70 points to pass, and
everything is graded on the **real state of the server**, after a restart. Two
hints exist, and they cost dearly.

Credentials: the `labadmin` administration account, password `Adm1n!Lab2026`.
The password of the service account to create is imposed by the brief, because
a test has to be able to use it.

The level's guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/)
