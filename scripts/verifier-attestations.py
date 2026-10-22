#!/usr/bin/env python3
"""Dit si chaque verdict vaut encore, en comparant des CONTENUS, pas des dates.

Ce que la commande rend, et c'est TROIS issues et non deux :

    atteste         l'empreinte du contenu est celle qui a ete mesuree
    PERIME          le contenu a change depuis : le verdict ne vaut plus
    NON MESURABLE   le verdict ne porte pas d'empreinte, donc on ne peut rien
                    en dire. Ce n'est pas « il va bien », et ce n'est pas non
                    plus « il est faux » : c'est « on ne sait pas ».

CE CONTROLE EST UNE CORROBORATION, PAS L'ARBITRE

Le controle de peremption qui fait foi vit cote site, et il compare deux arbres
git : `git diff <ancre>..HEAD -- <chemins du lab>`. Les arbres git SONT deja des
empreintes de contenu, et leur comparaison ne depend pas du chemin parcouru
pour arriver a HEAD : ni le squash, ni le rebase, ni le cherry-pick n'y
changent quoi que ce soit. Il n'y a donc rien a inscrire dans les quatorze
catalogues pour qu'il fonctionne, et c'est ce qui l'a fait preferer a une
empreinte calculee.

Ce verificateur-ci garde un role etroit : quand un releve PORTE une empreinte,
il dit si le contenu a bouge depuis. Il ne la reclame pas. Un verdict sans
empreinte n'est pas un defaut, c'est une corroboration qu'on n'a pas, et crier
sur les dix-sept labs d'un catalogue apprendrait surtout a ignorer la sortie.

Le cas que NI l'un NI l'autre ne peut rattraper apres coup, c'est une pull
request squashee qui retouche un test APRES sa campagne : le commit unique
porte les deux, et le squash a detruit l'information. Celui-la ne se mesure
pas, il s'empeche, et c'est le role du hook `verdicts-et-commun-separes`.

Codes de sortie :

    0   rien de perime (des empreintes peuvent manquer, c'est dit et c'est tout)
    1   au moins un PERIME          -> rejouer ces labs
    10  avec --strict seulement : au moins un verdict sans empreinte

Usage :
    python3 scripts/verifier-attestations.py
    python3 scripts/verifier-attestations.py --strict
    python3 scripts/verifier-attestations.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import empreinte_lab

RACINE = Path(__file__).resolve().parent.parent
VERDICTS = RACINE / "validation-labs.json"

# Doit rester identique a `PARTAGES` de `valider-labs.py` : deux listes qui
# divergent, et le verificateur conclut a la peremption de tout le catalogue
# au premier changement du commun.
PARTAGES: tuple[str, ...] = ("conftest.py",)

ATTESTE = "atteste"
PERIME = "PERIME"
NON_MESURABLE = "NON MESURABLE"

RC_TOUT_ATTESTE = 0
RC_UN_PERIME = 1
RC_UN_NON_MESURABLE = 10


def etat_des_labs() -> dict[str, dict[str, str]]:
    if not VERDICTS.is_file():
        sys.exit(f"2|{VERDICTS.name} absent : aucune attestation a lire")
    donnees = json.loads(VERDICTS.read_text(encoding="utf-8"))
    labs = donnees.get("labs", donnees)
    entrees = labs if isinstance(labs, dict) else {x["id"]: x for x in labs}

    etats: dict[str, dict[str, str]] = {}
    for identifiant, entree in sorted(entrees.items()):
        chemin = entree.get("chemin") or identifiant
        inscrite = entree.get("empreinte")
        if not inscrite:
            etats[identifiant] = {
                "etat": NON_MESURABLE,
                "pourquoi": "ce verdict ne porte pas d'empreinte : il date d'avant "
                "cette mesure, ou la campagne ne l'a pas inscrite",
                "date": entree.get("date", ""),
            }
            continue
        actuelle = empreinte_lab.empreinte(RACINE, chemin, PARTAGES)
        etats[identifiant] = {
            "etat": ATTESTE if actuelle == inscrite else PERIME,
            "pourquoi": ""
            if actuelle == inscrite
            else f"inscrite {inscrite[:12]}, actuelle {actuelle[:12]}",
            "date": entree.get("date", ""),
        }
    return etats


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--json", action="store_true", help="sortie machine")
    analyseur.add_argument(
        "--strict",
        action="store_true",
        help="sortir en 10 si un verdict ne porte pas d'empreinte",
    )
    options = analyseur.parse_args()

    etats = etat_des_labs()
    if options.json:
        print(json.dumps(etats, ensure_ascii=False, indent=2))
    else:
        for identifiant, e in etats.items():
            detail = f"  {e['pourquoi']}" if e["pourquoi"] else ""
            print(f"  {e['etat']:<14} {identifiant:<34} {e['date']}{detail}")
        print()

    perimes = [i for i, e in etats.items() if e["etat"] == PERIME]
    inconnus = [i for i, e in etats.items() if e["etat"] == NON_MESURABLE]
    attestes = len(etats) - len(perimes) - len(inconnus)

    if not options.json:
        print(f"{attestes} atteste(s), {len(perimes)} perime(s), {len(inconnus)} non mesurable(s)")

    if perimes:
        if not options.json:
            print(f"\nA REJOUER, leur contenu a change : {', '.join(perimes)}", file=sys.stderr)
        return RC_UN_PERIME
    if inconnus and not options.json:
        print(
            f"\n{len(inconnus)} verdict(s) sans empreinte. Ce n'est pas un defaut : "
            "l'empreinte\ns'inscrit a la prochaine campagne, et la peremption qui fait "
            "foi se mesure\ncote site en comparant deux arbres git, sans rien demander "
            "au catalogue."
        )
    if inconnus and options.strict:
        return RC_UN_NON_MESURABLE
    return RC_TOUT_ATTESTE


if __name__ == "__main__":
    sys.exit(main())
