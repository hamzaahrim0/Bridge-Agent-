# BRIDGE - Status

## Portée actuelle

BRIDGE est recentré sur deux disciplines :

- Finance
- Informatique

Le système utilise un LLM local via Ollama, un RAG local ChromaDB et un glossaire
GDID persistant en JSON.

## Composants actifs

- `app.py` : interface Streamlit.
- `orchestrator.py` : routage ReAct Finance/Informatique.
- `agents/finance_agent.py` : agent Finance.
- `agents/informatique_agent.py` : agent Informatique.
- `rag/indexer.py` : indexation des documents Finance/Informatique.
- `rag/retriever.py` : récupération ChromaDB.
- `llm/provider.py` : appels Ollama locaux.
- `gdid/glossary.py` : gestion du glossaire interdisciplinaire.

## Corpus RAG

Objectif du corpus :

- 25 papiers Finance.
- 25 papiers Informatique.
- Focalisation : finance quantitative, IA, séries temporelles financières,
  optimisation de portefeuille, pricing, hedging, trading automatique,
  graph learning, transformers et modèles de langage financiers.

Le manifeste du corpus se trouve dans `documents/corpus_manifest.json`.

## Commandes utiles

```bash
docker compose up --build
```

```bash
python -m rag.indexer
```
