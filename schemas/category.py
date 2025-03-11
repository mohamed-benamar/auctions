from pydantic import BaseModel, Field, RootModel
from typing import Optional, List

class CategoryBase(BaseModel):
    """Schéma de base pour les catégories"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Schéma pour la création d'une catégorie"""
    pass

class CategoryUpdate(BaseModel):
    """Schéma pour la mise à jour d'une catégorie"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    """Schéma pour la réponse d'une catégorie"""
    id: int

    model_config = {
        "from_attributes": True
    }

class CategoryPaginatedResponse(BaseModel):
    """Schéma pour la réponse paginée des catégories"""
    items: List[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int

class CategoryListResponse(RootModel):
    """Schéma pour une liste simple de catégories sans pagination"""
    root: List[CategoryResponse]

class CategoryList(BaseModel):
    """Schéma pour la liste des catégories"""
    categories: List[CategoryResponse]
    total: int
