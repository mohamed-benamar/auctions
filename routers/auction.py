from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, File, UploadFile, Form, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
import json

# Configuration du logger
logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.user import User, UserRole
from app.models.auction import AuctionStatus, AuctionType
from app.crud import auction as auction_crud
from app.crud import category as category_crud
from app.schemas.auction import (
    AuctionCreate, 
    AuctionUpdate, 
    AuctionResponse, 
    AuctionDetailResponse, 
    AuctionPaginatedResponse,
    AuctionStatusUpdate,
    AuctionFilter,
    AuctionListResponse
)
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/auctions",
    tags=["Auctions"],
    responses={404: {"description": "Not found"}},
)

def is_admin_user(user: User) -> bool:
    """Vérifie si l'utilisateur a des droits d'administration"""
    return user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]

@router.post("/", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
def create_auction(
    auction_data: AuctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Crée une nouvelle enchère.
    Nécessite d'être authentifié.
    """
    # Ajouter l'ID du créateur
    auction_data_dict = auction_data.model_dump()
    auction_data_dict["creator_id"] = current_user.id
    auction_data_updated = AuctionCreate(**auction_data_dict)
    
    return auction_crud.create_auction(db=db, auction_data=auction_data_updated)

@router.get("/", response_model=AuctionPaginatedResponse)
def read_auctions(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    status: Optional[AuctionStatus] = None,
    type: Optional[AuctionType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les enchères avec pagination et filtrage.
    Cet endpoint est public.
    """
    # Construire l'objet de filtre
    filter_data = {}
    if category_id is not None:
        filter_data["category_id"] = category_id
    if status is not None:
        filter_data["status"] = status
    if type is not None:
        filter_data["type"] = type
    if min_price is not None:
        filter_data["min_price"] = min_price
    if max_price is not None:
        filter_data["max_price"] = max_price
    if featured is not None:
        filter_data["featured"] = featured
    if location is not None:
        filter_data["location"] = location
    if search is not None:
        filter_data["search"] = search
    
    auction_filter = AuctionFilter(**filter_data) if filter_data else None
    
    auctions, total = auction_crud.get_auctions(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=auction_filter
    )
    
    # Retourner la liste des enchères avec le total uniquement
    return {
        "auctions": auctions,
        "total": total
    }

@router.get("/list", response_model=AuctionListResponse)
def read_auctions_as_array(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    status: Optional[AuctionStatus] = None,
    type: Optional[AuctionType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les enchères et les renvoie sous forme de tableau simple.
    Cet endpoint est public.
    """
    # Construire l'objet de filtre
    filter_data = {}
    if category_id is not None:
        filter_data["category_id"] = category_id
    if status is not None:
        filter_data["status"] = status
    if type is not None:
        filter_data["type"] = type
    if min_price is not None:
        filter_data["min_price"] = min_price
    if max_price is not None:
        filter_data["max_price"] = max_price
    if featured is not None:
        filter_data["featured"] = featured
    if location is not None:
        filter_data["location"] = location
    if search is not None:
        filter_data["search"] = search
    
    auction_filter = AuctionFilter(**filter_data) if filter_data else None
    
    auctions, _ = auction_crud.get_auctions(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=auction_filter
    )
    
    # Retourner directement le tableau d'enchères
    return auctions

@router.get("/{auction_id}", response_model=AuctionDetailResponse)
def read_auction(
    auction_id: int = Path(..., description="The ID of the auction to get"),
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'une enchère par son ID.
    Cet endpoint est public.
    """
    # Récupérer l'enchère avec ses détails
    auction_details = auction_crud.get_auction_with_details(db=db, auction_id=auction_id)
    
    return auction_details

@router.put("/{auction_id}", response_model=AuctionDetailResponse, dependencies=[Depends(JWTBearer())])
async def update_auction(
    request: Request,
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour une enchère existante.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    Utilise le système de validation global pour des messages d'erreur cohérents.
    """
    # Récupérer l'enchère existante
    existing_auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not existing_auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if existing_auction.creator_id != current_user.id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette enchère"
        )
    
    # Récupérer et valider les données JSON directement via FastAPI
    try:
        # Lire le corps de la requête
        body = await request.body()
        request_data = json.loads(body.decode('utf-8'))
        
        # Logger le corps pour le débogage
        logger.debug(f"Corps de la requête pour l'enchère {auction_id}: {json.dumps(request_data)}")
        
        # Corriger les fautes de frappe courantes dans les clés
        if "ategory_id" in request_data and "category_id" not in request_data:
            logger.warning(f"Clé mal orthographiée trouvée: 'ategory_id' sera corrigée en 'category_id'")
            request_data["category_id"] = request_data["ategory_id"]
            del request_data["ategory_id"]
            
        # Conversion spéciale pour category_id si c'est une chaîne de caractères
        if "category_id" in request_data and isinstance(request_data["category_id"], str):
            try:
                # Essayer de convertir en entier
                request_data["category_id"] = int(request_data["category_id"])
            except ValueError:
                # Si c'est un nom de catégorie, essayer de trouver l'ID
                categories = category_crud.get_all_categories(db)
                category_found = False
                for cat in categories:
                    if cat.name == request_data["category_id"]:
                        request_data["category_id"] = cat.id
                        category_found = True
                        break
                        
                if not category_found:
                    # Utiliser RequestValidationError pour profiter du gestionnaire d'exceptions global
                    validation_errors = [
                        {
                            "loc": ["body", "category_id"],
                            "msg": f"Le champ 'category_id' doit être un ID de catégorie valide et non '{request_data['category_id']}'",
                            "type": "type_error.integer"
                        }
                    ]
                    raise RequestValidationError(errors=validation_errors)
        
        # Vérification cohérence des dates
        if "startDate" in request_data and "endDate" in request_data:
            try:
                start_date = datetime.fromisoformat(request_data["startDate"].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(request_data["endDate"].replace('Z', '+00:00'))
                if end_date <= start_date:
                    validation_errors = [
                        {
                            "loc": ["body", "endDate"],
                            "msg": "La date de fin doit être postérieure à la date de début",
                            "type": "value_error.date_comparison"
                        }
                    ]
                    raise RequestValidationError(errors=validation_errors)
            except (ValueError, TypeError) as e:
                # Laisser la validation Pydantic gérer ce cas
                pass
        
        # Utiliser Pydantic pour la validation avec son gestionnaire d'erreurs global
        auction_data = AuctionUpdate(**request_data)
        
        # Tout est valide, mettre à jour l'enchère
        return auction_crud.update_auction(db=db, auction_id=auction_id, auction_data=auction_data)
        
    except json.JSONDecodeError:
        # JSON invalide
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format JSON invalide dans le corps de la requête. Veuillez vérifier la syntaxe de votre JSON."
        )
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'enchère {auction_id}: {str(e)}")
        if isinstance(e, RequestValidationError) or isinstance(e, ValidationError):
            # Laisser le middleware de gestion d'exceptions s'en occuper
            raise
        else:
            # Autres erreurs inattendues
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Une erreur inattendue est survenue lors de la mise à jour de l'enchère: {str(e)}"
            )

@router.put("/{auction_id}/status", response_model=AuctionResponse, dependencies=[Depends(JWTBearer())])
def update_auction_status(
    auction_id: int,
    status_data: AuctionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour le statut d'une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer l'enchère existante
    existing_auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not existing_auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if existing_auction.creator_id != current_user.id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette enchère"
        )
    
    # Mettre à jour le statut de l'enchère
    return auction_crud.update_auction_status(db=db, auction_id=auction_id, status_data=status_data)

@router.delete("/{auction_id}", response_model=Dict[str, bool], dependencies=[Depends(JWTBearer())])
def delete_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Supprime une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    Seules les enchères en brouillon ou annulées peuvent être supprimées.
    """
    # Récupérer l'enchère existante
    existing_auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not existing_auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if existing_auction.creator_id != current_user.id and not is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette enchère"
        )
    
    # Supprimer l'enchère
    result = auction_crud.delete_auction(db=db, auction_id=auction_id)
    
    # Si la suppression a réussi, nettoyer les fichiers associés
    if result:
        from app.utils.file_utils import cleanup_auction_files
        cleanup_auction_files(auction_id)
    
    return {"success": result}

@router.get("/my/auctions", response_model=AuctionPaginatedResponse, dependencies=[Depends(JWTBearer())])
def read_my_auctions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[AuctionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Récupère les enchères de l'utilisateur actuel.
    Nécessite d'être authentifié.
    """
    # Construire l'objet de filtre
    filter_data = {"creator_id": current_user.id}
    if status is not None:
        filter_data["status"] = status
    
    auction_filter = AuctionFilter(**filter_data)
    
    auctions, total = auction_crud.get_auctions(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=auction_filter
    )
    
    # Retourner la liste des enchères avec le total uniquement
    return {
        "auctions": auctions,
        "total": total
    }
