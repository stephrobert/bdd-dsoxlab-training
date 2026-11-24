# A backup that succeeds, and a restore that is missing something

## The situation

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

The guide: [https://www.stephane-robert.info/en/docs/databases/relational/mysql/backup-restore/](https://www.stephane-robert.info/en/docs/databases/relational/mysql/backup-restore/)

## What is asked

On `db1.lab`. The `appli` database holds two tables, a `chiffre_affaires()`
stored procedure and a `montant_positif` trigger. The `labadmin` account exists
with password `Adm1n!Lab2026`, and `~/sauvegardes/` is empty.

### 1. Produce a COMPLETE logical backup

A `~/sauvegardes/appli.sql` file, a logical backup of the `appli` database.

**Complete** means: the schema, the data, the trigger **and the stored
procedure**. Mind this, it is the lab's trap: procedures are **not** in a dump
by default. Look at what `mysqldump --help` reports for `routines`.

### 2. Restore it into a FRESH database

An `appli_restauree` database that receives the file's contents. You do not
restore over the live database: a copy is where you prove a backup is worth
something.

### 3. Prove the copy is USABLE

Three proofs, and none of them is read from a catalog:

- the **same rows** as `appli`, table by table;
- the `appli_restauree.chiffre_affaires()` procedure **answers**, and returns
  the same value as the one in `appli`;
- the trigger **fires**: inserting a negative amount into
  `appli_restauree.commandes` must turn it positive.

```bash
# the procedure must answer, not raise an ERROR 1305
MYSQL_PWD='Adm1n!Lab2026' mysql -u labadmin -e 'call appli_restauree.chiffre_affaires()'
```

### 4. Fill in the report

The `~/rapport-sauvegarde.txt` file holds three values to fill in:

- `defaut_de_routines`: what `mysqldump --help` reports for `routines`, copied
  as is;
- `lignes_dans_la_base_restauree`: the total number of rows in the two tables
  of `appli_restauree`;
- `total_rendu_par_la_procedure`: what `appli_restauree.chiffre_affaires()`
  answers.

**Edit the file in place.** Its header must survive.

### What is not graded, and why that is said

`--single-transaction` is good practice, and the guide explains why. No test
requires it: measured on MySQL 8.4, a dump taken with it and a dump taken
without are **indistinguishable** once the file is written, `LOCK TABLES`
appearing in both. A test claiming to check it would be grading a command line
rather than a state. Use it anyway: on a live database it avoids blocking
writes.

### Check

```bash
dsoxlab check mysql-05-sauvegarder
```
