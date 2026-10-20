"""La documentation ne cite pas de commande qui n'existe pas.

POURQUOI CE FICHIER EXISTE

Le 2026-10-20, `RELEASING.md` prescrivait, dans les deux langues :

    python3 scripts/verify-solutions.py --deux-sens --check

Ce drapeau n'a jamais existé : le script accepte `--check` et `--negative`.
Quiconque suivait la procédure de release obtenait une erreur d'argument au
troisième point d'une liste de cinq, sans savoir si la faute venait de lui.

Une procédure qu'on ne peut pas suivre est pire qu'une procédure absente :
l'absence se remarque, le mensonge se contourne, et le contournement devient
la vraie procédure, celle que personne n'écrit.

CE QUE CE CONTRÔLE MESURE, ET CE QU'IL NE MESURE PAS

Il lit les drapeaux longs cités dans les fichiers Markdown du dépôt, et les
confronte à l'aide RÉELLE du script visé. C'est donc une mesure et non une
lecture : l'aide est produite par le script lui-même, pas recopiée.

Il ne dit pas que la commande fait ce que la phrase annonce, ni que la
procédure est complète. Il dit seulement qu'elle est jouable, ce qui est le
minimum qu'on devrait pouvoir supposer.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parent.parent

# Les drapeaux de la forme `--nom` ou `--nom=valeur`, sur une ligne qui invoque
# un script du dépôt. On s'arrête au premier `|` ou `>` : au-delà, la ligne
# parle d'un autre programme.
# `(?<![/\w.-])` borne le motif aux scripts DE CE DÉPÔT : un chemin précédé
# d'un séparateur, comme `../test-astro-5/scripts/reattester-labs.py`, désigne
# un script d'un autre dépôt, dont ce test ne peut rien savoir. Le dire dans le
# motif vaut mieux que de deviner le répertoire courant d'un bloc de code, ce
# qu'un test ne peut pas faire.
_INVOCATION = re.compile(
    r"(?<![/\w.-])(?:python3?\s+)?(scripts/[\w.-]+\.py)([^\n|>]*)",
)
_DRAPEAU = re.compile(r"(?<![\w-])--([a-z][a-z0-9-]*)")


def _lignes_citant_un_script() -> list[tuple[pathlib.Path, str, str]]:
    """Rend (fichier markdown, script cité, reste de la ligne)."""
    trouvees = []
    for markdown in sorted(RACINE.glob("*.md")):
        for ligne in markdown.read_text(encoding="utf-8").splitlines():
            for script, reste in _INVOCATION.findall(ligne):
                trouvees.append((markdown, script, reste))
    return trouvees


def _aide(script: pathlib.Path) -> str:
    """L'aide que le script PRODUIT, et non celle qu'on lui prête."""
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=RACINE,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return proc.stdout + proc.stderr


def test_la_documentation_cite_des_scripts_qui_existent() -> None:
    citations = _lignes_citant_un_script()
    assert citations, (
        "aucune invocation de script trouvée dans les Markdown : le motif de "
        "ce test ne reconnaît plus rien, donc il ne mesure plus rien"
    )
    absents = {
        f"{markdown.name} cite {script}"
        for markdown, script, _ in citations
        if not (RACINE / script).is_file()
    }
    assert not absents, "\n  ".join(["scripts cités et absents :", *sorted(absents)])


def test_aucun_drapeau_cite_n_est_inconnu_du_script() -> None:
    """Le cas de 2026-10-20 : `--deux-sens`, qui n'a jamais existé."""
    inconnus = []
    aides: dict[str, str] = {}
    for markdown, script, reste in _lignes_citant_un_script():
        chemin = RACINE / script
        if not chemin.is_file():
            continue  # déjà dit par le test précédent
        if script not in aides:
            aides[script] = _aide(chemin)
        for drapeau in _DRAPEAU.findall(reste):
            if f"--{drapeau}" not in aides[script]:
                inconnus.append(f"{markdown.name} : {script} --{drapeau}")

    assert not inconnus, "\n  ".join(
        [
            "drapeaux cités dans la documentation et inconnus du script :",
            *sorted(inconnus),
            "",
            "Une procédure qu'on ne peut pas suivre est pire qu'une procédure",
            "absente. Corrige la documentation, ou ajoute le drapeau.",
        ]
    )


@pytest.mark.parametrize("script", ["scripts/verify-solutions.py"])
def test_le_controle_des_deux_sens_porte_bien_ce_nom(script: str) -> None:
    """Le drapeau qui a motivé ce fichier, nommé pour qu'on ne le reperde pas.

    `--negative` est le contrôle des deux sens : il rejoue les tests SANS la
    solution, et ils doivent alors échouer. Un test qui passe dans les deux
    sens ne prouve rien.
    """
    aide = _aide(RACINE / script)
    assert "--negative" in aide, (
        f"{script} n'offre plus `--negative` : si le contrôle des deux sens a "
        "changé de nom, RELEASING.md doit changer avec lui, dans les DEUX "
        "langues."
    )
