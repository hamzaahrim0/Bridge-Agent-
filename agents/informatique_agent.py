"""
Agent Informatique pour BRIDGE.

Agent spécialisé dans l'explication de concepts informatiques
et la médiation interdisciplinaire depuis la perspective informatique.
"""

import logging
from typing import Optional

from llm.provider import LLMProvider
from prompts.informatique_prompt import INFORMATIQUE_AGENT_SYSTEM_PROMPT
from agents.base_agent import Agent

logger = logging.getLogger(__name__)


class InformatiqueAgent(Agent):
    """
    Agent disciplinaire spécialisé en Informatique.
    
    Explique les concepts informatiques et établit des ponts
    vers la Finance.
    """
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        """
        Initialise l'agent Informatique.

        Args:
            llm_provider: Fournisseur LLM partagé par l'orchestrateur.
        
        Raises:
            RuntimeError: Si le fournisseur LLM ne peut pas être initialisé.
        """
        try:
            self.llm_provider: LLMProvider = llm_provider or LLMProvider()
            logger.info("Agent Informatique initialisé")
        except Exception as e:
            error_msg = f"Impossible d'initialiser l'agent Informatique : {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    @property
    def discipline(self) -> str:
        """
        Retourne le nom de la discipline de cet agent.
        
        Returns:
            "Informatique"
        """
        return "Informatique"
    
    @property
    def color(self) -> str:
        """
        Retourne la couleur hexadécimale associée à l'agent Informatique.
        
        Returns:
            Code couleur vert : "#2ca02c"
        """
        return "#2ca02c"
    
    def respond(self, question: str, user_discipline: str, rag_context: str) -> str:
        """
        Génère une réponse informatique à la question.
        
        Construit un prompt qui inclut le contexte RAG et génère une réponse
        en utilisant le prompt système Informatique.
        
        Args:
            question: La question posée par l'utilisateur.
            user_discipline: La discipline de l'utilisateur.
            rag_context: Contexte extrait de la base de données vectorielle Informatique.
        
        Returns:
            Réponse texte générée par l'agent Informatique.
        
        Raises:
            RuntimeError: En cas d'erreur lors de la génération LLM.
        """
        try:
            # Construction du prompt avec contexte RAG
            prompt = f"""Discipline de l'utilisateur : {user_discipline}

Question : {question}

Contexte RAG (documents Informatique) :
{rag_context}

Réponds à la question en expliquant les concepts informatiques pertinents.
Utilise le contexte RAG fourni et cite les sources.
Détecte et signale les termes polysèmes qui pourraient avoir des sens différents 
selon la discipline de l'utilisateur."""
            
            logger.debug(f"Génération de réponse Informatique pour : {question[:50]}...")
            
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=INFORMATIQUE_AGENT_SYSTEM_PROMPT
            )
            
            # Détection des termes polysèmes dans la réponse
            ambiguous = self.detect_ambiguous_terms(response)
            if ambiguous:
                logger.info(f"Termes polysèmes détectés : {ambiguous}")
            
            return response
        
        except RuntimeError as e:
            error_msg = f"Erreur lors de la génération de réponse Informatique : {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        agent = InformatiqueAgent()
        print(f"Agent Informatique créé : discipline={agent.discipline}, couleur={agent.color}")
    except RuntimeError as e:
        print(f"Erreur : {e}")
