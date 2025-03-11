from pydantic import BaseModel, Field, validator, RootModel
from typing import Optional, List, Dict, Any, ForwardRef, TypeVar, Generic
from datetime import datetime, date
from enum import Enum
from fastapi import UploadFile, Form, File

from app.models.auction import AuctionType, AuctionStatus

class AuctionBase(BaseModel):
    """Schéma de base pour les enchères"""
    title: str = Field(..., min_length=5, max_length=200)
    category_id: int
    description: Optional[str] = None
    startingPrice: float = Field(..., gt=0)
    reservePrice: Optional[float] = Field(None, gt=0)
    incrementAmount: float = Field(1.0, gt=0)
    location: Optional[str] = None
    sellerName: str
    termsConditions: Optional[str] = None
    productHistory: Optional[str] = None
    startDate: datetime
    endDate: datetime
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    auctionType: AuctionType = AuctionType.NORMAL
    auctionStatus: AuctionStatus = AuctionStatus.DRAFT
    featuredAuction: bool = False

    @validator('endDate')
    def end_date_after_start_date(cls, v, values):
        if 'startDate' in values and v < values['startDate']:
            raise ValueError('La date de fin doit être postérieure à la date de début')
        return v
    
    @validator('startTime', 'endTime')
    def validate_time_format(cls, v):
        if v and not validate_time_format(v):
            raise ValueError('Le format de l\'heure doit être HH:MM')
        return v

def validate_time_format(time_str: str) -> bool:
    """Valider le format de l'heure (HH:MM)"""
    if not time_str:
        return True
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

class AuctionCreate(AuctionBase):
    """Schéma pour la création d'une enchère"""
    creator_id: Optional[int] = None

class AuctionUpdate(BaseModel):
    """Schéma pour la mise à jour d'une enchère"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    category_id: Optional[int] = None
    description: Optional[str] = None
    startingPrice: Optional[float] = Field(None, gt=0)
    reservePrice: Optional[float] = Field(None, gt=0)
    incrementAmount: Optional[float] = Field(None, gt=0)
    location: Optional[str] = None
    sellerName: Optional[str] = None
    termsConditions: Optional[str] = None
    productHistory: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    auctionType: Optional[AuctionType] = None
    auctionStatus: Optional[AuctionStatus] = None
    featuredAuction: Optional[bool] = None
    specifications: Optional[List[Dict[str, Any]]] = None

    @validator('endDate')
    def end_date_after_start_date(cls, v, values):
        if v and 'startDate' in values and values['startDate'] and v < values['startDate']:
            raise ValueError('La date de fin doit être postérieure à la date de début')
        return v
    
    @validator('startTime', 'endTime')
    def validate_time_format(cls, v):
        if v and not validate_time_format(v):
            raise ValueError('Le format de l\'heure doit être HH:MM')
        return v

class AuctionStatusUpdate(BaseModel):
    """Schéma pour la mise à jour du statut d'une enchère"""
    status: AuctionStatus

class AuctionResponse(AuctionBase):
    """Schéma pour la réponse d'une enchère"""
    id: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {
        "from_attributes": True
    }

class CategoryInfo(BaseModel):
    """Schéma simple pour la catégorie"""
    id: int
    name: Optional[str] = None

class AuctionDetailedResponse(AuctionResponse):
    """Schéma détaillé pour la réponse d'une enchère avec les relations"""
    category: CategoryInfo
    specifications: List[Any] = []  # Pour éviter la référence circulaire
    highestBid: Optional[float] = None
    totalBids: int = 0

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }
        
# Alias pour la compatibilité avec les anciennes routes
AuctionDetailResponse = AuctionDetailedResponse


class AuctionImageItem(BaseModel):
    """Schéma pour une image d'enchère à télécharger"""
    filename: str
    content: bytes
    is_main: bool = False
    order: Optional[int] = None
    caption: Optional[str] = None

class AuctionDocumentItem(BaseModel):
    """Schéma pour un document d'enchère à télécharger"""
    filename: str
    content: bytes
    document_type: str
    document_name: str
    is_public: bool = True

class AuctionCompleteCreate(BaseModel):
    """Schéma pour la création d'une enchère complète avec images et documents"""
    auction_data: AuctionCreate
    images: Optional[List[AuctionImageItem]] = []
    documents: Optional[List[AuctionDocumentItem]] = []

class AuctionCompleteResponse(BaseModel):
    """Schéma pour la réponse après création d'une enchère complète"""
    auction: AuctionResponse
    images: List[Any] = []
    documents: List[Any] = []

class AuctionList(BaseModel):
    """Schéma pour la liste des enchères"""
    auctions: List[AuctionResponse]
    total: int
    
class AuctionPaginatedResponse(BaseModel):
    """Schéma pour la réponse des enchères avec uniquement la liste et le total"""
    auctions: List[AuctionResponse]
    total: int

class AuctionListResponse(RootModel):
    """Schéma pour la réponse des enchères sous forme de tableau simple"""
    root: List[AuctionResponse]

class AuctionFilter(BaseModel):
    """Filtre pour la recherche d'enchères"""
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    status: Optional[AuctionStatus] = None
    type: Optional[AuctionType] = None
    location: Optional[str] = None
    featured: Optional[bool] = None
    search: Optional[str] = None  # Recherche dans le titre et la description

class AuctionSummaryResponse(BaseModel):
    """Schéma simplifié pour l'aperçu d'une enchère"""
    id: int
    title: str
    startingPrice: float
    currentPrice: float  # Prix actuel (enchère la plus élevée ou prix de départ)
    imageUrl: Optional[str] = None  # Image principale
    endDate: datetime
    auctionStatus: AuctionStatus
    totalBids: int
    
    model_config = {
        "from_attributes": True
    }
