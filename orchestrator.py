"""
Orchestrateur BRIDGE avec pattern ReAct.

Module responsable de la coordination entre agents disciplinaires
et de la médiation des concepts polysèmes.
"""

import json
import logging
import os
import re
import unicodedata
from typing import Dict, List, Any

from llm.provider import LLMProvider
from rag.retriever import RAGRetriever
from agents.finance_agent import FinanceAgent
from agents.informatique_agent import InformatiqueAgent
from agents.base_agent import Agent

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrateur BRIDGE utilisant le pattern ReAct.
    
    Coordonne l'interaction entre agents disciplinaires,
    récupère le contexte RAG, détecte les termes polysèmes
    et génère des propositions de médiation.
    """

    VALID_DISCIPLINES = ["Finance", "Informatique"]
    LLM_ROUTING_ENABLED_VALUES = {"1", "true", "yes", "on"}
    ENABLED_VALUES = {"1", "true", "yes", "on"}
    SMALL_TALK_MESSAGES = {
        "bonjour",
        "bonsoir",
        "salut",
        "hello",
        "hi",
        "coucou",
        "salam",
        "ca va",
        "merci",
        "merci beaucoup",
    }
    DISCIPLINE_KEYWORDS = {
        "Finance": [
            "finance", "financier", "financiere", "portefeuille", "marche",
            "bourse", "banque", "credit", "capital", "actif", "rendement",
            "risque", "volatilite", "investissement", "taux", "cout",
        ],
        "Informatique": [
            "informatique", "algorithme", "code", "programmation", "logiciel",
            "donnee", "donnees", "base de donnees", "ia", "intelligence artificielle",
            "machine learning", "apprentissage automatique", "reseau de neurones",
            "neurone", "architecture", "systeme", "serveur",
        ],
    }
    POLYSEMOUS_DISCIPLINES = {
        "optimisation": ["Finance", "Informatique"],
        "modele": ["Finance", "Informatique"],
        "performance": ["Finance", "Informatique"],
        "apprentissage": ["Informatique"],
        "reseau": ["Finance", "Informatique"],
        "parametre": ["Finance", "Informatique"],
        "regression": ["Finance", "Informatique"],
        "variable": ["Finance", "Informatique"],
    }
    
    def __init__(self) -> None:
        """
        Initialise l'orchestrateur avec tous les composants.
        
        Raises:
            RuntimeError: Si un composant critique ne peut pas être initialisé.
        """
        try:
            logger.info("Initialisation de l'Orchestrateur BRIDGE...")
            
            self.llm_provider: LLMProvider = LLMProvider()
            logger.debug("✓ Fournisseur LLM initialisé")
            
            self.retriever: RAGRetriever = RAGRetriever()
            logger.debug("✓ Récupérateur RAG initialisé")
            
            # Initialisation des deux agents avec le fournisseur LLM partagé.
            self.finance_agent: FinanceAgent = FinanceAgent(
                llm_provider=self.llm_provider
            )
            self.informatique_agent: InformatiqueAgent = InformatiqueAgent(
                llm_provider=self.llm_provider
            )
            logger.debug("✓ Tous les agents initialisés")
            
            # Dictionnaire d'accès aux agents
            self.agents: Dict[str, Agent] = {
                "Finance": self.finance_agent,
                "Informatique": self.informatique_agent
            }
            
            logger.info("✓ Orchestrateur BRIDGE prêt")
        
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de l'Orchestrateur : {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour les règles rapides sans dépendre du LLM."""
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = re.sub(r"[^a-zA-Z0-9]+", " ", ascii_text).lower()
        return re.sub(r"\s+", " ", ascii_text).strip()

    def _contains_keyword(self, normalized_text: str, keyword: str) -> bool:
        """Teste un mot-clé entier pour éviter les faux positifs par sous-chaîne."""
        return re.search(rf"\b{re.escape(keyword)}\b", normalized_text) is not None

    def _env_bool(self, name: str, default: bool = False) -> bool:
        """Lit un booléen d'environnement avec une valeur par défaut explicite."""
        raw_value = os.getenv(name)
        if raw_value is None:
            return default
        return raw_value.strip().lower() in self.ENABLED_VALUES

    def _env_int(self, name: str, default: int) -> int:
        """Lit un entier d'environnement avec repli si la valeur est invalide."""
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            logger.warning("Variable %s invalide, valeur utilisée : %s", name, default)
            return default

    def _ordered_disciplines(
        self,
        disciplines: List[str],
        user_discipline: str
    ) -> List[str]:
        """Déduplique les disciplines en gardant la discipline utilisateur en premier."""
        ordered: List[str] = []

        if user_discipline in self.VALID_DISCIPLINES:
            ordered.append(user_discipline)

        for discipline in disciplines:
            if discipline in self.VALID_DISCIPLINES and discipline not in ordered:
                ordered.append(discipline)

        return ordered or ["Finance"]

    def _small_talk_response(self, question: str) -> str:
        """
        Répond aux salutations simples sans lancer RAG + LLM.

        Cela évite qu'un message comme "Bonjour" déclenche un appel lourd
        à llama3.1:8b et finisse en timeout.
        """
        normalized = self._normalize_text(question)
        if normalized not in self.SMALL_TALK_MESSAGES:
            return ""

        return (
            "Bonjour ! Je suis BRIDGE. Posez-moi une question interdisciplinaire "
            "en Finance ou Informatique, et je mobiliserai les agents "
            "pertinents avec les sources RAG disponibles."
        )

    def _detect_disciplines_by_keywords(
        self,
        question: str,
        user_discipline: str
    ) -> List[str]:
        """Route rapidement les questions par mots-clés avant d'appeler le LLM."""
        normalized = self._normalize_text(question)
        explicit_disciplines: List[str] = []

        for discipline, keywords in self.DISCIPLINE_KEYWORDS.items():
            if any(self._contains_keyword(normalized, keyword) for keyword in keywords):
                explicit_disciplines.append(discipline)

        if explicit_disciplines:
            return self._ordered_disciplines(explicit_disciplines, user_discipline)

        inferred_disciplines: List[str] = []

        for keyword, disciplines in self.POLYSEMOUS_DISCIPLINES.items():
            if self._contains_keyword(normalized, keyword):
                inferred_disciplines.extend(disciplines)

        if not inferred_disciplines:
            return []

        max_inferred = self._env_int("BRIDGE_MAX_INFERRED_DISCIPLINES", 2)
        return self._ordered_disciplines(
            inferred_disciplines,
            user_discipline,
        )[:max_inferred]
    
    def _detect_target_disciplines(
        self,
        question: str,
        user_discipline: str
    ) -> List[str]:
        """
        THOUGHT 1 — Détecte les disciplines cibles pertinentes.
        
        Utilise d'abord des règles déterministes pour éviter un appel LLM
        inutile. Le routage LLM reste disponible avec LLM_ROUTING_ENABLED=true.
        
        Args:
            question: La question de l'utilisateur.
            user_discipline: La discipline de l'utilisateur.
        
        Returns:
            Liste des disciplines cibles : ["Finance", "Informatique"]
        """
        heuristic_disciplines = self._detect_disciplines_by_keywords(
            question,
            user_discipline,
        )
        if heuristic_disciplines:
            logger.info(
                "Disciplines cibles détectées par mots-clés : %s",
                heuristic_disciplines,
            )
            return heuristic_disciplines

        llm_routing_enabled = os.getenv(
            "LLM_ROUTING_ENABLED",
            "false",
        ).strip().lower() in self.LLM_ROUTING_ENABLED_VALUES

        if not llm_routing_enabled:
            disciplines = self._ordered_disciplines([], user_discipline)
            logger.info(
                "Routage LLM désactivé, discipline de repli : %s",
                disciplines,
            )
            return disciplines

        try:
            prompt = f"""Analyse la question suivante et identifie les disciplines académiques 
qui pourraient apporter une réponse pertinente.

Question : "{question}"
Discipline de l'utilisateur : {user_discipline}

Disciplines disponibles : Finance, Informatique

Réponds uniquement avec une liste JSON contenant les noms des disciplines pertinentes.
Format : ["Discipline1", "Discipline2"]
Ne réponds RIEN d'autre."""
            
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt="Tu es un expert en identification de domaines académiques. Réponds de manière très brève."
            )
            
            disciplines = self._parse_json_response(response, list)
            if disciplines is None:
                logger.warning("Impossible de parser la réponse LLM pour les disciplines cibles")
                disciplines = [user_discipline]
            
            # Validation des disciplines
            disciplines = self._ordered_disciplines(disciplines, user_discipline)
            
            logger.info(f"Disciplines cibles détectées : {disciplines}")
            return disciplines
        
        except Exception as e:
            logger.error(f"Erreur lors de la détection des disciplines : {str(e)}")
            return [user_discipline]

    def _parse_json_response(self, response: str, expected_type: type) -> Any:
        """
        Extrait du JSON même si le modèle ajoute du texte autour.

        Les modèles locaux renvoient parfois des blocs ```json ...```;
        cette méthode garde l'orchestrateur robuste sans complexifier les prompts.
        """
        text = response.strip()
        candidates = [text]

        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3:
                candidates.append("\n".join(lines[1:-1]).strip())

        boundaries = {
            list: ("[", "]"),
            dict: ("{", "}"),
        }
        start_token, end_token = boundaries.get(expected_type, ("", ""))
        if start_token and end_token:
            start = text.find(start_token)
            end = text.rfind(end_token)
            if start != -1 and end != -1 and end > start:
                candidates.append(text[start:end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, expected_type):
                    return parsed
            except json.JSONDecodeError:
                continue

        return None
    
    def _format_rag_context(self, rag_sources: List[Dict[str, Any]]) -> str:
        """
        Formate les sources RAG en texte lisible.
        
        Args:
            rag_sources: Liste des sources du récupérateur RAG.
        
        Returns:
            Texte formaté pour inclusion dans les prompts.
        """
        if not rag_sources:
            return "Aucun contexte RAG disponible."
        
        max_chars = self._env_int("RAG_CONTEXT_CHARS", 220)
        formatted = "Contexte extrait des documents :\n"
        for i, source in enumerate(rag_sources, 1):
            formatted += f"\n[Doc {i}] (source: {source.get('source', 'inconnu')}, discipline: {source.get('discipline', 'inconnu')})\n"
            formatted += f"{source.get('content', '')[:max_chars]}...\n"
        
        return formatted
    
    def _merge_responses(
        self,
        question: str,
        agent_responses: Dict[str, str],
        rag_context: str
    ) -> str:
        """
        THOUGHT 2 — Fusionne les réponses de plusieurs agents.
        
        Si plusieurs agents ont répondu, utilise le LLM pour créer
        une réponse cohérente et intégrée.
        
        Args:
            question: La question originale.
            agent_responses: Dict {discipline: response}.
            rag_context: Contexte RAG utilisé.
        
        Returns:
            Réponse fusionnée et cohérente.
        """
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]

        if not self._env_bool("BRIDGE_LLM_MERGE_ENABLED", False):
            sections = [
                f"### Perspective {discipline}\n{response}"
                for discipline, response in agent_responses.items()
            ]
            return (
                "Voici les réponses disciplinaires mises côte à côte pour accélérer "
                "le mode test. Activez BRIDGE_LLM_MERGE_ENABLED=true pour une "
                "synthèse fusionnée par le LLM.\n\n"
                + "\n\n".join(sections)
            )
        
        try:
            # Formatage des réponses par discipline
            responses_text = "\n".join([
                f"Réponse de {discipline}:\n{response}"
                for discipline, response in agent_responses.items()
            ])
            
            merge_prompt = f"""Fusionne les réponses suivantes pour créer une explication 
interdisciplinaire cohérente et enrichissante. 

Question originale : {question}

{responses_text}

Crée une réponse synthétisée qui :
1. Intègre les perspectives de toutes les disciplines
2. Souligne les complémentarités
3. Signale les différences conceptuelles importantes
4. Reste académique et précis
5. Est écrite en français"""
            
            merged_response = self.llm_provider.generate(
                prompt=merge_prompt,
                system_prompt="Tu es un expert en synthèse interdisciplinaire. Fusionne les réponses de manière cohérente et enrichissante."
            )
            
            logger.info("Réponses fusionnées avec succès")
            return merged_response
        
        except Exception as e:
            logger.error(f"Erreur lors de la fusion des réponses : {str(e)}")
            return "\n".join(agent_responses.values())
    
    def generate_mediation_proposal(
        self,
        terme: str,
        disc_a: str,
        disc_b: str
    ) -> Dict[str, Any]:
        """
        Génère une proposition de médiation pour un terme polysème.
        
        Args:
            terme: Le terme polysème.
            disc_a: Première discipline.
            disc_b: Deuxième discipline.
        
        Returns:
            Dict avec : terme, discipline_a, definition_a,
            discipline_b, definition_b, analogie, confiance.
        """
        try:
            prompt = f"""Réponds UNIQUEMENT avec un objet JSON valide. Aucun texte avant ni après.

{{
  "terme": "{terme}",
  "discipline_a": "{disc_a}",
  "definition_a": "définition en {disc_a} en 15 mots max",
  "discipline_b": "{disc_b}",
  "definition_b": "définition en {disc_b} en 15 mots max",
  "analogie": "pont entre les deux définitions en 20 mots max",
  "confiance": 0.80
}}

Remplis uniquement les champs "definition_a", "definition_b" et "analogie" pour le terme "{terme}"."""
            
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt="Tu es un expert en médiation terminologique interdisciplinaire. Réponds uniquement avec du JSON valide."
            )
            
            proposal = self._parse_json_response(response, dict)

            required_keys = [
                "terme", "discipline_a", "definition_a",
                "discipline_b", "definition_b", "analogie", "confiance"
            ]
            if proposal and all(key in proposal for key in required_keys):
                try:
                    confidence = float(proposal.get("confiance", 0.5))
                    proposal["confiance"] = min(1.0, max(0.0, confidence))
                except (TypeError, ValueError):
                    proposal["confiance"] = 0.5
                logger.info(f"Proposition de médiation générée : {terme}")
                return proposal
            else:
                logger.warning(f"Impossible de parser la proposition pour '{terme}'")
            
            # Réponse par défaut en cas d'échec
            return {
                "terme": terme,
                "discipline_a": disc_a,
                "definition_a": f"Concept de {disc_a}",
                "discipline_b": disc_b,
                "definition_b": f"Concept de {disc_b}",
                "analogie": "Analogie à définir",
                "confiance": 0.5
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de médiation : {str(e)}")
            return {
                "terme": terme,
                "discipline_a": disc_a,
                "definition_a": f"Concept de {disc_a}",
                "discipline_b": disc_b,
                "definition_b": f"Concept de {disc_b}",
                "analogie": "Erreur lors de la génération",
                "confiance": 0.0
            }
    
    def route(
        self,
        question: str,
        user_discipline: str
    ) -> Dict[str, Any]:
        """
        Route la question à travers l'orchestrateur avec pattern ReAct.
        
        Exécute les phases THOUGHT et ACTION du pattern ReAct :
        1. THOUGHT 1 : Détecte les disciplines cibles
        2. ACTION 1 : Récupère le contexte RAG
        3. ACTION 2 : Appelle les agents pertinents
        4. THOUGHT 2 : Fusionne les réponses
        5. ACTION 3 : Détecte les termes polysèmes et génère les médiations
        
        Args:
            question: La question de l'utilisateur.
            user_discipline: La discipline de l'utilisateur.
        
        Returns:
            Dict avec :
            - response (str) : réponse finale fusionnée
            - agents_used (list[str]) : disciplines utilisées
            - rag_sources (list[dict]) : sources citées
            - ambiguous_terms (list[str]) : termes polysèmes détectés
            - mediation_proposals (list[dict]) : propositions de médiation
        """
        try:
            logger.info(f"Routage de la question : {question[:50]}...")

            quick_response = self._small_talk_response(question)
            if quick_response:
                logger.info("Message conversationnel détecté, réponse directe")
                return {
                    "response": quick_response,
                    "agents_used": [],
                    "rag_sources": [],
                    "ambiguous_terms": [],
                    "mediation_proposals": []
                }
            
            # THOUGHT 1 — Détecter les disciplines cibles
            target_disciplines = self._detect_target_disciplines(question, user_discipline)
            logger.info(f"THOUGHT 1 ✓ Disciplines cibles : {target_disciplines}")
            
            # ACTION 1 — Récupérer le contexte RAG
            rag_top_k = self._env_int("RAG_TOP_K", 1)
            rag_sources = self.retriever.retrieve_multi(question, target_disciplines, k=rag_top_k)
            formatted_rag = self._format_rag_context(rag_sources)
            logger.info(f"ACTION 1 ✓ RAG récupéré : {len(rag_sources)} sources")
            
            # ACTION 2 — Appeler les agents pertinents
            agent_responses: Dict[str, str] = {}
            for discipline in target_disciplines:
                if discipline in self.agents:
                    try:
                        response = self.agents[discipline].respond(
                            question=question,
                            user_discipline=user_discipline,
                            rag_context=formatted_rag
                        )
                        agent_responses[discipline] = response
                        logger.info(f"ACTION 2 ✓ Agent {discipline} a répondu")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'appel à l'agent {discipline} : {str(e)}")

            if not agent_responses:
                return {
                    "response": (
                        "Je n'ai pas pu générer de réponse car aucun agent disciplinaire "
                        "n'a répondu. Vérifiez la disponibilité du fournisseur LLM."
                    ),
                    "agents_used": [],
                    "rag_sources": rag_sources,
                    "ambiguous_terms": [],
                    "mediation_proposals": []
                }
            
            # THOUGHT 2 — Fusionner les réponses
            final_response = self._merge_responses(question, agent_responses, formatted_rag)
            logger.info("THOUGHT 2 ✓ Réponses fusionnées")
            
            # ACTION 3 — Détecter les termes polysèmes et générer les médiations
            ambiguous_terms = self.finance_agent.detect_ambiguous_terms(final_response)
            mediation_proposals: List[Dict[str, Any]] = []
            
            if (
                ambiguous_terms
                and len(target_disciplines) > 1
                and self._env_bool("BRIDGE_MEDIATION_ENABLED", False)
            ):
                max_terms = self._env_int("BRIDGE_MAX_MEDIATION_TERMS", 1)
                max_pairs = self._env_int("BRIDGE_MAX_MEDIATION_PAIRS", 1)
                generated_pairs = 0

                for terme in ambiguous_terms[:max_terms]:
                    for i, disc_a in enumerate(target_disciplines):
                        for disc_b in target_disciplines[i+1:]:
                            if disc_a != disc_b:
                                proposal = self.generate_mediation_proposal(terme, disc_a, disc_b)
                                mediation_proposals.append(proposal)
                                generated_pairs += 1
                                if generated_pairs >= max_pairs:
                                    break
                        if generated_pairs >= max_pairs:
                            break
                    if generated_pairs >= max_pairs:
                        break
                
                logger.info(f"ACTION 3 ✓ Termes polysèmes détectés : {ambiguous_terms}")
            
            return {
                "response": final_response,
                "agents_used": list(agent_responses.keys()),
                "rag_sources": rag_sources,
                "ambiguous_terms": ambiguous_terms,
                "mediation_proposals": mediation_proposals
            }
        
        except Exception as e:
            error_msg = f"Erreur lors du routage : {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        orchestrator = Orchestrator()
        print("✓ Orchestrateur BRIDGE initialisé avec succès")
    except RuntimeError as e:
        print(f"Erreur : {e}")
