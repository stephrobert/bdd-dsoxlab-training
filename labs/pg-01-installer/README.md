# pg-01-installer

**Audience:** the learner.

Install PostgreSQL 18 on a bare Debian 13 machine from the project's own
repository (PGDG), and leave it as a service that starts at boot.

## What you will be able to do

- declare a third-party APT repository tied to its signing key, and check the
  key's fingerprint;
- tell the distribution's PostgreSQL from the PGDG one, and install the right
  major version;
- read the state of a Debian cluster: `pg_lsclusters`, `pg_isready`, the
  systemd unit;
- check that data checksums are on, and that a fresh server does not listen to
  the network.

## Before you start

- You can use `sudo` and `apt` on Debian.
- The lesson
  [Install PostgreSQL 18 from PGDG](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/installation/)
  explains each step. This lab does not repeat it.
- Machine: `db1.lab` (2 vCPU, 2 GB, Debian 13). No account, no paid service.

## Run it

```bash
dsoxlab use --provider kvm      # or incus
dsoxlab provision --host db1.lab
dsoxlab run pg-01-installer     # bare machine
dsoxlab ssh pg-01-installer     # open a session on db1.lab
dsoxlab check pg-01-installer   # grade the state of the machine
dsoxlab clean pg-01-installer   # leave nothing behind
```

## How to know you succeeded

`dsoxlab check` reports every test green. Each test reads the machine: the
repository APT knows, the installed package, the cluster, the checksums and
the sockets that listen. The last one reboots the machine and checks that the
instance comes back.

## If it fails

- Version 17 installed: you took the Debian package. Add the PGDG repository
  first, then install `postgresql-18`.
- `NO_PUBKEY` or `not signed` during `apt-get update`: the key is missing or
  the `Signed-By` path is wrong.
- Active but not enabled: the instance answers now and disappears at the next
  boot. Check `systemctl is-enabled postgresql`.
- A listener on `0.0.0.0` or `*`: someone changed `listen_addresses`. Put it
  back to `localhost`.
