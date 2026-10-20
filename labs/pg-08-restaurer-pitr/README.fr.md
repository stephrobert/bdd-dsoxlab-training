# pg-08 : restaurer à un instant donné

## Ce que ce lab éprouve

Le geste qui donne un sens à tout ce qui précède. Une sauvegarde physique seule
ramène à l'heure de la sauvegarde ; les journaux seuls ne ramènent nulle part.
Ensemble, ils ramènent à **l'instant qu'on choisit**, et c'est ce choix que le
lab note.

Trois points d'arrivée sont possibles, et deux sont faux :

- la sauvegarde physique seule : la dernière ligne insérée avant l'incident
  manque ;
- le dernier WAL disponible : le `DROP TABLE` est rejoué, donc on reproduit
  l'incident ;
- l'instant noté juste avant : le seul qui rende la base utilisable.

## Le piège qu'il fait rencontrer

Il n'y a **plus de `recovery.conf`** depuis PostgreSQL 12. Les paramètres de
restauration vivent dans `postgresql.conf`, et c'est le fichier
**`recovery.signal`** qui déclenche le mode restauration au démarrage. Un
apprenant qui a appris PostgreSQL avant la 12, ou qui lit un billet daté, écrit
un fichier que le serveur ignore, et conclut que le PITR ne marche pas.

Second piège, moins connu : le serveur s'arrête **en pause** une fois la cible
atteinte, parce que `recovery_target_action` vaut `pause` par défaut. La base
est alors en lecture seule et paraît inachevée. Il faut soit reprendre la main
(`pg_wal_replay_resume()`), soit avoir demandé `promote` dès le départ.

## Comment il est noté, et pourquoi

Sur les données **et** sur la **timeline**. Une restauration menée à son terme
promeut la grappe, et une promotion incrémente la timeline : une grappe neuve
est en 1, une grappe restaurée et promue est en 2.

C'est ce qui permet de noter le geste plutôt que son résultat apparent. Sans ce
contrôle, recréer la table à la main passerait tous les autres.

## Ce qu'il ne couvre pas

La restauration ciblée par identifiant de transaction (`recovery_target_xid`)
ou par point nommé (`recovery_target_name`), qui suivent la même mécanique.
pgBackRest, qui automatise tout ceci et que le guide range ailleurs.

## Durée

50 minutes. Les indices coûtent de 5 à 20 points. C'est une épreuve : le seuil
de réussite est à 80 %.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/sauvegarde-restauration/)
