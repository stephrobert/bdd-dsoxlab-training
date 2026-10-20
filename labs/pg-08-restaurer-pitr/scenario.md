# A DROP TABLE in production

It is 2:30 pm. A poorly reviewed migration has just run a `DROP TABLE` on
`appli.clients`, in the `facturation` database on `db1.lab`. The table is gone,
and the application is down.

What saves you is that continuous WAL archiving was in place, and that a
physical backup of the cluster exists in `/var/lib/postgresql/backups/base`.

Someone had the presence of mind to note the instant just before the incident,
before the table disappeared. It is in `/home/student/instant-de-securite.txt`.

You are asked to bring the database back to that instant. Not to the last
available WAL: replaying everything means replaying the `DROP TABLE`. And not to
the physical backup alone either: the last row inserted before the incident is
not in it, it exists only in the logs.

So there is exactly one correct landing point, and that is the whole subject.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
