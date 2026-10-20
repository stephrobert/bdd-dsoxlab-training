# pg-09 : un secondaire en flux

## Ce que ce lab éprouve

Le premier lab du catalogue à **deux machines**. `db1.lab` est le primaire,
`db2.lab` le secondaire, et le lab est noté sur le **flux** entre les deux :
une ligne écrite sur le primaire doit être lisible sur le secondaire.

C'est le seul contrôle qui prouve quelque chose. Un `primary_conninfo` écrit,
un slot créé, une ligne `pg_hba` posée : tout cela peut être juste et rien ne
couler.

## Les quatre pièges qu'il fait rencontrer

**Le répertoire de données du secondaire doit être vide** avant la copie. Sur
Debian, l'installation initialise une grappe : `pg_basebackup` refuse d'écrire
dans un répertoire qui n'est pas vide, et le message ne dit pas qu'il faut
vider celui que le paquet vient de créer.

**Une ligne `pg_hba` ordinaire ne suffit pas.** La réplication est une base
virtuelle : il faut une ligne dont la colonne base vaut littéralement
`replication`, et `all` ne la couvre pas. C'est la faute la plus fréquente sur
ce sujet, et le message d'erreur parle d'une base qui n'existe pas.

**Sans slot, un secondaire déconnecté peut ne jamais revenir.** Le primaire
recycle ses journaux : s'il recycle ceux dont le secondaire a besoin, la
synchronisation est perdue et il faut refaire la copie de base. Le slot est ce
qui lui dit de les retenir.

**Une commande lancée sous un autre compte ne peut pas revenir d'où elle
part.** `find` sauvegarde son répertoire de départ et y revient en fin de
course : lancé en `postgres` depuis un répertoire personnel en 0700, il échoue
sur « Failed to restore initial working directory », et le message désigne ce
répertoire plutôt que la cause. Les deux comptes de ces machines ont un
répertoire en 0700, mesuré : la parade est de se placer dans `/tmp` d'abord.

## Ce qu'il ne couvre pas

Le basculement manuel (`pg_ctl promote`) et la réplication logique par
publication et souscription, que le guide traite et qui demandent chacun leur
propre lab. La réplication synchrone, qui change le comportement du primaire en
cas de panne du secondaire.

## Durée

50 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/replication/)
