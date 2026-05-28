"""
Configuration helpers for BRIDGE.

Centralises environment loading so local runs and Docker runs
behave consistently.
"""

import logging
import unicodedata

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment() -> bool:
    """
    Load variables from a .env file when available.

    Returns:
        True if a .env file was found and loaded, otherwise False.
    """
    loaded = load_dotenv()
    if loaded:
        logger.debug("Environment variables loaded from .env")
    return loaded


def collection_name_for_discipline(discipline: str) -> str:
    """
    Convertit un nom de discipline en nom de collection ChromaDB stable.

    Exemple : "Finance de marché" devient "bridge_finance_de_marche".
    """
    normalized = unicodedata.normalize("NFKD", discipline)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    safe_name = "".join(
        char.lower() if char.isalnum() else "_"
        for char in ascii_name
    ).strip("_")

    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")

    return f"bridge_{safe_name}"
