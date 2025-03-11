# app/routes/deposit.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.database import get_db
from app.models.deposit import DepositStatus, DepositMethod
from app.schemas.deposit import (
    DepositCreate, 
    DepositUpdate, 
    DepositResponse, 
    DepositFilter, 
    DepositWithAuctionInfo,
    PaginatedDeposits
)
from app.crud.deposit import CRUDDeposit
from app.crud.auction import get_auction
from app.utils.file_utils import save_upload_file, generate_unique_filename
from app.utils.security import get_current_user, get_admin_user

from app.config import settings

router = APIRouter(
    prefix="/deposits",
    tags=["deposits"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=DepositResponse)
async def create_deposit(
    amount: float = Form(...),
    auctionId: int = Form(...),
    depositMethod: DepositMethod = Form(...),
    receiptFile: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Créer un nouveau dépôt de caution pour une enchère.
    Nécessite un utilisateur authentifié.
    """
    # Vérifier que l'enchère existe
    auction = get_auction(db, auctionId)
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Préparer l'objet DepositCreate
    deposit_data = {
        "amount": amount,
        "auctionId": auctionId,
        "userId": current_user.id,
        "depositMethod": depositMethod,
        "receiptFile": None
    }
    
    # Gérer le fichier de reçu si fourni
    if receiptFile:
        unique_filename = await generate_unique_filename(receiptFile.filename, "receipt")
        upload_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Sauvegarder le fichier
        await save_upload_file(receiptFile, file_path)
        deposit_data["receiptFile"] = unique_filename
    
    # Créer le dépôt dans la base de données
    db_deposit = CRUDDeposit.create(db, DepositCreate(**deposit_data))
    
    return DepositResponse.from_orm(db_deposit)

@router.get("/", response_model=PaginatedDeposits)
async def read_deposits(
    status: Optional[DepositStatus] = Query(None, description="Filtre par statut"),
    auctionId: Optional[int] = Query(None, description="Filtre par ID d'enchère"),
    searchTerm: Optional[str] = Query(None, description="Terme de recherche"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments à retourner"),
    db: Session = Depends(get_db),
    current_user = Depends(get_admin_user)  # Seuls les admins peuvent voir tous les dépôts
):
    """
    Récupère la liste des dépôts avec pagination et filtrage.
    Réservé aux administrateurs.
    """
    filters = DepositFilter(
        status=status,
        auctionId=auctionId,
        searchTerm=searchTerm
    )
    
    # Récupérer les dépôts filtrés
    deposits, total = CRUDDeposit.get_multi(db, skip, limit, filters)
    
    # Préparer la réponse avec les informations d'enchère
    enriched_deposits = []
    for deposit in deposits:
        deposit_data = DepositResponse.from_orm(deposit).dict()
        deposit_data["auctionTitle"] = deposit.auction.title
        enriched_deposits.append(DepositWithAuctionInfo(**deposit_data))
    
    return {
        "items": enriched_deposits,
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/my", response_model=List[DepositWithAuctionInfo])
async def read_user_deposits(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Récupère tous les dépôts de l'utilisateur connecté.
    """
    deposits = CRUDDeposit.get_by_user(db, current_user.id)
    
    # Enrichir avec les informations d'enchère
    enriched_deposits = []
    for deposit in deposits:
        deposit_data = DepositResponse.from_orm(deposit).dict()
        deposit_data["auctionTitle"] = deposit.auction.title
        enriched_deposits.append(DepositWithAuctionInfo(**deposit_data))
    
    return enriched_deposits

@router.get("/{deposit_id}", response_model=DepositWithAuctionInfo)
async def read_deposit(
    deposit_id: int = Path(..., description="ID du dépôt à récupérer"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Récupère les détails d'un dépôt spécifique.
    L'utilisateur doit être le propriétaire du dépôt ou un administrateur.
    """
    deposit = CRUDDeposit.get(db, deposit_id)
    
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépôt non trouvé"
        )
    
    # Vérifier les autorisations
    if not current_user.is_admin and deposit.userId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce dépôt"
        )
    
    # Enrichir avec les informations d'enchère
    deposit_data = DepositResponse.from_orm(deposit).dict()
    deposit_data["auctionTitle"] = deposit.auction.title
    
    return DepositWithAuctionInfo(**deposit_data)

@router.put("/{deposit_id}", response_model=DepositResponse)
async def update_deposit_status(
    deposit_id: int = Path(..., description="ID du dépôt à mettre à jour"),
    status: DepositStatus = Form(..., description="Nouveau statut du dépôt"),
    adminMessage: Optional[str] = Form(None, description="Message de l'administrateur"),
    db: Session = Depends(get_db),
    current_user = Depends(get_admin_user)  # Seuls les admins peuvent mettre à jour les dépôts
):
    """
    Mettre à jour le statut d'un dépôt.
    Réservé aux administrateurs.
    Un message est requis en cas de rejet.
    """
    # Vérifier que le dépôt existe
    deposit = CRUDDeposit.get(db, deposit_id)
    
    if not deposit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dépôt non trouvé"
        )
    
    # Valider que le message est présent en cas de rejet
    if status == DepositStatus.REJECTED and not adminMessage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un message explicatif est requis pour rejeter un dépôt"
        )
    
    # Préparer les données de mise à jour
    update_data = DepositUpdate(
        status=status,
        adminMessage=adminMessage,
        reviewedBy=current_user.username  # Utiliser le nom d'utilisateur comme identifiant de réviseur
    )
    
    # Mettre à jour le dépôt
    updated_deposit = CRUDDeposit.update(db, deposit_id, update_data)
    
    if not updated_deposit:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de la mise à jour du dépôt"
        )
    
    return DepositResponse.from_orm(updated_deposit)

@router.get("/{deposit_id}/receipt")
async def download_deposit_receipt(
    deposit_id: int = Path(..., description="ID du dépôt"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Récupère le chemin du fichier de reçu d'un dépôt.
    L'utilisateur doit être le propriétaire du dépôt ou un administrateur.
    """
    deposit = CRUDDeposit.get(db, deposit_id)
    
    if not deposit or not deposit.receiptFile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reçu non trouvé"
        )
    
    # Vérifier les autorisations
    if not current_user.is_admin and deposit.userId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce reçu"
        )
    
    file_path = os.path.join(settings.UPLOAD_DIR, "receipts", deposit.receiptFile)
    
    # Vérifier que le fichier existe
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier de reçu non trouvé sur le serveur"
        )
    
    return {"file_path": file_path}

@router.get("/stats/summary")
async def get_deposit_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_admin_user)  # Seuls les admins peuvent voir les statistiques
):
    """
    Obtient des statistiques sur les dépôts.
    Réservé aux administrateurs.
    """
    stats = CRUDDeposit.count_by_status(db)
    return stats