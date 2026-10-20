# A purged table that gave nothing back, and a query that reads everything

The instance on `db1.lab` serves the `appli` database. Its `evenements` table
received 200,000 rows of application log, then the monthly purge deleted nine
out of ten. 20,000 are left.

The disk gave nothing back. The table still occupies what it occupied before
the purge, and the operator who ran the `DELETE` thought the job was done.

And a query the dashboard calls every minute reads the table **whole** every
time:

```sql
SELECT COUNT(*) FROM evenements WHERE service = 'svc-7';
```

An index does exist on that table. It does not serve this query, and nothing in
the catalog says so: `SHOW INDEX` displays an index, the operator concludes the
table is indexed, and the plan keeps reading everything.

You are asked for three things, and the third is the one people forget:

1. that the dashboard query **stops reading the table whole**;
2. that the table **gives back the space** the purge did not;
3. that this query be **findable** in the server's diagnostic views, under its
   database name.

Everything is graded on the real state: the **execution plan** the server
reports, the **size** the table really occupies, and what the diagnostic views
hold. No test looks at a command you might have typed.

Credentials: the `labadmin` administration account, password `Adm1n!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/monitoring-maintenance/)
