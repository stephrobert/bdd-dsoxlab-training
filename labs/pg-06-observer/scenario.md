# A slow query, and nothing to tell you

The application complains about a page taking several seconds to answer. It
queries the `appli.journal` table, which holds a hundred thousand rows.

You connect to `db1.lab` to see which queries cost the most. There is nothing to
see: the extension that collects those statistics is not loaded. The server
works, and keeps no record of what it has done.

You eventually find the query in the application's code:

```sql
select count(*) from appli.journal where client_id = 42
```

A second problem remains, which nobody reported because it is invisible from the
application: a purge deleted tens of thousands of rows from that table, and the
space they occupied has never been given back. Autovacuum was disabled on that
table during an operation, and never re-enabled.

Three moves, in this order: make the server observable, fix the query, reclaim
the space.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/monitoring-maintenance/)
