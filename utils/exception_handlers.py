from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import List, Dict, Any, Union
import re
from datetime import datetime


async def validation_exception_handler(request: Request, exc: Union[RequestValidationError, ValidationError]):
    """
    Gestionnaire d'exception personnalisé pour les erreurs de validation.
    Affiche des messages d'erreur détaillés et conviviaux en français avec les noms des champs et suggestions de correction.
    """
    errors = []
    
    for error in exc.errors():
        error_type = error.get("type", "")
        location = error.get("loc", [])
        field_name = location[-1] if len(location) > 0 else "corps de la requête"
        
        # Format du message original pour analyse
        original_msg = error.get("msg", "")
        
        # Construction de messages d'erreur améliorés par type
        if error_type == "missing" or error_type == "value_error.missing":
            error["msg"] = f"Le champ '{field_name}' est obligatoire et manquant dans votre requête"
        
        # Erreurs de type
        elif error_type.startswith("type_error"):
            # Personnalisations spécifiques par type attendu
            if "integer" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être un nombre entier valide"
            elif "float" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être un nombre décimal valide"
            elif "bool" in error_type or "boolean" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être un booléen (true/false)"
            elif "str" in error_type or "string" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une chaîne de caractères"
            elif "list" in error_type or "array" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une liste d'éléments"
            elif "dict" in error_type or "object" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être un objet"
            elif "date" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une date valide au format ISO (YYYY-MM-DDTHH:MM:SS)"
            else:
                # Extrait le type attendu à partir de l'erreur
                match = re.search(r'got (.+); expected (.+)', original_msg)
                if match:
                    got_type, expected_type = match.groups()
                    error["msg"] = f"Le champ '{field_name}' est de type '{got_type}', mais doit être de type '{expected_type}'"
                else:
                    expected_type = error_type.split(".")[-1] if "." in error_type else "du type attendu"
                    error["msg"] = f"Le champ '{field_name}' doit être {expected_type}"
        
        # Erreurs de validation générale
        elif "value_error" in error_type:
            # Personnalisations spécifiques par sous-type
            if "datetime" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une date et heure valide au format ISO (ex: 2023-01-31T14:30:00)"
            elif "date" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une date valide au format ISO (ex: 2023-01-31)"
            elif "email" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une adresse email valide"
            elif "url" in error_type:
                error["msg"] = f"Le champ '{field_name}' doit être une URL valide"
            elif "number.not_gt" in error_type:
                match = re.search(r'not greater than (.+)', original_msg)
                limit = match.group(1) if match else "la valeur minimum"
                error["msg"] = f"Le champ '{field_name}' doit être supérieur à {limit}"
            elif "number.not_lt" in error_type:
                match = re.search(r'not less than (.+)', original_msg)
                limit = match.group(1) if match else "la valeur maximum"
                error["msg"] = f"Le champ '{field_name}' doit être inférieur à {limit}"
            elif "number.not_ge" in error_type:
                match = re.search(r'not greater than or equal to (.+)', original_msg)
                limit = match.group(1) if match else "la valeur minimum"
                error["msg"] = f"Le champ '{field_name}' doit être supérieur ou égal à {limit}"
            elif "number.not_le" in error_type:
                match = re.search(r'not less than or equal to (.+)', original_msg)
                limit = match.group(1) if match else "la valeur maximum"
                error["msg"] = f"Le champ '{field_name}' doit être inférieur ou égal à {limit}"
            elif "str.min_length" in error_type:
                match = re.search(r'shorter than (.+)', original_msg)
                length = match.group(1) if match else "la longueur minimum"
                error["msg"] = f"Le champ '{field_name}' doit contenir au moins {length} caractères"
            elif "str.max_length" in error_type:
                match = re.search(r'longer than (.+)', original_msg)
                length = match.group(1) if match else "la longueur maximum"
                error["msg"] = f"Le champ '{field_name}' ne doit pas dépasser {length} caractères"
            elif "enum" in error_type:
                match = re.search(r'value is not a valid enumeration member; permitted: (.+)', original_msg)
                if match:
                    permitted = match.group(1).replace('\'', '"')
                    error["msg"] = f"Le champ '{field_name}' doit être l'une des valeurs suivantes : {permitted}"
                else:
                    error["msg"] = f"La valeur fournie pour '{field_name}' n'est pas une option valide"
            else:
                # Message générique enrichi pour les autres cas
                error["msg"] = f"Erreur de validation pour '{field_name}': {original_msg}"
                
        # JSON invalide ou erreur de parsing
        elif "json" in error_type.lower():
            error["msg"] = "Le corps de la requête contient du JSON invalide. Vérifiez la syntaxe de votre requête."
        
        # Erreurs diverses non classifiées
        else:
            error["msg"] = f"Erreur pour '{field_name}': {original_msg}"
        
        # Ajout d'informations complémentaires
        error["field"] = field_name
        error["error_type"] = error_type
        
        errors.append(error)
    
    # Formatage de la réponse pour l'API
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "message": "Erreur de validation des données",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        },
    )
