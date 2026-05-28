"""
Récupérateur RAG pour BRIDGE.

Module responsable de la récupération des documents pertinents
depuis ChromaDB en réponse à une question utilisateur.
"""

import logging
import os
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import collection_name_for_discipline, load_environment

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Récupérateur Retrieval-Augmented Generation pour BRIDGE.
    
    Utilise ChromaDB et sentence-transformers pour rechercher
    les documents les plus pertinents par rapport à une question.
    """
    
    def __init__(self) -> None:
        """
        Initialise le récupérateur RAG.
        
        Raises:
            RuntimeError: Si ChromaDB ne peut pas être initialisé.
        """
        try:
            load_environment()
            chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
            self.client: chromadb.PersistentClient = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False),
            )
            
            # Chargement du modèle d'embedding
            self.embedding_model: SentenceTransformer = SentenceTransformer(
                "paraphrase-multilingual-mpnet-base-v2"
            )
            
            logger.info("Récupérateur RAG initialisé")
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation du récupérateur RAG : {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def retrieve(
        self,
        question: str,
        discipline: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Récupère les documents les plus pertinents pour une discipline donnée.
        
        Args:
            question: Question de l'utilisateur.
            discipline: Discipline cible (Finance ou Informatique).
            k: Nombre de résultats à retourner. Défaut: 3.
        
        Returns:
            Liste de dictionnaires avec clés :
            - content (str): Contenu du chunk
            - source (str): Nom du fichier source
            - discipline (str): Discipline
        """
        try:
            question_embedding = self.embedding_model.encode(
                question,
                convert_to_numpy=False
            ).tolist()
            return self._retrieve_with_embedding(question_embedding, discipline, k)
        except Exception as e:
            error_msg = f"Erreur lors de la récupération RAG : {str(e)}"
            logger.error(error_msg)
            return []

    def _retrieve_with_embedding(
        self,
        embedding: List[float],
        discipline: str,
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les documents avec un embedding de question déjà calculé.
        """
        try:
            collection_name = collection_name_for_discipline(discipline)
            
            # Vérification de l'existence de la collection
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                warning_msg = (
                    f"Collection ChromaDB non trouvée : {collection_name}. "
                    f"Collections disponibles : {collection_names}"
                )
                logger.warning(warning_msg)
                return []
            
            collection = self.client.get_collection(name=collection_name)

            # Requête à ChromaDB
            logger.debug(f"Recherche RAG pour la discipline : {discipline}")
            
            results = collection.query(
                query_embeddings=[embedding],
                n_results=k
            )
            
            # Formatage des résultats
            formatted_results = []
            
            if results and results["documents"]:
                for i, (content, metadata) in enumerate(
                    zip(results["documents"][0], results["metadatas"][0])
                ):
                    formatted_results.append({
                        "content": content,
                        "source": metadata.get("source", "inconnu"),
                        "discipline": metadata.get("discipline", discipline)
                    })
            
            logger.debug(f"Récupération réussie : {len(formatted_results)} documents")
            return formatted_results
        
        except Exception as e:
            error_msg = f"Erreur lors de la récupération RAG : {str(e)}"
            logger.error(error_msg)
            return []
    
    def retrieve_multi(
        self,
        question: str,
        disciplines: List[str],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Récupère les documents les plus pertinents pour plusieurs disciplines.
        
        Args:
            question: Question de l'utilisateur.
            disciplines: Liste des disciplines cibles.
            k: Nombre de résultats par discipline. Défaut: 3.
        
        Returns:
            Liste agrégée de dictionnaires de résultats.
        """
        try:
            question_embedding = self.embedding_model.encode(
                question,
                convert_to_numpy=False
            ).tolist()
            all_results = []
            
            logger.debug(f"Récupération multi-disciplinaire pour : {question[:50]}...")
            
            for discipline in disciplines:
                results = self._retrieve_with_embedding(question_embedding, discipline, k)
                all_results.extend(results)
            
            logger.info(f"Récupération multi-disciplinaire : {len(all_results)} documents")
            return all_results
        
        except Exception as e:
            error_msg = f"Erreur lors de la récupération multi-disciplinaire : {str(e)}"
            logger.error(error_msg)
            return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        retriever = RAGRetriever()
        print("Récupérateur RAG initialisé avec succès")
    except RuntimeError as e:
        print(f"Erreur : {e}")
