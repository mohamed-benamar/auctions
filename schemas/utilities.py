"""
Schémas pour les données géographiques et les tribunaux
"""

from pydantic import BaseModel
from typing import List, Optional

class PaysBase(BaseModel):
    """Schéma de base pour un pays"""
    nom_fr: str
    nom_ar: str
    code: Optional[str] = None

class PaysCreate(PaysBase):
    """Schéma pour la création d'un pays"""
    pass

class Pays(PaysBase):
    """Schéma pour un pays complet"""
    id: int
    
    class Config:
        from_attributes = True

class PaysResponse(Pays):
    """Schéma de réponse pour un pays"""
    pass

# Format d'origine avec total
class PaysList(BaseModel):
    """Schéma pour la liste des pays"""
    pays: List[PaysResponse]
    total: int
    
# Liste simple de pays
type PaysResponseList = List[PaysResponse]

class VilleBase(BaseModel):
    """Schéma de base pour une ville"""
    nom_fr: str
    nom_ar: str
    pays_id: int

class VilleCreate(VilleBase):
    """Schéma pour la création d'une ville"""
    pass

class Ville(VilleBase):
    """Schéma pour une ville complète"""
    id: int
    
    class Config:
        from_attributes = True

class VilleResponse(Ville):
    """Schéma de réponse pour une ville"""
    pass

# Format d'origine avec total
class VilleList(BaseModel):
    """Schéma pour la liste des villes"""
    villes: List[VilleResponse]
    total: int
    
# Liste simple de villes
type VilleResponseList = List[VilleResponse]

class TribunalBase(BaseModel):
    """Schéma de base pour un tribunal"""
    nom: str
    nom_ar: Optional[str] = None
    ville: str
    type: Optional[str] = None

class TribunalCreate(TribunalBase):
    """Schéma pour la création d'un tribunal"""
    pass

class Tribunal(TribunalBase):
    """Schéma pour un tribunal complet"""
    id: int
    
    class Config:
        from_attributes = True

class TribunalResponse(Tribunal):
    """Schéma de réponse pour un tribunal"""
    pass

# Format d'origine avec total
class TribunalList(BaseModel):
    """Schéma pour la liste des tribunaux"""
    tribunaux: List[TribunalResponse]
    total: int
    
# Liste simple de tribunaux
type TribunalResponseList = List[TribunalResponse]

class OrganismCreditBase(BaseModel):
    """Schéma de base pour un organisme de crédit"""
    nom: str
    nom_ar: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    site_web: Optional[str] = None

class OrganismCreditCreate(OrganismCreditBase):
    """Schéma pour la création d'un organisme de crédit"""
    pass

class OrganismCredit(OrganismCreditBase):
    """Schéma pour un organisme de crédit complet"""
    id: int
    
    class Config:
        from_attributes = True

class OrganismCreditResponse(OrganismCredit):
    """Schéma de réponse pour un organisme de crédit"""
    pass

# Format d'origine avec total
class OrganismCreditList(BaseModel):
    """Schéma pour la liste des organismes de crédit"""
    organismes: List[OrganismCreditResponse]
    total: int
    
# Liste simple d'organismes de crédit
type OrganismCreditResponseList = List[OrganismCreditResponse]
