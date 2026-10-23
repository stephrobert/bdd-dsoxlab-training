# Changelog

All notable changes to this catalog are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this catalog
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**What a version means here.** A catalog is not a library: a MINOR bump adds
labs, a PATCH fixes a statement or a test without changing what a lab proves,
and a MAJOR renames or removes labs, which breaks the progress already recorded
by learners.

## [0.4.3] - 2026-10-23

### Added

- A verdict can no longer be committed together with what it measures. The
  `verdicts-et-commun-separes` hook refuses a commit carrying
  `validation-labs.json` alongside anything the cycle plays:
  `challenge/tests/`, `setup.yaml`, `cleanup.yaml`, `lab.yaml` of any lab, and
  the shared tooling. It is itself tested, in both directions, by a hook of its
  own.

  This closes a case **no measurement can catch afterwards**. The staleness of
  a verdict used to be judged by comparing DATES, and that comparison was wrong
  in both directions on 2026-10-22: a correction committed together with the
  verdicts it invalidated passed as healthy, and labs re-attested on a branch
  came back "to be re-attested" after their squash merge, their content
  unchanged. When a squashed pull request touches a test *after* its campaign,
  the single commit carries both and the squash has destroyed what told them
  apart. It cannot be observed, so it is prevented.

  The statement stays allowed next to a verdict: it is not played by the cycle,
  and forbidding it would demand a campaign for a typo.

### Fixed

- `pipelineMustNotLeakSecretsInConfig` is removed from `.plumber.yaml`, where
  it was declared twice. Plumber dropped that control and answers "was removed
  and is now ignored: secret detection is no longer part of Plumber; remove
  this block". Keeping it suggested that secret detection was covered here. It
  is not, and `detect-private-key` is what comes closest, as a hook.

## [0.4.2] - 2026-10-22

### Added

- A verdict can no longer be committed together with what it measures. The
  `verdicts-et-commun-separes` hook refuses a commit carrying
  `validation-labs.json` alongside anything the cycle plays:
  `challenge/tests/`, `setup.yaml`, `cleanup.yaml`, `lab.yaml` of any lab, plus
  the shared tooling.

  This closes a case **no measurement can catch afterwards**. When a squashed
  pull request touches a test *after* its campaign, the single commit carries
  both and the squash has destroyed what told them apart: neither a date, nor a
  diff between two trees, nor a fingerprint recorded later can say which came
  first. It cannot be observed, so it is prevented.

  The statement stays allowed next to a verdict: it is not played by the cycle,
  and forbidding it would demand a campaign for a typo.

- `scripts/empreinte_lab.py` and `scripts/verifier-attestations.py`, a local
  corroboration: a sha256 of what the cycle plays, recorded beside each verdict
  by future campaigns. It is **not required**: a verdict without one is not a
  defect, and the check says so and exits 0. `--strict` restores exit code 10
  for an automated caller.

### Fixed

- The staleness of a verdict is no longer judged by comparing **dates**, which
  answers a different question from the one being asked. It was wrong in both
  directions on 2026-10-22: a correction committed together with the verdicts
  it invalidated passed as healthy, and labs re-attested on a branch came back
  "to be re-attested" after their squash merge, their content unchanged.

  Git trees already are content fingerprints, so the authoritative check now
  compares two trees and no longer depends on how a branch was merged.

## [0.4.1] - 2026-10-21

### Added

- `scripts/verifier-release.py` refuses to let a tag be posted on a tree that
  does not carry that version. Written because a `v0.4.1` went out on the
  0.4.0 tree: the pull request carrying 0.4.1 was not merged yet, so
  `git switch main && git pull` succeeded without bringing anything back, and
  `git tag` has no reason to know about `pyproject.toml`. The release workflow
  then built a signed, attested bundle of the wrong content. The script checks,
  in order, that the tree is clean, that `main` matches `origin/main`, that
  **`pyproject.toml` carries exactly the version asked for**, that both
  CHANGELOG files have its entry, that the tag is free locally and on `origin`,
  and that no lab in `validation-labs.json` is anything but VALIDE. It exits 1
  on the first failed check and **2** when it could not measure, because
  "I checked nothing" is not "all is well".

### Fixed

- The replication account of `mysql-07-repliquer` is renamed `repl` ->
  **`replicator`**, the name `pg-09-repliquer` already teaches. The two labs
  were each self-consistent, so no check had anything to say: a learner taking
  both tracks simply learned two names for one concept. The statements, the
  scenario, the reference solution and the test follow, and `setup.yaml` now
  drops both names so a learner who played the previous version keeps no
  orphan account. The lab was re-attested on `db1.lab` and `db2.lab`, 0 before
  the work and 100 after.

- Two more names diverged, found by applying that same rule to the whole
  catalog. `mysql-02-client-admin` called its database `labdb` where the five
  other MySQL labs call it `appli`, an outlier **inside** the track rather than
  a difference between engines; its report field follows, `nb_tables_labdb` ->
  `nb_tables_appli`. And `pg-03-configurer` wrote `rapport-config.txt` where
  `mysql-03-configurer` writes `rapport-configuration.txt`, while every other
  report of the catalog spells the word out (`installation`, `observation`,
  `restauration`, `sauvegarde`). Both labs were re-attested, 0 before the work
  and 100 after.

- `README.md` and `README.fr.md` said six things the catalog no longer does.
  They announced **nine encrypted solutions** where all seventeen are, a MySQL
  track stopping at **level 1** where it now has three, **one** lab using a
  second machine where `mysql-07-repliquer` is a second one, and a `lab.yaml`
  declaring `fixtures` and `services` that this catalog never declares. The
  clone command was still the skeleton's `<this repository>` placeholder.

- The five-minute quickstart **provisioned nothing**, although all seventeen
  labs are `vm` labs and the provider is declared as a list, which does not
  resolve on its own. A learner following it to the letter could not play a
  single lab: `run` had no machine to open a session on. It now runs
  `dsoxlab use --provider kvm` and `dsoxlab provision` first, and gives the
  machines back with `clean` and `destroy`.

- The requirements now carry the machine table the sibling catalogs have, and
  the declarative contract says that `meta.yml` holds the `infra:` block and
  that the Terraform and cloud-init templates are packaged inside dsoxlab.

## [0.4.0] - 2026-10-20

### Added

- **The two MySQL labs that open levels 2 and 3**, each proven in both
  directions (0 before the work, 100 after). The four operation and
  replication modules of the course finally have a validation device, which
  was their only real defect.

  | Lab | What it proves |
  |---|---|
  | `mysql-06-observer` | the plan stopped reading the table whole, which an index's existence does not prove, and the space a purge did not give back. Measured: after deleting nine rows out of ten the table still occupies 45 MB, `CREATE INDEX` changes the plan without reclaiming a single byte, and only a rebuild brings it down to 6 MB. |
  | `mysql-07-repliquer` | a row written on the source arrives on the replica, both replication threads are running, and a direct write is refused. Measured: `gtid_mode` refuses to go from OFF to ON in one step (error 1788), and the default authentication plugin blocks the channel with error 2061. |

  `mysql-07-repliquer` is the catalogue's second two-machine lab, after
  `pg-09-repliquer`, and the first to declare `roles.replica`.

- Two sections in `meta.yml` and `meta.fr.yml`, `mysql-niveau-2` and
  `mysql-niveau-3`, which open the MySQL track's levels 2 and 3.

### Changed

- `CLAUDE.md` records two authoring traps more, both of them mine: a solution
  that is not idempotent breaks on the state it has just produced, and a
  measurement taken under conditions that are not the lab's does not prove the
  lab works. The second one cost a complete diagnostic.

## [0.3.0] - 2026-10-20

### Added

- **MySQL level 1, complete: five labs and a graded exam**, each proven in both
  directions (0 before the work, 100 after). It is a track PARALLEL to the
  PostgreSQL one: you pick an engine, you do not go through one to reach the
  other.

  | Lab | What it proves |
  |---|---|
  | `mysql-01-installer` | the 8.4 LTS instance comes from the Oracle repository with a key whose SUBKEYS are checked for expiry too, and both doors are shut. The Oracle packages ship no `bind-address` at all, the variable defaults to `*`, and `bind-address` alone does not restrict port 33060, which has its own variable. |
  | `mysql-02-client-admin` | a connection that really works with no password typed and no terminal. `mysql_config_editor` reads `/dev/tty` when a controlling terminal exists, and Ansible always provides one. |
  | `mysql-03-configurer` | graded on a RESTART: `performance_schema.variables_info` reports the same source after a `SET GLOBAL` that will be lost and a `SET PERSIST` that will survive. The slow log is graded on a slow query really landing in it. |
  | `mysql-04-securiser` | a granted role is NOT an active role, and no catalog table says so. Cleartext refused, encrypted working, TLS required on the ACCOUNT rather than in a file. |
  | `mysql-05-sauvegarder` | `mysqldump --help` reports `routines FALSE`: a dump taken without `--routines` omits stored procedures while keeping triggers, and the restore still succeeds with exit code 0. Graded on the file AND on the restored database. |
  | `mysql-epreuve-n1` | the level's exam: ten tasks, 100 points, 70 to pass. The catalog's first GRADED lab (`lab_type: challenge` with `exam_passing_score`), where `dsoxlab submit` returns a verdict. |

- `tests/test_documentation_executable.py`, which confronts the flags quoted in
  the Markdown with what the scripts' own `--help` accepts. A documented
  command that no longer exists sends a reader to a dead end, and nothing in
  the repository used to say it.

### Changed

- `scripts/valider-labs.py` now tells a container a lab LEFT BEHIND from one it
  could not possibly have created. The pilot blamed `pg-02` for a container
  another session had started, and an accusation that names the wrong lab is
  worse than silence.

- `README.md` and `README.fr.md` no longer announce nine labs, and describe the
  two parallel tracks and the exam.

### Fixed

- **A statement of mine in `mysql-03-configurer` was too strong**: "nothing
  else proves persistence". `performance_schema.persisted_variables` does tell
  `SET GLOBAL` from `SET PERSIST`. Measured on 8.4.10, it reflects MEMORY
  rather than the file: emptying `mysqld-auto.cnf` behind the server's back
  leaves the table reporting the value. So it proves the intent to persist, and
  the restart alone proves the round trip. Nine documents corrected, including
  both `lab.yaml` descriptions and the central test's docstring.

- `pg-02-psql-admin`: a `.pgpass` with permissions that are too wide is NOT
  silently ignored. libpq warns about it, and only the host-mismatch case is
  silent, both ending on the same `fe_sendauth: no password supplied`.

- `RELEASING.md` and `RELEASING.fr.md` no longer quote a `--deux-sens` flag
  that the script never accepted: it is `--check --negative`.

- **`scripts/verify-solutions.py` concluded green without looking, three times
  in the same hour**, each time with the same symptom: `0 red, 15 ignored, exit
  code 0`. Found while running a step of this very release procedure.

  The three causes, each hidden by the previous one: an `except ImportError:
  return False` turned a MISSING LIBRARY into a MISSING INFRASTRUCTURE, and the
  message sent the reader to a `dsoxlab provision` already done; then
  `dsoxlab reset` asked for a confirmation that no terminal could give, the
  `--yes` flag being absent; then an unreadable Terraform state was reported as
  "no infrastructure", where dsoxlab itself had just written "Nothing can be
  concluded about what is running".

  The probe now returns THREE states rather than a boolean, as dsoxlab's
  `doctor` does with `unknown`, and under `--check` a lab that had to be
  measured and was not exits **3**, distinct from the **1** of a broken
  solution: the first is re-measured, the second is repaired. The guard was
  proven by making it fail, and that attempt is what found the third cause.

- `RELEASING.md` and `RELEASING.fr.md` name the interpreter that
  `verify-solutions.py` needs, which must carry pytest AND dsoxlab, and
  document its exit codes. The procedure quoted `python3`, which on the
  reference machine carries neither.

- **`dsoxlab reset pg-03-configurer` failed, so a learner could not reset that
  lab.** Its cleanup ran `pkill -f "temoin-pg-03" || true`, and `pkill -f`
  compares the pattern against each process's WHOLE command line: the
  `bash -c` running the task carried the pattern in its own argv, so pkill
  killed its parent and the shell died before evaluating `|| true`. The pattern
  is now bracketed, `[t]emoin-pg-03`, which matches the target process and not
  the calling shell.

  It had stayed hidden because `valider-labs.py` does not treat a failing final
  `clean` as fatal. `verify-solutions`, which resets BEFORE measuring, exposed
  it, and only once its own exit code had been fixed: the first guard repaired
  revealed what the second was hiding.

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
