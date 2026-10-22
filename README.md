# Relational Database Training: administer PostgreSQL or MySQL, and prove it

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/bdd-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/bdd-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/bdd-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/bdd-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/bdd-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/bdd-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Seventeen hands-on labs to put a relational database into production and keep
it there: install it, drive it, configure it, harden it, back it up, watch it,
recover it after a mistake, and replicate it. **Two engines, two parallel
tracks**: nine labs on PostgreSQL over three levels, eight on MySQL over three
levels, one of which is a graded exam. You pick an engine, you do not go
through one to reach the other.

Written for sysadmins and DevOps engineers who will be on call for a database
they did not design. Every lab is graded on the **state of the system**, never
on the commands typed.

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
| MySQL, levels 1 to 3 | install, drive the client and MySQL Shell, configure with persistence, grant through roles with TLS, back up logically, then a **graded exam**; observe a slow query and reclaim what a purge did not return; replicate with GTID |

**Two labs are GRADED** (`lab_type: challenge`), and on those `dsoxlab submit`
returns a verdict rather than a bare score: `pg-08-restaurer-pitr`, eight tasks
and 80 points to pass, and `mysql-epreuve-n1`, ten tasks and 70 to pass, which
measures the whole of MySQL level 1 at once.

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

### The machines, and which labs need two

Three machines, declared in [`meta.yml`](./meta.yml) on the `lab-bdd` network
(`10.10.100.0/24`) and provisioned in one go:

| Host | Distribution | vCPU | RAM | Disk |
|---|---|---|---|---|
| `db1.lab` | Debian 13 | 2 | 2 GB | 20 GB |
| `db2.lab` | Debian 13 | 2 | 2 GB | 20 GB |
| `db3.lab` | Debian 13 | 2 | 2 GB | 20 GB |

About 6 GB of RAM and 60 GB of disk in all. Fifteen labs run on `db1.lab`
alone; two need a second machine, `pg-09-repliquer` and `mysql-07-repliquer`,
which declare `db2.lab` under a `replica` role. `db3.lab` is provisioned but
no lab uses it yet.

The provider is declared as a **list** (`kvm`, `incus`), and **a list does not
resolve on its own**: pick one with `dsoxlab use --provider kvm`. Without it,
the infra commands refuse to run rather than guessing.

`dsoxlab doctor` says what this repository needs and what it does not, and
tells apart a check that failed from one it could not measure.

## Install

`dsoxlab` is published on [PyPI](https://pypi.org/project/dsoxlab/). Install it
as a standalone tool, so it stays out of this repository:

```bash
# 1. The dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab

# 2. This lab catalog
git clone https://github.com/stephrobert/bdd-dsoxlab-training.git
cd bdd-dsoxlab-training

# 3. Check the contract and the machines
dsoxlab validate-structure
dsoxlab doctor
```

### Your first lab, in five minutes

The machines have to exist first: nothing here runs on your own host.

```bash
export LAB_HOME=$PWD
dsoxlab use --provider kvm             # a list of providers does not resolve on its own
dsoxlab provision                      # creates db1.lab, db2.lab and db3.lab, once

dsoxlab list-labs                      # the seventeen labs, in teaching order
dsoxlab run       pg-01-installer      # sets the starting state and opens the session
dsoxlab challenge pg-01-installer      # read the mission, no step-by-step
dsoxlab check     pg-01-installer      # run the tests, record the score

dsoxlab clean     pg-01-installer      # undoes the lab, keeps the machines
dsoxlab destroy                        # gives the machines back
```

`run` is what prepares the lab. Running `check` on a lab you never started
measures nothing, and says so rather than recording a 0. `provision` exits
non-zero if a host does not answer, and names the orphan domains it left
behind rather than claiming success.

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

- **`meta.yml`** at the root declares the repository identity, the
  **infrastructure** (provider, network `lab-bdd`, `10.10.100.0/24` and the
  three `db*.lab` hosts) and the **order** of the sections shown by
  `list-labs`;
- **`lab.yaml`** per lab declares its `skills`, `level`, `runtime` (type and
  targets), `distros`, `doc_url` and a `validation` block. A `lab.fr.yaml`
  overrides `title` and `description` in French, and nothing else;
- **`setup.yaml`** and **`cleanup.yaml`** lay down and undo the machine state;
- **`challenge/tests/test_functional.py`** carries the proof.

The Terraform and cloud-init templates are **packaged inside dsoxlab**, not
here: this repository declares only its `infra:` block and its public key in
`ssh/`.

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

The reference solutions live in `solution/<lab>/solution.yaml`, and
**all seventeen are encrypted** with `ansible-vault`. A solution shipped in
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

### MySQL, level 1: put a safe instance into service

| Lab | What it proves |
|---|---|
| `mysql-01-installer` | the 8.4 LTS instance comes from the Oracle repository, key and **subkeys** checked, and **both** doors are shut |
| `mysql-02-client-admin` | a connection works with no password typed and **no terminal** |
| `mysql-03-configurer` | the settings survive a **restart**, which nothing else proves |
| `mysql-04-securiser` | a granted role is **not** an active role, and cleartext is refused |
| `mysql-05-sauvegarder` | the dump carries the **stored procedure**, and the restore is usable |
| `mysql-epreuve-n1` | the level's **exam**: ten tasks, 100 points, 70 to pass |

### MySQL, level 2: operate what is in service

| Lab | What it proves |
|---|---|
| `mysql-06-observer` | the plan stopped reading the table whole, and the space a purge did **not** give back |

### MySQL, level 3: replicate and make available

| Lab | What it proves |
|---|---|
| `mysql-07-repliquer` | a row written on the source arrives, both threads run, and a direct write is refused |

## Contributing

Read [`CONTRIBUTING.md`](./CONTRIBUTING.md). In short: a lab is proven **in both
directions** before it is merged, `dsoxlab validate-structure` is green, and the
statement exists in English and in French.

Anything user-facing is bilingual. A document translated on one side only is
reported by the validator, not left to goodwill.

## License

See [`LICENSE`](./LICENSE).
