# Ce qui est demandé

Sur `db1.lab`. La base `appli` porte une table `evenements` de 20 000 lignes,
reste d'une purge qui en a supprimé 180 000. Le compte `labadmin` existe avec
le mot de passe `Adm1n!Lab2026`.

La requête du tableau de bord, celle qu'il faut rendre rapide :

```sql
SELECT COUNT(*) FROM evenements WHERE service = 'svc-7';
```

## 1. Faire que le plan cesse de lire la table entière

`EXPLAIN` doit annoncer autre chose que `ALL` pour cette requête, et examiner
nettement moins de lignes que la table n'en contient.

Attention : **un index existe déjà** sur cette table. Il ne sert pas cette
requête, et `SHOW INDEX` ne le dit pas. C'est le plan qui tranche, pas le
catalogue.

## 2. Récupérer l'espace que la purge n'a pas rendu

La table occupe encore ce qu'elle occupait avec ses 200 000 lignes. Elle doit
redescendre sous **20 Mo**, sans perdre une seule des 20 000 lignes qui
restent.

Deux précisions mesurées, qui font gagner du temps :

- un `DELETE` ne rend **rien** au disque, InnoDB garde les pages pour les
  réemployer ;
- surveiller `data_free` ne montrera rien, il bouge à peine.

```sql
-- la taille réelle, en mégaoctets
SELECT ROUND((data_length + index_length) / 1024 / 1024) AS mo
  FROM information_schema.tables
 WHERE table_schema = 'appli' AND table_name = 'evenements';
```

## 3. Rendre la requête retrouvable sous sa base

Un `SELECT` citant `evenements`, avec son filtre, doit apparaître dans
`sys.statement_analysis` pour `db = 'appli'`.

C'est le piège d'exploitation du lab : une requête jouée **sans base
sélectionnée** est enregistrée avec un schéma **nul**, et n'apparaît donc
jamais quand on cherche « les requêtes coûteuses de cette base ».

## 4. Remplir le rapport

Le fichier `~/rapport-observation.txt` porte trois valeurs à compléter :

- `type_d_acces_du_plan` : ce que le plan annonce pour la requête, recopié tel
  quel ;
- `megaoctets_de_la_table` : la taille réelle, en mégaoctets entiers ;
- `lignes_restantes` : combien de lignes la table porte.

**Édite le fichier sur place.** Son en-tête doit survivre.

## Vérifier

```bash
dsoxlab check mysql-06-observer
```
