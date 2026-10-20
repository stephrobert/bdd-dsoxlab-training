# Changelog

All notable changes to this catalog are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this catalog
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**What a version means here.** A catalog is not a library: a MINOR bump adds
labs, a PATCH fixes a statement or a test without changing what a lab proves,
and a MAJOR renames or removes labs, which breaks the progress already recorded
by learners.

## [0.2.0] - 2026-10-20

### Added

- The catalog skeleton, created by `dsoxlab new catalog`, and the first two
  labs: `pg-01-installer` (the instance comes from the PGDG repository, and
  its key is checked) and `pg-02-psql-admin` (a script connects over the
  network without a typed password, which `.pgpass` only allows in 0600,
  since psql does not honour a file
  readable by group or others, which it warns about).

- **Seven labs, all proven in both directions** (0 before the work, 100 after),
  which brings the catalog from two labs to nine and opens levels 2 and 3:

  | Lab | What it proves |
  |---|---|
  | `pg-03-configurer` | the reloadable parameters are EFFECTIVE, and the postmaster-context one is known to be pending. A reload never reports a parameter left without effect: only `pending_restart` does. |
  | `pg-04-securiser` | a cleartext network connection is REFUSED and an encrypted one still works, on a dedicated certificate, with the owner/writer/reader pattern. |
  | `pg-05-sauvegarder` | the dump restores into a verification database whose content matches row by row, and the cluster-global roles that `pg_dump` leaves out are captured too. |
  | `pg-06-observer` | the planner stopped reading the table whole, which an index's existence does not prove, and the dead rows a purge left came back. |
  | `pg-07-archiver` | WAL segments really leave, with no archiving failure, and the physical backup is declared valid by `pg_verifybackup`. |
  | `pg-08-restaurer-pitr` | a dropped table comes back at the chosen instant, and the TIMELINE proves the recovery happened rather than the table being recreated. An assessment, pass mark 80. |
  | `pg-09-repliquer` | a row written on the primary is readable on the standby. The catalog's first two-machine lab. |

- `scripts/auditer-replis-yaml.py`, which refuses a command whose newline
  survives YAML folding. In a folded scalar (`>`), a line break is NOT folded
  into a space as soon as one of the two lines it separates is more indented
  than the first. Harmless inside a quoted SQL string, fatal between two shell
  words, and the message then mentions neither YAML nor indentation. It cost
  two labs on 2026-10-19, one of which passed for the wrong reason.

- `CLAUDE.md`, which records the four authoring traps met for real, so they are
  not met again.

### Changed

- `README.md` and `README.fr.md` no longer carry the skeleton's placeholders:
  the requirements, the runtime, the solutions and the catalog are described
  from measured values.

- The labs are now ordered across the three sections of `meta.yml` by subject
  rather than by creation. `dsoxlab new lab` had placed four of them in the
  wrong section, announcing one section while writing into another.
