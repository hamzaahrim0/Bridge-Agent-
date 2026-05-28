# BRIDGE

**Bridging Research Intelligence for Disciplinary Gap Eradication**

BRIDGE is a local research prototype for agentic, retrieval-augmented
interdisciplinary assistance between **Finance** and **Computer Science**. It
helps researchers ask cross-domain questions, retrieve grounded context from a
local corpus, compare disciplinary perspectives, detect polysemous terms, and
validate terminology bridges in a dynamic interdisciplinary glossary.

> Université Mohammed V de Rabat, Département MIS, 2026  
> Authors: Ahrim Hamza 
## What BRIDGE Does

- Routes a user question to Finance and/or Computer Science agents.
- Retrieves supporting passages from a local ChromaDB vector store.
- Generates concise discipline-aware answers through a local Ollama model.
- Detects ambiguous terms such as `modèle`, `optimisation`, `performance`,
  `signal`, `réseau`, `variable`, and `régression`.
- Proposes terminology mediation entries that can be validated by a human.
- Stores validated terminology mappings in a JSON-based GDID glossary.

BRIDGE is intentionally local-first: no hosted LLM API key is required.

## Architecture

```text
Interface Streamlit
        |
        v
Orchestrateur ReAct
        |
        v
Agents Finance + Informatique
        |
        v
RAG local ChromaDB
        |
        v
Corpus documentaire arXiv
        |
        v
GDID JSON pour les médiations validées
```

### Main Components

| Component | Responsibility | File |
| --- | --- | --- |
| Streamlit UI | Chat, corpus view, GDID view, status panel | `app.py` |
| Orchestrator | Routing, ReAct flow, RAG calls, agent coordination | `orchestrator.py` |
| Finance agent | Finance-grounded explanations and bridges | `agents/finance_agent.py` |
| Computer Science agent | Computing-grounded explanations and bridges | `agents/informatique_agent.py` |
| RAG indexer | PDF/TXT loading, chunking, embedding, ChromaDB indexing | `rag/indexer.py` |
| RAG retriever | Multi-discipline vector retrieval | `rag/retriever.py` |
| LLM provider | Local Ollama HTTP calls | `llm/provider.py` |
| GDID glossary | Persistent terminology mappings | `gdid/glossary.py` |
| Report generator | Academic PDF generation with ReportLab | `reports/generate_bridge_report.py` |

## Agentic Flow

1. The user selects a source discipline: `Finance` or `Informatique`.
2. The orchestrator handles simple greetings without invoking the LLM.
3. The question is normalized and routed by deterministic keyword heuristics.
4. Optional LLM-based routing can be enabled with `LLM_ROUTING_ENABLED=true`.
5. The RAG retriever searches the relevant ChromaDB collections.
6. The selected agents generate discipline-specific responses using the RAG
   context.
7. Multi-agent answers are merged or juxtaposed, depending on configuration.
8. Ambiguous terms are detected.
9. Mediation proposals can be generated and validated into the GDID glossary.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.11+ |
| UI | Streamlit |
| LLM runtime | Ollama local |
| Default model | `llama3.2:1b` |
| Vector database | ChromaDB |
| Embeddings | `sentence-transformers` |
| Embedding model | `paraphrase-multilingual-mpnet-base-v2` |
| PDF parsing | PyPDF2 |
| Configuration | python-dotenv |
| Deployment | Docker, Docker Compose |
| Report generation | ReportLab |

## Repository Layout

```text
bridge/
├── app.py
├── orchestrator.py
├── config.py
├── agents/
│   ├── base_agent.py
│   ├── finance_agent.py
│   └── informatique_agent.py
├── rag/
│   ├── indexer.py
│   └── retriever.py
├── llm/
│   └── provider.py
├── prompts/
│   ├── finance_prompt.py
│   ├── informatique_prompt.py
│   └── orchestrator_prompt.py
├── gdid/
│   ├── glossary.py
│   └── gdid.json
├── documents/
│   ├── CORPUS.md
│   ├── corpus_manifest.json
│   ├── finance/
│   └── informatique/
├── reports/
│   └── generate_bridge_report.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Corpus

The intended RAG corpus contains 50 arXiv papers:

- 25 Finance papers.
- 25 Computer Science papers.

The repository keeps `documents/CORPUS.md` and
`documents/corpus_manifest.json` as the corpus description. The PDF files are
ignored by Git to keep the repository lightweight. Place PDFs under:

```text
documents/finance/
documents/informatique/
```

Then reindex the corpus before using RAG.

## Local Installation

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2:1b
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Docker Usage

Make sure Ollama is running on the host and the configured model is available:

```bash
ollama pull llama3.2:1b
```

Start the full stack:

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | Role |
| --- | --- |
| `bridge-chromadb` | Local vector store service |
| `bridge-indexer` | Corpus indexing job |
| `bridge-app` | Streamlit application on port `8501` |

## Reindexing

From the UI, use the sidebar button:

```text
Réindexer les documents
```

From the terminal:

```bash
python -m rag.indexer
```

With Docker:

```bash
docker compose run --rm bridge-indexer
```

Reindex after adding or replacing PDFs, or after changing `CHUNK_SIZE`,
`CHUNK_OVERLAP`, or embedding settings.

## Key Environment Variables

| Variable | Default / Example | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` locally | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2:1b` | Local LLM model |
| `LLM_TIMEOUT` | `300` | LLM request timeout |
| `OLLAMA_NUM_PREDICT` | `450` | Maximum generated tokens |
| `OLLAMA_NUM_CTX` | `4096` | Context window setting |
| `LLM_ROUTING_ENABLED` | `false` | Optional LLM-based routing |
| `BRIDGE_LLM_MERGE_ENABLED` | `true` | Enable LLM answer merging |
| `BRIDGE_MEDIATION_ENABLED` | `true` | Enable mediation proposals |
| `CHUNK_SIZE` | `800` | RAG chunk size |
| `CHUNK_OVERLAP` | `150` | RAG chunk overlap |
| `RAG_TOP_K` | `3` | Retrieved chunks per discipline |
| `CHROMA_DB_PATH` | `./chroma_db` | Local ChromaDB persistence path |
| `GDID_PATH` | `./gdid/gdid.json` | Glossary JSON path |

## Generate the Academic Report

BRIDGE includes a ReportLab-based report generator:

```bash
python reports/generate_bridge_report.py
```

The generated PDF is written to:

```text
reports/BRIDGE_Technical_Report.pdf
```

Generated PDFs are ignored by Git; regenerate them locally when needed.

## Development Notes

- Keep `.env`, `chroma_db/`, PDF corpora, caches, and generated PDFs out of Git.
- Keep `gdid/gdid.json` tracked only as an initial empty glossary skeleton.
- Use deterministic routing by default for fast local testing.
- Use LLM routing and mediation only when Ollama is responsive enough for the
  configured model.

## Limitations

BRIDGE is a research prototype. It does not guarantee scientific truth, full
source fidelity, or production-grade reliability. Known limitations include:

- dependence on a local Ollama runtime;
- variable quality and latency depending on the selected local model;
- imperfect PDF extraction;
- a corpus currently limited to Finance and Computer Science;
- simple keyword-based polysemy detection;
- no complete quantitative evaluation protocol yet.

## License

BRIDGE IS AN OPEN-SOURCE PROJECT

