from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.crud import auction as auction_crud
from app.crud import auction_specification as spec_crud
from app.schemas.auction_specification import (
    AuctionSpecificationCreate, 
    AuctionSpecificationUpdate, 
    AuctionSpecificationResponse, 
    AuctionSpecificationPaginatedResponse
)
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/auction-specifications",
    tags=["Auction Specifications"],
    responses={404: {"description": "Not found"}},
)

@router.post("/{auction_id}", response_model=AuctionSpecificationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
def create_specification(
    auction_id: int,
    spec_data: AuctionSpecificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Ajoute une nouvelle spécification à une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des spécifications à cette enchère"
        )
    
    # Créer la spécification
    return spec_crud.create_specification(db=db, spec_data=spec_data)

@router.post("/bulk/{auction_id}", response_model=List[AuctionSpecificationResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
def create_bulk_specifications(
    auction_id: int,
    specs_data: List[AuctionSpecificationCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Ajoute plusieurs spécifications à une enchère en une seule opération.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des spécifications à cette enchère"
        )
    
    # Créer les spécifications en masse
    return spec_crud.create_bulk_specifications(db=db, auction_id=auction_id, specs_data=specs_data)

@router.get("/auction/{auction_id}", response_model=AuctionSpecificationPaginatedResponse)
def read_auction_specifications(
    auction_id: int = Path(..., description="The ID of the auction to get specifications for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les spécifications pour une enchère spécifique.
    Cet endpoint est public.
    """
    specs, total = spec_crud.get_auction_specifications(db=db, auction_id=auction_id, skip=skip, limit=limit)
    
    return {
        "items": specs,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/{spec_id}", response_model=AuctionSpecificationResponse)
def read_specification(
    spec_id: int = Path(..., description="The ID of the specification to get"),
    db: Session = Depends(get_db)
):
    """
    Récupère une spécification spécifique par son ID.
    Cet endpoint est public.
    """
    db_spec = spec_crud.get_specification(db=db, spec_id=spec_id)
    if not db_spec:
        raise HTTPException(status_code=404, detail="Spécification non trouvée")
    
    return db_spec

@router.put("/{spec_id}", response_model=AuctionSpecificationResponse, dependencies=[Depends(JWTBearer())])
def update_specification(
    spec_id: int,
    spec_data: AuctionSpecificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour une spécification existante.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer la spécification existante
    db_spec = spec_crud.get_specification(db=db, spec_id=spec_id)
    if not db_spec:
        raise HTTPException(status_code=404, detail="Spécification non trouvée")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_spec.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette spécification"
        )
    
    # Mettre à jour la spécification
    return spec_crud.update_specification(db=db, spec_id=spec_id, spec_data=spec_data)

@router.delete("/{spec_id}", response_model=Dict[str, bool], dependencies=[Depends(JWTBearer())])
def delete_specification(
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Supprime une spécification.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer la spécification existante
    db_spec = spec_crud.get_specification(db=db, spec_id=spec_id)
    if not db_spec:
        raise HTTPException(status_code=404, detail="Spécification non trouvée")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_spec.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette spécification"
        )
    
    # Supprimer la spécification
    result = spec_crud.delete_specification(db=db, spec_id=spec_id)
    
    return {"success": result}
