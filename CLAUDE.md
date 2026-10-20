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

## L'état, le 2026-10-19

Neuf labs, **78 tests fonctionnels**, **164 assertions**, **9 solutions sur 9
chiffrées**. Trois niveaux, dont le troisième vient de s'ouvrir.

| Niveau | Labs | Sujet |
| --- | --- | --- |
| 1 | `pg-01` → `pg-05` | installer, piloter avec psql, configurer, sécuriser, sauvegarder en logique |
| 2 | `pg-06` → `pg-08` | observer et maintenir, archivage WAL et sauvegarde physique, restauration à un instant donné |
| 3 | `pg-09` | réplication en flux |

`pg-08-restaurer-pitr` est le seul `lab_type: challenge` du catalogue, avec un
`exam_passing_score` de 80. `pg-09-repliquer` est le seul lab à **deux
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

## Les cinq pièges d'écriture, tous rencontrés pour de vrai

Ils ont coûté une soirée, et chacun a été mesuré plutôt que déduit : le
quatrième a été vérifié dans un conteneur PostgreSQL jetable avant d'être
écrit ici. Les relire avant d'écrire un lab coûte deux minutes.

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

---

## Ce que le catalogue ne couvre pas encore

Les **sept** guides PostgreSQL du site qui décrivent un geste sont tous
jumelés à un lab, mesuré sur les `doc_url` des neuf `lab.yaml` :
`installation`, `prise-en-main-psql`, `configuration`, `securisation`,
`sauvegarde-restauration` (trois labs à lui seul), `monitoring-maintenance` et
`replication`. Les deux pages restantes n'ont pas de lab et n'en auront pas :
`decouvrir-postgresql` est une introduction, `index` une page d'accueil, et ni
l'une ni l'autre ne propose de geste à prouver.

Restent sans lab, faute de guide publié : la montée de version majeure, pgBackRest, le
basculement manuel, la réplication logique, Patroni et le point d'entrée
stable.

**La règle est : le lab d'abord, le guide ensuite.** Un guide écrit avant son
lab décrit ce qu'on imagine ; un guide écrit après décrit ce qui marche.

Aucun lab ne déclare de `course.yaml` : les neuf affichent donc leur cours d'un
seul bloc.
