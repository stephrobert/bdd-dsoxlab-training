# Journal des modifications

Les changements notables de ce catalogue sont consignés ici. Le format suit
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce catalogue suit
le [versionnage sémantique](https://semver.org/lang/fr/).

**Ce qu'une version veut dire ici.** Un catalogue n'est pas une bibliothèque :
un incrément MINEUR ajoute des labs, un CORRECTIF corrige un énoncé ou un test
sans changer ce qu'un lab prouve, et un incrément MAJEUR renomme ou retire des
labs, ce qui casse la progression déjà enregistrée des apprenants.

## [0.2.0] - 2026-10-20

### Ajouté

- Le squelette du catalogue, créé par `dsoxlab new catalog`, et les deux
  premiers labs : `pg-01-installer` (l'instance vient du dépôt PGDG, et sa clé
  est contrôlée) et `pg-02-psql-admin` (un script se connecte par le réseau
  sans mot de passe tapé, ce que `.pgpass` n'autorise qu'en 0600, psql
  l'ignorant en silence autrement).

- **Sept labs, tous éprouvés dans les deux sens** (0 avant le travail, 100
  après), ce qui porte le catalogue de deux labs à neuf et ouvre les niveaux 2
  et 3 :

  | Lab | Ce qu'il prouve |
  |---|---|
  | `pg-03-configurer` | les paramètres rechargeables sont EFFECTIFS, et celui de contexte postmaster est su en attente. Un rechargement ne signale jamais un paramètre resté sans effet : seul `pending_restart` le dit. |
  | `pg-04-securiser` | une connexion réseau en clair est REFUSÉE et une connexion chiffrée aboutit encore, sur un certificat dédié, avec le motif owner/writer/reader. |
  | `pg-05-sauvegarder` | le dump se restaure dans une base de vérification dont le contenu concorde ligne à ligne, et les rôles globaux au cluster que `pg_dump` laisse de côté sont capturés aussi. |
  | `pg-06-observer` | le planificateur a cessé de lire la table en entier, ce que l'existence d'un index ne prouve pas, et les lignes mortes qu'une purge a laissées sont revenues. |
  | `pg-07-archiver` | des segments WAL partent vraiment, sans aucun échec d'archivage, et la sauvegarde physique est déclarée valide par `pg_verifybackup`. |
  | `pg-08-restaurer-pitr` | une table supprimée revient à l'instant choisi, et la TIMELINE prouve que la restauration a eu lieu plutôt qu'une table recréée. Une épreuve, seuil à 80. |
  | `pg-09-repliquer` | une ligne écrite sur le primaire est lisible sur le secondaire. Premier lab du catalogue à deux machines. |

- `scripts/auditer-replis-yaml.py`, qui refuse une commande dont un saut de
  ligne survit au repli YAML. Dans un scalaire replié (`>`), un saut de ligne
  n'est PAS replié en espace dès qu'une des deux lignes qu'il sépare est plus
  indentée que la première. Inoffensif dans une chaîne SQL entre guillemets,
  fatal entre deux mots du shell, et le message ne parle alors ni de YAML ni
  d'indentation. Il a coûté deux labs le 2026-10-19, dont un qui passait pour
  la mauvaise raison.

- `CLAUDE.md`, qui consigne les quatre pièges d'écriture rencontrés pour de
  vrai, afin de ne pas les rencontrer deux fois.

### Modifié

- `README.md` et `README.fr.md` ne portent plus les trous du gabarit : les
  prérequis, le runtime, les solutions et le catalogue sont décrits à partir de
  valeurs mesurées.

- Les labs sont désormais rangés dans les trois sections du `meta.yml` par
  sujet et non par ordre de création. `dsoxlab new lab` en avait placé quatre
  dans la mauvaise section, en annonçant une section et en écrivant dans une
  autre.
