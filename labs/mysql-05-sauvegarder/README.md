# mysql-05: a complete backup, proven by restoring it

## What this lab exercises

The logical backup of a MySQL database, and above all the **proof** that it is
worth something. The learner produces a dump, restores it into a fresh
database, and establishes that the copy is **usable**: same rows, stored
procedure answering, trigger firing.

It is graded on **two distinct objects**, and that is not a redundancy:

- the backup **file**, because that is what you restore from on the day the
  machine burned down;
- the **restored database**, because a complete dump does not prove it
  restores.

A learner can produce an incomplete dump and then recreate the procedure by
hand in the copy: the database would be right, the file would stay unusable.
The converse holds too. So the two families of tests guard each other.

## The central trap, and it is measured

**An incomplete backup announces itself nowhere.** Measured on MySQL 8.4 on
2026-10-20, `mysqldump --help` reports in its summary of effective values:

| Option | Default |
|---|---|
| `routines` | `FALSE` |
| `events` | `FALSE` |
| `triggers` | `TRUE` |

So a dump taken without `--routines` omits **stored procedures** and functions
while **keeping** triggers. And here is what restoring it into a fresh database
gives, measured in the same container:

| What is observed | Result |
|---|---|
| restore exit code | `0`, it **succeeds** |
| rows restored | all of them |
| triggers restored | present |
| procedures restored | **none** |
| `call base.chiffre_affaires()` | `ERROR 1305 ... does not exist` |

Three steps therefore succeed without a word: the dump, the restore, and the
application starting. The failure arrives on the first page that calls the
procedure, sometimes weeks later, and the backup file looks blameless since it
"restored without an error".

## What this lab does not grade, and why that is written in the brief

**`--single-transaction`.** It is the good practice, the guide explains why,
and it leaves **no verifiable trace** in the file produced. Measured: a dump
taken with it and one taken without both carry a `LOCK TABLES`, and are
indistinguishable once written. A test claiming to check it would be grading a
command line rather than a state, which this catalogue refuses. The brief says
so to the learner rather than hiding it: a useful option whose use cannot be
proven is still a useful option.

That choice has a consequence to own: a learner who forgets
`--single-transaction` scores 100. The lab measures the **completeness** of the
backup, not the way to take it on a database under load.

## What it does not cover

**PITR** and binary log archiving, which deserve a lab of their own and a
notion of time. **MySQL Shell** (`util.dumpSchemas()`), which produces a
parallel backup in several files: another tool for the same capability, and the
guide covers it. **Physical** backup (Percona XtraBackup), which assumes the
same major version at restore time.

## An implementation detail that decided the setup

The procedure and the trigger are created **by `labadmin`**, the account the
learner uses. Their `DEFINER` is therefore `labadmin@localhost`, and restoring
with that same account requires no dynamic privilege: measured, a
`GRANT ALL PRIVILEGES` does not grant `SET_USER_ID`, which would be required to
restore a routine whose `DEFINER` is another account.

## Duration

35 minutes. Hints cost from 5 to 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/sauvegarde-restauration/)
