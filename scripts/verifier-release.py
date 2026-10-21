#!/usr/bin/env python3
"""Refuse de laisser poser un tag sur un arbre qui ne porte pas cette version.

Pourquoi ce script existe
-------------------------
Le 2026-10-21, un `v0.4.1` est parti sur `c6004bc`, c'est-à-dire sur l'arbre de
la 0.4.0 : la PR qui portait la 0.4.1 n'était pas encore fusionnée. La séquence
jouée était pourtant la bonne dans l'ordre et dans l'intention :

    git switch main && git pull     # ne ramène rien si la PR n'est pas fusionnée
    git tag -a v0.4.1 -m "..."      # ne dit rien de la version du pyproject
    git push origin v0.4.1          # le workflow Release part là-dessus

Aucune des trois commandes ne mesure quoi que ce soit. `pull` sur un `main` qui
n'a pas avancé réussit en silence, et `git tag` n'a aucune raison de connaître
`pyproject.toml`. Le workflow, lui, a construit un bundle signé et attesté du
mauvais contenu, et seule son annulation à la main a évité la publication.

Ce que le script contrôle, et dans cet ordre
--------------------------------------------
1. l'arbre est propre ;
2. on est sur `main`, et `main` est au niveau de `origin/main` ;
3. `pyproject.toml` porte EXACTEMENT la version demandée ;
4. les deux CHANGELOG portent une entrée pour cette version ;
5. le tag n'existe ni en local ni sur `origin` ;
6. `validation-labs.json` ne porte aucun lab qui ne soit pas VALIDE.

Le troisième contrôle est celui qui aurait suffi. Les autres sont là parce
qu'un garde-fou qui ne regarde qu'une chose finit par en laisser passer une
autre.

Usage :
    python3 scripts/verifier-release.py 0.4.1
    python3 scripts/verifier-release.py v0.4.1   # le « v » est accepté

Sort en 0 si tout va bien, en 1 au premier contrôle qui échoue, et en 2 s'il
n'a pas pu mesurer : « je n'ai rien pu vérifier » n'est pas « tout va bien ».
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    """Rend la sortie d'une commande git, ou sort en 2 si elle n'a pas répondu."""
    try:
        issue = subprocess.run(
            ["git", "-C", str(REPO), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as erreur:
        sys.exit(f"2|git {' '.join(args)} n'a pas répondu : {erreur}")
    if issue.returncode != 0:
        sys.exit(f"2|git {' '.join(args)} a échoué : {issue.stderr.strip()}")
    return issue.stdout.strip()


def echouer(message: str) -> None:
    print(f"✘ {message}")
    sys.exit(1)


def reussir(message: str) -> None:
    print(f"✔ {message}")


def version_du_pyproject() -> str:
    texte = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    trouve = re.search(r'^version\s*=\s*"([^"]+)"', texte, flags=re.M)
    if trouve is None:
        sys.exit("2|pyproject.toml ne porte aucune ligne version")
    return trouve.group(1)


def main(demande: str) -> None:
    version = demande.removeprefix("v")
    tag = f"v{version}"

    if git("status", "--porcelain", "--untracked-files=no"):
        echouer("l'arbre n'est pas propre : committer ou ranger avant de taguer")
    reussir("arbre propre")

    branche = git("rev-parse", "--abbrev-ref", "HEAD")
    if branche != "main":
        echouer(f"on est sur « {branche} », une version se tague depuis main")
    reussir("sur main")

    git("fetch", "--quiet", "origin", "main")
    local, distant = git("rev-parse", "HEAD"), git("rev-parse", "origin/main")
    if local != distant:
        echouer(
            f"main local ({local[:9]}) et origin/main ({distant[:9]}) diffèrent. "
            "Une PR pas encore fusionnée donne exactement cet écart, et un "
            "`git pull` y réussit sans rien ramener."
        )
    reussir(f"main au niveau de origin/main ({local[:9]})")

    portee = version_du_pyproject()
    if portee != version:
        echouer(
            f"pyproject.toml porte {portee}, pas {version}. C'EST LE CONTRÔLE "
            "QUI MANQUAIT : le commit tagué doit porter la version qu'on publie."
        )
    reussir(f"pyproject.toml porte bien {version}")

    for nom in ("CHANGELOG.md", "CHANGELOG.fr.md"):
        texte = (REPO / nom).read_text(encoding="utf-8")
        if f"## [{version}]" not in texte:
            echouer(f"{nom} n'a pas d'entrée « ## [{version}] »")
    reussir("les deux CHANGELOG portent l'entrée")

    if tag in git("tag", "--list", tag).splitlines():
        echouer(f"le tag {tag} existe déjà en local")
    if git("ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        echouer(
            f"le tag {tag} existe déjà sur origin. Republier une version, c'est "
            "DÉPLACER le tag, jamais relancer le run."
        )
    reussir(f"{tag} libre en local et sur origin")

    verdicts = REPO / "validation-labs.json"
    if not verdicts.exists():
        sys.exit("2|validation-labs.json absent : aucune attestation à lire")
    donnees = json.loads(verdicts.read_text(encoding="utf-8"))
    labs = donnees.get("labs", donnees)
    entrees = labs.values() if isinstance(labs, dict) else labs
    fautifs = [e["id"] for e in entrees if e.get("verdict") != "VALIDE"]
    if fautifs:
        echouer(f"labs non VALIDE dans validation-labs.json : {', '.join(fautifs)}")
    reussir(f"les {len(list(entrees))} labs sont VALIDE")

    print(f"\n{tag} peut être posé sur {local[:9]}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
