# Ce qui est demandé

Sur `db1.lab`. Le collecteur de journaux est **déjà actif** : il est de contexte
`postmaster`, donc l'activer aurait exigé un redémarrage, et ce lab l'interdit.

## 1. Rendre les journaux exploitables

Trois paramètres, tous rechargeables, qui doivent être **effectifs** sur le
serveur en marche :

- un seuil de requête lente à **250 ms** (`log_min_duration_statement`) ;
- la journalisation des connexions, activée (`log_connections`) ;
- un préfixe de ligne (`log_line_prefix`) qui porte au moins l'horodatage
  (`%m`), l'identifiant de processus (`%p`), l'utilisateur et la base
  (`%u` et `%d`).

« Effectif » veut dire lu dans `pg_settings`, pas écrit dans un fichier. Un
paramètre présent dans `postgresql.auto.conf` mais jamais rechargé ne compte
pas.

## 2. Préparer le relèvement de `max_connections`

`max_connections` doit valoir **200** dans la configuration, et le serveur doit
tourner **encore avec 100**, en attente de son prochain démarrage.

C'est l'état normal d'un paramètre de contexte `postmaster` qu'on vient de
changer, et c'est ce que le lab demande : la fenêtre de redémarrage est prévue
pour cette nuit, pas maintenant.

## 3. Ne couper personne

Le serveur **ne doit pas avoir redémarré**. Une session ouverte par le setup
porte le nom applicatif `temoin-pg-03` : elle doit être encore là. Un
redémarrage la tue, et le test le voit.

Un `systemctl restart`, un `pg_ctl restart` ou un `reboot` font donc échouer le
lab, même si tous les paramètres sont justes.

## 4. Remplir le rapport

Le fichier `~/rapport-config.txt` porte trois valeurs à compléter, toutes lues
sur le serveur :

- `max_connections_effectif` : la valeur avec laquelle il tourne ;
- `max_connections_en_attente` : celle que les fichiers déclarent. Elle ne se
  lit pas au même endroit que la précédente ;
- `nb_parametres_en_attente` : combien de paramètres attendent un redémarrage.

**Édite le fichier sur place.** Son en-tête doit survivre : il disparaît si tu
le recrées avec une redirection `>`, et le test le refuse.

## Vérifier

```bash
dsoxlab check pg-03-configurer
```
