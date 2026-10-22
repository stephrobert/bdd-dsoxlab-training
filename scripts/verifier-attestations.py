#!/usr/bin/env python3
"""Dit si chaque verdict vaut encore, en comparant des CONTENUS, pas des dates.

Ce que la commande rend, et c'est TROIS issues et non deux :

    atteste         l'empreinte du contenu est celle qui a ete mesuree
    PERIME          le contenu a change depuis : le verdict ne vaut plus
    NON MESURABLE   le verdict ne porte pas d'empreinte, donc on ne peut rien
                    en dire. Ce n'est pas « il va bien », et ce n'est pas non
                    plus « il est faux » : c'est « on ne sait pas ».

Codes de sortie, calques sur ceux de `dsoxlab doctor --strict`, ou 9 et 10 sont
distincts a dessein : le premier se repare, le second se remesure.

    0   tous attestes
    1   au moins un PERIME          -> rejouer ces labs
    10  au moins un NON MESURABLE   -> rejouer pour inscrire l'empreinte

Quand les deux coexistent, 1 l'emporte : une certitude est plus forte qu'une
ignorance.

Usage :
    python3 scripts/verifier-attestations.py
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
    if inconnus:
        if not options.json:
            print(
                f"\nSANS EMPREINTE, donc rien a conclure : {', '.join(inconnus)}\n"
                "Les rejouer inscrira leur empreinte.",
                file=sys.stderr,
            )
        return RC_UN_NON_MESURABLE
    return RC_TOUT_ATTESTE


if __name__ == "__main__":
    sys.exit(main())
