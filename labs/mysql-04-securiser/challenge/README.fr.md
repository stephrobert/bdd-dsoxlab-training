# Un compte applicatif qui peut tout, et sur un canal en clair

## La situation

L'instance de `db1.lab` sert la base `appli`. L'audit interne a relevé deux
choses, et la seconde est plus sournoise que la première.

Le compte que l'application emploie possède **tous** les droits sur **toutes**
les bases, parce qu'on l'a posé « le temps de faire marcher l'application » et
qu'on ne l'a jamais repris. Il peut donc lire les mots de passe de la base
`mysql`, et supprimer n'importe quelle table.

Et rien n'exige qu'il se connecte sur un canal chiffré. MySQL ne contrôle pas
cela dans un fichier comme PostgreSQL : l'exigence se pose **sur le compte**.

On te demande de refaire le dispositif proprement : des **rôles** qui portent
les privilèges, un compte applicatif qui n'en reçoit qu'un, et du TLS exigé.

Un avertissement, parce qu'il coûte cher à qui l'ignore. En MySQL, un rôle
accordé n'est **pas actif** à la connexion. Le compte voit alors ses droits
refusés, `CURRENT_ROLE()` répond `NONE`, et aucune table du catalogue ne dit
que le rôle dort : le `GRANT` est bien là, et il ne sert à rien.

Les identifiants : le compte d'administration `labadmin`, mot de passe
`Adm1n!Lab2026`. Le compte applicatif à créer s'appellera `app_lecture`, avec le
mot de passe `L3cture!2026`.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/securisation/)

## Ce qui est demandé

Sur `db1.lab`. La base `appli` porte ses tables, le compte `labadmin` existe
avec le mot de passe `Adm1n!Lab2026`, et le serveur écoute sur sa boucle locale.

### 1. Créer deux rôles de privilèges

- `role_reader` : `SELECT` sur `appli.*`, et rien d'autre ;
- `role_writer` : `SELECT`, `INSERT`, `UPDATE`, `DELETE` sur `appli.*`.

Ce sont des **rôles**, pas des comptes : ils ne doivent pas pouvoir se
connecter.

### 2. Créer le compte applicatif, et ACTIVER son rôle

Un compte `app_lecture` avec le mot de passe `L3cture!2026`, qui reçoit
`role_reader` et **lui seul**.

Il doit pouvoir se connecter **par le réseau**, donc depuis `127.0.0.1`.
Attention : un compte déclaré en `@localhost` refuse une connexion TCP, et
l'erreur nomme un hôte que tu n'as pas déclaré.

Et surtout : **accorder un rôle ne l'active pas**. À la connexion,
`CURRENT_ROLE()` doit répondre le rôle et non `NONE`, sinon le compte n'a aucun
droit malgré le `GRANT`.

### 3. Exiger le chiffrement sur ce compte

Une connexion de `app_lecture` **sans TLS** doit être **refusée**, et une
connexion chiffrée doit aboutir.

MySQL pose cette exigence sur le **compte**, pas dans un fichier. Les deux
preuves attendues :

```bash
# doit ECHOUER
MYSQL_PWD='L3cture!2026' mysql -h 127.0.0.1 -u app_lecture --ssl-mode=DISABLED -e 'select 1'

# doit REUSSIR
MYSQL_PWD='L3cture!2026' mysql -h 127.0.0.1 -u app_lecture --ssl-mode=REQUIRED -e 'select 1'
```

### 4. Et rien de plus que la lecture

Le compte `app_lecture` doit pouvoir lire les tables de `appli`, mais **ni y
écrire**, **ni lire** la base `mysql`, qui porte les mots de passe.

### 5. Remplir le rapport

Le fichier `~/rapport-securite.txt` porte trois valeurs à compléter :

- `role_actif_a_la_connexion` : ce que `CURRENT_ROLE()` répond dans une session
  de `app_lecture`, recopié tel quel ;
- `exigence_tls_du_compte` : ce que la colonne `ssl_type` de `mysql.user`
  annonce pour ce compte ;
- `nb_roles_sans_connexion` : combien de rôles de ce serveur ne peuvent pas se
  connecter.

**Édite le fichier sur place.** Son en-tête doit survivre.

### Vérifier

```bash
dsoxlab check mysql-04-securiser
```
