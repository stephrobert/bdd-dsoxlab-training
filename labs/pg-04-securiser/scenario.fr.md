# Chiffré « quand le client veut bien »

L'audit interne est passé sur `db1.lab`. Deux constats, et ils se ressemblent
plus qu'il n'y paraît.

Le premier : les connexions de l'application **peuvent** être chiffrées, mais
rien ne l'exige. La ligne réseau de `pg_hba.conf` est un `host`, qui accepte
indifféremment une session chiffrée et une session en clair. C'est donc le
client qui décide, et un client mal configuré ne s'en aperçoit jamais. Le
certificat présenté, lui, est celui que Debian a posé à l'installation, le même
sur toutes les machines du parc.

Le second : le rôle `appli` est **propriétaire** de son schéma et de ses tables.
Il peut donc les supprimer, et l'application tourne avec ce droit en
permanence. Un outil de reporting qui ne fait que lire se connecte avec le même
rôle, faute d'en avoir un autre.

On te demande de fermer les deux. Le serveur doit refuser une connexion non
chiffrée, et les droits doivent être séparés : qui crée, qui écrit, qui lit.

Attention à un détail que le guide signale : sur Debian, `ssl = on` est déjà
actif. Activer SSL ne changera donc rien, et ce n'est pas ce qu'on te demande.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/)
