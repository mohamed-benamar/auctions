from pydantic import BaseModel, Field
from typing import Optional, List

class AuctionSpecificationBase(BaseModel):
    """Schéma de base pour les spécifications d'enchères"""
    auctionId: int
    property: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1)

class AuctionSpecificationCreate(AuctionSpecificationBase):
    """Schéma pour la création d'une spécification d'enchère"""
    pass

class AuctionSpecificationBulkCreate(BaseModel):
    """Schéma pour la création en masse de spécifications d'enchère"""
    auctionId: int
    specifications: List[dict]

class AuctionSpecificationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une spécification d'enchère"""
    property: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = Field(None, min_length=1)

class AuctionSpecificationResponse(AuctionSpecificationBase):
    """Schéma pour la réponse d'une spécification d'enchère"""
    id: int

    model_config = {
        "from_attributes": True
    }
        
class AuctionSpecificationPaginatedResponse(BaseModel):
    """Schéma pour la réponse paginée des spécifications d'enchères"""
    items: List[AuctionSpecificationResponse]
    total: int
    page: int
    size: int
    pages: int
