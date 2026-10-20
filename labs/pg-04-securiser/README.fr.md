# pg-04 : refuser le clair, et séparer les droits

## Ce que ce lab éprouve

Deux durcissements que l'on croit faits alors qu'ils ne le sont pas.

**Le chiffrement.** `ssl = on` sur un serveur dont la ligne `pg_hba.conf` est un
`host` ne protège rien : la session est chiffrée si le client le demande, et en
clair s'il ne le demande pas. Le lab est noté sur le comportement, pas sur le
réglage : une connexion `sslmode=disable` doit **échouer**, et une connexion
chiffrée doit aboutir en se déclarant chiffrée dans `pg_stat_ssl`.

**Le moindre privilège.** Le motif du guide, trois rôles-groupes sans droit de
connexion : qui crée, qui écrit, qui lit. Les privilèges sont lus dans le
catalogue, pas dans un fichier `.sql` laissé sur le disque.

## Les deux pièges qu'il fait rencontrer

`hostssl` sans `ssl = on` est **silencieusement ignoré**, avec un simple
avertissement dans le journal. Et l'inverse se tient aussi : `ssl = on` sans
`hostssl` ne force rien. Les deux réglages ne valent qu'ensemble, et c'est
justement le genre de couple qu'un audit de fichiers déclare conforme.

Sans `DEFAULT PRIVILEGES`, chaque **future** table créée par le propriétaire
n'aura aucun droit pour les deux autres rôles. Tout sera juste le jour de la
mise en place, et faux à la première migration.

## Ce qu'il ne couvre pas

Une PKI : le certificat est auto-signé, donc `verify-full` échoue par
construction, et c'est dit. Les politiques de ligne (`Row-Level Security`) et
OAuth, que le guide range en cas avancés.

Et deux contrôles que le guide donne comme **déjà acquis** sur cette grappe,
donc hors note : `ssl = on`, posé par Debian, et la révocation de `CREATE` sur
le schéma `public`, faite d'office depuis PostgreSQL 15.

## Durée

40 minutes. Les indices coûtent de 5 à 20 points.

Le guide : [https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/postgresql/securisation/)
