"""
Glossaire Dynamique Inter-Disciplinaire (GDID) pour BRIDGE.

Module responsable de la gestion persistante des correspondances
terminologiques entre disciplines.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from config import load_environment

logger = logging.getLogger(__name__)


class GlossaireDynamique:
    """
    Gestionnaire du Glossaire Dynamique Inter-Disciplinaire.
    
    Permet l'ajout, la récupération, la modification et la suppression
    de correspondances terminologiques entre disciplines.
    
    Les données sont persistées dans un fichier JSON (gdid.json).
    """
    
    def __init__(self, path: Optional[str] = None) -> None:
        """
        Initialise le gestionnaire de glossaire.
        
        Args:
            path: Chemin vers le fichier gdid.json. 
                  Si None, utilise GDID_PATH de l'environnement.
                  Sinon utilise ./gdid/gdid.json par défaut.
        
        Raises:
            IOError: Si le fichier existe mais n'est pas lisible.
        """
        load_environment()
        self.path: str = path or os.getenv("GDID_PATH", "./gdid/gdid.json")
        
        logger.debug(f"Initialisation du GDID avec chemin : {self.path}")
        
        self._ensure_file_exists()
        self._load_data()
    
    def _ensure_file_exists(self) -> None:
        """
        Crée le fichier gdid.json s'il n'existe pas.
        
        Initialise la structure de base si le fichier est vide.
        """
        if not os.path.exists(self.path):
            logger.info(f"Création du fichier GDID : {self.path}")
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            
            initial_structure = {
                "version": "1.0",
                "description": "Glossaire Dynamique Inter-Disciplinaire — BRIDGE",
                "correspondances": []
            }
            
            try:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(initial_structure, f, indent=2, ensure_ascii=False)
                logger.info("Fichier GDID créé avec succès")
            except IOError as e:
                error_msg = f"Impossible de créer le fichier GDID : {str(e)}"
                logger.error(error_msg)
                raise IOError(error_msg) from e
    
    def _load_data(self) -> None:
        """
        Charge les données depuis le fichier GDID.
        
        Raises:
            IOError: Si le fichier n'est pas lisible.
            json.JSONDecodeError: Si le JSON est invalide.
        """
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data: Dict[str, Any] = json.load(f)
            logger.debug(f"Données GDID chargées : {len(self.data.get('correspondances', []))} entrées")
        except IOError as e:
            error_msg = f"Impossible de lire le fichier GDID : {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"Format JSON invalide pour GDID : {str(e)}"
            logger.error(error_msg)
            raise json.JSONDecodeError(error_msg, "", 0) from e
    
    def _save_data(self) -> None:
        """
        Sauvegarde les données dans le fichier GDID.
        
        Raises:
            IOError: Si le fichier n'est pas accessible en écriture.
        """
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug("Données GDID sauvegardées")
        except IOError as e:
            error_msg = f"Impossible de sauvegarder le fichier GDID : {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg) from e
    
    def add_correspondance(self, entry: Dict[str, Any]) -> str:
        """
        Ajoute une nouvelle correspondance au glossaire.
        
        Args:
            entry: Dictionnaire contenant les clés :
                - terme_source (str)
                - discipline_source (str)
                - definition_source (str)
                - terme_cible (str)
                - discipline_cible (str)
                - definition_cible (str)
                - analogie (str)
                - validé_par (str): "humain" ou "système"
                - confiance (float): 0.0 à 1.0
        
        Returns:
            ID (UUID4) de l'entrée créée.
        
        Raises:
            ValueError: Si des champs requis sont manquants.
        """
        required_fields = [
            "terme_source", "discipline_source", "definition_source",
            "terme_cible", "discipline_cible", "definition_cible",
            "analogie", "validé_par", "confiance"
        ]
        
        missing = [field for field in required_fields if field not in entry]
        if missing:
            error_msg = f"Champs manquants dans l'entrée GDID : {missing}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            entry["confiance"] = min(1.0, max(0.0, float(entry["confiance"])))
        except (TypeError, ValueError) as e:
            raise ValueError("Le champ confiance doit être un nombre entre 0.0 et 1.0") from e

        entry_id = str(uuid4())
        entry["id"] = entry_id
        entry["date_validation"] = datetime.now().isoformat()
        
        if "correspondances" not in self.data:
            self.data["correspondances"] = []

        duplicate_id = self._find_duplicate_id(entry)
        if duplicate_id:
            logger.info(f"Correspondance déjà existante : {duplicate_id}")
            return duplicate_id
        
        self.data["correspondances"].append(entry)
        self._save_data()
        
        logger.info(f"Correspondance ajoutée avec ID : {entry_id}")
        return entry_id

    def _find_duplicate_id(self, entry: Dict[str, Any]) -> Optional[str]:
        """
        Retourne l'ID d'une correspondance identique, si elle existe.
        """
        duplicate_fields = [
            "terme_source", "discipline_source", "definition_source",
            "terme_cible", "discipline_cible", "definition_cible",
            "analogie"
        ]

        for existing in self.data.get("correspondances", []):
            if all(existing.get(field) == entry.get(field) for field in duplicate_fields):
                return existing.get("id")

        return None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les correspondances du glossaire.
        
        Returns:
            Liste de toutes les entrées de correspondance.
        """
        correspondances = self.data.get("correspondances", [])
        logger.debug(f"Récupération de {len(correspondances)} correspondances")
        return correspondances
    
    def delete_by_id(self, entry_id: str) -> bool:
        """
        Supprime une correspondance par son ID.
        
        Args:
            entry_id: UUID de l'entrée à supprimer.
        
        Returns:
            True si l'entrée a été supprimée, False si elle n'existait pas.
        
        Raises:
            ValueError: Si l'ID est invalide.
        """
        if not entry_id or not isinstance(entry_id, str):
            error_msg = "ID d'entrée invalide"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        correspondances = self.data.get("correspondances", [])
        original_length = len(correspondances)
        
        self.data["correspondances"] = [
            entry for entry in correspondances if entry.get("id") != entry_id
        ]
        
        if len(self.data["correspondances"]) < original_length:
            self._save_data()
            logger.info(f"Correspondance supprimée : {entry_id}")
            return True
        else:
            logger.warning(f"Correspondance non trouvée : {entry_id}")
            return False

    def clear(self) -> None:
        """
        Supprime toutes les correspondances du glossaire.
        """
        self.data["correspondances"] = []
        self._save_data()
        logger.info("Toutes les correspondances GDID ont été supprimées")
    
    def update_by_id(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """
        Met à jour une correspondance existante.
        
        Args:
            entry_id: UUID de l'entrée à mettre à jour.
            updates: Dictionnaire contenant les champs à mettre à jour.
        
        Returns:
            True si la mise à jour a réussi, False si l'entrée n'existait pas.
        
        Raises:
            ValueError: Si l'ID ou les updates sont invalides.
        """
        if not entry_id or not isinstance(entry_id, str):
            error_msg = "ID d'entrée invalide"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(updates, dict):
            error_msg = "Les mises à jour doivent être un dictionnaire"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        correspondances = self.data.get("correspondances", [])
        
        for entry in correspondances:
            if entry.get("id") == entry_id:
                entry.update(updates)
                entry["date_validation"] = datetime.now().isoformat()
                self._save_data()
                logger.info(f"Correspondance mise à jour : {entry_id}")
                return True
        
        logger.warning(f"Correspondance non trouvée pour mise à jour : {entry_id}")
        return False
    
    def search(self, terme: str) -> List[Dict[str, Any]]:
        """
        Recherche des correspondances contenant un terme spécifique.
        
        La recherche est insensible à la casse et cherche dans :
        - terme_source
        - terme_cible
        - definition_source
        - definition_cible
        
        Args:
            terme: Terme à rechercher.
        
        Returns:
            Liste des correspondances contenant le terme.
        
        Raises:
            ValueError: Si le terme est vide.
        """
        if not terme or not isinstance(terme, str):
            error_msg = "Le terme de recherche ne peut pas être vide"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        terme_lower = terme.lower()
        correspondances = self.data.get("correspondances", [])
        
        results = []
        for entry in correspondances:
            if (terme_lower in entry.get("terme_source", "").lower() or
                terme_lower in entry.get("terme_cible", "").lower() or
                terme_lower in entry.get("definition_source", "").lower() or
                terme_lower in entry.get("definition_cible", "").lower()):
                results.append(entry)
        
        logger.debug(f"Recherche '{terme}' : {len(results)} résultats trouvés")
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    gdid = GlossaireDynamique()
    print(f"GDID initialisé avec {len(gdid.get_all())} correspondances")
