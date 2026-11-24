# Un serveur de base de données que personne n'a installé exprès

## La situation

L'équipe tient son inventaire dans un tableur et veut une vraie base de
données pour le remplacer. Quelqu'un a lancé `apt install postgresql` sur une
machine de test le mois dernier, et personne ne se souvient de la version
obtenue, d'où elle vient, ni si elle revient après un redémarrage.

La décision est prise : PostgreSQL 18, depuis le dépôt de paquets du projet
(PGDG), sur une machine Debian 13 neuve. Vous héritez de `db1.lab`. Elle est
vierge : aucun PostgreSQL, aucun dépôt pour lui.

## Mission

Mettre en service une instance que vous pourriez laisser en production.

Trois points comptent plus que de voir `psql` répondre.

Le premier est **l'origine des paquets**. Debian livre son propre PostgreSQL,
d'une version majeure plus ancienne. La version voulue vit dans un autre dépôt,
et vous ne lui faites confiance que si vous savez dire au système quelle clé le
signe.

Le deuxième est **ce qui survit à un redémarrage**. Un serveur lancé à la main
répond aujourd'hui et a disparu demain.

Le troisième est **ce que le serveur expose**. Une instance neuve ne doit pas
écouter le réseau : vous l'ouvrirez volontairement plus tard, quand vous saurez
à qui.

## Un PostgreSQL 18 que l'on peut laisser en production

Vous travaillez sur `db1.lab`, une machine Debian 13 vierge. Vous avez `sudo`.

### Ce qui est attendu

1. une **source PGDG** pour Debian 13 (`trixie-pgdg`) est déclarée dans APT et
   liée à une **clé de signature** (`Signed-By`) ; `apt-get update` passe sans
   aucune plainte de signature ;
2. le paquet **`postgresql-18`** est installé, issu de PGDG, et le serveur en
   marche annonce la même version ;
3. le **cluster `18/main` est en ligne**, son unité systemd est active, et il
   **démarre au boot** (le correcteur redémarre la machine) ;
4. **`pg_isready`** répond que le serveur accepte les connexions ;
5. les **sommes de contrôle des données sont actives**, pour le serveur en
   marche (`SHOW data_checksums`) comme sur le disque (`pg_controldata`) ;
6. le serveur **n'écoute que sur la boucle locale** : port 5432 sur
   `127.0.0.1` et `::1`, jamais sur une adresse externe.

### Ce qui est prouvé, et comment

Les tests ne lisent pas votre historique. Ils interrogent la machine : APT, la
base des paquets, systemd, le serveur par `psql`, et les sockets qui écoutent
vraiment. Vous pouvez atteindre le résultat par le chemin de votre choix.

Le dernier test vérifie que l'instance est toujours là après un redémarrage.

### Contraintes

- Restez sur PostgreSQL **18**, depuis PGDG. La version de Debian n'est pas la
  réponse.
- N'ouvrez pas le serveur au réseau : l'adresse d'écoute par défaut est la
  bonne.
- Pas de `trusted=yes` sur le dépôt : un dépôt sans clé n'est pas un dépôt que
  vous avez vérifié.

```bash
dsoxlab check pg-01-installer   # noter
dsoxlab hint  pg-01-installer   # un indice, au prix de points
```
