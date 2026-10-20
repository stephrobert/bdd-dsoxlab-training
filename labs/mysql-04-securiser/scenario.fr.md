# Un compte applicatif qui peut tout, et sur un canal en clair

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
