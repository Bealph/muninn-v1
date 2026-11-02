"""Schémas dessinés de la chaîne de livraison et de l'exécution (sprint 5).

Cinq planches au format 16:9 (`svg/<nom>.svg`, et `png/<nom>.png` avec `--png`), qui reprennent
les blocs de `infra/azure/README.md`, section « Schémas » : même contenu, mis en forme pour la
soutenance. Comme les blocs, ce sont des lectures datées (26 octobre 2026) des scripts et des
workflows, qui font foi.

Code des couleurs : vert foncé, ce que Muninn exécute ; contour vert vif, le point central d'une
planche ; gris, un service extérieur à l'application ; rouge, un point d'attention ; pointillés, un
groupe (déclenchement ou planification à part).

Usage : `uv run python infra/azure/schemas/generer.py [--png]` ; le PNG demande le navigateur de
Playwright (`uv run playwright install chromium`). Sortie déterministe : le test
`tests/test_schemas.py` refuse un SVG qui ne correspond plus à ce fichier.
"""

import re
import sys
from collections.abc import Callable
from pathlib import Path
from xml.sax.saxutils import escape

DOSSIER = Path(__file__).resolve().parent
README = DOSSIER.parent / "README.md"
BLOC = re.compile(r"<!-- schema: ([a-z0-9-]+) -->\n```text\n(.*?)\n```", re.S)

LARGEUR, HAUTEUR = 1600, 1000
BANDEAU = "MUNINN · INFRASTRUCTURE AZURE · V1"
POLICE = "'Segoe UI', 'DejaVu Sans', Arial, sans-serif"
FONCE, VIF, FOND, GRIS, ROUGE, TEXTE = (
    "#0f4d3a",
    "#2fbf71",
    "#eef4f1",
    "#8a8f8c",
    "#d7192e",
    "#0f4d3a",
)
STYLES = {  # fond, contour, épaisseur, couleur du texte
    "fonce": (FONCE, FONCE, 1, "#ffffff"),
    "vif": (FONCE, VIF, 4, "#ffffff"),
    "clair": ("#ffffff", FONCE, 2, TEXTE),
    "gris": (GRIS, GRIS, 1, "#ffffff"),
    "rouge": (ROUGE, ROUGE, 1, "#ffffff"),
}


def schemas(texte: str) -> dict[str, str]:
    """Les blocs ASCII du README, par nom, dans l'ordre du document."""
    return dict(BLOC.findall(texte))


class Planche:
    """Une planche SVG : en-tête, boîtes, groupes, flèches, notes."""

    def __init__(
        self, numero: int, titre: str, *, bandeau: str = BANDEAU, repere: str | None = None
    ) -> None:
        self.elements: list[str] = []
        self.titre = titre
        self.texte(60, 62, bandeau, 16, VIF, gras=True, espacement=3)
        self.texte(60, 118, titre, 40, FONCE, gras=True)
        self.texte(LARGEUR - 60, 62, repere or f"{numero} / 5", 16, GRIS, gras=True, ancre="end")

    def texte(
        self, x: float, y: float, contenu: str, taille: int, couleur: str, *, gras: bool = False,
        ancre: str = "start", italique: bool = False, espacement: int = 0,
    ) -> None:  # fmt: skip
        attributs = f'x="{x}" y="{y}" font-size="{taille}" fill="{couleur}" text-anchor="{ancre}"'
        if gras:
            attributs += ' font-weight="700"'
        if italique:
            attributs += ' font-style="italic"'
        if espacement:
            attributs += f' letter-spacing="{espacement}"'
        self.elements.append(f"<text {attributs}>{escape(contenu)}</text>")

    def boite(self, x: float, y: float, larg: float, h: float, lignes: list[str],
              style: str = "fonce") -> None:  # fmt: skip
        fond, contour, epaisseur, couleur = STYLES[style]
        self.elements.append(
            f'<rect x="{x}" y="{y}" width="{larg}" height="{h}" rx="8" fill="{fond}" '
            f'stroke="{contour}" stroke-width="{epaisseur}"/>'
        )
        hauteurs = [19 if i == 0 else 16 for i in range(len(lignes))]
        total = sum(hauteurs) + 6 * (len(lignes) - 1)
        y_ligne = y + (h - total) / 2
        for i, (ligne, taille) in enumerate(zip(lignes, hauteurs, strict=True)):
            y_ligne += taille
            self.texte(x + larg / 2, y_ligne - 3, ligne, taille - 2 if i else taille, couleur,
                       gras=i == 0, ancre="middle")  # fmt: skip
            y_ligne += 6

    def groupe(self, x: float, y: float, larg: float, h: float, titre: str, *,
               pointille: bool = False) -> None:  # fmt: skip
        tirets = ' stroke-dasharray="10 7"' if pointille else ""
        self.elements.append(
            f'<rect x="{x}" y="{y}" width="{larg}" height="{h}" rx="12" fill="{FOND}" '
            f'stroke="{FONCE}" stroke-width="2"{tirets}/>'
        )
        self.texte(x + larg / 2, y + 30, titre, 17, FONCE, gras=True, ancre="middle")

    def fleche(self, *points: tuple[float, float], couleur: str = FONCE,
               pointille: bool = False) -> None:  # fmt: skip
        trace = " ".join(f"{x},{y}" for x, y in points)
        tirets = ' stroke-dasharray="7 5"' if pointille else ""
        marque = "pointe-rouge" if couleur == ROUGE else "pointe"
        self.elements.append(
            f'<polyline points="{trace}" fill="none" stroke="{couleur}" stroke-width="3"'
            f'{tirets} marker-end="url(#{marque})"/>'
        )

    def trait(self, *points: tuple[float, float]) -> None:
        trace = " ".join(f"{x},{y}" for x, y in points)
        self.elements.append(
            f'<polyline points="{trace}" fill="none" stroke="{FONCE}" stroke-width="3"/>'
        )

    def etiquette(self, x: float, y: float, contenu: str, *, ancre: str = "middle",
                  couleur: str = "#1f6b4f") -> None:  # fmt: skip
        self.texte(x, y, contenu, 14, couleur, italique=True, ancre=ancre)

    def note(self, y: float, contenu: str) -> None:
        self.elements.append(
            f'<rect x="60" y="{y}" width="{LARGEUR - 120}" height="56" rx="8" fill="#ffffff" '
            f'stroke="{ROUGE}" stroke-width="2" stroke-dasharray="10 7"/>'
        )
        self.texte(84, y + 35, contenu, 17, ROUGE, gras=True)

    def svg(self, nom: str) -> str:
        pointes = "".join(
            f'<marker id="{ident}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
            f'fill="{couleur}"/></marker>'
            for ident, couleur in (("pointe", FONCE), ("pointe-rouge", ROUGE))
        )
        return "\n".join([
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{LARGEUR}" height="{HAUTEUR}" '
            f'viewBox="0 0 {LARGEUR} {HAUTEUR}" role="img" aria-labelledby="titre">',
            f'<title id="titre">{escape(self.titre)} ({escape(nom)})</title>',
            f"<defs>{pointes}</defs>",
            f'<rect width="{LARGEUR}" height="{HAUTEUR}" fill="#ffffff"/>',
            f'<g font-family="{escape(POLICE)}">',
            *self.elements,
            "</g>",
            "</svg>",
            "",
        ])  # fmt: skip


def chaine_de_livraison() -> Planche:
    p = Planche(1, "Chaîne de livraison : workflow ci")
    p.groupe(40, 250, 230, 250, "Déclencheurs")
    p.boite(65, 300, 180, 70, ["Pull request", "vers main"])
    p.boite(65, 400, 180, 70, ["Fusion sur main", "(push)"])
    p.fleche((270, 375), (318, 375))
    p.groupe(320, 160, 800, 750, "GitHub Actions · workflow ci")
    p.boite(350, 215, 170, 80, ["lint", "ruff · mypy strict"])
    p.boite(560, 215, 220, 80, ["tests", "PostgreSQL 16 · axe-core"])
    p.boite(820, 215, 270, 80, ["build", "image + test de fumée"])
    p.fleche((520, 255), (558, 255))
    p.fleche((780, 255), (818, 255))
    p.boite(350, 340, 260, 110, ["evaluation", "si l'empreinte change",
                                 "id-muninn-evaluation", "1 € au plus"])  # fmt: skip
    p.boite(640, 340, 190, 110, ["secrets", "gitleaks", "tout l'historique"])
    p.boite(860, 340, 230, 110, ["test · hors de main", "image → crmuninntest",
                                 "ca-muninn-api-test", "id-muninn-test"])  # fmt: skip
    p.fleche((590, 295), (590, 338))
    p.fleche((975, 295), (975, 338))
    p.fleche((480, 450), (480, 480), (620, 480), (620, 498))
    p.fleche((735, 450), (735, 498))
    p.fleche((975, 450), (975, 480), (840, 480), (840, 498))
    p.fleche((1090, 255), (1105, 255), (1105, 550), (882, 550))
    p.boite(560, 500, 320, 100, ["verdict", "attend lint, tests, build, secrets,",
                                 "evaluation et test (hors de main)"], "vif")  # fmt: skip
    p.etiquette(1000, 590, "PR : s'arrête ici", ancre="middle")
    p.groupe(350, 640, 740, 250, "Livraison continue · push sur main seulement", pointille=True)
    p.fleche((720, 600), (720, 620), (362, 620), (362, 780), (373, 780))
    p.boite(375, 700, 320, 160, ["preproduction", "OIDC id-muninn-deploiement",
                                 "image muninn:<sha> → crmuninn",
                                 "deployer.sh preproduction <sha>"])  # fmt: skip
    p.boite(760, 700, 305, 160, ["production", "même image, non reconstruite",
                                 "deployer.sh production <sha>"])  # fmt: skip
    p.fleche((695, 780), (758, 780))
    p.etiquette(727, 770, "si vert")
    externes = [
        (215, ["crmuninn", "registre d'images"]),
        (305, ["Foundry · modèle", "evaluation · app. de test"]),
        (395, ["Langfuse", "projet muninn-evaluation"]),
        (485, ["crmuninntest", "ca-muninn-api-test"]),
        (705, ["Container Apps", "préproduction"]),
        (795, ["Container Apps", "production"]),
    ]
    p.trait((1120, 540), (1150, 540))
    p.trait((1150, 250), (1150, 830))
    for y, lignes in externes:
        p.fleche((1150, y + 35), (1178, y + 35))
        p.boite(1180, y, 360, 70, lignes, "gris")
    p.note(925, "À noter : ni étiquette de version ni canari ; la production suit la"
                " préproduction ; la livraison ne migre pas la base.")  # fmt: skip
    return p


def deployer() -> Planche:
    p = Planche(2, "Livraison dans un environnement : deployer.sh <env> <sha>")
    p.etiquette(60, 170, "Pour ca-muninn-api-<env>, puis pour ca-muninn-console-<env>",
                ancre="start")  # fmt: skip
    p.boite(60, 200, 260, 80, ["rien à livrer", "pas une erreur (INC-03)"], "gris")
    p.boite(60, 360, 260, 120, ["0. image <sha>", "déjà en service ?"], "clair")
    p.fleche((190, 360), (190, 282))
    p.etiquette(210, 325, "oui", ancre="start")
    p.fleche((320, 420), (378, 420))
    p.etiquette(349, 400, "non")
    p.boite(380, 360, 260, 120, ["1. trafic figé", "100 % sur la révision", "en service"])
    p.fleche((640, 420), (698, 420))
    p.boite(700, 360, 300, 120, ["2. nouvelle révision", "update --image <sha> · 0 %",
                                 "nom relu (INC-07)"])  # fmt: skip
    p.fleche((1000, 420), (1058, 420))
    p.boite(1060, 340, 300, 160, ["3. contrôle à son adresse", "API : /health · /version",
                                  "POST /llm/essai (modèle A)",
                                  "console : /health · SHA affiché"], "vif")  # fmt: skip
    p.fleche((1360, 420), (1398, 420), couleur=ROUGE)
    p.etiquette(1380, 398, "échec", couleur=ROUGE)
    p.boite(1400, 360, 160, 120, ["échec", "trafic laissé sur", "la précédente", "arrêt"],
            "rouge")  # fmt: skip
    p.fleche((1210, 500), (1210, 568))
    p.etiquette(1230, 540, "ok", ancre="start")
    p.boite(1060, 570, 300, 110, ["4. bascule 100 %", "précédente active à 0 %",
                                  "(retour arrière possible)"])  # fmt: skip
    p.groupe(60, 720, 1480, 160, "Puis, les deux applications livrées")
    p.boite(90, 775, 680, 80, ["job-muninn-donnees-<env>", "image <sha>, si la tâche existe"])
    p.boite(
        830, 775, 680, 80, ["contrôle final", "/health des adresses publiques · /version = <sha>"]
    )
    p.note(910, "Un contrôle en échec arrête la livraison : la production n'est jamais touchée"
                " si la préproduction échoue.")  # fmt: skip
    return p


def workflows_manuels() -> Planche:
    p = Planche(3, "Workflows manuels et planification")
    colonnes = [
        (60, "retour-arriere · workflow manuel", False, [
            ["entrées", "environnement · sha (facultatif)"],
            ["cible de l'API", "la révision précédente, ou ce commit"],
            ["console", "alignée sur le même commit"],
            ["bascule", "révision réactivée si besoin · 100 %"],
            ["contrôle", "/version · durée mesurée"],
        ]),
        (570, "donnees · workflow manuel", False, [
            ["entrée", "environnement"],
            ["job-muninn-donnees-<env>", "lancé, suivi jusqu'au terme"],
            ["dans la tâche", "migrations · rôles · ingestion"],
            ["jeu de questions", "contre l'API publique"],
        ]),
        (1080, "Planification de la tâche (Azure)", True, [
            ["le 3 du mois", "3 h UTC en préproduction"],
            ["le 3 du mois", "4 h UTC en production"],
            ["tâche seule", "sans le jeu de questions"],
        ]),
    ]  # fmt: skip
    for x, titre, pointille, etapes in colonnes:
        p.groupe(x, 160, 460, 620, titre, pointille=pointille)
        for i, lignes in enumerate(etapes):
            y = 215 + i * 110
            p.boite(x + 40, y, 380, 80, lignes)
            if i and not pointille:
                p.fleche((x + 230, y - 30), (x + 230, y - 2))
    p.boite(60, 810, 970, 80, ["verrou livraison-<env>", "partagé avec la livraison : "
                               "jamais deux workflows en même temps"], "vif")  # fmt: skip
    p.note(915, "Un retour arrière ne reconstruit aucune image et ne crée aucune révision :"
                " seul le trafic bascule.")  # fmt: skip
    return p


def mise_en_place() -> Planche:
    p = Planche(4, "Mise en place de l'infrastructure")
    p.groupe(40, 160, 330, 300, "Reconstruction")
    p.boite(65, 215, 280, 130, ["00-foundry", "Foundry West Europe", "AIServices S0",
                                "modèles A (50 k) et B (20 k)"])  # fmt: skip
    p.fleche((370, 280), (408, 280))
    p.groupe(410, 160, 400, 720, "Socle · sprint 2")
    socle = [
        ["01-socle", "Log Analytics · registre", "Container Apps · 2 identités",
         "PostgreSQL 16 · 2 bases"],
        ["02-image", "première image muninn:<sha>"],
        ["03-applications", "API et console × 2 env.", "OIDC GitHub"],
        ["04-budget", "60 € par mois", "alertes 50, 80, 100 %"],
    ]  # fmt: skip
    hauteurs = [140, 80, 110, 110]
    y = 215
    for i, (lignes, h) in enumerate(zip(socle, hauteurs, strict=True)):
        if i:
            p.fleche((610, y - 30), (610, y - 2))
        p.boite(440, y, 340, h, lignes)
        y += h + 32
    p.fleche((810, 280), (848, 280))
    p.groupe(850, 160, 710, 720, "Sprints 3 à 5, puis C20 et C19")
    suite = [
        (["05-donnees", "tâche des données", "API en rôle de lecture"], "fonce"),
        (["06-evaluation", "identité Foundry User seule", "OIDC evaluation"], "fonce"),
        (["07-langfuse", "clés de prod sur l'API", "clés d'évaluation dans GitHub"], "vif"),
        (["08-traitements", "rôle _traitements", "enregistrement des appels"], "vif"),
        (["09-observabilite", "appi-muninn", "lié à log-muninn"], "vif"),
        (["10-classeur", "« Muninn, exploitation »", "modèle ARM"], "fonce"),
        (["11-alertes", "AL-04 toutes les 15 min", "ag-muninn → courriel"], "fonce"),
        (["12-panne", "exercice d'exploitation", "--provoquer / --reparer"], "vif"),
        (["13-voix", "Azure AI Speech", "contrôle par une synthèse"], "vif"),
        (["14-vigie", "Monitoring Reader seul", "OIDC vigie · issues Incident"], "fonce"),
        (["15-test", "crmuninntest · app. de test", "id-muninn-test · AcrPush, AcrDelete"],
         "fonce"),
    ]  # fmt: skip
    for i, (lignes, style) in enumerate(suite):
        colonne, rang = divmod(i, 6)
        p.boite(880 + colonne * 345, 210 + rang * 108, 315, 92, lignes, style)
    p.boite(1225, 750, 315, 92, ["contour vert vif", "même séquence que deployer.sh",
                                 "(révision contrôlée)"], "clair")  # fmt: skip
    p.note(910, "R10 : le porteur lance lui-même ces scripts ; tous sont relançables ;"
                " aucun secret n'est écrit dans le dépôt.")  # fmt: skip
    return p


def execution() -> Planche:
    p = Planche(5, "Exécution : un environnement")
    p.groupe(40, 300, 220, 150, "Accès")
    p.boite(65, 350, 170, 70, ["Navigateur", "HTTPS · entrée externe"])
    p.groupe(300, 160, 770, 720, "Container Apps · cae-muninn · France Central")
    p.fleche((235, 385), (280, 385), (280, 270), (338, 270))
    p.boite(340, 215, 300, 110, ["ca-muninn-console-<env>", "interface web"])
    p.boite(720, 200, 320, 140, ["ca-muninn-api-<env>", "API et agent d'extraction",
                                 "identité id-muninn-execution",
                                 "Entra, sans clé"], "vif")  # fmt: skip
    p.fleche((640, 270), (718, 270))
    p.etiquette(679, 255, "adresse")
    p.etiquette(679, 295, "interne")
    p.groupe(340, 500, 700, 220, "Tâche planifiée · le 3 du mois, ou workflow donnees",
             pointille=True)  # fmt: skip
    p.boite(380, 560, 620, 120, ["job-muninn-donnees-<env>", "migrations · rôles · ingestion",
                                 "1 vCPU · 2 Gio"])  # fmt: skip
    externes = [
        (175, ["Foundry · West Europe", "modèles A et B · Speech (voix)"]),
        (265, ["Application Insights", "appi-muninn · traces"]),
        (355, ["Langfuse Cloud UE", "projet muninn · traces LLM"]),
        (445, ["PostgreSQL psql-muninn", "muninn_<env> · rôles _api et _traitements"]),
        (580, ["Sources publiques", "INSEE · data.gouv · Wikidata · geo.api.gouv"]),
    ]
    p.trait((1040, 270), (1100, 270))
    p.trait((1100, 210), (1100, 465))
    for y in (210, 300, 390, 465):
        p.fleche((1100, y), (1158, y))
    p.fleche((1000, 615), (1158, 615), pointille=True)
    p.fleche((1000, 595), (1130, 595), (1130, 500), (1158, 500), pointille=True)
    for y, lignes in externes:
        p.boite(1160, y, 400, 70, lignes, "gris")
    journaux = ["Log Analytics · log-muninn", "journaux des applications · traces"]
    p.boite(1160, 700, 400, 70, journaux, "gris")
    p.fleche((1070, 820), (1110, 820), (1110, 735), (1158, 735))
    p.fleche((1260, 770), (1260, 798))
    p.fleche((1460, 770), (1460, 798))
    p.boite(1160, 800, 190, 80, ["classeur", "Muninn, exploitation"])
    p.boite(1365, 800, 195, 80, ["AL-04", "API de prod · courriel"], "rouge")
    p.etiquette(340, 860, "Lignes pleines : appels de l'API ; pointillés : la tâche des données.",
                ancre="start")  # fmt: skip
    p.note(910, "À noter : la console n'appelle l'API que par son adresse interne ;"
                " AL-04 ne surveille que l'API de production.")  # fmt: skip
    return p


PLANCHES: dict[str, Callable[[], Planche]] = {
    "1-chaine-de-livraison": chaine_de_livraison,
    "2-deployer": deployer,
    "3-workflows-manuels": workflows_manuels,
    "4-mise-en-place": mise_en_place,
    "5-execution": execution,
}


def svg(nom: str) -> str:
    """Le SVG d'une planche, déterministe."""
    return PLANCHES[nom]().svg(nom)


def png(sources: dict[str, Path]) -> None:
    """Chaque SVG rendu en PNG par Chromium, à double résolution."""
    from playwright.sync_api import sync_playwright  # noqa: PLC0415 : seulement avec --png

    (DOSSIER / "png").mkdir(exist_ok=True)
    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        page = navigateur.new_page(device_scale_factor=2)
        for nom, source in sources.items():
            page.set_content(
                "<!doctype html><html><body style='margin:0;background:#fff'>"
                f"{source.read_text(encoding='utf-8')}</body></html>"
            )
            page.locator("svg").screenshot(path=str(DOSSIER / "png" / f"{nom}.png"))
        navigateur.close()


def main() -> int:
    (DOSSIER / "svg").mkdir(exist_ok=True)
    sources: dict[str, Path] = {}
    for nom in PLANCHES:
        sources[nom] = DOSSIER / "svg" / f"{nom}.svg"
        sources[nom].write_text(svg(nom), encoding="utf-8", newline="\n")
    if "--png" in sys.argv[1:]:
        png(sources)
    print(f"{len(sources)} planches : {', '.join(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
