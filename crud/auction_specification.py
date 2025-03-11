from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.auction_specification import AuctionSpecification
from app.models.auction import Auction, AuctionStatus
from app.schemas.auction_specification import AuctionSpecificationCreate, AuctionSpecificationUpdate
from fastapi import HTTPException, status

def get_specification(db: Session, spec_id: int) -> Optional[AuctionSpecification]:
    """
    Récupère une spécification par son ID
    """
    return db.query(AuctionSpecification).filter(AuctionSpecification.id == spec_id).first()

def get_auction_specifications(
    db: Session, 
    auction_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[AuctionSpecification], int]:
    """
    Récupère toutes les spécifications pour une enchère spécifique
    """
    query = db.query(AuctionSpecification).filter(AuctionSpecification.auctionId == auction_id)
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    specs = query.offset(skip).limit(limit).all()
    
    return specs, total

def create_specification(db: Session, spec_data: AuctionSpecificationCreate) -> AuctionSpecification:
    """
    Ajoute une nouvelle spécification à une enchère
    """
    # Vérifier si l'enchère existe
    auction = db.query(Auction).filter(Auction.id == spec_data.auctionId).first()
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
    
    # Vérifier si une spécification avec le même nom existe déjà pour cette enchère
    existing_spec = db.query(AuctionSpecification).filter(
        AuctionSpecification.auctionId == spec_data.auctionId,
        AuctionSpecification.name == spec_data.name
    ).first()
    
    if existing_spec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Une spécification avec le nom '{spec_data.name}' existe déjà pour cette enchère"
        )
    
    # Créer la spécification
    db_spec = AuctionSpecification(
        auctionId=spec_data.auctionId,
        name=spec_data.name,
        value=spec_data.value
    )
    
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    
    return db_spec

def update_specification(db: Session, spec_id: int, spec_data: AuctionSpecificationUpdate) -> AuctionSpecification:
    """
    Met à jour une spécification existante
    """
    db_spec = get_specification(db, spec_id)
    if not db_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spécification non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_spec.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    update_data = spec_data.model_dump(exclude_unset=True)
    
    # Si le nom est modifié, vérifier qu'il n'existe pas déjà
    if 'name' in update_data and update_data['name'] != db_spec.name:
        existing_spec = db.query(AuctionSpecification).filter(
            AuctionSpecification.auctionId == db_spec.auctionId,
            AuctionSpecification.name == update_data['name']
        ).first()
        
        if existing_spec:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une spécification avec le nom '{update_data['name']}' existe déjà pour cette enchère"
            )
    
    # Mettre à jour les champs modifiables
    for key, value in update_data.items():
        setattr(db_spec, key, value)
    
    db.commit()
    db.refresh(db_spec)
    
    return db_spec

def delete_specification(db: Session, spec_id: int) -> bool:
    """
    Supprime une spécification
    """
    db_spec = get_specification(db, spec_id)
    if not db_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spécification non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_spec.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    db.delete(db_spec)
    db.commit()
    
    return True

def create_bulk_specifications(db: Session, auction_id: int, specs_data: List[AuctionSpecificationCreate]) -> List[AuctionSpecification]:
    """
    Ajoute plusieurs spécifications à une enchère en une seule opération
    """
    # Vérifier si l'enchère existe
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
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
    
    # Vérifier les noms en double dans les nouvelles spécifications
    spec_names = [spec.name for spec in specs_data]
    if len(spec_names) != len(set(spec_names)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Des noms de spécifications en double ont été détectés dans les données fournies"
        )
    
    # Vérifier les spécifications existantes
    existing_specs = db.query(AuctionSpecification).filter(
        AuctionSpecification.auctionId == auction_id
    ).all()
    
    existing_names = [spec.name for spec in existing_specs]
    
    for spec_data in specs_data:
        if spec_data.name in existing_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une spécification avec le nom '{spec_data.name}' existe déjà pour cette enchère"
            )
    
    # Créer toutes les spécifications
    db_specs = []
    for spec_data in specs_data:
        db_spec = AuctionSpecification(
            auctionId=auction_id,
            name=spec_data.name,
            value=spec_data.value
        )
        db.add(db_spec)
        db_specs.append(db_spec)
    
    db.commit()
    
    # Rafraîchir tous les objets
    for db_spec in db_specs:
        db.refresh(db_spec)
    
    return db_specs
