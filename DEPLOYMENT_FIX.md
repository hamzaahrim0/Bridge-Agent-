# BRIDGE - Notes de Déploiement

Cette version est recentrée sur une pile locale :

- Ollama pour le LLM.
- ChromaDB pour le RAG.
- Streamlit pour l'interface.
- Deux disciplines : Finance et Informatique.

Le corpus RAG doit être réindexé après tout remplacement de document :

```bash
docker compose run --rm bridge-indexer
```
