# pg-03: configure an instance, and know what reloads

## What this lab exercises

Setting a PostgreSQL parameter is not writing it into a file. It is writing it
**and** having it taken into account, which happens one of two ways depending on
the parameter: a reload, which cuts nobody, or a restart, which cuts everybody.

The lab asks for both behaviours in the same exercise. Reloadable parameters
must be **effective**, that is, read from `pg_settings` and not merely present
in a file. A postmaster-context parameter must be written and stay **pending**.
And the server must not have restarted, which a session left open by the setup
proves better than any claim.

## The trap it makes you meet

**A reload always succeeds.** `pg_reload_conf()` returns `t`, `systemctl reload`
exits 0, and neither reports that a parameter stayed without effect because it
required a restart. The mistake surfaces weeks later, when you find the setting
you made has never been in use.

The only thing that says so is `pending_restart`, in `pg_settings`. And the
pending value is not there: `pg_settings.setting` keeps the value **in
service**. You need `pg_file_settings`, the view that shows what the files
declare.

## What it does not cover

Sizing memory against real load, which requires measuring before setting, and
WAL archiving, which belongs to the backup lab.

## Duration

35 minutes. Hints cost between 5 and 20 points.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/configuration/)
