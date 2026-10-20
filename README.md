# bdd-dsoxlab-training

**Language:** [English](./README.md) · [Français](./README.fr.md)

Nine hands-on labs to put a PostgreSQL instance into production and keep
it there: install it, drive it, configure it, harden it, back it up,
watch it, recover it after a mistake, and replicate it. Written for
sysadmins and DevOps engineers who will be on call for a database they
did not design.

## What it is

At the end, a learner can take a bare Debian machine and return a database
service that refuses cleartext connections, grants no more rights than
needed, says what it is doing, survives a dropped table, and has a standby
following it. Each of those is proven by tests that read the system's
state, not by a checklist.

**Two engines, two PARALLEL tracks.** You pick yours, you do not go through
one to reach the other:

| Track | What it covers |
|---|---|
| PostgreSQL, levels 1 to 3 | install, administer, configure, secure, back up, observe, archive, restore point-in-time, replicate |
| MySQL, level 1 | install, drive the client and MySQL Shell, configure with persistence, grant through roles with TLS, back up logically, then a **graded exam** measuring the five together |

The `mysql-epreuve-n1` exam is the catalog's first GRADED lab: ten tasks,
100 points, 70 to pass, and `dsoxlab submit` returns a verdict.

**The order matters, and it is not the order of the topics.** It follows
what a machine needs before the next step is even possible: an instance
before a client, a client before a configuration, a configuration before
hardening. Level 2 then assumes a running service and asks what happens
when it breaks; level 3 assumes you can repair one and asks how to avoid
the outage altogether.

`dsoxlab next` follows that order, derived from the position of each lab
in `meta.yml`.

## Requirements

A missing requirement costs the learner an hour of searching, so this list
is exact and measured against `meta.yml`.

- **Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)**
- **`git`**
- **`dsoxlab`**, the engine, installed as a standalone tool (see below).
- **`terraform`** and **`ansible-playbook`**, which every `vm` lab needs
- **libvirt/KVM 8.0 or above**, the hypervisor the machines run on

Nothing PostgreSQL- or MySQL-related is needed on your own machine: the
labs install them inside the virtual machines, from the PGDG repository and
from the Oracle repository, which is itself the subject of each track's
first lab.

**All seventeen labs are `vm` labs**, so `dsoxlab provision` is always needed.
The catalog declares three Debian 13 machines (`db1.lab`, `db2.lab`,
`db3.lab`) on the `lab-bdd` network, each with 2 GB of RAM, 2 vCPU and
20 GB of disk: about 6 GB of RAM and 60 GB of disk in all.

Only `pg-09-repliquer` uses a second machine. `db3.lab` is provisioned but
no lab uses it yet.

`dsoxlab doctor` says what this repository needs and what it does not, and
tells apart a check that failed from one it could not measure.

## Install

`dsoxlab` is published on [PyPI](https://pypi.org/project/dsoxlab/). Install it
as a standalone tool, so it stays out of this repository:

```bash
# 1. The dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab

# 2. This lab catalog
git clone <this repository>
cd bdd-dsoxlab-training

# 3. Check the contract is valid
dsoxlab validate-structure
```

### Your first lab, in five minutes

```bash
export LAB_HOME=$PWD
dsoxlab list-labs                # the catalog, in teaching order
dsoxlab run       <id>           # set the starting state
dsoxlab challenge <id>           # read the mission
dsoxlab check     <id>           # run the tests, record the score
```

`run` is what prepares the lab. Running `check` on a lab you never started
measures nothing, and says so rather than recording a 0.

### Keeping it up to date

```bash
uv tool upgrade dsoxlab        # the engine, published on PyPI
git -C <this repo> pull        # the catalog
```

The engine and the catalog move independently: a new `dsoxlab` never requires
re-cloning the labs, and new labs never require upgrading the tool, as long as
the contract version matches.

## How it works

### The declarative contract (two levels)

The catalog is described by data, not code, which is what keeps the `dsoxlab`
engine domain-agnostic:

- **`meta.yml`** at the root declares the repository identity and the **order**
  of the sections shown by `list-labs`;
- **`lab.yaml`** per lab declares its `skills`, `level`, `runtime` (type,
  fixtures, services), `distros`, `doc_url` and a `validation` block. A
  `lab.fr.yaml` overrides `title` and `description` in French, and nothing else.

`dsoxlab validate-structure` checks the whole contract: `meta.yml` is well
formed, every referenced lab exists with a valid `lab.yaml`, every declared
test and fixture file is really there, and every relative link in a README
leads somewhere.

### The lab lifecycle

```bash
dsoxlab list-labs              # browse the catalog
dsoxlab show      <id>         # metadata and status of one lab
dsoxlab run       <id>         # set the starting state
dsoxlab challenge <id>         # read the mission, no step-by-step
dsoxlab hint      <id>         # reveal a hint (deducted from the score)
dsoxlab check     <id>         # run the tests, compute and record the score
dsoxlab clean     <id>         # undo what the lab set up
dsoxlab progress               # per-section progress, average score
```

### Runtimes

This catalog uses one runtime only.

| Runtime | What the lab asks for |
|---|---|
| `vm` | one or two Debian 13 machines, provisioned by `dsoxlab provision`. The session opens over SSH on the target, and the tests read the system's state through `pytest-testinfra`. |

### The validation model

Validation **proves the state, it does not trust the learner**. Each lab ships
`pytest` tests under `challenge/tests/` that read what the system holds, never
what a file contains or which commands were typed.

And a lab is proven **in both directions**: the tests must fail before the work
and pass after it. A test that is green before the work is not a test, it is an
assumption about the setup.

The reference solutions live in `solution/<lab>/solution.yaml`, and the
**nine of them are encrypted** with `ansible-vault`. A solution shipped in
clear text spoils the lab, and git keeps it forever.

`scripts/verify-solutions.py` decrypts them, plays them on a fresh machine
and requires a score of 100. `scripts/valider-labs.py` goes further and
requires **0 before the work and 100 after**: a lab whose tests pass on the
starting state measures nothing.

### Scoring, hints, progress

`check` records a score (tests passed out of total, minus the cost of any hints
revealed). Hints are **base64-encoded** in `challenge/hints.yaml`, so that
opening the file does not give them away, and their cost grows with their
precision. History lives in a SQLite database **local to this repository**.

A run that measured nothing is neither a pass nor a failure: if every collected
test skips, `check` records no score and says why. A score of 0 would accuse the
lab of what is missing from the machine.

## Catalog

### Level 1: put a safe database into service

| Lab | What it proves |
|---|---|
| `pg-01-installer` | the instance comes from the PGDG repository, and its key is checked |
| `pg-02-psql-admin` | a script connects over the network without a typed password |
| `pg-03-configurer` | the parameters are **effective**, and the one that waits is known to wait |
| `pg-04-securiser` | a cleartext connection is **refused**, and the rights are separated |
| `pg-05-sauvegarder` | the backup **restores**, compared row by row |

### Level 2: protect and run

| Lab | What it proves |
|---|---|
| `pg-06-observer` | the planner stopped reading the table whole, and the dead space came back |
| `pg-07-archiver` | logs really leave, and the physical backup is verified |
| `pg-08-restaurer-pitr` | a dropped table comes back, and the timeline proves the recovery |

### Level 3: replicate and make available

| Lab | What it proves |
|---|---|
| `pg-09-repliquer` | a row written on the primary is readable on the standby |

## Contributing

Read [`CONTRIBUTING.md`](./CONTRIBUTING.md). In short: a lab is proven **in both
directions** before it is merged, `dsoxlab validate-structure` is green, and the
statement exists in English and in French.

Anything user-facing is bilingual. A document translated on one side only is
reported by the validator, not left to goodwill.

## License

See [`LICENSE`](./LICENSE).
