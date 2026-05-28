"""
Interface Streamlit pour BRIDGE.

Application web interactive pour la collaboration
interdisciplinaire assistee par IA.
"""

import html
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import load_environment
from gdid.glossary import GlossaireDynamique
from llm.provider import LLMProvider
from orchestrator import Orchestrator
from rag.indexer import index_documents


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_environment()

BRIDGE_FULL_NAME = "Bridging Research Intelligence for Disciplinary Gap Eradication"
BRIDGE_VERSION = os.getenv("BRIDGE_VERSION", "v1.0")
DISCIPLINE_COLORS = {
    "Finance": "#4f8ef7",
    "Informatique": "#2ecc71",
}


st.set_page_config(
    page_title="BRIDGE",
    layout="wide",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bridge-bg: #0f1117;
    --bridge-surface: #1a1f2e;
    --bridge-surface-strong: #13182a;
    --bridge-border: #2a3045;
    --bridge-border-hover: #3a4060;
    --bridge-text: #e8eaf0;
    --bridge-text-muted: #7a8399;
    --bridge-finance: #4f8ef7;
    --bridge-finance-bg: rgba(79, 142, 247, 0.12);
    --bridge-info: #2ecc71;
    --bridge-info-bg: rgba(46, 204, 113, 0.12);
    --bridge-accent: #f7c94f;
    --bridge-danger: #e74c6c;
    --bridge-danger-bg: rgba(231, 76, 108, 0.12);
    --bridge-radius: 8px;
    --bridge-radius-lg: 16px;
    --font-mono: 'IBM Plex Mono', 'Courier New', monospace;
    --font-sans: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.35);
    --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stApp {
    background-color: var(--bridge-bg) !important;
    font-family: var(--font-sans) !important;
}

.main .block-container {
    max-width: 1100px !important;
    padding-top: 2rem !important;
}

[data-testid="stSidebar"] {
    background: var(--bridge-surface) !important;
    border-right: 1px solid var(--bridge-border) !important;
}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li {
    color: var(--bridge-text-muted) !important;
    font-size: 0.86rem !important;
}

[data-testid="stSidebar"] h1 {
    color: var(--bridge-text) !important;
    font-family: var(--font-mono) !important;
    font-size: 1.6rem !important;
    letter-spacing: 0 !important;
    margin-bottom: 0.2rem !important;
}

[data-testid="stSidebar"] .stSelectbox label {
    color: var(--bridge-text-muted) !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

h1 {
    background: linear-gradient(135deg, #4f8ef7 0%, #2ecc71 100%);
    background-clip: text !important;
    color: var(--bridge-text) !important;
    font-family: var(--font-mono) !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    letter-spacing: 0 !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}

h2 {
    border-bottom: 1px solid var(--bridge-border) !important;
    color: var(--bridge-text) !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
    margin-top: 1.5rem !important;
    padding-bottom: 0.4rem !important;
}

h3 {
    color: var(--bridge-text) !important;
    font-family: var(--font-sans) !important;
    font-weight: 500 !important;
}

p, li, label {
    color: var(--bridge-text) !important;
    font-family: var(--font-sans) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--bridge-surface) !important;
    border-bottom: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius) var(--bridge-radius) 0 0 !important;
    gap: 0 !important;
    padding: 0 1rem !important;
}

.stTabs [data-baseweb="tab"] {
    border-bottom: 2px solid transparent !important;
    color: var(--bridge-text-muted) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.8rem 1.2rem !important;
    text-transform: uppercase !important;
    transition: var(--transition) !important;
}

.stTabs [aria-selected="true"] {
    background: transparent !important;
    border-bottom: 2px solid var(--bridge-finance) !important;
    color: var(--bridge-finance) !important;
}

[data-testid="stChatMessage"] {
    background: var(--bridge-surface) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius-lg) !important;
    box-shadow: var(--shadow-card) !important;
    margin-bottom: 0.75rem !important;
    padding: 1rem 1.2rem !important;
    transition: var(--transition) !important;
}

[data-testid="stChatMessage"]:hover {
    border-color: var(--bridge-border-hover) !important;
}

[data-testid="stChatMessage"] p {
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
}

[data-testid="stChatInput"] {
    background: var(--bridge-surface) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius-lg) !important;
    color: var(--bridge-text) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--bridge-finance) !important;
    box-shadow: 0 0 0 2px rgba(79, 142, 247, 0.2) !important;
}

.stButton > button,
.stDownloadButton > button {
    background: var(--bridge-surface) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius) !important;
    color: var(--bridge-text) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.5rem 1rem !important;
    text-transform: uppercase !important;
    transition: var(--transition) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: var(--bridge-finance-bg) !important;
    border-color: var(--bridge-finance) !important;
    color: var(--bridge-finance) !important;
    transform: translateY(-1px) !important;
}

.streamlit-expanderHeader {
    background: var(--bridge-surface) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius) !important;
    color: var(--bridge-text) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
}

.streamlit-expanderContent {
    background: var(--bridge-surface-strong) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: 0 0 var(--bridge-radius) var(--bridge-radius) !important;
    border-top: none !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius) !important;
    overflow: hidden !important;
}

.stSelectbox > div > div {
    background: var(--bridge-surface) !important;
    border: 1px solid var(--bridge-border) !important;
    border-radius: var(--bridge-radius) !important;
    color: var(--bridge-text) !important;
}

[data-testid="stAlert"] {
    border-radius: var(--bridge-radius) !important;
    font-family: var(--font-sans) !important;
    font-size: 0.88rem !important;
}

[data-testid="stSpinner"] {
    color: var(--bridge-finance) !important;
}

hr {
    border-color: var(--bridge-border) !important;
    margin: 1rem 0 !important;
}

.bridge-hero {
    border-bottom: 1px solid var(--bridge-border);
    margin-bottom: 1.5rem;
    padding: 1.5rem 0 1rem 0;
    position: relative;
}

.bridge-hero::after {
    background: linear-gradient(90deg, transparent, var(--bridge-finance), var(--bridge-info), transparent);
    bottom: -1px;
    content: "";
    height: 1px;
    left: 0;
    opacity: 0.8;
    position: absolute;
    width: 100%;
}

.bridge-hero .subtitle {
    color: var(--bridge-text-muted);
    font-family: var(--font-sans);
    font-size: 0.95rem;
    letter-spacing: 0.01em;
    margin-top: 0.2rem;
}

.bridge-badge {
    align-items: center;
    border-radius: 20px;
    display: inline-flex;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 600;
    gap: 6px;
    letter-spacing: 0.06em;
    margin: 2px 4px 2px 0;
    padding: 4px 12px;
    text-transform: uppercase;
}

.bridge-badge-finance {
    background: var(--bridge-finance-bg);
    border: 1px solid var(--bridge-finance);
    color: var(--bridge-finance);
}

.bridge-badge-informatique {
    background: var(--bridge-info-bg);
    border: 1px solid var(--bridge-info);
    color: var(--bridge-info);
}

.bridge-status {
    border-radius: var(--bridge-radius);
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    padding: 0.65rem 0.8rem;
    text-transform: uppercase;
}

.bridge-status-ok {
    background: var(--bridge-info-bg);
    border: 1px solid var(--bridge-info);
    color: var(--bridge-info);
}

.bridge-status-error {
    background: var(--bridge-danger-bg);
    border: 1px solid var(--bridge-danger);
    color: var(--bridge-danger);
}

.bridge-notice {
    border-radius: var(--bridge-radius);
    font-family: var(--font-sans);
    font-size: 0.9rem;
    margin: 0.5rem 0;
    padding: 0.75rem 0.9rem;
}

.bridge-notice-info {
    background: var(--bridge-finance-bg);
    border: 1px solid var(--bridge-finance);
    color: var(--bridge-text);
}

.bridge-notice-success {
    background: var(--bridge-info-bg);
    border: 1px solid var(--bridge-info);
    color: var(--bridge-text);
}

.bridge-notice-warning {
    background: rgba(247, 201, 79, 0.12);
    border: 1px solid var(--bridge-accent);
    color: var(--bridge-text);
}

.bridge-notice-error {
    background: var(--bridge-danger-bg);
    border: 1px solid var(--bridge-danger);
    color: var(--bridge-text);
}

.mediation-card {
    background: linear-gradient(135deg, rgba(79, 142, 247, 0.06) 0%, rgba(46, 204, 113, 0.06) 100%);
    border: 1px solid var(--bridge-border);
    border-radius: var(--bridge-radius-lg);
    margin: 0.5rem 0;
    padding: 1rem 1.2rem;
}

.mediation-label {
    color: var(--bridge-accent);
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
}

.corpus-file-card {
    align-items: center;
    background: var(--bridge-surface);
    border: 1px solid var(--bridge-border);
    border-radius: var(--bridge-radius);
    display: flex;
    gap: 12px;
    margin: 0.3rem 0;
    padding: 0.6rem 1rem;
    transition: var(--transition);
}

.corpus-file-card:hover {
    border-color: var(--bridge-border-hover);
    transform: translateX(2px);
}

.corpus-file-number {
    color: var(--bridge-text-muted);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    min-width: 2rem;
}

.corpus-file-name {
    color: var(--bridge-text);
    flex: 1;
    font-family: var(--font-mono);
    font-size: 0.82rem;
}

.corpus-file-size,
.corpus-file-type {
    color: var(--bridge-text-muted);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    white-space: nowrap;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_llm_provider() -> LLMProvider | None:
    """Initialise le fournisseur LLM une seule fois."""
    try:
        return LLMProvider()
    except Exception as exc:
        logger.error("Erreur lors de l'initialisation du LLMProvider : %s", exc)
        return None


@st.cache_resource
def init_orchestrator() -> Orchestrator | None:
    """Initialise l'orchestrateur une seule fois."""
    try:
        return Orchestrator()
    except Exception as exc:
        logger.error("Erreur lors de l'initialisation de l'Orchestrateur : %s", exc)
        return None


@st.cache_resource
def init_glossary() -> GlossaireDynamique | None:
    """Initialise le glossaire une seule fois."""
    try:
        return GlossaireDynamique()
    except Exception as exc:
        logger.error("Erreur lors de l'initialisation du Glossaire : %s", exc)
        return None


def _render_agent_badges(agents: list[str]) -> None:
    """Affiche les badges colorés des agents utilisés."""
    if not agents:
        return

    badge_map = {
        "Finance": "bridge-badge bridge-badge-finance",
        "Informatique": "bridge-badge bridge-badge-informatique",
    }
    labels = {
        "Finance": "FIN",
        "Informatique": "INFO",
    }
    badges_html = " ".join(
        f'<span class="{badge_map.get(agent, "bridge-badge")}">'
        f'{labels.get(agent, "AGT")} {html.escape(agent)}</span>'
        for agent in agents
    )
    st.markdown(
        f'<div style="margin: 0.4rem 0">{badges_html}</div>',
        unsafe_allow_html=True,
    )


def _render_rag_sources(sources: list[dict[str, Any]]) -> None:
    """Affiche les sources RAG dans un expander."""
    if not sources:
        return

    with st.expander("Sources citees"):
        sources_data = [
            {
                "Document": source.get("source", "inconnu"),
                "Discipline": source.get("discipline", ""),
                "Apercu": f"{source.get('content', '')[:140]}...",
            }
            for source in sources
        ]
        st.dataframe(sources_data, use_container_width=True)


def _mediation_entry(proposal: dict[str, Any]) -> dict[str, Any]:
    """Convertit une proposition de mediation en entree GDID."""
    terme = proposal.get("terme", "terme")
    return {
        "terme_source": terme,
        "discipline_source": proposal.get("discipline_a", ""),
        "definition_source": proposal.get("definition_a", ""),
        "terme_cible": terme,
        "discipline_cible": proposal.get("discipline_b", ""),
        "definition_cible": proposal.get("definition_b", ""),
        "analogie": proposal.get("analogie", ""),
        "validé_par": "humain",
        "confiance": proposal.get("confiance", 0.5),
    }


def _render_mediation_proposals(
    proposals: list[dict[str, Any]],
    key_prefix: str,
) -> None:
    """Affiche et gère les propositions de médiation."""
    if not proposals:
        return

    for idx, proposal in enumerate(proposals):
        terme = proposal.get("terme", "terme")
        disc_a = proposal.get("discipline_a", "")
        disc_b = proposal.get("discipline_b", "")
        safe_key = f"{key_prefix}_{idx}_{terme}".replace(" ", "_")

        with st.expander(f"Mediation : {terme}"):
            st.markdown(
                '<div class="mediation-card"><div class="mediation-label">'
                f"Mediation terminologique</div><div>Terme : {html.escape(str(terme))}</div></div>",
                unsafe_allow_html=True,
            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"### {disc_a}")
                st.markdown(proposal.get("definition_a", ""))
            with col_b:
                st.markdown(f"### {disc_b}")
                st.markdown(proposal.get("definition_b", ""))

            st.markdown("**Analogie :**")
            st.markdown(f"*{proposal.get('analogie', '')}*")
            st.markdown(f"Confiance : {proposal.get('confiance', 0.5):.2f}")

            col_validate, col_ignore = st.columns(2)
            with col_validate:
                if st.button("Valider", key=f"validate_{safe_key}", use_container_width=True):
                    glossary = init_glossary()
                    if glossary:
                        try:
                            glossary.add_correspondance(_mediation_entry(proposal))
                            st.toast("Correspondance sauvegardee")
                            logger.info("Correspondance validee : %s", terme)
                        except Exception as exc:
                            _render_notice(
                                f"Erreur lors de la sauvegarde : {str(exc)}",
                                kind="error",
                            )

            with col_ignore:
                if st.button("Ignorer", key=f"ignore_{safe_key}", use_container_width=True):
                    st.toast("Mediation ignoree")


def _render_message_details(message: dict[str, Any], key_prefix: str) -> None:
    """Affiche les elements enrichis d'un message assistant."""
    _render_agent_badges(message.get("agents_used", []))
    _render_rag_sources(message.get("rag_sources", []))
    _render_mediation_proposals(
        message.get("mediation_proposals", []),
        key_prefix=key_prefix,
    )


def _render_status(provider_name: str, available: bool, error_detail: str | None) -> None:
    """Affiche l'etat du fournisseur LLM dans la sidebar."""
    status_class = "bridge-status-ok" if available else "bridge-status-error"
    status_text = "operationnel" if available else "hors ligne"
    st.markdown(
        f'<div class="bridge-status {status_class}">'
        f'{html.escape(provider_name)} {status_text}</div>',
        unsafe_allow_html=True,
    )
    if error_detail and not available:
        st.caption(error_detail)


def _render_notice(message: str, kind: str = "info") -> None:
    """Affiche un message d'etat sans icone par defaut Streamlit."""
    safe_kind = kind if kind in {"info", "success", "warning", "error"} else "info"
    st.markdown(
        f'<div class="bridge-notice bridge-notice-{safe_kind}">'
        f'{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def _format_file_size(file_path: Path) -> str:
    """Retourne une taille lisible pour les fichiers du corpus."""
    size_kb = file_path.stat().st_size / 1024
    if size_kb > 1024:
        return f"{size_kb / 1024:.1f} MB"
    return f"{size_kb:.0f} KB"


def _display_corpus_file(file_path: Path) -> None:
    """Affiche les metadonnees d'un fichier corpus sans lecture du contenu."""
    stem_parts = file_path.stem.split("_")
    number = stem_parts[0] if stem_parts and stem_parts[0].isdigit() else "--"
    name_clean = "_".join(stem_parts[1:]).replace("_", " ").title()
    if not name_clean:
        name_clean = file_path.stem.replace("_", " ").title()

    st.markdown(
        f"""
<div class="corpus-file-card">
    <span class="corpus-file-number">#{html.escape(number)}</span>
    <span class="corpus-file-name">{html.escape(name_clean)}</span>
    <span class="corpus-file-size">{html.escape(_format_file_size(file_path))}</span>
    <span class="corpus-file-type">{html.escape(file_path.suffix.lower() or "file")}</span>
</div>
""",
        unsafe_allow_html=True,
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_mediations" not in st.session_state:
    st.session_state.pending_mediations = []

if "discipline" not in st.session_state:
    st.session_state.discipline = "Finance"


with st.sidebar:
    st.markdown("# BRIDGE")
    st.markdown(f"**{BRIDGE_FULL_NAME}**")
    st.divider()

    discipline = st.selectbox(
        "Votre discipline :",
        ["Finance", "Informatique"],
        key="discipline_select",
    )
    st.session_state.discipline = discipline

    st.divider()

    llm_provider = init_llm_provider()
    provider_name = llm_provider.display_name if llm_provider else "LLM"
    llm_available = llm_provider.is_available() if llm_provider else False
    error_detail = getattr(llm_provider, "last_error", None)
    _render_status(provider_name, llm_available, error_detail)

    st.divider()

    if st.button("Reindexer les documents", use_container_width=True):
        with st.spinner("Indexation en cours..."):
            try:
                index_documents()
                st.toast("Documents reindexes avec succes")
                logger.info("Reindexation manuelle reussie")
            except Exception as exc:
                _render_notice(
                    f"Erreur lors de la reindexation : {str(exc)}",
                    kind="error",
                )
                logger.error("Erreur reindexation : %s", exc)

    st.divider()

    st.markdown(
        f"""
---
**BRIDGE {BRIDGE_VERSION}**

UM5 Rabat, 2026

Departement MIS

Stack local gratuit
"""
    )


st.markdown(
    f"""
<div class="bridge-hero">
    <h1>BRIDGE</h1>
    <div class="subtitle">{BRIDGE_FULL_NAME} · UM5 Rabat · 2026</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_chat, tab_glossary, tab_corpus, tab_about = st.tabs(
    ["Chat", "Glossaire GDID", "Corpus", "A propos"]
)


with tab_chat:
    st.markdown("## Posez votre question interdisciplinaire")

    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
                _render_message_details(message, key_prefix=f"history_{index}")

    user_input = st.chat_input(
        "Posez votre question interdisciplinaire...",
        key="chat_input",
    )

    if user_input:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        orchestrator = init_orchestrator()
        if orchestrator:
            with st.spinner("Reflexion en cours..."):
                try:
                    result = orchestrator.route(user_input, st.session_state.discipline)
                    assistant_message = {
                        "role": "assistant",
                        "content": result["response"],
                        "agents_used": result.get("agents_used", []),
                        "rag_sources": result.get("rag_sources", []),
                        "mediation_proposals": result.get("mediation_proposals", []),
                    }
                    st.session_state.messages.append(assistant_message)

                    with st.chat_message("assistant"):
                        st.markdown(result["response"])
                        _render_message_details(assistant_message, key_prefix="live")

                    st.rerun()
                except Exception as exc:
                    _render_notice(
                        f"Erreur lors du traitement : {str(exc)}",
                        kind="error",
                    )
                    logger.error("Erreur orchestrateur : %s", exc)
        else:
            _render_notice("Orchestrateur indisponible", kind="error")


with tab_glossary:
    glossary = init_glossary()

    if glossary:
        correspondances = glossary.get_all()
        st.markdown(f"## {len(correspondances)} correspondances validees")

        if not correspondances:
            _render_notice(
                "Aucune correspondance validee pour l'instant. "
                "Validez des mediations dans le chat pour les ajouter.",
                kind="info",
            )
        else:
            display_data = [
                {
                    "Terme source": item.get("terme_source", ""),
                    "Discipline source": item.get("discipline_source", ""),
                    "Terme cible": item.get("terme_cible", ""),
                    "Discipline cible": item.get("discipline_cible", ""),
                    "Analogie": f"{item.get('analogie', '')[:50]}...",
                    "Valide par": item.get("validé_par", ""),
                    "Date": item.get("date_validation", "")[:10],
                }
                for item in correspondances
            ]
            st.dataframe(display_data, use_container_width=True)

            json_data = json.dumps(correspondances, indent=2, ensure_ascii=False)
            col_export, col_clear = st.columns(2)

            with col_export:
                st.download_button(
                    label="Exporter JSON",
                    data=json_data,
                    file_name=f"bridge_gdid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            with col_clear:
                confirm_clear = st.checkbox(
                    "Confirmer la suppression",
                    key="confirm_clear_glossary",
                )
                if st.button(
                    "Vider le glossaire",
                    use_container_width=True,
                    disabled=not confirm_clear,
                ):
                    glossary.clear()
                    _render_notice("Glossaire vide", kind="success")
                    st.rerun()
    else:
        _render_notice("Glossaire indisponible", kind="error")


with tab_corpus:
    st.markdown("## Documents indexes")

    disciplines_docs = {
        "Finance": "documents/finance",
        "Informatique": "documents/informatique",
    }

    for discipline, directory in disciplines_docs.items():
        color = DISCIPLINE_COLORS.get(discipline, "#7a8399")
        st.markdown(
            f"### <span style='color: {color}'>"
            f"{html.escape(discipline)}</span>",
            unsafe_allow_html=True,
        )

        dir_path = Path(directory)
        if dir_path.exists():
            files = sorted(
                file_path
                for file_path in dir_path.glob("*.*")
                if file_path.is_file()
            )
            if files:
                for file_path in files:
                    _display_corpus_file(file_path)
            else:
                _render_notice("Aucun document dans ce repertoire", kind="info")
        else:
            _render_notice(f"Repertoire non trouve : {directory}", kind="warning")

        st.divider()


with tab_about:
    st.markdown("# BRIDGE")
    st.markdown(f"## {BRIDGE_FULL_NAME}")

    st.markdown(
        """
### Description

BRIDGE est un systeme multi-agent alimente par IA pour faciliter la collaboration
interdisciplinaire entre chercheurs. Il reduit les barrieres terminologiques et
epistemiques en utilisant une generation augmentee par recuperation (RAG) et
la mediation intelligente de concepts polysemes.

### Architecture

```text
Interface Streamlit
        |
Orchestrateur ReAct
        |
Agents Finance + Informatique
        |
GDID et validation humaine
        |
Corpus RAG ChromaDB
```

### Stack technique
"""
    )

    tech_stack = {
        "Composant": [
            "LLM",
            "Embeddings",
            "Base vectorielle",
            "Framework LLM",
            "Interface",
            "Parsing PDF",
            "Env",
            "Langage",
            "Containerisation",
        ],
        "Outil": [
            "Ollama local (llama3.2:1b)",
            "sentence-transformers (paraphrase-multilingual-mpnet-base-v2)",
            "ChromaDB local persistant",
            "LangChain + LangChain-community",
            "Streamlit",
            "PyPDF2",
            "python-dotenv",
            "Python 3.11+",
            "Docker + Docker Compose",
        ],
    }
    st.dataframe(pd.DataFrame(tech_stack), use_container_width=True)

    st.markdown(
        """
### Auteurs

- **Ahrim Hamza** - Developpement
- **Mouafiq Saad** - Recherche

**Superviseur** : Pr. Bennis

**Institution** : Universite Mohammed V de Rabat

Departement MIS - Modelisation et Informatique Scientifique

**Annee** : 2026

---

### LLM local gratuit

BRIDGE utilise Ollama par defaut. Installez le modele avec `ollama pull llama3.2:1b`.
"""
    )
