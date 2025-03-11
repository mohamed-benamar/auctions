from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from app.models.auction import Auction, AuctionStatus, AuctionType
from app.models.auction_image import AuctionImage
from app.models.bid import Bid
from app.schemas.auction import AuctionCreate, AuctionUpdate, AuctionStatusUpdate, AuctionFilter
from fastapi import HTTPException, status

def get_auction(db: Session, auction_id: int) -> Optional[Auction]:
    """
    Récupère une enchère par son ID avec toutes les relations chargées
    """
    return db.query(Auction).options(
        joinedload(Auction.category),
        joinedload(Auction.specifications)
    ).filter(Auction.id == auction_id).first()

def get_auctions(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    filters: Optional[AuctionFilter] = None
) -> Tuple[List[Auction], int]:
    """
    Récupère une liste d'enchères avec pagination et filtrage
    """
    query = db.query(Auction)
    
    # Appliquer les filtres si fournis
    if filters:
        filter_data = filters.model_dump(exclude_unset=True)
        
        if 'category_id' in filter_data:
            query = query.filter(Auction.category_id == filter_data['category_id'])
        
        if 'min_price' in filter_data:
            query = query.filter(Auction.startingPrice >= filter_data['min_price'])
        
        if 'max_price' in filter_data:
            query = query.filter(Auction.startingPrice <= filter_data['max_price'])
        
        if 'status' in filter_data:
            query = query.filter(Auction.auctionStatus == filter_data['status'])
        
        if 'type' in filter_data:
            query = query.filter(Auction.auctionType == filter_data['type'])
        
        if 'location' in filter_data:
            query = query.filter(Auction.location.ilike(f"%{filter_data['location']}%"))
        
        if 'featured' in filter_data:
            query = query.filter(Auction.featuredAuction == filter_data['featured'])
        
        if 'search' in filter_data and filter_data['search']:
            search_term = f"%{filter_data['search']}%"
            query = query.filter(
                or_(
                    Auction.title.ilike(search_term),
                    Auction.description.ilike(search_term)
                )
            )
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    auctions = query.order_by(desc(Auction.createdAt)).offset(skip).limit(limit).all()
    
    return auctions, total

def create_auction(db: Session, auction_data: AuctionCreate) -> Auction:
    """
    Crée une nouvelle enchère
    """
    # Créer l'enchère
    db_auction = Auction(
        **auction_data.model_dump()
    )
    
    db.add(db_auction)
    db.commit()
    db.refresh(db_auction)
    
    return db_auction

def update_auction(db: Session, auction_id: int, auction_data: AuctionUpdate) -> Dict[str, Any]:
    """
    Met à jour une enchère existante et ses spécifications si fournies.
    Retourne un dictionnaire avec les détails de l'enchère comme get_auction_with_details
    """
    from app.models.auction_specification import AuctionSpecification
    
    db_auction = get_auction(db, auction_id)
    if not db_auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée (pas déjà active ou terminée)
    if db_auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Extraire les spécifications de l'objet de mise à jour
    update_data = auction_data.model_dump(exclude_unset=True)
    specifications_data = update_data.pop('specifications', None)
    
    # Mettre à jour les champs modifiables
    for key, value in update_data.items():
        setattr(db_auction, key, value)
    
    # Mettre à jour les spécifications si elles sont fournies
    if specifications_data is not None:
        # Supprimer toutes les spécifications existantes
        db.query(AuctionSpecification).filter(AuctionSpecification.auctionId == auction_id).delete()
        
        # Ajouter les nouvelles spécifications
        for spec_data in specifications_data:
            db_spec = AuctionSpecification(
                auctionId=auction_id,
                property=spec_data.get('property'),
                value=spec_data.get('value')
            )
            db.add(db_spec)
    
    db_auction.updatedAt = datetime.now()
    db.commit()
    db.refresh(db_auction)
    
    # Au lieu de retourner directement l'enchère, on appelle get_auction_with_details
    # pour bénéficier de la même structure de réponse
    return get_auction_with_details(db, auction_id)

def update_auction_status(db: Session, auction_id: int, status_data: AuctionStatusUpdate) -> Auction:
    """
    Met à jour le statut d'une enchère
    """
    db_auction = get_auction(db, auction_id)
    if not db_auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier les transitions de statut valides
    current_status = db_auction.auctionStatus
    new_status = status_data.status
    
    # Validation des transitions de statut (à adapter selon vos règles métier)
    valid_transitions = {
        AuctionStatus.DRAFT: [AuctionStatus.SCHEDULED, AuctionStatus.CANCELLED],
        AuctionStatus.SCHEDULED: [AuctionStatus.ACTIVE, AuctionStatus.CANCELLED],
        AuctionStatus.ACTIVE: [AuctionStatus.CLOSED, AuctionStatus.CANCELLED],
        AuctionStatus.CLOSED: [AuctionStatus.SOLD],
        AuctionStatus.CANCELLED: [],
        AuctionStatus.SOLD: []
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition de statut invalide: {current_status} -> {new_status}"
        )
    
    db_auction.auctionStatus = new_status
    db_auction.updatedAt = datetime.now()
    db.commit()
    db.refresh(db_auction)
    
    return db_auction

def delete_auction(db: Session, auction_id: int) -> bool:
    """
    Supprime une enchère (seulement si elle est en brouillon ou annulée)
    """
    db_auction = get_auction(db, auction_id)
    if not db_auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère peut être supprimée
    if db_auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les enchères en brouillon ou annulées peuvent être supprimées"
        )
    
    db.delete(db_auction)
    db.commit()
    
    return True

def get_highest_bid(db: Session, auction_id: int) -> Optional[float]:
    """
    Récupère le montant de l'enchère la plus élevée pour une enchère
    """
    highest_bid = db.query(func.max(Bid.amount)).filter(Bid.auctionId == auction_id).scalar()
    return highest_bid

def get_auction_with_details(db: Session, auction_id: int) -> Dict[str, Any]:
    """
    Récupère une enchère avec des détails supplémentaires (enchère la plus élevée, nombre d'enchères, etc.)
    Convertit l'enchère en dictionnaire pour éviter les problèmes de sérialisation
    """
    auction = get_auction(db, auction_id)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Récupérer des informations supplémentaires
    highest_bid = get_highest_bid(db, auction_id)
    total_bids = db.query(Bid).filter(Bid.auctionId == auction_id).count()
    
    # Convertir les spécifications en liste de dictionnaires
    specifications_list = []
    if auction.specifications:
        for spec in auction.specifications:
            specifications_list.append({
                "id": spec.id,
                "auctionId": spec.auctionId,
                "property": spec.property,
                "value": spec.value
            })
    
    # Convertir l'enchère en dictionnaire
    auction_dict = {
        "id": auction.id,
        "title": auction.title,
        "category_id": auction.category_id,
        "description": auction.description,
        "startingPrice": auction.startingPrice,
        "reservePrice": auction.reservePrice,
        "incrementAmount": auction.incrementAmount,
        "location": auction.location,
        "sellerName": auction.sellerName,
        "termsConditions": auction.termsConditions,
        "productHistory": auction.productHistory,
        "startDate": auction.startDate,
        "endDate": auction.endDate,
        "startTime": auction.startTime,
        "endTime": auction.endTime,
        "auctionType": auction.auctionType,
        "auctionStatus": auction.auctionStatus,
        "featuredAuction": auction.featuredAuction,
        "creator_id": auction.creator_id,
        "createdAt": auction.createdAt,
        "updatedAt": auction.updatedAt,
        "highestBid": highest_bid,
        "totalBids": total_bids,
        # Inclure les spécifications correctement formatées
        "specifications": specifications_list,
        # Supprime les images et documents de la réponse
        "category": {"id": auction.category_id, "name": auction.category.name if auction.category else None}
    }
    
    return auction_dict
