from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class BidBase(BaseModel):
    """Schéma de base pour les enchères"""
    auctionId: int
    amount: float = Field(..., gt=0)

class BidCreate(BidBase):
    """Schéma pour la création d'une enchère"""
    pass

class BidResponse(BidBase):
    """Schéma pour la réponse d'une enchère"""
    id: int
    bidderId: int
    timestamp: datetime
    bidderName: Optional[str] = None  # Ajouté lors de la réponse

    class Config:
        from_attributes = True

class BidWithUserResponse(BidResponse):
    """Schéma pour la réponse d'une enchère avec les informations de l'utilisateur"""
    bidderFirstName: str
    bidderLastName: str
    bidderEmail: str

    class Config:
        from_attributes = True
        
# Alias pour la compatibilité avec les anciennes routes
BidDetailResponse = BidWithUserResponse

class BidPaginatedResponse(BaseModel):
    """Schéma pour la réponse paginée des enchères"""
    items: List[BidResponse]
    total: int
    page: int
    size: int
    pages: int
