"""L'empreinte de ce qu'un verdict a REELLEMENT mesure.

CE FICHIER EST DESTINE A ETRE IDENTIQUE DANS TOUS LES CATALOGUES, comme
`verdict_check.py` l'est deja. Ne le modifier que pour le repercuter partout :
douze variantes d'une meme mesure, c'est douze reponses differentes a la meme
question.

POURQUOI IL EXISTE
------------------
La peremption d'un verdict se mesurait par des DATES : un lab etait « a
reattester » des qu'un commit posterieur a son verdict touchait ses fichiers.
Cette comparaison repond a une autre question que celle qu'on croit poser, et
elle s'est trompee DANS LES DEUX SENS le 2026-10-22.

FAUX NEGATIF, le sens dangereux. Une correction de `labs/_commun/` et les
verdicts qu'elle rendait caducs ont ete commites ENSEMBLE. Aucun verdict
n'etait posterieur a quoi que ce soit, le controle a conclu que tout allait
bien, et vingt et un verdicts VALIDE ne valaient plus rien.

FAUX POSITIF. Trois labs reattestes la veille sur une branche sont ressortis
« a reattester » apres la fusion, parce que le SQUASH ecrase la branche en un
commit date de la fusion. Leur contenu n'avait pas bouge d'un octet. Et ce
n'est pas un accident : dans un depot qui ne fusionne qu'en squash, TOUT lab
atteste sur une branche ressort perime apres sa PR.

La question n'est pas « ce fichier a-t-il ete touche apres le verdict », elle
est **« le contenu est-il encore celui qui a ete atteste »**. Une empreinte y
repond directement, et elle survit au squash, au rebase et a toute reecriture
d'historique, parce qu'elle ne regarde pas l'historique.

CE QU'ELLE COUVRE, ET POURQUOI CELA ET RIEN D'AUTRE
---------------------------------------------------
Uniquement ce que le CYCLE JOUE, c'est-a-dire ce dont la validite du verdict
depend reellement :

    lab.yaml              le runtime, les targets, le type de lab
    setup.yaml            l'etat de depart, donc le « 0 avant »
    cleanup.yaml          la remise a zero entre deux cycles
    challenge/tests/**    la mesure elle-meme
    les chemins partages  conftest.py, labs/_commun/… selon le catalogue

L'ENONCE EN EST EXCLU, et c'est un choix motive : `README.md`, `scenario.md`,
`hints.yaml` et `lab.fr.yaml` ne sont pas executes par le cycle. Corriger une
coquille dans un enonce ne change pas ce que les tests mesurent, et faire
basculer vingt et un labs en « a reattester » pour une faute d'orthographe
apprendrait surtout a ignorer le statut.

Le risque assume de ce choix : un enonce qui demanderait autre chose que ce que
les tests verifient ne serait pas signale ici. Ce n'est pas le role de cette
empreinte, c'est celui du controle de bareme de `validate-structure`, qui
compare les taches annoncees au nombre de tests.

La SOLUTION de reference en est exclue aussi, bien qu'elle soit jouee : elle
est chiffree, donc son octet change a chaque rechiffrement sans que son
contenu change. Une solution fausse ressort de toute facon en ROUGE au cycle
suivant, qui la rejoue.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# Ce que le cycle joue, relatif au repertoire du lab. Un repertoire est pris
# entierement, un fichier tel quel.
CE_QUI_EST_JOUE = (
    "lab.yaml",
    "setup.yaml",
    "cleanup.yaml",
    "challenge/tests",
)

# Ce qu'on ne lit jamais : volatil, ou appartenant a l'apprenant.
ECARTES = ("__pycache__", ".pytest_cache", ".ruff_cache", "work")
SUFFIXES_ECARTES = (".pyc", ".pyo")


def _fichiers(racine: Path) -> list[Path]:
    """Les fichiers stables sous `racine`, qui peut etre un fichier."""
    if not racine.exists():
        return []
    if racine.is_file():
        return [racine]
    retenus = []
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file():
            continue
        parties = chemin.relative_to(racine).parts
        if any(p in ECARTES for p in parties):
            continue
        if chemin.suffix in SUFFIXES_ECARTES:
            continue
        retenus.append(chemin)
    return retenus


def _nommer(base: Path, chemin: Path, prefixe: str) -> str:
    if base.is_file():
        return prefixe
    return f"{prefixe}/{chemin.relative_to(base).as_posix()}"


def empreinte(racine_depot: Path, chemin_lab: str, partages: tuple[str, ...] = ()) -> str:
    """Le sha256 de ce que le cycle joue pour ce lab.

    `chemin_lab` est relatif a `labs/`, comme dans `validation-labs.json`.
    `partages` nomme les chemins communs a inclure, relatifs a la racine du
    depot : au moins `conftest.py`, et `labs/_commun` la ou il existe.

    Le NOM de chaque fichier entre dans le calcul autant que son contenu :
    sans lui, renommer un test sans le modifier laisserait l'empreinte
    inchangee, alors que le lab ne joue plus le meme fichier.
    """
    cibles: list[tuple[str, Path]] = []

    base_lab = racine_depot / "labs" / chemin_lab
    for relatif in CE_QUI_EST_JOUE:
        cible = base_lab / relatif
        prefixe = f"labs/{chemin_lab}/{relatif}"
        for f in _fichiers(cible):
            cibles.append((_nommer(cible, f, prefixe), f))

    for partage in partages:
        cible = racine_depot / partage
        for f in _fichiers(cible):
            cibles.append((_nommer(cible, f, partage), f))

    condensat = hashlib.sha256()
    for nom, chemin in sorted(cibles):
        condensat.update(nom.encode("utf-8"))
        condensat.update(b"\0")
        condensat.update(chemin.read_bytes())
        condensat.update(b"\0")
    return condensat.hexdigest()
