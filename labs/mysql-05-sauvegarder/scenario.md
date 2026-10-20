# A backup that succeeds, and a restore that is missing something

The instance on `db1.lab` serves the `appli` database. It holds two tables, and
more than that: a **stored procedure** the application calls to compute its
revenue, and a **trigger** that normalises amounts on insert.

The nightly backup exists. It has been running for months, it has never said a
word, and the file it produces weighs what it should. Last month that backup
was restored onto a staging server. The restore finished **without a single
error**, the tables were there, the rows too. The application started, then
failed on the first page that shows the revenue:

```text
ERROR 1305 (42000): PROCEDURE appli.chiffre_affaires does not exist
```

So the trap is not in the restore: the **backup** was incomplete, and nothing
in its output said so. Measured on MySQL 8.4, `mysqldump --help` reports
`routines FALSE`: stored procedures and functions are **omitted by default**,
where triggers are included. An incomplete file restores perfectly, with exit
code 0.

You are asked to rebuild the arrangement and prove it holds. Produce a
**complete** logical backup of `appli`, restore it into a fresh
`appli_restauree` database, and check the copy is **usable**: the same rows,
the procedure answering, the trigger firing.

A backup that has never been restored is not a backup: it is a file.

Credentials: the `labadmin` administration account, password `Adm1n!Lab2026`.
The `~/sauvegardes/` working directory is waiting for you, empty.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/)
