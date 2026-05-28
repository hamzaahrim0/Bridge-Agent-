"""
Generate a rigorous technical PDF report for the BRIDGE project.

The report is intentionally generated with ReportLab rather than LaTeX so it can
be reproduced from the project workspace without an external typesetting stack.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Frame,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "BRIDGE_Technical_Report.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 1.75 * cm
MARGIN_TOP = 1.65 * cm
MARGIN_BOTTOM = 1.45 * cm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN_X

BLUE = colors.HexColor("#2457A6")
GREEN = colors.HexColor("#18865A")
INK = colors.HexColor("#1B1E28")
MUTED = colors.HexColor("#5D6678")
LINE = colors.HexColor("#CBD3E1")
ACCENT = colors.HexColor("#C79A21")


def register_fonts() -> None:
    """Register DejaVu fonts to support French accents in generated PDF."""
    font_dir = Path("/usr/share/fonts/dejavu")
    pdfmetrics.registerFont(TTFont("DejaVuSans", str(font_dir / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(font_dir / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSerif", str(font_dir / "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuSerif-Bold", str(font_dir / "DejaVuSerif-Bold.ttf")))


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="DejaVuSerif-Bold",
            fontSize=24,
            leading=30,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            fontName="DejaVuSans",
            fontSize=11,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "H1": ParagraphStyle(
            "H1",
            fontName="DejaVuSerif-Bold",
            fontSize=15,
            leading=20,
            textColor=BLUE,
            spaceBefore=12,
            spaceAfter=7,
        ),
        "H2": ParagraphStyle(
            "H2",
            fontName="DejaVuSans-Bold",
            fontSize=11.5,
            leading=15,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName="DejaVuSans",
            fontSize=9.4,
            leading=13.2,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "BodyLeft": ParagraphStyle(
            "BodyLeft",
            fontName="DejaVuSans",
            fontSize=9.4,
            leading=13.2,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "Small": ParagraphStyle(
            "Small",
            fontName="DejaVuSans",
            fontSize=8,
            leading=10.5,
            textColor=MUTED,
            spaceAfter=3,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            fontName="DejaVuSans",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=9,
        ),
        "Abstract": ParagraphStyle(
            "Abstract",
            fontName="DejaVuSans",
            fontSize=9.2,
            leading=13.4,
            textColor=INK,
            leftIndent=0.45 * cm,
            rightIndent=0.45 * cm,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "Code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#273142"),
            backColor=colors.HexColor("#F1F4F8"),
            borderColor=LINE,
            borderWidth=0.4,
            borderPadding=5,
            spaceBefore=3,
            spaceAfter=6,
        ),
    }
    return styles


STYLES: dict[str, ParagraphStyle]


class Rule(Flowable):
    def __init__(self, color=LINE, thickness=0.7, space=8):
        super().__init__()
        self.width = CONTENT_WIDTH
        self.height = space
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


class Diagram(Flowable):
    """Custom ReportLab flowable for architecture and pipeline diagrams."""

    def __init__(self, kind: str, width: float = CONTENT_WIDTH, height: float = 250):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height = height

    def draw_box(self, x, y, w, h, label, fill, stroke=LINE, text=INK, size=7.4):
        c = self.canv
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
        c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
        c.setFillColor(text)
        c.setFont("DejaVuSans-Bold", size)
        lines = wrap(label, width=max(10, int(w / 4.3)))
        total = len(lines) * (size + 2)
        yy = y + h / 2 + total / 2 - size
        for line in lines:
            c.drawCentredString(x + w / 2, yy, line)
            yy -= size + 2

    def arrow(self, x1, y1, x2, y2, color=BLUE):
        c = self.canv
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) >= abs(dy):
            direction = 1 if dx >= 0 else -1
            pts = [(x2, y2), (x2 - direction * 7, y2 + 3.5), (x2 - direction * 7, y2 - 3.5)]
        else:
            direction = 1 if dy >= 0 else -1
            pts = [(x2, y2), (x2 - 3.5, y2 - direction * 7), (x2 + 3.5, y2 - direction * 7)]
        p = c.beginPath()
        p.moveTo(*pts[0])
        p.lineTo(*pts[1])
        p.lineTo(*pts[2])
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    def title(self, text):
        self.canv.setFont("DejaVuSans-Bold", 8.2)
        self.canv.setFillColor(MUTED)
        self.canv.drawString(0, self.height - 10, text)

    def draw(self):
        if self.kind == "architecture":
            self.draw_architecture()
        elif self.kind == "react":
            self.draw_react()
        elif self.kind == "rag":
            self.draw_rag()
        elif self.kind == "gdid":
            self.draw_gdid()

    def draw_architecture(self):
        self.title("Architecture fonctionnelle de BRIDGE")
        w = self.width
        y = self.height - 55
        bw = 145
        bh = 34
        x = (w - bw) / 2
        nodes = [
            ("Interface Streamlit\nChat, Corpus, GDID", BLUE, y),
            ("Orchestrateur ReAct\nroutage, coordination, fusion", colors.HexColor("#DCE8FF"), y - 48),
            ("Agents disciplinaires\nFinance + Informatique", colors.HexColor("#E6F5EE"), y - 96),
            ("RAG ChromaDB\nrecherche vectorielle locale", colors.HexColor("#FFF4D6"), y - 144),
            ("Corpus arXiv + GDID\nsources et médiations validées", colors.HexColor("#F7E8EA"), y - 192),
        ]
        last_y = None
        for label, fill, yy in nodes:
            text = colors.white if fill == BLUE else INK
            self.draw_box(x, yy, bw, bh, label, fill, text=text)
            if last_y is not None:
                self.arrow(x + bw / 2, last_y, x + bw / 2, yy + bh)
            last_y = yy

        self.draw_box(18, y - 96, 110, 34, "LLM local\nOllama", colors.HexColor("#EEF1F6"))
        self.draw_box(w - 128, y - 96, 110, 34, "Configuration\n.env", colors.HexColor("#EEF1F6"))
        self.arrow(128, y - 79, x, y - 79, GREEN)
        self.arrow(w - 128, y - 79, x + bw, y - 79, GREEN)

    def draw_react(self):
        self.title("Pipeline de décision de l'orchestrateur")
        xs = [8, 119, 230, 341]
        ys = [155, 155, 155, 155]
        labels = [
            "Question\nutilisateur",
            "Thought 1\nDétecter disciplines",
            "Action 1\nRécupérer RAG",
            "Action 2\nAppeler agents",
        ]
        fills = [colors.HexColor("#EEF1F6"), colors.HexColor("#DCE8FF"), colors.HexColor("#FFF4D6"), colors.HexColor("#E6F5EE")]
        for i, (x, y, label, fill) in enumerate(zip(xs, ys, labels, fills)):
            self.draw_box(x, y, 95, 42, label, fill)
            if i:
                self.arrow(xs[i - 1] + 95, y + 21, x, y + 21)

        xs2 = [341, 230, 119, 8]
        labels2 = [
            "Thought 2\nFusionner réponses",
            "Action 3\nDétecter polysémie",
            "Médiation\nproposition JSON",
            "Réponse finale\nsources + agents",
        ]
        fills2 = [colors.HexColor("#DCE8FF"), colors.HexColor("#F7E8EA"), colors.HexColor("#FFF4D6"), BLUE]
        for i, (x, label, fill) in enumerate(zip(xs2, labels2, fills2)):
            self.draw_box(x, 70, 95, 42, label, fill, text=colors.white if fill == BLUE else INK)
            if i:
                self.arrow(xs2[i - 1], 91, x + 95, 91)
        self.arrow(388.5, 155, 388.5, 112)

    def draw_rag(self):
        self.title("Pipeline d'indexation et de récupération RAG")
        top_y = 158
        labels = [
            "PDF / TXT\nFinance",
            "Extraction\nPyPDF2",
            "Chunking\n800 / 150",
            "Embeddings\nmultilingues",
            "ChromaDB\nbridge_finance",
        ]
        x = 4
        for i, label in enumerate(labels):
            self.draw_box(x, top_y, 86, 40, label, colors.HexColor("#DCE8FF") if i < 4 else colors.HexColor("#FFF4D6"))
            if i:
                self.arrow(x - 10, top_y + 20, x, top_y + 20)
            x += 96

        labels2 = [
            "PDF / TXT\nInformatique",
            "Extraction\nPyPDF2",
            "Chunking\n800 / 150",
            "Embeddings\nmultilingues",
            "ChromaDB\nbridge_informatique",
        ]
        x = 4
        for i, label in enumerate(labels2):
            self.draw_box(x, 88, 86, 40, label, colors.HexColor("#E6F5EE") if i < 4 else colors.HexColor("#FFF4D6"))
            if i:
                self.arrow(x - 10, 108, x, 108, GREEN)
            x += 96

        self.draw_box(165, 17, 155, 38, "Requête utilisateur\nembedding unique puis retrieve_multi", colors.HexColor("#EEF1F6"))
        self.arrow(242, 55, 434, 88, ACCENT)
        self.arrow(242, 55, 434, 158, ACCENT)

    def draw_gdid(self):
        self.title("Cycle de médiation terminologique et validation humaine")
        self.draw_box(18, 150, 115, 42, "Terme polysème\nex. modèle, signal", colors.HexColor("#F7E8EA"))
        self.draw_box(178, 150, 115, 42, "Proposition LLM\nJSON structuré", colors.HexColor("#FFF4D6"))
        self.draw_box(338, 150, 115, 42, "Validation humaine\nStreamlit", colors.HexColor("#DCE8FF"))
        self.draw_box(178, 66, 115, 42, "GDID JSON\ncorrespondance stable", colors.HexColor("#E6F5EE"))
        self.draw_box(18, 66, 115, 42, "Réutilisation\ncapital terminologique", colors.HexColor("#EEF1F6"))
        self.arrow(133, 171, 178, 171)
        self.arrow(293, 171, 338, 171)
        self.arrow(395, 150, 236, 108, GREEN)
        self.arrow(178, 87, 133, 87, GREEN)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVuSans", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN_X, PAGE_HEIGHT - 1.05 * cm, "BRIDGE Technical Report")
    canvas.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 1.05 * cm, "UM5 Rabat - Département MIS")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, PAGE_HEIGHT - 1.18 * cm, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 1.18 * cm)
    canvas.drawCentredString(PAGE_WIDTH / 2, 0.82 * cm, str(canvas.getPageNumber()))
    canvas.restoreState()


def p(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def bullets(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, "BodyLeft"), leftIndent=10) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=16,
        bulletFontName="DejaVuSans",
        bulletFontSize=7,
    )


def table(data, widths=None, header=True) -> Table:
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("LEADING", (0, 0), (-1, -1), 9.4),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#FAFBFD")]),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ]
        )
    t.setStyle(TableStyle(style))
    return t


def section(title: str) -> list:
    return [Spacer(1, 5), p(title, "H1"), Rule()]


def subsection(title: str) -> Paragraph:
    return p(title, "H2")


def build_story() -> list:
    story = []

    story += [
        Spacer(1, 2.0 * cm),
        p("BRIDGE", "Title"),
        p("Bridging Research Intelligence for Disciplinary Gap Eradication", "Subtitle"),
        Spacer(1, 0.7 * cm),
        Rule(BLUE, 1.1, 12),
        Spacer(1, 0.55 * cm),
        p("Rapport technique académique sur un prototype local d'IA agentique pour la médiation interdisciplinaire Finance - Informatique.", "Abstract"),
        Spacer(1, 0.7 * cm),
        table(
            [
                ["Élément", "Valeur"],
                ["Auteurs", "Ahrim Hamza, Mouafiq Saad"],
                ["Superviseur", "Pr. Bennis"],
                ["Institution", "Université Mohammed V de Rabat, Département MIS"],
                ["Année", "2026"],
                ["Statut", "Prototype local de recherche"],
            ],
            widths=[4.2 * cm, 10.6 * cm],
        ),
        Spacer(1, 1.1 * cm),
        Diagram("architecture", height=270),
        p("Figure 1 - Vue synthétique des composants de BRIDGE et du flux principal entre interface, orchestration, agents, RAG et GDID.", "Caption"),
        PageBreak(),
    ]

    story += section("Résumé")
    story += [
        p("BRIDGE est un système multi-agent local conçu pour aider deux communautés de recherche, Finance et Informatique, à produire des explications croisées fondées sur des sources documentaires et sur une médiation terminologique contrôlée. Le système combine une interface Streamlit, un orchestrateur inspiré du patron ReAct, deux agents disciplinaires, un pipeline Retrieval-Augmented Generation local basé sur ChromaDB, et un glossaire dynamique interdisciplinaire persistant en JSON."),
        p("L'objectif central n'est pas d'automatiser la vérité scientifique, mais de réduire le coût cognitif du passage d'un cadre disciplinaire à l'autre. BRIDGE formalise ce passage par trois mécanismes: sélection de perspective, récupération de contexte documenté, et proposition de correspondances terminologiques soumises à validation humaine. Cette conception place l'agentique au service d'une coopération académique explicable, locale et révisable."),
        p("Le présent rapport décrit l'architecture, les flux de données, les choix d'implémentation, les limites et les pistes d'amélioration du prototype. Il adopte une position rigoureuse: aucune performance quantitative n'est revendiquée en l'absence de protocole d'évaluation complet; les bénéfices sont décrits comme des propriétés de conception et non comme des résultats expérimentaux démontrés."),
    ]

    story += section("1. Problématique et objectifs")
    story += [
        p("La collaboration entre Finance et Informatique repose souvent sur un vocabulaire partagé en surface mais divergent en profondeur. Des termes comme modèle, performance, optimisation, signal ou risque peuvent recevoir des interprétations distinctes selon que l'on parle de marchés financiers, d'apprentissage automatique, d'architecture logicielle ou de séries temporelles. Cette polysémie crée un risque d'accord apparent: les interlocuteurs utilisent le même mot sans stabiliser le même concept."),
        p("BRIDGE répond à ce problème en construisant une couche de médiation. L'utilisateur indique sa discipline, pose une question, puis le système mobilise les agents pertinents et des extraits documentaires issus d'un corpus local. Le résultat attendu est une réponse qui explicite les perspectives disciplinaires, cite les sources RAG disponibles et signale les zones de friction conceptuelle."),
        subsection("Objectifs fonctionnels"),
        bullets(
            [
                "Permettre à un utilisateur Finance ou Informatique de poser une question interdisciplinaire en français.",
                "Router la question vers un ou deux agents disciplinaires selon son contenu.",
                "Injecter un contexte documentaire récupéré dans des collections vectorielles séparées par discipline.",
                "Détecter des termes polysèmes et générer des propositions de médiation terminologique.",
                "Capitaliser les correspondances validées dans un Glossaire Dynamique Inter-Disciplinaire.",
            ]
        ),
        subsection("Objectifs non fonctionnels"),
        bullets(
            [
                "Fonctionnement local et gratuit, sans clé API externe, via Ollama.",
                "Architecture modulaire permettant l'ajout futur d'autres disciplines.",
                "Traçabilité minimale des sources par affichage des documents récupérés.",
                "Déploiement reproductible par Docker Compose.",
                "Contrôle humain explicite sur l'enrichissement du glossaire.",
            ]
        ),
    ]

    story += section("2. Architecture générale")
    story += [
        p("BRIDGE est organisé comme une chaîne d'orchestration. L'interface Streamlit collecte la discipline de l'utilisateur et sa question. L'orchestrateur analyse la requête, choisit les disciplines cibles, récupère le contexte RAG, appelle les agents, fusionne éventuellement les réponses et construit un objet de sortie contenant la réponse finale, les agents utilisés, les sources RAG, les termes ambigus et les médiations proposées."),
        Diagram("architecture", height=270),
        p("Figure 2 - Architecture logique détaillant la dépendance centrale de l'orchestrateur aux agents, au fournisseur LLM, au RAG et au GDID.", "Caption"),
        subsection("Principes de conception"),
        p("Le prototype privilégie une séparation nette des responsabilités. Le fournisseur LLM encapsule les appels Ollama; les agents ne manipulent pas directement la base vectorielle; le récupérateur RAG ne génère pas de texte; le GDID ne valide pas automatiquement les médiations. Cette séparation réduit le couplage et rend les erreurs plus localisables."),
        table(
            [
                ["Composant", "Responsabilité", "Fichier principal"],
                ["Interface", "Interaction utilisateur, affichage chat, sources, corpus, GDID", "app.py"],
                ["Orchestrateur", "Routage, ReAct simplifié, fusion, médiation", "orchestrator.py"],
                ["Agents", "Réponses disciplinaires contextualisées", "agents/*.py"],
                ["RAG", "Indexation et récupération vectorielle", "rag/indexer.py, rag/retriever.py"],
                ["LLM", "Appels HTTP vers Ollama local", "llm/provider.py"],
                ["GDID", "Persistance des correspondances validées", "gdid/glossary.py"],
            ],
            widths=[3.2 * cm, 7.5 * cm, 4.2 * cm],
        ),
    ]

    story += section("3. Conception agentique")
    story += [
        p("La couche agentique de BRIDGE repose sur un orchestrateur et deux agents spécialisés. L'orchestrateur ne se contente pas de transmettre une question à un modèle unique: il décompose la tâche en étapes, sélectionne les perspectives utiles, récupère des observations documentaires, puis construit une réponse intégrée. Cette logique reprend l'esprit du patron ReAct, où raisonnement et action sont alternés, tout en restant déterministe sur plusieurs décisions pour limiter les coûts et les délais."),
        Diagram("react", height=230),
        p("Figure 3 - Chaîne ReAct simplifiée: la décision de routage précède la récupération RAG, l'appel des agents et la médiation terminologique.", "Caption"),
        subsection("Routage disciplinaire"),
        p("Le routage commence par des heuristiques lexicales. Des mots-clés financiers, informatiques et polysémiques sont normalisés sans accents afin de réduire les faux négatifs. Si aucun signal n'est trouvé, la discipline déclarée par l'utilisateur sert de repli. Un routage par LLM est prévu mais désactivé par défaut, ce qui rend le prototype plus prévisible et plus rapide sur des modèles locaux légers."),
        subsection("Agents Finance et Informatique"),
        p("Chaque agent hérite d'une interface abstraite commune et reçoit trois éléments: la question, la discipline de l'utilisateur et le contexte RAG formaté. L'agent Finance mobilise les cadres conceptuels de la finance quantitative, du portefeuille, du risque ou du pricing. L'agent Informatique mobilise les cadres de l'apprentissage automatique, des algorithmes, des architectures et des représentations. Les deux prompts imposent une réponse courte, en français, avec citation des documents RAG sous forme [Doc N]."),
        subsection("Fusion et médiation"),
        p("Lorsque deux agents répondent, l'orchestrateur peut soit juxtaposer les perspectives, soit demander au LLM une fusion interdisciplinaire si BRIDGE_LLM_MERGE_ENABLED est activé. La médiation terminologique est ensuite déclenchée seulement si des termes polysèmes sont détectés, si plusieurs disciplines sont impliquées et si BRIDGE_MEDIATION_ENABLED est activé. Ce choix évite la génération systématique de médiations inutiles."),
    ]

    story += section("4. Pipeline RAG")
    story += [
        p("Le RAG constitue le mécanisme d'ancrage documentaire. Les documents sont séparés en deux répertoires, Finance et Informatique, puis indexés dans des collections ChromaDB distinctes. Cette séparation explicite permet de récupérer des passages cohérents avec les perspectives disciplinaires sélectionnées par l'orchestrateur."),
        Diagram("rag", height=220),
        p("Figure 4 - Pipeline RAG: indexation hors ligne des documents, puis récupération vectorielle au moment de la question.", "Caption"),
        subsection("Corpus documentaire"),
        p("Le corpus local contient cinquante documents issus d'arXiv: vingt-cinq côté Finance et vingt-cinq côté Informatique. Les thèmes couvrent la finance quantitative, l'optimisation de portefeuille, le pricing, le hedging, le trading automatique, les séries temporelles financières, les graph neural networks, les transformers, les LLM financiers et l'analyse de sentiment financier."),
        subsection("Indexation"),
        p("Le module d'indexation charge les fichiers PDF ou TXT, extrait le texte avec PyPDF2, découpe le contenu par RecursiveCharacterTextSplitter, calcule les embeddings avec paraphrase-multilingual-mpnet-base-v2, puis stocke les chunks dans ChromaDB avec des métadonnées de source, discipline et indice de chunk. L'opération est idempotente: les collections actives sont supprimées et recréées à chaque indexation."),
        subsection("Récupération"),
        p("Lorsqu'une question arrive, son embedding est calculé une seule fois puis utilisé contre chaque collection disciplinaire pertinente. La méthode retrieve_multi agrège les passages récupérés. L'orchestrateur formate ensuite ces passages en blocs [Doc N] avant de les injecter dans le prompt de l'agent. Ce design limite la duplication de calcul et préserve une séparation claire entre recherche documentaire et génération."),
        table(
            [
                ["Paramètre", "Valeur typique", "Rôle"],
                ["CHUNK_SIZE", "800", "Taille maximale des passages indexés"],
                ["CHUNK_OVERLAP", "150", "Conservation du contexte entre chunks"],
                ["RAG_TOP_K", "3", "Nombre de résultats par discipline"],
                ["RAG_CONTEXT_CHARS", "500", "Longueur maximale affichée par source"],
                ["CHROMA_DB_PATH", "./chroma_db", "Persistance locale de la base vectorielle"],
            ],
            widths=[3.6 * cm, 3.2 * cm, 8.0 * cm],
        ),
    ]

    story += section("5. Glossaire Dynamique Inter-Disciplinaire")
    story += [
        p("Le GDID formalise la mémoire terminologique du système. Il ne remplace pas l'expertise humaine: il conserve uniquement les correspondances validées ou explicitement ajoutées. Chaque entrée contient un terme source, une discipline source, une définition source, un terme cible, une discipline cible, une définition cible, une analogie, un niveau de confiance, une date et un identifiant UUID."),
        Diagram("gdid", height=225),
        p("Figure 5 - Cycle de vie d'une médiation: détection, proposition, validation humaine, persistance et réutilisation.", "Caption"),
        p("Cette conception introduit une boucle de gouvernance. Le LLM propose, mais l'utilisateur valide. Le glossaire devient ainsi un artefact de capitalisation académique, utile pour stabiliser progressivement les ponts terminologiques entre communautés de recherche."),
        table(
            [
                ["Champ", "Description"],
                ["terme_source / terme_cible", "Terme à aligner entre les disciplines"],
                ["discipline_source / discipline_cible", "Perspectives disciplinaires concernées"],
                ["definition_source / definition_cible", "Définitions contextualisées"],
                ["analogie", "Pont conceptuel court entre les deux sens"],
                ["validé_par", "Origine de la validation, généralement humaine"],
                ["confiance", "Score borné entre 0.0 et 1.0"],
                ["date_validation / id", "Traçabilité temporelle et identifiant stable"],
            ],
            widths=[4.2 * cm, 10.6 * cm],
        ),
    ]

    story += section("6. Interface, configuration et déploiement")
    story += [
        p("L'interface Streamlit organise l'expérience en quatre onglets: Chat, Glossaire GDID, Corpus et À propos. La barre latérale permet de choisir la discipline utilisateur, de vérifier la disponibilité du LLM local et de lancer une réindexation documentaire. Les réponses affichent les agents mobilisés, les sources RAG et les éventuelles médiations validables."),
        subsection("Configuration"),
        p("La configuration est portée par des variables d'environnement chargées via python-dotenv. Les plus importantes concernent l'URL Ollama, le modèle, les paramètres de génération, le routage LLM, la fusion, la médiation, les paramètres RAG et les chemins persistants."),
        p("OLLAMA_BASE_URL=http://host.docker.internal:11434<br/>OLLAMA_MODEL=llama3.2:1b<br/>LLM_TIMEOUT=300<br/>BRIDGE_LLM_MERGE_ENABLED=true<br/>BRIDGE_MEDIATION_ENABLED=true", "Code"),
        subsection("Déploiement local"),
        p("Le lancement local suppose Python 3.11+, Ollama démarré et le modèle téléchargé. La commande principale est streamlit run app.py. Le déploiement conteneurisé passe par Docker Compose avec trois services: bridge-chromadb, bridge-indexer et bridge-app. L'application est servie par défaut sur http://localhost:8501."),
        table(
            [
                ["Service", "Rôle"],
                ["bridge-chromadb", "Service ChromaDB exposé sur le port 8000"],
                ["bridge-indexer", "Indexation des documents dans les collections locales"],
                ["bridge-app", "Interface Streamlit exposée sur le port 8501"],
            ],
            widths=[4.0 * cm, 10.8 * cm],
        ),
    ]

    story += section("7. Analyse de rigueur et sûreté")
    story += [
        p("Un système agentique de médiation académique doit être évalué selon des critères différents d'un simple chatbot. Les dimensions critiques sont la fidélité documentaire, la clarté des perspectives, la capacité à signaler les ambiguïtés, la résistance aux hallucinations, la traçabilité des sources, la sobriété des inférences et la qualité de l'intervention humaine."),
        subsection("Invariants de conception"),
        bullets(
            [
                "Aucun ajout au GDID n'est supposé valide sans validation explicite.",
                "Les agents reçoivent un contexte RAG borné et cité.",
                "Les erreurs Ollama sont propagées avec messages exploitables.",
                "Les collections vectorielles sont nommées de manière stable à partir des disciplines.",
                "Le routage LLM est optionnel afin de préserver un comportement déterministe en mode prototype.",
            ]
        ),
        subsection("Protocole d'évaluation recommandé"),
        p("Pour passer d'un prototype à un artefact expérimental, BRIDGE devrait être soumis à un protocole comprenant: un jeu de questions interdisciplinaires annotées, une mesure de pertinence RAG par juges humains, une évaluation de fidélité des citations, une mesure de détection de polysémie, une analyse comparative avec et sans GDID, et une étude qualitative auprès d'utilisateurs Finance et Informatique."),
    ]

    story += section("8. Limites")
    story += [
        bullets(
            [
                "Le système dépend de la disponibilité et de la vitesse d'Ollama local.",
                "La qualité des réponses dépend fortement du modèle local configuré.",
                "L'extraction PDF par PyPDF2 peut produire du texte bruité ou incomplet.",
                "Le corpus est limité à deux disciplines et à cinquante documents.",
                "Aucune évaluation quantitative complète n'est encore fournie.",
                "La détection de polysémie repose sur une liste de termes et non sur une analyse sémantique profonde.",
                "Les citations [Doc N] indiquent les passages injectés, mais ne garantissent pas seules la fidélité de toutes les affirmations générées.",
            ]
        )
    ]

    story += section("9. Perspectives")
    story += [
        bullets(
            [
                "Étendre l'architecture à d'autres disciplines, par exemple économie, mathématiques appliquées ou droit financier.",
                "Ajouter une évaluation systématique du RAG: rappel, précision, pertinence et attribution.",
                "Introduire une mémoire de conversations contrôlée et désactivable.",
                "Améliorer la médiation par extraction automatique de définitions contrastives depuis les documents.",
                "Ajouter un tableau de bord d'administration pour inspecter les collections, chunks, scores et versions de modèles.",
                "Tracer les décisions de routage sous forme d'observations auditables.",
                "Mettre en place un mode benchmark pour comparer plusieurs modèles Ollama.",
            ]
        )
    ]

    story += section("10. Conclusion")
    story += [
        p("BRIDGE démontre une architecture locale cohérente pour la médiation interdisciplinaire assistée par IA. Sa valeur technique réside dans la combinaison d'un orchestrateur agentique, de perspectives disciplinaires explicites, d'un RAG local séparé par discipline et d'un glossaire validé par l'humain. Le système évite de confondre génération automatique et validation scientifique: il fournit des propositions contextualisées, cite ses sources disponibles et laisse la stabilisation terminologique à un processus contrôlé."),
        p("Le prototype constitue une base solide pour un travail de recherche appliquée sur l'IA agentique académique. Les prochaines étapes doivent porter sur l'évaluation, la traçabilité fine, l'extension du corpus et l'amélioration de la gouvernance des médiations."),
    ]

    story += section("Références techniques")
    refs = [
        ["ReAct", "Yao et al., ReAct: Synergizing Reasoning and Acting in Language Models."],
        ["RAG", "Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks."],
        ["Ollama", "Plateforme locale d'exécution de modèles de langage."],
        ["ChromaDB", "Base vectorielle locale pour recherche par similarité."],
        ["Sentence Transformers", "Bibliothèque d'embeddings textuels multilingues."],
        ["Streamlit", "Framework Python pour interfaces de données interactives."],
        ["ReportLab", "Bibliothèque Python de génération programmatique de PDF."],
    ]
    story += [table([["Référence", "Description"]] + refs, widths=[4.0 * cm, 10.8 * cm])]

    return story


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=MARGIN_X,
        leftMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="BRIDGE Technical Report",
        author="Ahrim Hamza, Mouafiq Saad",
        subject="Agentic AI technical report for BRIDGE",
    )
    frame = Frame(
        MARGIN_X,
        MARGIN_BOTTOM,
        CONTENT_WIDTH,
        PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=on_page)])
    doc.build(build_story())


if __name__ == "__main__":
    register_fonts()
    STYLES = build_styles()
    build_pdf()
    print(f"PDF generated: {OUTPUT}")
