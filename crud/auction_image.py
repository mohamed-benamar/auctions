from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.auction_image import AuctionImage
from app.models.auction import Auction, AuctionStatus
from app.schemas.auction_image import AuctionImageCreate, AuctionImageUpdate
from fastapi import HTTPException, status

def get_image(db: Session, image_id: int) -> Optional[AuctionImage]:
    """
    Récupère une image par son ID
    """
    return db.query(AuctionImage).filter(AuctionImage.id == image_id).first()

def get_auction_images(
    db: Session, 
    auction_id: int,
    skip: int = 0, 
    limit: int = 100
) -> Tuple[List[AuctionImage], int]:
    """
    Récupère toutes les images pour une enchère spécifique
    """
    query = db.query(AuctionImage).filter(AuctionImage.auctionId == auction_id)
    
    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination et trier par ordre d'affichage
    images = query.order_by(AuctionImage.order).offset(skip).limit(limit).all()
    
    return images, total

def get_main_image(db: Session, auction_id: int) -> Optional[AuctionImage]:
    """
    Récupère l'image principale d'une enchère
    """
    return db.query(AuctionImage).filter(
        AuctionImage.auctionId == auction_id,
        AuctionImage.isMain == True
    ).first()

def create_image(db: Session, image_data: AuctionImageCreate) -> AuctionImage:
    """
    Ajoute une nouvelle image à une enchère
    """
    # Vérifier si l'enchère existe
    auction = db.query(Auction).filter(Auction.id == image_data.auctionId).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    if auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Si l'image est marquée comme principale, mettre à jour les autres images
    if image_data.isMain:
        db.query(AuctionImage).filter(
            AuctionImage.auctionId == image_data.auctionId,
            AuctionImage.isMain == True
        ).update({AuctionImage.isMain: False})
    
    # Déterminer l'ordre d'affichage si non spécifié
    order_value = image_data.order
    if order_value == 0:  # Valeur par défaut, assignons un ordre séquentiel
        max_order = db.query(AuctionImage).filter(
            AuctionImage.auctionId == image_data.auctionId
        ).count()
        order_value = max_order + 1
    
    # Créer l'image
    db_image = AuctionImage(
        auctionId=image_data.auctionId,
        imageUrl=image_data.imageUrl,
        caption=image_data.caption,
        isMain=image_data.isMain,
        order=order_value
    )
    
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return db_image

def update_image(db: Session, image_id: int, image_data: AuctionImageUpdate) -> AuctionImage:
    """
    Met à jour une image existante
    """
    db_image = get_image(db, image_id)
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_image.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    update_data = image_data.model_dump(exclude_unset=True)
    
    # Si l'image devient principale, mettre à jour les autres images
    if update_data.get('isMain', False) and not db_image.isMain:
        db.query(AuctionImage).filter(
            AuctionImage.auctionId == db_image.auctionId,
            AuctionImage.isMain == True
        ).update({AuctionImage.isMain: False})
    
    # Mettre à jour les champs modifiables
    for key, value in update_data.items():
        setattr(db_image, key, value)
    
    db.commit()
    db.refresh(db_image)
    
    return db_image

def delete_image(db: Session, image_id: int) -> bool:
    """
    Supprime une image
    """
    db_image = get_image(db, image_id)
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    auction = db.query(Auction).filter(Auction.id == db_image.auctionId).first()
    if auction and auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Vérifier si c'est l'image principale
    if db_image.isMain:
        # Trouver une autre image à définir comme principale
        next_image = db.query(AuctionImage).filter(
            AuctionImage.auctionId == db_image.auctionId,
            AuctionImage.id != image_id
        ).first()
        
        if next_image:
            next_image.isMain = True
            db.commit()
    
    # Supprimer l'image
    db.delete(db_image)
    db.commit()
    
    return True

def reorder_images(db: Session, auction_id: int, image_ids: List[int]) -> List[AuctionImage]:
    """
    Réordonne les images d'une enchère selon la liste d'IDs fournie
    """
    # Vérifier si l'enchère existe
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enchère non trouvée"
        )
    
    # Vérifier si l'enchère peut être modifiée
    if auction.auctionStatus not in [AuctionStatus.DRAFT, AuctionStatus.SCHEDULED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'enchère ne peut pas être modifiée car elle est déjà active, terminée ou annulée"
        )
    
    # Vérifier que tous les IDs appartiennent à des images de cette enchère
    images = db.query(AuctionImage).filter(
        AuctionImage.auctionId == auction_id,
        AuctionImage.id.in_(image_ids)
    ).all()
    
    if len(images) != len(image_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certaines images n'appartiennent pas à cette enchère ou n'existent pas"
        )
    
    # Mettre à jour l'ordre d'affichage
    for idx, image_id in enumerate(image_ids):
        db.query(AuctionImage).filter(AuctionImage.id == image_id).update(
            {AuctionImage.displayOrder: idx}
        )
    
    db.commit()
    
    # Récupérer les images mises à jour
    updated_images = db.query(AuctionImage).filter(
        AuctionImage.auctionId == auction_id
    ).order_by(AuctionImage.displayOrder).all()
    
    return updated_images

def update_main_image(db: Session, auction_id: int) -> None:
    """
    Met à jour toutes les images d'une enchère pour qu'aucune ne soit l'image principale
    Cette fonction est utilisée avant de définir une nouvelle image principale
    """
    db.query(AuctionImage).filter(
        AuctionImage.auctionId == auction_id,
        AuctionImage.isMain == True
    ).update({AuctionImage.isMain: False})
    
    db.commit()
