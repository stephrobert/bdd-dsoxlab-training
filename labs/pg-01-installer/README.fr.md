# pg-01-installer

**Public :** l'apprenant.

Installer PostgreSQL 18 sur une machine Debian 13 vierge depuis le dépôt du
projet (PGDG), et le laisser en service démarrant au boot.

## Ce que vous saurez faire

- déclarer un dépôt APT tiers lié à sa clé de signature, et contrôler
  l'empreinte de cette clé ;
- distinguer le PostgreSQL de la distribution de celui de PGDG, et installer la
  bonne version majeure ;
- lire l'état d'un cluster Debian : `pg_lsclusters`, `pg_isready`, l'unité
  systemd ;
- vérifier que les sommes de contrôle sont actives et qu'un serveur neuf
  n'écoute pas le réseau.

## Avant de commencer

- Vous savez utiliser `sudo` et `apt` sur Debian.
- La leçon
  [Installer PostgreSQL 18 depuis PGDG](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/installation/)
  détaille chaque étape. Ce lab ne la répète pas.
- Machine : `db1.lab` (2 vCPU, 2 Go, Debian 13). Aucun compte, aucun service
  payant.

## Le lancer

```bash
dsoxlab use --provider kvm      # ou incus
dsoxlab provision --host db1.lab
dsoxlab run pg-01-installer     # machine vierge
dsoxlab ssh pg-01-installer     # ouvre une session sur db1.lab
dsoxlab check pg-01-installer   # note l'état de la machine
dsoxlab clean pg-01-installer   # ne laisse rien derrière soi
```

## Reconnaître la réussite

`dsoxlab check` rend tous les tests verts. Chaque test lit la machine : le dépôt
que connaît APT, le paquet installé, le cluster, les sommes de contrôle et les
sockets qui écoutent. Le dernier redémarre la machine et vérifie que l'instance
revient.

## En cas d'échec

- Version 17 installée : vous avez pris le paquet de Debian. Ajoutez d'abord le
  dépôt PGDG, puis installez `postgresql-18`.
- `NO_PUBKEY` ou `not signed` pendant `apt-get update` : la clé manque ou le
  chemin de `Signed-By` est faux.
- Actif mais pas activé : l'instance répond maintenant et disparaîtra au
  prochain boot. Vérifiez `systemctl is-enabled postgresql`.
- Un écouteur sur `0.0.0.0` ou `*` : quelqu'un a changé `listen_addresses`.
  Remettez `localhost`.
