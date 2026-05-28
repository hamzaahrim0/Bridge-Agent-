# BRIDGE - Deployment

## Prérequis

- Docker et Docker Compose.
- Ollama lancé sur la machine hôte.
- Le modèle configuré dans `.env`, par défaut `llama3.2:1b`.

```bash
ollama pull llama3.2:1b
```

## Lancement

```bash
cd /home/hamzaahrim/Desktop/HERMES-SEMANTIC/bridge
docker compose up --build
```

Services :

- `bridge-chromadb` : stockage vectoriel local.
- `bridge-indexer` : indexation des documents Finance/Informatique.
- `bridge-app` : interface Streamlit sur `http://localhost:8501`.

## Variables principales

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:1b
LLM_TIMEOUT=300
LLM_MAX_TOKENS=192
OLLAMA_NUM_PREDICT=160
OLLAMA_NUM_CTX=2048
CHROMA_DB_PATH=./chroma_db
GDID_PATH=./gdid/gdid.json
```

## Réindexer

Après ajout de documents :

```bash
docker compose run --rm bridge-indexer
```

Ou depuis l'interface Streamlit avec le bouton **Réindexer les documents**.
