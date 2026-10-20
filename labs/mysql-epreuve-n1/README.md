# mysql-epreuve-n1: the level 1 exam

## What this exam exercises

The level's five labs, together, on a single instance and from a single brief.
It explains nothing again: it measures what is left when the step-by-step
instructions are gone.

It is this catalogue's **first graded lab**: `lab_type: challenge` and
`exam_passing_score: 70`, so `dsoxlab submit` returns a verdict rather than
only a score.

| What it measures | The lab that taught it |
|---|---|
| an all-powerful account that disappears | mysql-04 |
| a role with exact rights, and its activation | mysql-04 |
| TLS required on the account | mysql-04 |
| three settings that survive a restart | mysql-03 |
| listening closed back to the loopback | mysql-01 and mysql-03 |
| a complete backup and a proven restore | mysql-05 |
| reading the server rather than guessing it | mysql-02 |

## The scoring is contractual, and a guard holds it

Ten tasks announced at ten points, ten tests in the file. dsoxlab grades **per
test**: adding a test without adding a task would shift the whole scoring
without anyone seeing it, and dsoxlab's content validator refuses exactly that
gap. So any change to this lab must touch the brief **and** the tests together.

## The two design decisions that cost the most

**The setup DISASSEMBLES the instance on every pass.** It recreates `app_tout`,
restores `bind-address = 0.0.0.0`, erases `mysqld-auto.cnf` and **removes the
configuration files the candidate may have added**. Without that last point, a
`z-zz-candidat.cnf` from an earlier pass would win over the setup's own, since
files are read in alphabetical order: the second pass would then grade the work
of the first.

**No probe destroys what another one measures.** The first draft checked least
privilege by attempting a `DROP TABLE`. On an over-permissive copy that `DROP`
succeeds: the table is gone, the test turns red, and so do the next two, for a
reason nobody connects to the right cause. So the refusal probes are harmless
if they succeed: read `mysql.user`, and create a database that is then removed.

## What it does not measure

`--single-transaction`, for the reason explained in mysql-05: no verifiable
trace in the file produced. PITR and replication, which are later levels. And
time: the exam is announced at 1h15, nothing times it.

## The hints cost dearly, by design

20 and 30 points. A candidate taking both drops to 50 and can no longer reach
70: that is intended. They are there to get going again when stuck, and the
exam can be retaken. They name the level's two traps without giving a single
command.

## Duration

1h15.

The level's guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/)
