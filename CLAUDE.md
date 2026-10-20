# Instructions Claude Code : `bdd-dsoxlab-training`

Catalogue de labs **PostgreSQL** pour le moteur
[`dsoxlab`](https://github.com/stephrobert/dsoxlab). Il ne contient aucun code
d'orchestration : `dsoxlab` est installé comme outil externe
(`uv tool install dsoxlab`), et le catalogue ne déclare que son `meta.yml`, ses
labs et ses solutions.

> **Ce document décrit le code, pas l'intention.** Écrit le 2026-10-19, chaque
> valeur mesurée. Les comptes ne se recopient pas, ils se mesurent :
>
> ```bash
> dsoxlab list-labs                                    # les labs découverts
> grep -c '^def test_' labs/*/challenge/tests/test_functional.py
> ```

---

## L'état, le 2026-10-20

Quinze labs, **131 tests fonctionnels**, **294 assertions**, **15 solutions sur
15 chiffrées**. Deux moteurs, et le niveau 1 MySQL est complet.

| Parcours | Niveau | Labs | Sujet |
| --- | --- | --- | --- |
| PostgreSQL | 1 | `pg-01` → `pg-05` | installer, piloter avec psql, configurer, sécuriser, sauvegarder en logique |
| PostgreSQL | 2 | `pg-06` → `pg-08` | observer et maintenir, archivage WAL et sauvegarde physique, restauration à un instant donné |
| PostgreSQL | 3 | `pg-09` | réplication en flux |
| MySQL | 1 | `mysql-01` → `mysql-05` et `mysql-epreuve-n1` | installer, piloter le client et MySQL Shell, configurer avec persistance, accorder par rôles avec TLS, sauvegarder en logique, puis l'épreuve du niveau |

Les deux parcours sont **parallèles** : on choisit son moteur, on ne traverse
pas l'un pour atteindre l'autre. Rien dans le contrat ne lie les deux sections,
et `dsoxlab next` suit l'ordre de chacune.

Deux labs seulement ÉVALUENT, et ce sont les deux `lab_type: challenge` du
catalogue : `pg-08-restaurer-pitr` avec un `exam_passing_score` de 80, et
`mysql-epreuve-n1` avec 70. `pg-09-repliquer` est le seul lab à **deux
machines** : il déclare `roles.standby: db2.lab`, ce qui crée le groupe Ansible
`lab_standby` et fait entrer `db2` dans l'isolation.

L'infrastructure est de trois VM Debian 13 (`db1.lab`, `db2.lab`, `db3.lab`),
réseau `lab-bdd`. `db3` n'est employée par aucun lab pour l'instant.

---

## Règles non négociables

### 1. On tire `main`, on crée la branche, **puis** on code

```bash
git switch main && git pull
git switch -c <type>/<sujet-court>
```

Commit et `git push` **uniquement sur demande**. Aucun `gh pr create`
autonome. Jamais de commit direct sur `main`. Jamais de `git add -A` : nommer
les fichiers un par un.

**Nommer le dépôt dans chaque commande.** Une session touche presque toujours
ce dépôt et `~/Projets/dsoxlab`, et le répertoire courant du shell revient à
l'un ou l'autre sans rien signaler. Donc `git -C ~/Projets/bdd-dsoxlab-training
status`, et des chemins absolus pour `pytest` comme pour les scripts.

### 2. `dsoxlab destroy` se propose, il ne s'initie pas

Détruire une infrastructure par IaC ne se rattrape pas : il n'y a ni
confirmation ni retour. Un agent emploie donc `dsoxlab clean <id>`, qui remet
un lab à zéro en laissant les VM debout, et **propose** la destruction au lieu
de la décider.

Sur instruction explicite, il la lance et en rend compte : le code de sortie
distingue une destruction propre (`0`) d'orphelins laissés derrière (`6`), et
ce compte rendu fait partie du geste. Ce qui est interdit n'est pas la
commande, c'est de la prendre pour soi.

Rien n'est perdu dans une VM détruite : les labs et les solutions vivent dans
le dépôt, et les verdicts dans `validation-labs.json`. Les remonter coûte un
`provision` suivi d'un `rebase-vms.sh`.

### 3. Un lab n'existe pas tant qu'il n'est pas éprouvé dans les deux sens

```bash
python3 scripts/valider-labs.py --lab <id>     # un lab
python3 scripts/valider-labs.py                # tout le catalogue
```

Le pilote exige **0 avant travail** et **100 après**. Il refuse un lab dont un
seul test passe sur l'état de départ, et il a raison : un test vert avant tout
travail n'est pas un test, c'est une hypothèse du setup.

**Après tout `provision`, rejouer `bash scripts/rebase-vms.sh`.** L'isolation
repose sur une base figée qui référence le **domaine** libvirt : un
`destroy` puis `provision` recrée les domaines, et le pilote refuse alors de
jouer sur « l'état figé appartient à un domaine disparu ». Ce n'est pas un faux
rouge, c'est un refus, mais il consomme une campagne entière si on le découvre
au bout.

### 4. Aucune solution en clair

Les neuf solutions sont chiffrées par `ansible-vault`. Le mot de passe vit dans
`.vault-pass`, gitignoré. Pour en relire une :

```bash
ansible-vault decrypt --vault-password-file .vault-pass \
  --output /tmp/solution-en-clair.yaml solution/<lab>/solution.yaml
```

Et pour la remettre : `ansible-vault encrypt --vault-password-file .vault-pass
--output solution/<lab>/solution.yaml /tmp/solution-en-clair.yaml`.

`scripts/verify-solutions.py` les déchiffre, les joue et exige 100.

---

## Les dix pièges d'écriture, tous rencontrés pour de vrai

Ils ont coûté deux soirées, et chacun a été mesuré plutôt que déduit : les
quatre premiers dans un conteneur PostgreSQL jetable, les trois derniers dans
un conteneur MySQL. Les relire avant d'écrire un lab coûte trois minutes.

Les cinq premiers viennent du parcours PostgreSQL, les trois suivants du
parcours MySQL, et le huitième a coûté un premier jet complet de l'épreuve.

### 1. Un test vert avant tout travail n'est pas un test

Rencontré deux fois, sous la même forme : un contrôle qui porte sur une
**contrainte** et non sur un **travail**.

- `pg-03` : « le serveur n'a pas redémarré », vert puisque c'est le setup qui
  ouvre la session témoin ;
- `pg-08` : « le serveur n'est plus en restauration », vert puisque avant tout
  travail c'est un primaire ordinaire.

**La parade :** une contrainte ne mérite pas un test à elle. Son contrôle vit
en tête de l'assertion qu'elle garde, dans un helper nommé `_exiger_*`.

La variante à connaître : un test qui porte sur un état que la **distribution**
fournit déjà. Sur Debian, `ssl = on` est posé par le paquet, et `CREATE` sur le
schéma `public` est révoqué d'office depuis PostgreSQL 15. Les noter
reviendrait à noter le paquet Debian, et le README du lab doit dire pourquoi
ils sont hors note.

### 2. Un saut de ligne survit au repli YAML

Dans un scalaire replié (`>`), un saut de ligne **n'est pas** replié en espace
dès qu'une des deux lignes qu'il sépare est plus indentée que la première.

Inoffensif quand il tombe **dans** une chaîne SQL entre guillemets, PostgreSQL
acceptant les sauts de ligne. **Fatal** entre deux mots du shell : la commande
casse en morceaux, `psql -c` se retrouve sans argument, et le message ne parle
ni de YAML ni d'indentation.

```bash
python3 scripts/auditer-replis-yaml.py                 # tout le dépôt
python3 scripts/auditer-replis-yaml.py <fichier>...     # une solution en clair
```

Le script écarte `solution/`, dont les fichiers sont chiffrés : une solution se
contrôle en clair, en lui donnant son chemin.

### 3. `ALTER SYSTEM` refuse une chaîne multi-commandes

Deux `alter system` dans un même `psql -c` forment une transaction implicite,
et le serveur répond « ALTER SYSTEM cannot run inside a transaction block ».
La solution échoue en une seconde, et **tous** les tests sortent en erreur de
fixture sans que rien ne nomme la cause.

**La parade :** un `ALTER SYSTEM` par appel, par une boucle Ansible.

### 4. Un booléen concaténé ne vaut pas ce que psql affiche

psql **affiche** une colonne booléenne en `t`, mais un booléen **concaténé**
passe par la conversion en texte et vaut `true`. Mesuré sur PostgreSQL 18, dans
un conteneur jetable :

```sql
select true                      -- t
select true::text                -- true
select true || ',' || false      -- true,false
```

Deux tests de `pg-09` comparaient donc `"t"` à `"true"` et échouaient sur un
serveur parfaitement configuré, avec un message qui accusait la configuration.

**La parade :** ne pas apprendre la convention par cœur, mais écrire
`case when <condition> then 't' else 'f' end`, qui dit ce qu'il produit et ne
dépend d'aucune des deux.

### 5. Un paramètre `postmaster` et une contrainte de continuité s'excluent

`pg-03` a été écrit insoluble : il demandait d'activer `logging_collector`,
de contexte `postmaster`, tout en interdisant le redémarrage, et le vérifiait
par une session témoin.

**La parade :** avant d'écrire un lab de configuration, relever la colonne
`context` de `pg_settings` pour chaque paramètre visé. Ce qui exige un
redémarrage ne peut pas être demandé en même temps qu'une continuité de
service, et doit donc être **donné par le setup**.

### 6. Une option sans trace vérifiable ne se note pas

`mysqldump --single-transaction` est la bonne pratique, et **rien dans le
fichier produit ne dit qu'elle a été employée** : mesuré, un dump pris avec et
un dump pris sans portent tous les deux un `LOCK TABLES`, et sont
indiscernables une fois écrits.

Un test qui prétendrait le vérifier noterait une **ligne de commande** et non
un état, ce que ce catalogue refuse. La parade n'est pas de se taire : l'énoncé
de `mysql-05` dit à l'apprenant que l'option est attendue de lui en production
et qu'elle n'est pas notée, et le README du lab dit pourquoi. Une option utile
dont on ne peut pas prouver l'emploi reste une option utile.

Le corollaire, plus dur à accepter : un apprenant qui l'oublie obtient 100. Le
lab mesure la complétude de la sauvegarde, pas la façon de la prendre sous
charge, et il faut l'écrire plutôt que de l'espérer.

### 7. Une affirmation absolue se dément toute seule

J'avais écrit dans six documents de `mysql-03` que « rien, sur un serveur en
marche, ne distingue une valeur qui survivra d'une valeur qui disparaîtra ».
C'était vrai de `performance_schema.variables_info`, la table que le lab
emploie, et **faux en général** : `performance_schema.persisted_variables`
distingue bien les deux.

La relecture d'une autre session l'a attrapé, et la correction a touché neuf
fichiers, dont les deux `lab.yaml` et une docstring de test que la relecture
n'avait pas vue.

**La parade :** borner l'affirmation à ce qu'on a mesuré. « `variables_info`
annonce la même source dans les deux cas » est vrai, vérifiable et suffisant.
« Rien ne distingue » ajoute une portée qu'aucune mesure ne couvre.

Et la nuance qui sauve le lab vaut d'être connue : `persisted_variables`
reflète la **mémoire** et non le fichier. En vidant `mysqld-auto.cnf` derrière
le dos du serveur, sans redémarrer, la table continue d'annoncer la valeur.
Elle prouve donc l'intention de persister, et seul le redémarrage prouve
l'**aller-retour**.

### 8. Une sonde destructrice détruit ce que les autres tests mesurent

Le premier jet de `mysql-epreuve-n1` prouvait le moindre privilège en tentant
un `DROP TABLE` avec le compte de service. Sur une copie trop permissive, ce
`DROP` **aboutit** : la table disparaît, le test passe au rouge comme prévu, et
les deux tests suivants tombent aussi, pour une raison que personne ne
rattache à la bonne cause. Un candidat irait chercher une faute de sauvegarde
là où il a seulement trop accordé de droits.

**La parade :** une sonde de refus doit être **inoffensive en cas de succès**.
Lire `mysql.user`, qui ne modifie rien. Créer une base, qu'un `finally`
retire. Insérer une ligne marquée, qu'un `finally` retire aussi.

La règle générale : avant d'écrire une sonde, se demander ce qu'elle fait **si
elle réussit**, et pas seulement ce qu'elle mesure quand elle échoue.

---

## Conventions d'un lab de ce catalogue

Chaque lab porte la même ossature, et s'en écarter se paie en relecture :

- `lab.yaml` **en anglais**, `lab.fr.yaml` surchargeant **titre et description
  seulement** ;
- `scenario.md` / `.fr.md` : la situation, pas la consigne ;
- `README.md` / `.fr.md` : ce que le lab éprouve, le piège qu'il fait
  rencontrer, et **ce qu'il ne couvre pas** ;
- `challenge/README.md` / `.fr.md` : la consigne notée, numérotée ;
- `challenge/hints.yaml` : **quatre** indices encodés en base64, de 5 à 20
  points, du plus vague au plus explicite, et aucun ne donne le fichier à
  recopier ;
- `challenge/tests/test_functional.py` : un module dont le docstring répond à
  « serait-il vert si l'apprenant ne faisait rien ? » ;
- `setup.yaml` : pose la situation, et **reconstruit l'état fautif à chaque
  passage** ;
- `cleanup.yaml` : **purge** PostgreSQL. Ne pas se contenter de défaire les
  réglages : le setup installe l'instance, et un nettoyage partiel laisse une
  grappe dont le prochain passage hérite.

### Le rapport à remplir

Huit labs sur neuf déposent un rapport de trois valeurs dans le répertoire de
`student`. Deux règles le gouvernent, et chacune vient d'un défaut rencontré :

- **les valeurs sont confrontées à ce que le serveur répond**, non à une
  constante : une valeur plausible mais fausse ne passe pas, et une valeur
  juste obtenue autrement passe ;
- **le test lit la VALEUR, jamais le fichier entier.** L'en-tête du rapport
  cite le marqueur à remplacer : un test qui cherche ce marqueur dans tout le
  fichier le trouve dans l'en-tête et conclut que rien n'est rempli. Cette
  faute s'est produite trois fois.

Le test exige aussi que l'en-tête **survive** : il disparaît si l'apprenant
recrée le fichier par une redirection `>` au lieu de l'éditer.

### 9. Un contrôle qui ne peut pas regarder ne conclut jamais au vert

Rencontré **trois fois dans la même heure**, le 2026-10-20, pendant une étape
de la procédure de version. Chaque fois le même symptôme, et il ne ressemble
pas à une panne :

    0 vert(s), 0 rouge(s), 15 ignoré(s) sur 15 lab(s)
    code de sortie : 0

Les trois causes, dans l'ordre où elles sont apparues, chacune cachée par la
précédente :

1. `verify-solutions.py` sondait l'infrastructure en important `dsoxlab`, et
   son `except ImportError: return False` transformait une **bibliothèque
   absente** en **infrastructure absente**. Le message envoyait faire un
   `dsoxlab provision` déjà fait ;
2. une fois `dsoxlab` installé, le script allait plus loin et butait sur
   `dsoxlab reset`, qui **demande une confirmation**. Sans terminal, l'invite
   échoue, et les quinze labs repartaient en « ignorés ». L'option manquait :
   `--yes` ;
3. en voulant prouver la correction, j'ai retiré `dsoxlab` du PATH. `terraform`
   est parti avec, `read_terraform_outputs` a rendu `None`, et ma sonde a
   traduit en « infra absente » ce que dsoxlab venait d'écrire mot pour mot :
   « Nothing can be concluded about what is running ».

**La parade, et elle est structurelle.** Une sonde rend TROIS états et non
deux, comme le `doctor` de dsoxlab dont `unknown` n'est ni `ok` ni `failed` :

| État | Sens | Geste |
| --- | --- | --- |
| mesuré | on sait | lire le verdict |
| délibérément non mesuré | pas de tests, pas de solution, infra qu'on sait absente | ignorer, c'est un choix |
| non mesurable | la sonde n'a pas abouti | **dire**, et sortir en non nul |

Et sous `--check`, un lab qui devait être mesuré et ne l'a pas été sort en
**3**, distinct du **1** d'une solution cassée : le premier se remesure, le
second se répare.

**Le contrôle se prouve en le faisant échouer.** Le code 3 a été éprouvé en
retirant `dsoxlab` du PATH, et c'est cet essai qui a trouvé la troisième
cause. Un garde-fou qu'on n'a pas vu refuser ne garde rien.

### 10. `pkill -f` et `pgrep -f` se désignent eux-mêmes

`dsoxlab reset pg-03-configurer` sortait en 2, donc un apprenant ne pouvait pas
réinitialiser ce lab. La tâche fautive :

    cmd: pkill -f "temoin-pg-03" || true

`pkill -f` compare le motif à la ligne de commande ENTIÈRE de chaque processus,
et le `bash -c 'pkill -f "temoin-pg-03" || true'` qui joue la tâche porte le
motif dans son propre argv. pkill tue donc son parent, le shell meurt avant
d'évaluer `|| true`, et Ansible rapporte « non-zero return code ».

**La parade est le crochet.** `[t]emoin-pg-03` est une expression régulière qui
reconnaît le texte `temoin-pg-03`, donc le processus visé, et PAS l'argv du
shell appelant, qui contient les crochets littéralement. Le motif cesse ainsi
de se désigner lui-même.

Deux leçons de méthode, et la seconde vaut plus que la première.

**Pourquoi il ne s'était pas vu.** `valider-labs.py` enchaîne ses propres
étapes, et l'échec du `clean` final n'y est pas fatal. C'est
`verify-solutions`, qui réinitialise AVANT de mesurer, qui l'a mis au jour, et
seulement une fois son propre code de sortie corrigé (piège 9). Un défaut peut
donc attendre derrière un autre : le premier garde-fou réparé révèle ce que le
second cachait.

**Le piège prend aussi l'auteur.** Le même `pgrep -f` m'a attrapé trois fois le
même jour dans mes propres scripts de mesure, dont une fois en tuant mon shell.
Ce n'est pas une faute de contenu, c'est une faute d'outillage, et elle ne
s'oublie qu'en se relisant.

---

## Écrire une épreuve de niveau

Une épreuve n'est pas un lab plus long : elle **évalue**, donc trois choses
changent.

**Le barème est contractuel, et un garde-fou le tient.** dsoxlab note PAR
TEST : dix tests valent dix points chacun. Si l'énoncé annonce dix tâches à dix
points et que le fichier en compte onze, chaque tâche vaut en réalité 9,09 et
le barème affiché ment. Le validateur de contenu de dsoxlab refuse justement
cet écart, à deux conditions de forme qu'il faut connaître :

- chaque tâche notée est un titre de niveau 3 finissant par `(N points)` ;
- l'annonce du total s'écrit de façon que le PREMIER nombre de points qui suit
  le mot « tâches » soit le total. « 10 tâches notées, 100 points en tout »
  fonctionne ; « 10 tâches à 10 points chacune, 100 points en tout » est lu
  comme un total de 10 et le contrôle échoue.

Toute modification d'une épreuve touche donc l'énoncé **et** les tests
ensemble.

**Le setup DÉSASSEMBLE l'instance à chaque passage.** Celui de
`mysql-epreuve-n1` recrée le compte tout-puissant, rétablit l'écoute sur
`0.0.0.0`, efface `mysqld-auto.cnf` et **retire les fichiers de configuration
que le candidat aurait ajoutés**. Sans ce dernier point, un
`z-zz-candidat.cnf` d'un passage précédent l'emporterait sur celui du setup,
les fichiers de `mysql.conf.d` étant lus dans l'ordre alphabétique : le
deuxième passage noterait le travail du premier.

**Les indices coûtent cher, et c'est un choix assumé.** 20 et 30 points sur
l'épreuve MySQL : qui prend les deux tombe à 50 et ne peut plus atteindre les
70 de réussite. Ils nomment les pièges du niveau sans donner une seule
commande, et un contrôle du script qui les écrit le vérifie. Les supprimer
serait pire : un candidat bloqué à 0 n'apprend rien, et une épreuve se
repasse.

---

## Ce que le catalogue ne couvre pas encore

Les **sept** guides PostgreSQL du site qui décrivent un geste sont tous
jumelés à un lab, mesuré sur les `doc_url` des quinze `lab.yaml` :
`installation`, `prise-en-main-psql`, `configuration`, `securisation`,
`sauvegarde-restauration` (trois labs à lui seul), `monitoring-maintenance` et
`replication`. Les deux pages restantes n'ont pas de lab et n'en auront pas :
`decouvrir-postgresql` est une introduction, `index` une page d'accueil, et ni
l'une ni l'autre ne propose de geste à prouver.

**Côté MySQL**, cinq guides sur neuf sont jumelés, mesuré de la même façon mais
sur les URL entières : `installation`, `prise-en-main-mysql-cli`,
`configuration`, `securisation` et `sauvegarde-restauration`. Deux restent sans
lab et en mériteraient un, `monitoring-maintenance` et `replication`, qui
ouvriraient les niveaux 2 et 3 du parcours MySQL. Les deux dernières,
`decouvrir-mysql` et `index`, sont une introduction et une page d'accueil.

Attention au comptage : les guides des deux moteurs portent les mêmes noms de
fichier. Comparer les derniers segments d'URL fait croire que
`monitoring-maintenance` est couvert, puisque `pg-06` cite celui de
PostgreSQL. Le comptage se fait sur l'URL entière.

Restent sans lab, faute de guide publié : la montée de version majeure, pgBackRest, le
basculement manuel, la réplication logique, Patroni et le point d'entrée
stable.

**La règle est : le lab d'abord, le guide ensuite.** Un guide écrit avant son
lab décrit ce qu'on imagine ; un guide écrit après décrit ce qui marche.

Aucun lab ne déclare de `course.yaml` : les quinze affichent donc leur cours
d'un seul bloc.
