from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.auction_document import AuctionDocument
from app.models.auction import Auction, AuctionStatus
from app.schemas.auction_document import AuctionDocumentCreate, AuctionDocumentUpdate
from fastapi import HTTPException, status

def get_document(db: Session, document_id: int) -> Optional[AuctionDocument]:
    """
    Récupère un document par son ID
    """
    return db.query(AuctionDocument).filter(AuctionDocument.id == document_id).first()

def get_auction_documents(
    db: Session, 
    auction_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[AuctionDocument], int]:
    """
    Récupère tous les documents pour une enchère spécifique
    """
    query = db.query(AuctionDocument).filter(AuctionDocument.auctionId == auction_id)
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    documents = query.offset(skip).limit(limit).all()
    
    return documents, total

def create_document(db: Session, document_data: AuctionDocumentCreate) -> AuctionDocument:
    """
    Ajoute un nouveau document à une enchère
    """
    # Vérifier si l'enchère existe
    auction = db.query(Auction).filter(Auction.id == document_data.auctionId).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    if auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Créer le document
    db_document = AuctionDocument(
        auctionId=document_data.auctionId,
        documentUrl=document_data.documentUrl,
        documentType=document_data.documentType,
        isPublic=document_data.isPublic,
        uploadedAt=datetime.now()
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document

def update_document(db: Session, document_id: int, document_data: AuctionDocumentUpdate) -> AuctionDocument:
    """
    Met à jour un document existant
    """
    db_document = get_document(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_document.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Mettre à jour les champs modifiables
    update_data = document_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_document, key, value)
    
    db.commit()
    db.refresh(db_document)
    
    return db_document

def delete_document(db: Session, document_id: int) -> bool:
    """
    Supprime un document
    """
    db_document = get_document(db, document_id)
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_document.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    db.delete(db_document)
    db.commit()
    
    return True
