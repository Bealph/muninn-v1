"""Schémas de `infra/azure/README.md` : blocs ASCII et planches dessinées.

Les blocs du README et les planches de `infra/azure/schemas/generer.py` sont deux mises en forme
de la même lecture des scripts ; ces tests gardent les images versionnées à jour.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

RACINE = Path(__file__).resolve().parents[1]
GENERER = RACINE / "infra" / "azure" / "schemas" / "generer.py"
ATTENDUS = ("1-chaine-de-livraison", "2-deployer", "3-workflows-manuels", "4-mise-en-place",
            "5-execution")  # fmt: skip


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generer", GENERER)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def blocs() -> dict[str, str]:
    m = module()
    resultat: dict[str, str] = m.schemas(m.README.read_text(encoding="utf-8"))
    return resultat


def test_un_bloc_et_une_planche_par_schema() -> None:
    assert tuple(blocs()) == ATTENDUS
    assert tuple(module().PLANCHES) == ATTENDUS


def test_chaque_svg_est_a_jour() -> None:
    m = module()
    for nom in ATTENDUS:
        fichier = m.DOSSIER / "svg" / f"{nom}.svg"
        assert fichier.read_text(encoding="utf-8") == m.svg(nom), (
            f"{fichier.name} périmé : relancer infra/azure/schemas/generer.py --png"
        )


def test_chaque_png_existe() -> None:
    m = module()
    for nom in ATTENDUS:
        image = m.DOSSIER / "png" / f"{nom}.png"
        assert image.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", image.name


def test_aucun_fichier_orphelin() -> None:
    m = module()
    for dossier, ext in (("svg", ".svg"), ("png", ".png")):
        assert {f.stem for f in (m.DOSSIER / dossier).glob(f"*{ext}")} == set(ATTENDUS)


def test_boites_alignees() -> None:
    # Une ligne bordée de « | » aux deux bouts a la longueur d'une ligne de cadre bordée de « + » :
    # sinon son bord droit sort de la boîte (défaut constaté le 26 octobre 2026).
    for nom, bloc in blocs().items():
        lignes = bloc.split("\n")
        cadres = {len(x) for x in lignes if x.startswith("+") and x.endswith("+")}
        for ligne in lignes:
            if ligne.startswith("|") and ligne.endswith("|"):
                assert len(ligne) in cadres, f"{nom} : {ligne!r}"


def test_texte_echappe() -> None:
    m = module()
    planche = m.Planche(1, "Essai <a> & « b »")
    rendu = planche.svg("essai")
    assert "Essai &lt;a&gt; &amp; « b »" in rendu
    assert "<a>" not in rendu
