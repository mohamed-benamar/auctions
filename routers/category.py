from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.crud import category as category_crud
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryPaginatedResponse, CategoryListResponse
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Crée une nouvelle catégorie.
    Seuls les administrateurs peuvent créer des catégories.
    """
    # Vérifier si l'utilisateur est un administrateur
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent créer des catégories"
        )
    
    return category_crud.create_category(db=db, category_data=category_data)

@router.get("/", response_model=CategoryListResponse)
def read_categories(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les catégories sans structure englobante, juste un tableau.
    Cet endpoint est public.
    """
    categories, _ = category_crud.get_categories(db, skip=skip, limit=limit, search=search)
    # Retourne directement le tableau de catégories
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
def read_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une catégorie par son ID.
    Cet endpoint est public.
    """
    db_category = category_crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")
    return db_category

@router.put("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(JWTBearer())])
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour une catégorie existante.
    Seuls les administrateurs peuvent mettre à jour des catégories.
    """
    # Vérifier si l'utilisateur est un administrateur
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent mettre à jour des catégories"
        )
    
    return category_crud.update_category(db=db, category_id=category_id, category_data=category_data)

@router.delete("/{category_id}", response_model=Dict[str, bool], dependencies=[Depends(JWTBearer())])
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Supprime une catégorie.
    Seuls les administrateurs peuvent supprimer des catégories.
    """
    # Vérifier si l'utilisateur est un administrateur
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent supprimer des catégories"
        )
    
    result = category_crud.delete_category(db=db, category_id=category_id)
    return {"success": result}
