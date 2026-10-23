# Journal des modifications

Les changements notables de ce catalogue sont consignés ici. Le format suit
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce catalogue suit
le [versionnage sémantique](https://semver.org/lang/fr/).

**Ce qu'une version veut dire ici.** Un catalogue n'est pas une bibliothèque :
un incrément MINEUR ajoute des labs, un CORRECTIF corrige un énoncé ou un test
sans changer ce qu'un lab prouve, et un incrément MAJEUR renomme ou retire des
labs, ce qui casse la progression déjà enregistrée des apprenants.

## [0.4.3] - 2026-10-23

### Ajouté

- Un verdict ne peut plus être commité avec ce qu'il mesure. Le hook
  `verdicts-et-commun-separes` refuse un commit portant `validation-labs.json`
  à côté de ce que le cycle joue : `challenge/tests/`, `setup.yaml`,
  `cleanup.yaml`, `lab.yaml` d'un lab, et l'outillage partagé. Il est lui-même
  éprouvé, dans les deux sens, par un hook à lui.

  Cela ferme un cas **qu'aucune mesure ne rattrape après coup**. La péremption
  d'un verdict se jugeait en comparant des DATES, et cette comparaison s'est
  trompée dans les deux sens le 2026-10-22 : une correction commitée avec les
  verdicts qu'elle périmait est passée pour saine, et des labs réattestés sur
  une branche sont ressortis « à réattester » après leur fusion en squash,
  contenu inchangé. Quand une pull request squashée retouche un test *après* sa
  campagne, le commit unique porte les deux et le squash a détruit ce qui les
  distinguait. Cela ne se constate pas, donc cela s'empêche.

  L'énoncé reste autorisé à côté d'un relevé : il n'est pas joué par le cycle,
  et l'interdire obligerait à une campagne pour une coquille.

### Corrigé

- `pipelineMustNotLeakSecretsInConfig` est retiré du `.plumber.yaml`, où il
  était déclaré deux fois. Plumber a supprimé ce contrôle et répond « was
  removed and is now ignored: secret detection is no longer part of Plumber;
  remove this block ». Le garder laissait croire que la détection de secrets
  était couverte ici. Elle ne l'est pas, et c'est `detect-private-key` qui s'en
  approche, en hook.

## [0.4.2] - 2026-10-22

### Ajouté

- Un verdict ne peut plus être commité avec ce qu'il mesure. Le hook
  `verdicts-et-commun-separes` refuse un commit portant `validation-labs.json`
  à côté de ce que le cycle joue : `challenge/tests/`, `setup.yaml`,
  `cleanup.yaml`, `lab.yaml` d'un lab, et l'outillage partagé.

  Cela ferme un cas **qu'aucune mesure ne rattrape après coup**. Quand une pull
  request squashée retouche un test *après* sa campagne, le commit unique porte
  les deux et le squash a détruit ce qui les distinguait : ni une date, ni un
  diff entre deux arbres, ni une empreinte inscrite ensuite ne peuvent dire
  lequel est venu avant. Il ne se constate pas, il s'empêche.

  L'énoncé reste autorisé à côté d'un relevé : il n'est pas joué par le cycle,
  et l'interdire obligerait à une campagne pour une coquille.

- `scripts/empreinte_lab.py` et `scripts/verifier-attestations.py`, une
  corroboration locale : un sha256 de ce que le cycle joue, inscrit à côté de
  chaque verdict par les campagnes à venir. Elle n'est **pas exigée** : un
  verdict qui n'en porte pas n'est pas un défaut, le contrôle le dit et sort en
  0. `--strict` rétablit le code 10 pour un appelant automatisé.

### Corrigé

- La péremption d'un verdict ne se juge plus en comparant des **dates**, ce qui
  répond à une autre question que celle qu'on pose. Elle s'est trompée dans les
  deux sens le 2026-10-22 : une correction commitée avec les verdicts qu'elle
  périmait est passée pour saine, et des labs réattestés sur une branche sont
  ressortis « à réattester » après leur fusion en squash, contenu inchangé.

  Les arbres git sont déjà des empreintes de contenu : le contrôle qui fait foi
  compare donc deux arbres, et ne dépend plus de la façon dont on a fusionné.

## [0.4.1] - 2026-10-21

### Ajouté

- `scripts/verifier-release.py` refuse de laisser poser un tag sur un arbre qui
  ne porte pas cette version. Écrit parce qu'un `v0.4.1` est parti sur l'arbre
  de la 0.4.0 : la pull request qui portait la 0.4.1 n'était pas encore
  fusionnée, donc `git switch main && git pull` a réussi sans rien ramener, et
  `git tag` n'a aucune raison de connaître `pyproject.toml`. Le workflow de
  release a alors construit un bundle signé et attesté du mauvais contenu. Le
  script contrôle, dans cet ordre, que l'arbre est propre, que `main` est au
  niveau de `origin/main`, que **`pyproject.toml` porte exactement la version
  demandée**, que les deux CHANGELOG portent son entrée, que le tag est libre
  en local et sur `origin`, et qu'aucun lab de `validation-labs.json` n'est
  autre chose que VALIDE. Il sort en 1 au premier contrôle en échec et en **2**
  s'il n'a pas pu mesurer, « je n'ai rien vérifié » n'étant pas « tout va
  bien ».

### Corrigé

- Le compte de réplication de `mysql-07-repliquer` est renommé `repl` ->
  **`replicator`**, le nom que `pg-09-repliquer` enseigne déjà. Les deux labs
  étaient cohérents chacun avec lui-même, donc aucun contrôle n'avait rien à
  dire : l'apprenant qui suivait les deux parcours apprenait simplement deux
  noms pour un même concept. Les énoncés, le scénario, la solution de
  référence et le test suivent, et `setup.yaml` retire désormais les deux noms
  pour qu'un apprenant ayant joué la version précédente ne garde pas de compte
  orphelin. Le lab a été réattesté sur `db1.lab` et `db2.lab`, 0 avant le
  travail et 100 après.

- Deux autres noms divergeaient, trouvés en appliquant cette même règle à tout
  le catalogue. `mysql-02-client-admin` nommait sa base `labdb` là où les cinq
  autres labs MySQL disent `appli`, un intrus **à l'intérieur** du parcours
  plutôt qu'une différence entre moteurs ; son champ de rapport suit,
  `nb_tables_labdb` -> `nb_tables_appli`. Et `pg-03-configurer` écrivait
  `rapport-config.txt` là où `mysql-03-configurer` écrit
  `rapport-configuration.txt`, alors que tous les autres rapports du catalogue
  portent le mot entier (`installation`, `observation`, `restauration`,
  `sauvegarde`). Les deux labs ont été réattestés, 0 avant le travail et 100
  après.

- `README.md` et `README.fr.md` affirmaient six choses que le catalogue ne fait
  plus. Ils annonçaient **neuf solutions chiffrées** là où les dix-sept le
  sont, un parcours MySQL arrêté au **niveau 1** là où il en porte trois,
  **un seul** lab à deux machines là où `mysql-07-repliquer` en est un second,
  et un `lab.yaml` déclarant des `fixtures` et des `services` que ce catalogue
  ne déclare nulle part. La commande de clonage portait encore le gabarit
  `<ce dépôt>`.

- Le démarrage en cinq minutes **ne provisionnait rien**, alors que les
  dix-sept labs sont des labs `vm` et que le provider est déclaré en liste,
  qui ne se résout pas d'elle-même. Un apprenant qui le suivait à la lettre ne
  pouvait jouer aucun lab : `run` n'avait aucune machine où ouvrir sa session.
  Il joue désormais `dsoxlab use --provider kvm` et `dsoxlab provision`
  d'abord, et rend les machines avec `clean` puis `destroy`.

- Les prérequis portent maintenant la table des machines que les catalogues
  frères ont, et le contrat déclaratif dit que `meta.yml` porte le bloc
  `infra:` et que les gabarits Terraform et cloud-init sont packagés dans
  dsoxlab.

## [0.4.0] - 2026-10-20

### Ajouté

- **Les deux labs MySQL qui ouvrent les niveaux 2 et 3**, chacun prouvé dans
  les deux sens (0 avant le travail, 100 après). Les quatre modules
  d'exploitation et de réplication du parcours ont enfin un dispositif de
  validation, ce qui était leur seul vrai défaut.

  | Lab | Ce qu'il prouve |
  |---|---|
  | `mysql-06-observer` | le plan a cessé de lire la table entière, ce que l'existence d'un index ne prouve pas, et l'espace qu'une purge n'a pas rendu. Mesuré : après la suppression de neuf lignes sur dix la table occupe toujours 45 Mo, `CREATE INDEX` change le plan sans récupérer un seul octet, et seule une reconstruction la ramène à 6 Mo. |
  | `mysql-07-repliquer` | une ligne écrite sur la source arrive sur le réplica, les deux fils de réplication tournent, et une écriture directe est refusée. Mesuré : `gtid_mode` refuse de passer de OFF à ON d'un coup (erreur 1788), et le greffon d'authentification par défaut bloque le canal sur une erreur 2061. |

  `mysql-07-repliquer` est le deuxième lab à deux machines du catalogue, après
  `pg-09-repliquer`, et le premier à déclarer `roles.replica`.

- Deux sections dans `meta.yml` et `meta.fr.yml`, `mysql-niveau-2` et
  `mysql-niveau-3`, qui ouvrent les niveaux 2 et 3 du parcours MySQL.

### Modifié

- `CLAUDE.md` consigne deux pièges d'écriture de plus, tous deux de ma main :
  une solution non idempotente casse sur l'état qu'elle vient de produire, et
  une mesure prise dans des conditions qui ne sont pas celles du lab ne prouve
  pas que le lab marche. Le second a coûté un diagnostic complet.

## [0.3.0] - 2026-10-20

### Ajouté

- **Le niveau 1 MySQL, complet : cinq labs et une épreuve notée**, chacun
  prouvé dans les deux sens (0 avant le travail, 100 après). C'est un parcours
  PARALLÈLE à celui de PostgreSQL : on choisit son moteur, on ne traverse pas
  l'un pour atteindre l'autre.

  | Lab | Ce qu'il prouve |
  |---|---|
  | `mysql-01-installer` | l'instance 8.4 LTS vient du dépôt Oracle, avec une clé dont les SOUS-CLÉS sont aussi contrôlées en expiration, et les deux portes sont fermées. Les paquets Oracle ne livrent aucun `bind-address`, la variable vaut `*` par défaut, et `bind-address` seul ne restreint pas le port 33060, qui a sa propre variable. |
  | `mysql-02-client-admin` | une connexion qui aboutit vraiment sans mot de passe tapé et sans terminal. `mysql_config_editor` lit `/dev/tty` dès qu'un terminal de contrôle existe, et Ansible en fournit toujours un. |
  | `mysql-03-configurer` | noté sur un REDÉMARRAGE : `performance_schema.variables_info` annonce la même source après un `SET GLOBAL` qui sera perdu et un `SET PERSIST` qui survivra. Le journal lent est noté sur une requête lente qui y atterrit vraiment. |
  | `mysql-04-securiser` | un rôle accordé n'est PAS un rôle actif, et aucune table du catalogue ne le dit. Le clair refusé, le chiffré debout, et le TLS exigé sur le COMPTE plutôt que dans un fichier. |
  | `mysql-05-sauvegarder` | `mysqldump --help` annonce `routines FALSE` : un dump pris sans `--routines` omet les procédures stockées tout en gardant les triggers, et la restauration réussit quand même avec un code 0. Noté sur le fichier ET sur la base restaurée. |
  | `mysql-epreuve-n1` | l'épreuve du niveau : dix tâches, 100 points, 70 pour réussir. Premier lab ÉVALUÉ du catalogue (`lab_type: challenge` avec `exam_passing_score`), où `dsoxlab submit` rend un verdict. |

- `tests/test_documentation_executable.py`, qui confronte les options citées
  dans les Markdown à ce que le `--help` des scripts accepte vraiment. Une
  commande documentée qui n'existe plus envoie un lecteur dans un mur, et rien
  dans le dépôt ne le disait.

### Modifié

- `scripts/valider-labs.py` distingue désormais un conteneur qu'un lab a
  LAISSÉ d'un conteneur qu'il ne pouvait pas avoir créé. Le pilote accusait
  `pg-02` d'un conteneur lancé par une autre session, et une accusation qui
  nomme le mauvais lab est pire que le silence.

- `README.md` et `README.fr.md` n'annoncent plus neuf labs, et décrivent les
  deux parcours parallèles ainsi que l'épreuve.

### Corrigé

- **Une affirmation de moi dans `mysql-03-configurer` était trop forte** :
  « rien d'autre ne prouve la persistance ».
  `performance_schema.persisted_variables` distingue bien un `SET GLOBAL` d'un
  `SET PERSIST`. Mesuré sur 8.4.10, elle reflète la MÉMOIRE et non le fichier :
  en vidant `mysqld-auto.cnf` derrière le dos du serveur, la table continue
  d'annoncer la valeur. Elle prouve donc l'intention de persister, et seul le
  redémarrage prouve l'aller-retour. Neuf documents corrigés, dont les deux
  descriptions de `lab.yaml` et la docstring du test central.

- `pg-02-psql-admin` : un `.pgpass` aux droits trop larges n'est PAS ignoré en
  silence. libpq l'avertit, et seul le cas de l'hôte qui ne correspond pas est
  muet, les deux finissant sur le même `fe_sendauth: no password supplied`.

- `RELEASING.md` et `RELEASING.fr.md` ne citent plus une option `--deux-sens`
  que le script n'a jamais acceptée : c'est `--check --negative`.

- **`scripts/verify-solutions.py` concluait au vert sans avoir regardé, trois
  fois dans la même heure**, chaque fois avec le même symptôme : `0 rouge,
  15 ignorés, code de sortie 0`. Trouvé en jouant une étape de cette procédure
  de publication même.

  Les trois causes, chacune cachée par la précédente : un
  `except ImportError: return False` transformait une BIBLIOTHÈQUE ABSENTE en
  INFRASTRUCTURE ABSENTE, et le message envoyait faire un `dsoxlab provision`
  déjà fait ; puis `dsoxlab reset` demandait une confirmation qu'aucun terminal
  ne pouvait donner, l'option `--yes` manquant ; puis un state Terraform
  illisible était annoncé comme « infra absente », là où dsoxlab venait
  d'écrire « Nothing can be concluded about what is running ».

  La sonde rend désormais TROIS états au lieu d'un booléen, comme le `doctor`
  de dsoxlab avec son `unknown`, et sous `--check` un lab qui devait être
  mesuré et ne l'a pas été sort en **3**, distinct du **1** d'une solution
  cassée : le premier se remesure, le second se répare. Le garde-fou a été
  prouvé en le faisant échouer, et c'est cet essai qui a trouvé la troisième
  cause.

- `RELEASING.md` et `RELEASING.fr.md` nomment l'interpréteur dont
  `verify-solutions.py` a besoin, qui doit porter pytest ET dsoxlab, et
  documentent ses codes de sortie. La procédure citait `python3`, qui sur la
  machine de référence ne porte ni l'un ni l'autre.

- **`dsoxlab reset pg-03-configurer` échouait, donc un apprenant ne pouvait pas
  réinitialiser ce lab.** Son cleanup jouait
  `pkill -f "temoin-pg-03" || true`, et `pkill -f` compare le motif à la ligne
  de commande ENTIÈRE de chaque processus : le `bash -c` qui exécutait la tâche
  portait le motif dans son propre argv, donc pkill tuait son parent et le
  shell mourait avant d'évaluer `|| true`. Le motif est désormais entre
  crochets, `[t]emoin-pg-03`, qui reconnaît le processus visé et pas le shell
  appelant.

  Il était resté caché parce que `valider-labs.py` ne traite pas l'échec du
  `clean` final comme fatal. C'est `verify-solutions`, qui réinitialise AVANT
  de mesurer, qui l'a mis au jour, et seulement une fois son propre code de
  sortie corrigé : le premier garde-fou réparé a révélé ce que le second
  cachait.

## [0.2.0] - 2026-10-20

### Ajouté

- Le squelette du catalogue, créé par `dsoxlab new catalog`, et les deux
  premiers labs : `pg-01-installer` (l'instance vient du dépôt PGDG, et sa clé
  est contrôlée) et `pg-02-psql-admin` (un script se connecte par le réseau
  sans mot de passe tapé, ce que `.pgpass` n'autorise qu'en 0600, psql
  n'honorant pas autrement un fichier que le groupe ou les autres
  peuvent lire, ce dont il avertit).

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
