"""Refuse une commande dont un saut de ligne survit au repli YAML.

POURQUOI CE SCRIPT EXISTE
-------------------------
Dans un scalaire replié (``>``), un saut de ligne N'EST PAS replié en espace
dès que l'une des deux lignes qu'il sépare est plus indentée que la première.
C'est la règle de YAML, et elle surprend à chaque fois.

Le saut est inoffensif quand il tombe DANS une chaîne entre guillemets, ce qui
est le cas de tout le SQL multiligne de ce catalogue : PostgreSQL accepte les
sauts de ligne. Il est FATAL dès qu'il tombe entre deux mots du shell, et le
message ne parle alors ni de YAML ni d'indentation.

Vécu deux fois le 2026-10-19, sur le même dépôt :

- la solution de pg-05 comparait deux comptes avec ``test "$(...)" = "$(...)"``
  sur deux lignes alignées sur le ``=``. La commande cassait en morceaux,
  ``psql -c`` se retrouvait sans argument, et bash tentait d'exécuter le SQL.
  Le lab sortait ROUGE sans que rien ne désigne la cause ;
- le setup de pg-04 terminait par ``2>/dev/null || true`` sur sa propre ligne.
  C'était donc une COMMANDE SÉPARÉE, qui réussit toujours : l'échec du psql
  était avalé par accident et non par intention. Le lab passait, pour la
  mauvaise raison, ce qui est le pire des deux cas.

CE QUE LE CONTRÔLE MESURE
-------------------------
Le RÉSULTAT du repli, pas la forme du YAML. Le fichier est chargé, les
commandes sont prises telles que Ansible les recevra, et on regarde où tombent
les sauts restants. Contrôler l'indentation du source dirait « c'est bizarre » ;
contrôler la commande obtenue dit « elle est cassée ».

Le saut FINAL, que ``>`` ajoute toujours, est écarté : il ne sépare pas deux
mots.

Usage :
    python3 scripts/auditer-replis-yaml.py     # sort en 1 s'il reste un cas
"""

from __future__ import annotations

import pathlib
import sys

import yaml

CLES = ("ansible.builtin.command", "ansible.builtin.shell", "command", "shell")
fautifs = []


def examiner(chemin: pathlib.Path, cmd: str, nom: str) -> None:
    if "\n" not in cmd:
        return
    # Un saut DANS une chaine entre guillemets est sans effet : on compte les
    # guillemets qui precedent chaque saut, un nombre impair voulant dire
    # « on est dedans ».
    for position in (i for i, c in enumerate(cmd) if c == "\n"):
        avant = cmd[:position]
        # Le saut FINAL, que `>` ajoute toujours, est inoffensif : il ne separe
        # pas deux mots. Seul un saut suivi d'autre chose compte.
        if not cmd[position + 1:].strip():
            continue
        if (avant.count('"') % 2 == 0) and (avant.count("'") % 2 == 0):
            fautifs.append((chemin, nom, repr(cmd[max(0, position - 45): position + 15])))
            return


def a_examiner() -> list[pathlib.Path]:
    """Les fichiers nommes en argument, sinon tous ceux du depot.

    Les solutions sont CHIFFREES dans le depot : les parcourir rendrait du
    bruit base64 et jamais un verdict, d'ou leur exclusion du parcours par
    defaut. Elles se controlent en clair, en donnant leur chemin en argument.
    """
    if len(sys.argv) > 1:
        return [pathlib.Path(x) for x in sys.argv[1:]]
    return [
        c
        for c in sorted(pathlib.Path(".").rglob("*.yaml"))
        if ".git" not in c.parts and "solution" not in c.parts
    ]


for chemin in a_examiner():
    try:
        charge = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(charge, list):
        continue
    for play in charge:
        if not isinstance(play, dict):
            continue
        for tache in play.get("tasks", []) or []:
            if not isinstance(tache, dict):
                continue
            for cle in CLES:
                bloc = tache.get(cle)
                valeur = bloc.get("cmd") if isinstance(bloc, dict) else bloc
                if isinstance(valeur, str):
                    examiner(chemin, valeur, tache.get("name", "?"))

if fautifs:
    print(f"{len(fautifs)} commande(s) dont un saut de ligne tombe hors chaine :\n")
    for chemin, nom, extrait in fautifs:
        print(f"  {chemin}\n    tache : {nom}\n    autour: {extrait}\n")
    sys.exit(1)
print("aucune commande cassee par le repli YAML")
