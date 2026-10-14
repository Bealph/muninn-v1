"""Vérifie, sans rien créer, que chaque option des commandes az des scripts existe dans la
version locale d'az. À lancer avant les scripts : une option retirée par une mise à jour d'az
ferait échouer un script au milieu de la création des ressources.

Usage : python infra/azure/verifier-options.py infra/azure/0*.sh
"""

import pathlib
import re
import shutil
import subprocess
import sys

AZ = shutil.which("az") or sys.exit("az introuvable dans le PATH.")

texte = "\n".join(pathlib.Path(f).read_text(encoding="utf-8") for f in sys.argv[1:])
texte = re.sub(r"\\\n\s*", " ", texte)  # lignes continuées
# Sous-commandes imbriquées « $(az ...) » : contrôlées comme des lignes à part, puis masquées.
imbriquees = re.findall(r"\$\((az [^)]*)\)", texte)
texte = re.sub(r"\$\([^)]*\)", "X", texte) + "\n" + "\n".join(imbriquees)

cmds: dict[str, set[str]] = {}
for ligne in texte.splitlines():
    for m in re.finditer(r"\baz ((?:[a-z][a-z-]*\s+){1,5}?)(?=-)", ligne):
        groupe = m.group(1).strip()
        reste = ligne[m.end() :]
        fin = re.search(r"\baz |\|\||&&|\)|;", reste)
        reste = reste[: fin.start()] if fin else reste
        opts = set(re.findall(r"(?:^|\s)(--?[a-zA-Z][a-zA-Z-]*)(?=\s|=|$)", reste))
        cmds.setdefault(groupe, set()).update(opts)

manque = 0
for groupe, opts in sorted(cmds.items()):
    aide = subprocess.run(  # noqa: S603 (commande az fixe, groupes lus dans nos scripts)
        [AZ, *groupe.split(), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout
    declarees: set[str] = set()
    for ligne_aide in aide.splitlines():
        m = re.match(r"^\s{4}((?:-{1,2}[a-zA-Z][\w-]*\s*)+)", ligne_aide)
        if m:
            declarees.update(m.group(1).split())
    absentes = sorted(opts - declarees)
    manque += len(absentes)
    print(("ABSENT " + " ".join(absentes) if absentes else "ok") + " :: az " + groupe)
print("options absentes :", manque)
