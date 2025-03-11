from pydantic import BaseModel, Field
from typing import Optional, List
import re

class AuctionImageBase(BaseModel):
    """Schéma de base pour les images d'enchères"""
    auctionId: int
    imageUrl: str
    isMain: bool = False
    order: int = 0
    caption: Optional[str] = None

class AuctionImageCreate(AuctionImageBase):
    """Schéma pour la création d'une image d'enchère"""
    pass

class AuctionImageUpdate(BaseModel):
    """Schéma pour la mise à jour d'une image d'enchère"""
    imageUrl: Optional[str] = None
    isMain: Optional[bool] = None
    order: Optional[int] = None

class AuctionImageResponse(AuctionImageBase):
    """Schéma pour la réponse d'une image d'enchère"""
    id: int

    model_config = {
        "from_attributes": True
    }
        
class AuctionImagePaginatedResponse(BaseModel):
    """Schéma pour la réponse paginée des images d'enchères"""
    items: List[AuctionImageResponse]
    total: int
    page: int
    size: int
    pages: int
