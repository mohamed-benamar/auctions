from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.crud import bid as bid_crud
from app.schemas.bid import BidCreate, BidResponse, BidDetailResponse, BidPaginatedResponse
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/bids",
    tags=["Bids"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=BidResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
def create_bid(
    bid_data: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Crée une nouvelle enchère sur un produit.
    Nécessite d'être authentifié.
    """
    return bid_crud.create_bid(db=db, bid_data=bid_data, user_id=current_user.id)

@router.get("/auction/{auction_id}", response_model=BidPaginatedResponse)
def read_auction_bids(
    auction_id: int = Path(..., description="The ID of the auction to get bids for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les enchères pour un produit spécifique.
    Cet endpoint est public.
    """
    bids, total = bid_crud.get_auction_bids(db=db, auction_id=auction_id, skip=skip, limit=limit)
    
    return {
        "items": bids,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/my/bids", response_model=BidPaginatedResponse, dependencies=[Depends(JWTBearer())])
def read_my_bids(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Récupère toutes les enchères de l'utilisateur actuel.
    Nécessite d'être authentifié.
    """
    bids, total = bid_crud.get_user_bids(db=db, user_id=current_user.id, skip=skip, limit=limit)
    
    return {
        "items": bids,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/{bid_id}", response_model=BidDetailResponse)
def read_bid(
    bid_id: int = Path(..., description="The ID of the bid to get"),
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'une enchère par son ID.
    Cet endpoint est public.
    """
    bid_details = bid_crud.get_bid_with_user_details(db=db, bid_id=bid_id)
    
    return bid_details
