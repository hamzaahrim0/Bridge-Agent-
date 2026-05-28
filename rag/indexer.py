"""
Indexeur RAG pour BRIDGE.

Module responsable de l'indexation des documents dans ChromaDB
en utilisant des embeddings multilinguels.
"""

import logging
import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

from config import collection_name_for_discipline, load_environment

logger = logging.getLogger(__name__)

DISCIPLINE_DIRECTORIES = {
    "Finance": "./documents/finance",
    "Informatique": "./documents/informatique",
}


def _get_embedding_function():
    """
    Crée et retourne une fonction d'embedding utilisant sentence-transformers.
    
    Returns:
        Fonction callable d'embedding.
    """
    model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    
    def embed_fn(texts: List[str]) -> List[List[float]]:
        """Encode une liste de textes en embeddings."""
        embeddings = model.encode(texts, convert_to_numpy=False)
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()

        return [
            embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
            for embedding in embeddings
        ]
    
    return embed_fn


def _load_documents(directory: str) -> List[tuple]:
    """
    Charge tous les documents .txt et .pdf d'un répertoire.
    
    Args:
        directory: Chemin du répertoire contenant les documents.
    
    Returns:
        Liste de tuples (contenu, nom_fichier).
    """
    documents = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.warning(f"Répertoire non trouvé : {directory}")
        return documents
    
    # Chargement des fichiers .txt
    for txt_file in dir_path.glob("*.txt"):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append((content, txt_file.name))
                logger.debug(f"Fichier TXT chargé : {txt_file.name}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {txt_file.name} : {str(e)}")
    
    # Chargement des fichiers .pdf
    for pdf_file in dir_path.glob("*.pdf"):
        try:
            reader = PdfReader(str(pdf_file))
            content = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            ).strip()
            if not content:
                logger.warning(f"PDF sans texte extractible : {pdf_file.name}")
                continue
            documents.append((content, pdf_file.name))
            logger.debug(f"Fichier PDF chargé : {pdf_file.name}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {pdf_file.name} : {str(e)}")
    
    return documents


def _index_discipline(
    client: chromadb.PersistentClient,
    discipline: str,
    directory: str,
    splitter: RecursiveCharacterTextSplitter,
    embedding_fn
) -> None:
    """
    Indexe les documents d'une discipline donnée.
    
    Args:
        client: Client ChromaDB persistant.
        discipline: Nom de la discipline (Finance ou Informatique).
        directory: Chemin du répertoire contenant les documents.
        splitter: Splitter de texte configuré.
        embedding_fn: Fonction d'embedding.
    """
    collection_name = collection_name_for_discipline(discipline)
    
    logger.info(f"Indexation {discipline}...")
    
    # Chargement des documents
    documents = _load_documents(directory)
    
    if not documents:
        logger.warning(f"Aucun document trouvé pour {discipline}")
        return
    
    # Suppression et recréation de la collection (idempotence)
    try:
        client.delete_collection(name=collection_name)
        logger.debug(f"Collection existante supprimée : {collection_name}")
    except Exception:
        pass
    
    # Création de la nouvelle collection
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Traitement et indexation des documents
    total_chunks = 0
    
    for content, filename in documents:
        try:
            # Découpage du texte
            chunks = splitter.split_text(content)
            
            # Création des embeddings
            embeddings = embedding_fn(chunks)
            
            # Ajout à la collection avec métadonnées
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Convertir embedding en list si c'est un numpy array
                if not isinstance(embedding, list):
                    embedding = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                
                doc_id = f"{filename}_{i}"
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "source": filename,
                        "discipline": discipline,
                        "chunk_index": i
                    }]
                )
                total_chunks += 1
            
            logger.debug(f"Document indexé : {filename} ({len(chunks)} chunks)")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation de {filename} : {str(e)}")
    
    logger.info(f"✓ {discipline} indexée ({total_chunks} chunks)")


def index_documents() -> None:
    """
    Indexe tous les documents Finance et Informatique dans ChromaDB.
    
    Opération idempotente : supprime et recrée les collections à chaque run.
    
    Raises:
        RuntimeError: En cas d'erreur irrécupérable.
    """
    try:
        load_environment()
        logger.info("Démarrage de l'indexation des documents BRIDGE...")
        
        # Configuration
        chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Initialisation du splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialisation de ChromaDB
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info(f"Client ChromaDB initialisé : {chroma_path}")
        
        # Fonction d'embedding
        embedding_fn = _get_embedding_function()
        logger.info("Modèle d'embedding chargé : paraphrase-multilingual-mpnet-base-v2")

        active_collections = {
            collection_name_for_discipline(discipline)
            for discipline in DISCIPLINE_DIRECTORIES
        }
        for collection in client.list_collections():
            if collection.name.startswith("bridge_") and collection.name not in active_collections:
                client.delete_collection(name=collection.name)
                logger.info(f"Collection obsolète supprimée : {collection.name}")

        # Indexation des deux disciplines du prototype ciblé.
        for discipline, directory in DISCIPLINE_DIRECTORIES.items():
            _index_discipline(client, discipline, directory, splitter, embedding_fn)
        
        logger.info("✓ Indexation terminée avec succès")
    
    except Exception as e:
        error_msg = f"Erreur fatale lors de l'indexation : {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    index_documents()
