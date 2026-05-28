"""
Classe de base pour les agents disciplinaires BRIDGE.

Module définissant l'interface abstraite que tous les agents
disciplinaires doivent implémenter.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class Agent(ABC):
    """
    Classe abstraite de base pour tous les agents disciplinaires BRIDGE.
    
    Définit l'interface que chaque agent (Finance, Informatique)
    doit implémenter pour participer à la collaboration interdisciplinaire.
    """
    
    @property
    @abstractmethod
    def discipline(self) -> str:
        """
        Retourne le nom de la discipline de cet agent.
        
        Returns:
            Chaîne représentant la discipline : "Finance" ou "Informatique".
        """
        pass
    
    @property
    @abstractmethod
    def color(self) -> str:
        """
        Retourne la couleur hexadécimale associée à cet agent pour l'UI.
        
        Returns:
            Code couleur hexadécimal (ex: "#1f77b4").
        """
        pass
    
    @abstractmethod
    def respond(self, question: str, user_discipline: str, rag_context: str) -> str:
        """
        Génère une réponse à la question en utilisant le contexte RAG.
        
        Args:
            question: La question posée par l'utilisateur.
            user_discipline: La discipline de l'utilisateur.
            rag_context: Contexte extrait de la base de données vectorielle.
        
        Returns:
            Réponse texte générée par l'agent.
        
        Raises:
            RuntimeError: En cas d'erreur lors de la génération.
        """
        pass
    
    def detect_ambiguous_terms(self, text: str) -> List[str]:
        """
        Détecte les termes polysèmes dans un texte.
        
        Cherche dans le texte les termes qui ont des significations différentes
        selon les disciplines. Utile pour signaler les ambiguïtés conceptuelles.
        
        Args:
            text: Texte à analyser.
        
        Returns:
            Liste des termes polysèmes trouvés dans le texte.
        """
        polysemous_terms = [
            "modèle",
            "optimisation",
            "apprentissage",
            "évaluation",
            "performance",
            "algorithme",
            "réseau",
            "paramètre",
            "régression",
            "variable",
            "liquidité",
            "signal"
        ]
        
        text_lower = text.lower()
        found_terms = []
        
        for term in polysemous_terms:
            if term in text_lower:
                if term not in found_terms:
                    found_terms.append(term)
        
        if found_terms:
            logger.debug(
                f"Termes polysèmes détectés dans {self.discipline} : {found_terms}"
            )
        
        return found_terms


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Classe abstraite Agent chargée. À implémenter par les agents concrets.")
