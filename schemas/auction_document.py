from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AuctionDocumentBase(BaseModel):
    """Schéma de base pour les documents d'enchères"""
    auctionId: int
    documentType: str = Field(..., min_length=1, max_length=100)
    documentUrl: str
    documentName: Optional[str] = None
    isPublic: bool = True

class AuctionDocumentCreate(AuctionDocumentBase):
    """Schéma pour la création d'un document d'enchère"""
    pass

class AuctionDocumentUpdate(BaseModel):
    """Schéma pour la mise à jour d'un document d'enchère"""
    documentType: Optional[str] = Field(None, min_length=1, max_length=100)
    documentUrl: Optional[str] = None

class AuctionDocumentResponse(AuctionDocumentBase):
    """Schéma pour la réponse d'un document d'enchère"""
    id: int
    uploadedAt: datetime

    model_config = {
        "from_attributes": True
    }
        
class AuctionDocumentPaginatedResponse(BaseModel):
    """Schéma pour la réponse paginée des documents d'enchères"""
    items: List[AuctionDocumentResponse]
    total: int
    page: int
    size: int
    pages: int
