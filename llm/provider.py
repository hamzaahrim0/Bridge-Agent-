"""
Fournisseur LLM pour BRIDGE.

Supporte uniquement Ollama local, gratuit et sans clé API.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from config import load_environment

logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Fournisseur d'accès LLM pour BRIDGE.

    BRIDGE utilise Ollama via son API HTTP locale.
    """

    def __init__(self) -> None:
        """
        Initialise la configuration Ollama locale.
        """
        load_environment()

        self.timeout: int = self._env_int("LLM_TIMEOUT", 300)
        self.max_tokens: int = self._env_int("LLM_MAX_TOKENS", 512)
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.last_error: Optional[str] = None
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.num_predict = self._env_int("OLLAMA_NUM_PREDICT", self.max_tokens)
        self.num_ctx = self._env_int("OLLAMA_NUM_CTX", 2048)
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "10m")
        self.client = None

        logger.info(
            "Fournisseur LLM initialisé : %s (%s)",
            self.display_name,
            self.model,
        )

    @property
    def display_name(self) -> str:
        """Nom lisible du fournisseur actif pour l'interface."""
        return "Ollama local"

    def _env_int(self, name: str, default: int) -> int:
        """Lit un entier depuis l'environnement avec valeur de repli sûre."""
        try:
            return int(os.getenv(name, str(default)))
        except ValueError:
            logger.warning("Variable %s invalide, valeur utilisée : %s", name, default)
            return default

    def _messages(self, prompt: str, system_prompt: str = "") -> List[Dict[str, str]]:
        """Construit le format de messages commun aux deux fournisseurs."""
        messages: List[Dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        Génère une réponse basée sur un prompt utilisateur.

        Args:
            prompt: Texte du prompt utilisateur.
            system_prompt: Prompt système pour conditionner le comportement du modèle.

        Returns:
            Texte de la réponse générée par le modèle.

        Raises:
            RuntimeError: En cas d'erreur lors de l'appel au fournisseur actif.
        """
        return self._generate_ollama(prompt, system_prompt)

    def _generate_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Génère une réponse avec Ollama local."""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": self._messages(prompt, system_prompt),
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.num_predict,
                        "num_ctx": self.num_ctx,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            generated_text = payload.get("message", {}).get("content", "")

            if not generated_text:
                raise RuntimeError("Réponse Ollama vide ou inattendue.")

            self.last_error = None
            return generated_text.strip()
        except requests.Timeout as e:
            error_msg = (
                f"Ollama n'a pas répondu en {self.timeout}s sur {self.base_url}. "
                "Le serveur est joignable, mais le modèle est trop lent ou trop chargé. "
                "Augmentez LLM_TIMEOUT, réduisez OLLAMA_NUM_PREDICT, ou utilisez un modèle plus léger."
            )
            self.last_error = error_msg
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except requests.ConnectionError as e:
            error_msg = (
                f"Ollama est indisponible sur {self.base_url}. "
                "Lancez Ollama puis téléchargez le modèle avec "
                f"`ollama pull {self.model}`."
            )
            self.last_error = error_msg
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except requests.HTTPError as e:
            detail = self._ollama_error_detail(e.response)
            self.last_error = detail
            logger.error(detail)
            raise RuntimeError(detail) from e
        except Exception as e:
            error_msg = f"Erreur inattendue Ollama : {str(e)}"
            self.last_error = error_msg
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def is_available(self) -> bool:
        """
        Vérifie la disponibilité du fournisseur actif.

        Returns:
            True si le service est disponible, False sinon.
        """
        return self._is_ollama_available()

    def _is_ollama_available(self) -> bool:
        """Vérifie que le serveur Ollama et le modèle demandé sont disponibles."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            payload = response.json()
            models = [model.get("name", "") for model in payload.get("models", [])]

            if self.model not in models:
                self.last_error = (
                    f"Modèle Ollama introuvable : {self.model}. "
                    f"Exécutez `ollama pull {self.model}`."
                )
                logger.warning(self.last_error)
                return False

            self.last_error = None
            return True
        except requests.ConnectionError:
            self.last_error = (
                f"Ollama est indisponible sur {self.base_url}. "
                "Démarrez Ollama avec `ollama serve` ou l'application Ollama."
            )
            logger.warning(self.last_error)
            return False
        except Exception as e:
            self.last_error = str(e)
            logger.warning("Erreur de disponibilité Ollama : %s", self.last_error)
            return False

    def _ollama_error_detail(self, response: requests.Response) -> str:
        """Formate les erreurs HTTP renvoyées par Ollama."""
        try:
            payload = response.json()
            message = payload.get("error") or payload.get("message")
        except ValueError:
            message = response.text

        if response.status_code == 404 and self.model in str(message):
            return (
                f"Modèle Ollama introuvable : {self.model}. "
                f"Exécutez `ollama pull {self.model}`."
            )

        return f"Erreur Ollama HTTP {response.status_code} : {message}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        provider = LLMProvider()
        available = provider.is_available()
        print(f"{provider.display_name} disponible : {available}")
        if provider.last_error:
            print(provider.last_error)
    except ValueError as e:
        print(f"Configuration insuffisante : {e}")
