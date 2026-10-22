# Formation Bases de données relationnelles : administrer PostgreSQL ou MySQL, et le prouver

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/bdd-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/bdd-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/bdd-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/bdd-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/bdd-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/bdd-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Licence : CC BY 4.0](https://img.shields.io/badge/Licence-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Dix-sept labs pour mettre une base relationnelle en production et la tenir :
l'installer, la piloter, la configurer, la durcir, la sauvegarder, l'observer,
la récupérer après une erreur, et la répliquer. **Deux moteurs, deux parcours
parallèles** : neuf labs sur PostgreSQL en trois niveaux, huit sur MySQL en
trois niveaux, dont une épreuve notée. On choisit son moteur, on ne traverse
pas l'un pour atteindre l'autre.

Écrit pour les administrateurs et les ingénieurs DevOps qui seront d'astreinte
sur une base qu'ils n'ont pas conçue. Chaque lab est noté sur l'**état du
système**, jamais sur les commandes tapées.

## Ce que c'est

À la fin, un apprenant sait prendre une machine Debian nue et rendre un
service de base de données qui refuse les connexions en clair, n'accorde
pas plus de droits que nécessaire, dit ce qu'il fait, survit à une table
supprimée, et porte un secondaire qui le suit. Chacun de ces points est
prouvé par des tests qui lisent l'état du système, et non par une liste à
cocher.

**Deux moteurs, deux parcours PARALLÈLES.** On choisit le sien, on ne
traverse pas l'un pour atteindre l'autre :

| Parcours | Ce qu'il couvre |
|---|---|
| PostgreSQL, niveaux 1 à 3 | installer, piloter, configurer, sécuriser, sauvegarder, observer, archiver, restaurer au point dans le temps, répliquer |
| MySQL, niveaux 1 à 3 | installer, piloter le client et MySQL Shell, configurer avec persistance, accorder par rôles avec TLS, sauvegarder en logique, puis une **épreuve notée** ; observer une requête lente et récupérer ce qu'une purge n'a pas rendu ; répliquer avec GTID |

**Deux labs sont ÉVALUÉS** (`lab_type: challenge`), et sur ceux-là
`dsoxlab submit` rend un verdict plutôt qu'un score brut :
`pg-08-restaurer-pitr`, huit tâches et 80 points pour réussir, et
`mysql-epreuve-n1`, dix tâches et 70 pour réussir, qui mesure tout le niveau 1
de MySQL d'un coup.

**L'ordre compte, et ce n'est pas celui des sujets.** Il suit ce dont une
machine a besoin pour que l'étape suivante soit seulement possible : une
instance avant un client, un client avant une configuration, une
configuration avant un durcissement. Le niveau 2 suppose ensuite un
service qui tourne et demande ce qui se passe quand il casse ; le niveau 3
suppose qu'on sait le réparer et demande comment éviter la coupure.

`dsoxlab next` suit cet ordre, dérivé de la position de chaque lab dans le
`meta.yml`.

## Prérequis

Un prérequis absent de cette liste coûte une heure de recherche à
l'apprenant : elle est donc exacte, et mesurée sur le `meta.yml`.

- **Python 3.11+ et [`uv`](https://docs.astral.sh/uv/)**
- **`git`**
- **`dsoxlab`**, le moteur, installé en outil autonome (voir plus bas).
- **`terraform`** et **`ansible-playbook`**, dont tout lab `vm` a besoin
- **libvirt/KVM 8.0 ou plus**, l'hyperviseur qui porte les machines

Rien de PostgreSQL ni de MySQL n'est nécessaire sur ton poste : les labs
les installent dans les machines virtuelles, depuis le dépôt PGDG et depuis
le dépôt Oracle, ce qui est justement le sujet du premier lab de chaque
parcours.

**Les dix-sept labs sont des labs `vm`**, donc `dsoxlab provision` est toujours
nécessaire.

### Les machines, et les labs qui en demandent deux

Trois machines, déclarées dans [`meta.yml`](./meta.yml) sur le réseau
`lab-bdd` (`10.10.100.0/24`) et provisionnées d'un seul coup :

| Hôte | Distribution | vCPU | RAM | Disque |
|---|---|---|---|---|
| `db1.lab` | Debian 13 | 2 | 2 Go | 20 Go |
| `db2.lab` | Debian 13 | 2 | 2 Go | 20 Go |
| `db3.lab` | Debian 13 | 2 | 2 Go | 20 Go |

Environ 6 Go de RAM et 60 Go de disque en tout. Quinze labs tiennent sur
`db1.lab` seule ; deux en demandent une seconde, `pg-09-repliquer` et
`mysql-07-repliquer`, qui déclarent `db2.lab` sous un rôle `replica`.
`db3.lab` est provisionnée mais aucun lab ne s'en sert encore.

Le provider est déclaré en **liste** (`kvm`, `incus`), et **une liste ne se
résout pas d'elle-même** : en choisir un avec `dsoxlab use --provider kvm`.
Sans ça, les commandes d'infra refusent de partir plutôt que de deviner.

`dsoxlab doctor` dit ce dont ce dépôt a besoin et ce dont il n'a pas besoin, et
distingue un contrôle qui a échoué d'un contrôle qu'il n'a pas pu mesurer.

## Installation

`dsoxlab` est publié sur [PyPI](https://pypi.org/project/dsoxlab/).
Installe-le en outil autonome, pour qu'il reste hors de ce dépôt :

```bash
# 1. La CLI dsoxlab (outil externe, hors de ce dépôt)
uv tool install dsoxlab

# 2. Ce catalogue de labs
git clone https://github.com/stephrobert/bdd-dsoxlab-training.git
cd bdd-dsoxlab-training

# 3. Vérifier le contrat et les machines
dsoxlab validate-structure
dsoxlab doctor
```

### Votre premier lab, en cinq minutes

Les machines doivent exister d'abord : rien ici ne tourne sur ton poste.

```bash
export LAB_HOME=$PWD
dsoxlab use --provider kvm             # une liste de providers ne se résout pas seule
dsoxlab provision                      # crée db1.lab, db2.lab et db3.lab, une fois

dsoxlab list-labs                      # les dix-sept labs, dans l'ordre pédagogique
dsoxlab run       pg-01-installer      # pose l'état de départ et ouvre la session
dsoxlab challenge pg-01-installer      # lire la mission, sans pas-à-pas
dsoxlab check     pg-01-installer      # joue les tests, enregistre le score

dsoxlab clean     pg-01-installer      # défait le lab, garde les machines
dsoxlab destroy                        # rend les machines
```

C'est `run` qui prépare le lab. Un `check` joué sur un lab jamais démarré ne
mesure rien, et le dit au lieu d'enregistrer un 0. `provision` sort en code
non nul si un hôte ne répond pas, et nomme les domaines orphelins qu'il a
laissés plutôt que d'annoncer un succès.

### Garder à jour

```bash
uv tool upgrade dsoxlab        # le moteur, publié sur PyPI
git -C <ce dépôt> pull         # le catalogue
```

Le moteur et le catalogue avancent indépendamment : un nouveau `dsoxlab` ne
demande jamais de recloner les labs, et de nouveaux labs ne demandent jamais de
mettre l'outil à jour, tant que la version du contrat correspond.

## Comment ça marche

### Le contrat déclaratif, à deux niveaux

Le catalogue est décrit par des données, pas par du code, et c'est ce qui garde
le moteur `dsoxlab` indépendant du domaine :

- **`meta.yml`** à la racine déclare l'identité du dépôt, l'**infrastructure**
  (provider, réseau `lab-bdd`, `10.10.100.0/24` et les trois hôtes
  `db*.lab`) et l'**ordre** des sections affichées par `list-labs` ;
- **`lab.yaml`** par lab déclare ses `skills`, son `level`, son `runtime`
  (type et targets), ses `distros`, son `doc_url` et un bloc `validation`. Un
  `lab.fr.yaml` surcharge `title` et `description` en français, et rien
  d'autre ;
- **`setup.yaml`** et **`cleanup.yaml`** posent et défont l'état des machines ;
- **`challenge/tests/test_functional.py`** porte la preuve.

Les gabarits Terraform et cloud-init sont **packagés dans dsoxlab**, pas ici :
ce dépôt ne déclare que son bloc `infra:` et sa clé publique dans `ssh/`.

`dsoxlab validate-structure` contrôle tout le contrat : `meta.yml` bien formé,
chaque lab référencé présent avec un `lab.yaml` valide, chaque fichier de test
et de fixture déclaré réellement là, et chaque lien relatif d'un README qui
mène quelque part.

### Le cycle de vie d'un lab

```bash
dsoxlab list-labs              # parcourir le catalogue
dsoxlab show      <id>         # métadonnées et état d'un lab
dsoxlab run       <id>         # poser l'état de départ
dsoxlab challenge <id>         # lire la mission, sans pas-à-pas
dsoxlab hint      <id>         # révéler un indice (déduit du score)
dsoxlab check     <id>         # lancer les tests, calculer et enregistrer le score
dsoxlab clean     <id>         # défaire ce que le lab a posé
dsoxlab progress               # avancement par section, score moyen
```

### Les runtimes

Ce catalogue n'emploie qu'un seul runtime.

| Runtime | Ce que le lab demande |
|---|---|
| `vm` | une ou deux machines Debian 13, provisionnées par `dsoxlab provision`. La session s'ouvre en SSH sur la cible, et les tests lisent l'état du système par `pytest-testinfra`. |

### Le modèle de validation

La validation **prouve l'état, elle ne fait pas confiance à l'apprenant**.
Chaque lab porte des tests `pytest` sous `challenge/tests/` qui lisent ce que
le système contient, jamais ce qu'un fichier contient ni quelles commandes ont
été tapées.

Et un lab est prouvé **dans les deux sens** : les tests doivent échouer avant
le travail et passer après. Un test vert avant le travail n'est pas un test,
c'est une hypothèse sur le setup.

Les solutions de référence vivent dans `solution/<lab>/solution.yaml`, et
les **dix-sept sont chiffrées** par `ansible-vault`. Une solution livrée en
clair gâche le lab, et git la garde pour toujours.

`scripts/verify-solutions.py` les déchiffre, les joue sur une machine
fraîche et exige un score de 100. `scripts/valider-labs.py` va plus loin et
exige **0 avant le travail et 100 après** : un lab dont les tests passent
sur l'état de départ ne mesure rien.

### Score, indices, avancement

`check` enregistre un score (tests réussis sur total, moins le coût des indices
révélés). Les indices sont **en base64** dans `challenge/hints.yaml`, pour qu'on
n'y accède pas en ouvrant le fichier, et leur coût croît avec leur précision.
L'historique vit dans une base SQLite **locale à ce dépôt**.

Une exécution qui n'a rien mesuré n'est ni une réussite ni un échec : si tous
les tests collectés skippent, `check` n'enregistre aucune note et dit pourquoi.
Un 0 accuserait le lab de ce qui manque au poste.

## Catalogue

### Niveau 1 : mettre une base en service, et sûre

| Lab | Ce qu'il prouve |
|---|---|
| `pg-01-installer` | l'instance vient du dépôt PGDG, et sa clé est contrôlée |
| `pg-02-psql-admin` | un script se connecte par le réseau sans mot de passe tapé |
| `pg-03-configurer` | les paramètres sont **effectifs**, et celui qui attend est su comme tel |
| `pg-04-securiser` | une connexion en clair est **refusée**, et les droits sont séparés |
| `pg-05-sauvegarder` | la sauvegarde **se restaure**, comparée ligne à ligne |

### Niveau 2 : protéger et exploiter

| Lab | Ce qu'il prouve |
|---|---|
| `pg-06-observer` | le planificateur a cessé de lire la table en entier, et l'espace mort est revenu |
| `pg-07-archiver` | des journaux partent vraiment, et la sauvegarde physique est vérifiée |
| `pg-08-restaurer-pitr` | une table supprimée revient, et la timeline prouve la restauration |

### Niveau 3 : répliquer et rendre disponible

| Lab | Ce qu'il prouve |
|---|---|
| `pg-09-repliquer` | une ligne écrite sur le primaire est lisible sur le secondaire |

### MySQL, niveau 1 : mettre en service une instance sûre

| Lab | Ce qu'il prouve |
|---|---|
| `mysql-01-installer` | l'instance 8.4 LTS vient du dépôt Oracle, clé et **sous-clés** contrôlées, et les **deux** portes sont fermées |
| `mysql-02-client-admin` | une connexion aboutit sans mot de passe tapé ni **terminal** |
| `mysql-03-configurer` | les réglages survivent à un **redémarrage**, que rien d'autre ne prouve |
| `mysql-04-securiser` | un rôle accordé n'est **pas** un rôle actif, et le clair est refusé |
| `mysql-05-sauvegarder` | le dump porte la **procédure stockée**, et la restauration est utilisable |
| `mysql-epreuve-n1` | l'**épreuve** du niveau : dix tâches, 100 points, 70 pour réussir |

### MySQL, niveau 2 : exploiter ce qui est en service

| Lab | Ce qu'il prouve |
|---|---|
| `mysql-06-observer` | le plan a cessé de lire la table entière, et l'espace qu'une purge n'a **pas** rendu |

### MySQL, niveau 3 : répliquer et rendre disponible

| Lab | Ce qu'il prouve |
|---|---|
| `mysql-07-repliquer` | une ligne écrite sur la source arrive, les deux fils tournent, et l'écriture directe est refusée |

## Contribuer

Lis [`CONTRIBUTING.fr.md`](./CONTRIBUTING.fr.md). En bref : un lab est prouvé
**dans les deux sens** avant d'être fusionné, `dsoxlab validate-structure` est
vert, et l'énoncé existe en anglais et en français.

Tout ce qui s'affiche est bilingue. Un document traduit d'un seul côté est
signalé par le validateur, et non laissé à la bonne volonté.

## Licence

Voir [`LICENSE`](./LICENSE).
