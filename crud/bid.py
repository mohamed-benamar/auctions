from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from app.models.bid import Bid
from app.models.auction import Auction, AuctionStatus
from app.models.user import User
from app.schemas.bid import BidCreate
from fastapi import HTTPException, status

def get_bid(db: Session, bid_id: int) -> Optional[Bid]:
    """
    Récupère une enchère par son ID
    """
    return db.query(Bid).filter(Bid.id == bid_id).first()

def get_auction_bids(
    db: Session, 
    auction_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[Bid], int]:
    """
    Récupère la liste des enchères pour une enchère spécifique
    """
    query = db.query(Bid).filter(Bid.auctionId == auction_id)
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination et trier par montant décroissant (enchère la plus élevée en premier)
    bids = query.order_by(desc(Bid.amount), desc(Bid.timestamp)).offset(skip).limit(limit).all()
    
    return bids, total

def get_user_bids(
    db: Session, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[Bid], int]:
    """
    Récupère la liste des enchères d'un utilisateur spécifique
    """
    query = db.query(Bid).filter(Bid.bidderId == user_id)
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination et trier par date décroissante (plus récente en premier)
    bids = query.order_by(desc(Bid.timestamp)).offset(skip).limit(limit).all()
    
    return bids, total

def get_highest_bid(db: Session, auction_id: int) -> Optional[Bid]:
    """
    Récupère l'enchère la plus élevée pour une enchère spécifique
    """
    return db.query(Bid).filter(Bid.auctionId == auction_id).order_by(desc(Bid.amount)).first()

def create_bid(db: Session, bid_data: BidCreate, user_id: int) -> Bid:
    """
    Crée une nouvelle enchère
    """
    # Récupérer l'enchère
    auction = db.query(Auction).filter(Auction.id == bid_data.auctionId).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère est active
    if auction.auctionStatus != AuctionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère n'est pas active"
        )
    
    # Vérifier si la date de l'enchère est valide
    now = datetime.now()
    if now < auction.startDate or now > auction.endDate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère n'est pas ouverte à cette date"
        )
    
    # Vérifier si le montant de l'enchère est valide
    highest_bid = get_highest_bid(db, bid_data.auctionId)
    if highest_bid:
        min_bid = highest_bid.amount + auction.incrementAmount
        if bid_data.amount < min_bid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'enchère doit être d'au moins {min_bid}"
            )
    else:
        # Première enchère, doit être au moins égale au prix de départ
        if bid_data.amount < auction.startingPrice:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'enchère doit être d'au moins {auction.startingPrice}"
            )
    
    # Créer l'enchère
    db_bid = Bid(
        auctionId=bid_data.auctionId,
        bidderId=user_id,
        amount=bid_data.amount,
        timestamp=datetime.now()
    )
    
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    
    return db_bid

def get_bid_with_user_details(db: Session, bid_id: int) -> Dict[str, Any]:
    """
    Récupère une enchère avec les détails de l'utilisateur
    """
    bid = get_bid(db, bid_id)
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Récupérer l'utilisateur qui a fait l'enchère
    user = db.query(User).filter(User.id == bid.bidderId).first()
    
    # Créer un dictionnaire avec les détails de l'enchère et de l'utilisateur
    bid_dict = {
        "id": bid.id,
        "auctionId": bid.auctionId,
        "amount": bid.amount,
        "timestamp": bid.timestamp,
        "bidderId": bid.bidderId,
        "bidderFirstName": user.first_name if user else None,
        "bidderLastName": user.last_name if user else None,
        "bidderEmail": user.email if user else None
    }
    
    return bid_dict
