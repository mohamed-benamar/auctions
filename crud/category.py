from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from fastapi import HTTPException, status

def get_category(db: Session, category_id: int) -> Optional[Category]:
    """
    Récupère une catégorie par son ID
    """
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """
    Récupère une catégorie par son nom
    """
    return db.query(Category).filter(Category.name == name).first()

def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None
) -> Tuple[List[Category], int]:
    """
    Récupère une liste de catégories avec pagination et filtrage
    """
    query = db.query(Category)
    
    # Recherche sur le nom ou la description
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Category.name.ilike(search_term),
                Category.description.ilike(search_term)
            )
        )
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    categories = query.order_by(Category.name).offset(skip).limit(limit).all()
    
    return categories, total

def create_category(db: Session, category_data: CategoryCreate) -> Category:
    """
    Crée une nouvelle catégorie
    """
    # Vérifier si le nom de catégorie existe déjà
    if get_category_by_name(db, category_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une catégorie avec ce nom existe déjà"
        )
    
    # Créer la catégorie
    db_category = Category(
        name=category_data.name,
        description=category_data.description
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

def update_category(db: Session, category_id: int, category_data: CategoryUpdate) -> Category:
    """
    Met à jour une catégorie existante
    """
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Vérifier si le nouveau nom de catégorie existe déjà
    if category_data.name and category_data.name != db_category.name:
        existing_category = get_category_by_name(db, category_data.name)
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une catégorie avec ce nom existe déjà"
            )
    
    # Mettre à jour les champs modifiables
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    
    return db_category

def delete_category(db: Session, category_id: int) -> bool:
    """
    Supprime une catégorie
    """
    db_category = get_category(db, category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catégorie non trouvée"
        )
    
    # Vérifier si la catégorie est utilisée par des enchères
    if hasattr(db_category, 'auctions') and db_category.auctions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer cette catégorie car elle est utilisée par des enchères"
        )
    
    db.delete(db_category)
    db.commit()
    
    return True
