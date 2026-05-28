# BRIDGE Requirements

BRIDGE fonctionne avec une pile locale :

```text
streamlit==1.40.2
langchain==0.2.16
langchain-community==0.2.16
chromadb==0.5.3
posthog<3.0.0
sentence-transformers==2.7.0
torch==2.3.1
PyPDF2==3.0.1
python-dotenv==1.0.0
pydantic==2.8.2
requests==2.32.3
reportlab==4.4.10
```

Les dépendances couvrent l'interface Streamlit, le RAG local, les embeddings
multilingues, le parsing PDF, les appels HTTP vers Ollama et la génération du
rapport technique PDF.
