"""
Module de routeur pour les données géographiques et tribunaux
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Pays, Ville, Tribunal, OrganismCredit, User
from app.schemas.utilities import (
    PaysResponse, 
    VilleResponse, 
    TribunalResponse, 
    PaysList, 
    VilleList, 
    TribunalList,
    OrganismCreditResponse,
    OrganismCreditList,
    OrganismCreditCreate
)

# Créer le routeur
router = APIRouter(
    prefix="/utilities",
    tags=["Utilities"],
    responses={404: {"description": "Not found"}},
)

# Routes pour les pays
@router.get("/pays", response_model=List[PaysResponse])
def get_all_pays(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les pays.
    """
    pays = db.query(Pays).offset(skip).limit(limit).all()
    
    return pays

@router.get("/pays/{pays_id}", response_model=PaysResponse)
def get_pays(
    pays_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un pays par son ID.
    """
    pays = db.query(Pays).filter(Pays.id == pays_id).first()
    if not pays:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pays non trouvé"
        )
    
    return pays

# Routes pour les villes
@router.get("/villes", response_model=List[VilleResponse])
def get_all_villes(
    pays_id: int = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de toutes les villes.
    Peut être filtré par pays_id.
    """
    query = db.query(Ville)
    
    if pays_id:
        query = query.filter(Ville.pays_id == pays_id)
    
    villes = query.offset(skip).limit(limit).all()
    
    return villes

@router.get("/villes/{ville_id}", response_model=VilleResponse)
def get_ville(
    ville_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une ville par son ID.
    """
    ville = db.query(Ville).filter(Ville.id == ville_id).first()
    if not ville:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ville non trouvée"
        )
    
    return ville

# Routes pour les tribunaux
@router.get("/tribunaux", response_model=List[TribunalResponse])
def get_all_tribunaux(
    ville: str = Query(None),
    type: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les tribunaux.
    Peut être filtré par ville et/ou type.
    """
    query = db.query(Tribunal)
    
    if ville:
        query = query.filter(Tribunal.ville == ville)
    
    if type:
        query = query.filter(Tribunal.type == type)
    
    tribunaux = query.offset(skip).limit(limit).all()
    
    return tribunaux

@router.get("/tribunaux/{tribunal_id}", response_model=TribunalResponse)
def get_tribunal(
    tribunal_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un tribunal par son ID.
    """
    tribunal = db.query(Tribunal).filter(Tribunal.id == tribunal_id).first()
    if not tribunal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tribunal non trouvé"
        )
    
    return tribunal

# Routes pour les organismes de crédit
@router.get("/organism-credit", response_model=List[OrganismCreditResponse])
def get_all_organism_credit(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste de tous les organismes de crédit.
    """
    organismes = db.query(OrganismCredit).offset(skip).limit(limit).all()
    
    return organismes

@router.get("/organism-credit/{organism_id}", response_model=OrganismCreditResponse)
def get_organism_credit(
    organism_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère un organisme de crédit par son ID.
    """
    organism = db.query(OrganismCredit).filter(OrganismCredit.id == organism_id).first()
    if not organism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisme de crédit non trouvé"
        )
    
    return organism

@router.post("/organism-credit", response_model=OrganismCreditResponse, status_code=status.HTTP_201_CREATED)
def create_organism_credit(
    organism_data: OrganismCreditCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel organisme de crédit.
    """
    # Vérifier si un organisme avec le même nom existe déjà
    existing_organism = db.query(OrganismCredit).filter(OrganismCredit.nom == organism_data.nom).first()
    if existing_organism:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un organisme de crédit avec ce nom existe déjà"
        )
    
    # Créer le nouvel organisme
    new_organism = OrganismCredit(**organism_data.dict())
    db.add(new_organism)
    db.commit()
    db.refresh(new_organism)
    
    return new_organism

@router.put("/organism-credit/{organism_id}", response_model=OrganismCreditResponse)
def update_organism_credit(
    organism_id: int,
    organism_data: OrganismCreditCreate,
    db: Session = Depends(get_db)
):
    """
    Met à jour un organisme de crédit existant.
    """
    # Récupérer l'organisme à mettre à jour
    organism = db.query(OrganismCredit).filter(OrganismCredit.id == organism_id).first()
    if not organism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisme de crédit non trouvé"
        )
    
    # Vérifier si le nouveau nom est déjà utilisé par un autre organisme
    if organism_data.nom != organism.nom:
        existing_organism = db.query(OrganismCredit).filter(OrganismCredit.nom == organism_data.nom).first()
        if existing_organism:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un organisme de crédit avec ce nom existe déjà"
            )
    
    # Mettre à jour les données
    for key, value in organism_data.dict().items():
        setattr(organism, key, value)
    
    db.commit()
    db.refresh(organism)
    
    return organism

@router.delete("/organism-credit/{organism_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organism_credit(
    organism_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime un organisme de crédit.
    """
    # Récupérer l'organisme à supprimer
    organism = db.query(OrganismCredit).filter(OrganismCredit.id == organism_id).first()
    if not organism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisme de crédit non trouvé"
        )
    
    # Vérifier si des utilisateurs sont associés à cet organisme
    users_count = db.query(User).filter(User.organism_credit_id == organism_id).count()
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer cet organisme car {users_count} utilisateur(s) y sont associés"
        )
    
    # Supprimer l'organisme
    db.delete(organism)
    db.commit()
    
    return None
