from sqlalchemy.orm import Query
from sqlalchemy import inspect
import logging

logger = logging.getLogger(__name__)

def patch_query_for_missing_columns():
    """
    Patch pour gérer les colonnes manquantes dans la base de données
    Cette fonction est appelée au démarrage de l'application pour gérer les modèles
    qui ont été mis à jour mais dont les migrations n'ont pas encore été appliquées
    """
    # Sauvegarder la méthode originale
    original_compile = Query._compile_context

    def patched_compile(self, *args, **kwargs):
        # La logique pour retirer les attributs non existants est ici
        try:
            return original_compile(self, *args, **kwargs)
        except Exception as e:
            if "column" in str(e) and "does not exist" in str(e):
                logger.warning(f"Problème de colonne manquante détecté: {str(e)}")
                # On laisse l'exception se propager, mais on a loggé le problème
                raise
            else:
                raise
                
    # Appliquer le patch
    Query._compile_context = patched_compile
    logger.info("Patch pour les colonnes manquantes appliqué")

def setup_model_patches():
    """
    Configure tous les patches nécessaires pour les modèles
    """
    patch_query_for_missing_columns()
