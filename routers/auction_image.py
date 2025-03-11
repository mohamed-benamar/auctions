from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.models.auction_image import AuctionImage
from app.crud import auction as auction_crud
from app.crud import auction_image as image_crud
from app.utils.file_utils import save_uploaded_image, delete_file_from_url
from app.schemas.auction_image import (
    AuctionImageCreate, 
    AuctionImageUpdate, 
    AuctionImageResponse, 
    AuctionImagePaginatedResponse
)
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/auction-images",
    tags=["Auction Images"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload/{auction_id}", response_model=AuctionImageResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_image(
    auction_id: int = Path(..., description="The ID of the auction to add an image to"),
    file: UploadFile = File(...),
    caption: str = Form(None),
    is_main: bool = Form(False),
    display_order: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Télécharge une nouvelle image pour une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des images à cette enchère"
        )
    
    # Enregistrer l'image téléchargée
    image_url = await save_uploaded_image(file=file, auction_id=auction_id)
    
    # Créer l'enregistrement dans la base de données
    image_data = AuctionImageCreate(
        auctionId=auction_id,
        imageUrl=image_url,
        caption=caption,
        isMain=is_main,
        displayOrder=display_order
    )
    
    return image_crud.create_image(db=db, image_data=image_data)

@router.post("/upload-multiple/{auction_id}", response_model=List[AuctionImageResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_multiple_images(
    auction_id: int = Path(..., description="The ID of the auction to add images to"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Télécharge plusieurs images pour une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    from app.models.user import UserRole
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    if auction.creator_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des images à cette enchère"
        )
    
    # Récupérer le nombre actuel d'images pour cet article
    _, total = image_crud.get_auction_images(db=db, auction_id=auction_id)
    
    # Créer une liste pour stocker les images créées
    created_images = []
    
    # Télécharger et créer chaque image
    for i, file in enumerate(files):
        # Enregistrer l'image téléchargée
        image_url = await save_uploaded_image(file=file, auction_id=auction_id)
        
        # Définir si c'est l'image principale (uniquement si c'est la première image et qu'il n'y a pas d'autres images)
        is_main = (i == 0 and total == 0)
        
        # Créer l'enregistrement dans la base de données
        image_data = AuctionImageCreate(
            auctionId=auction_id,
            imageUrl=image_url,
            caption=f"Image {i+1}",
            isMain=is_main,
            displayOrder=total + i
        )
        
        created_image = image_crud.create_image(db=db, image_data=image_data)
        created_images.append(created_image)
    
    return created_images

@router.post("/frontend-upload/{auction_id}", response_model=List[AuctionImageResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_images_from_frontend(
    auction_id: int = Path(..., description="The ID of the auction to add images to"),
    images: List[UploadFile] = File(...),
    names: List[str] = Form([], description="Les noms originaux des fichiers images"),
    is_main: bool = Form(False, description="Indique si l'image téléchargée est l'image principale"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    import logging
    logger = logging.getLogger(__name__)
    """
    Endpoint pour le frontend qui accepte plusieurs images avec le même nom de champ 'images'.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    from app.models.user import UserRole
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    if auction.creator_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des images à cette enchère"
        )
    
    # Récupérer le nombre actuel d'images pour cet article
    _, total = image_crud.get_auction_images(db=db, auction_id=auction_id)
    
    # Créer une liste pour stocker les images créées
    created_images = []
    
    # Débogage du paramètre is_main
    logger.info(f"Frontend a envoyé is_main={is_main} pour l'enchère {auction_id}")
    
    # Télécharger et créer chaque image
    for i, file in enumerate(images):
        # Enregistrer l'image téléchargée
        image_url = await save_uploaded_image(file=file, auction_id=auction_id)
        
        # Définir si c'est l'image principale - seulement la première image peut être principale
        # si le frontend a indiqué isMain=True
        image_is_main = (i == 0 and is_main)
        
        # Si cette image doit être principale, mettre à jour toutes les autres images
        if image_is_main:
            logger.info(f"Mise à jour de toutes les images existantes pour l'enchère {auction_id} à isMain=False")
            # Réinitialiser toutes les images existantes pour cette enchère à isMain=False
            db.query(AuctionImage).filter(
                AuctionImage.auctionId == auction_id,
                AuctionImage.isMain == True
            ).update({AuctionImage.isMain: False})
            db.commit()
            logger.info(f"Mise à jour terminée, nouvelle image {file.filename} sera définie comme isMain=True")
        
        # Récupérer le nom de l'image si disponible
        image_name = None
        if names and i < len(names):
            image_name = names[i]
        
        # Utiliser le nom du fichier original comme légende si disponible, sinon utiliser un numéro générique
        caption = image_name if image_name else f"Image {i+1}"
        
        # Créer l'enregistrement dans la base de données
        image_data = AuctionImageCreate(
            auctionId=auction_id,
            imageUrl=image_url,
            caption=caption,
            isMain=image_is_main,  # Utiliser la variable renommée
            displayOrder=i + total  # Ordre d'affichage basé sur l'index
        )
        
        # Ajouter l'image créée à la liste
        created_image = image_crud.create_image(db=db, image_data=image_data)
        created_images.append(created_image)
    
    return created_images



@router.get("/auction/{auction_id}", response_model=AuctionImagePaginatedResponse)
def read_auction_images(
    auction_id: int = Path(..., description="The ID of the auction to get images for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Récupère toutes les images pour une enchère spécifique.
    Cet endpoint est public.
    """
    images, total = image_crud.get_auction_images(db=db, auction_id=auction_id, skip=skip, limit=limit)
    
    return {
        "items": images,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/{image_id}", response_model=AuctionImageResponse)
def read_image(
    image_id: int = Path(..., description="The ID of the image to get"),
    db: Session = Depends(get_db)
):
    """
    Récupère une image spécifique par son ID.
    Cet endpoint est public.
    """
    db_image = image_crud.get_image(db=db, image_id=image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    return db_image

@router.put("/{image_id}", response_model=AuctionImageResponse, dependencies=[Depends(JWTBearer())])
def update_image(
    image_id: int,
    image_data: AuctionImageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour une image existante.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer l'image existante
    db_image = image_crud.get_image(db=db, image_id=image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_image.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette image"
        )
    
    # Mettre à jour l'image
    return image_crud.update_image(db=db, image_id=image_id, image_data=image_data)

@router.delete("/{image_id}", response_model=Dict[str, bool], dependencies=[Depends(JWTBearer())])
def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Supprime une image.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer l'image existante
    db_image = image_crud.get_image(db=db, image_id=image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image non trouvée")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_image.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette image"
        )
    
    # Supprimer l'image
    result = image_crud.delete_image(db=db, image_id=image_id)
    
    # Supprimer le fichier physique
    if result:
        delete_file_from_url(db_image.imageUrl)
    
    return {"success": result}

@router.post("/reorder/{auction_id}", response_model=List[AuctionImageResponse], dependencies=[Depends(JWTBearer())])
def reorder_images(
    auction_id: int,
    image_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Réordonne les images d'une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer l'enchère
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette enchère"
        )
    
    # Réordonner les images
    return image_crud.reorder_images(db=db, auction_id=auction_id, image_ids=image_ids)

@router.post("/frontend-simple/{auction_id}", response_model=List[AuctionImageResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_images_simple_frontend(
    request: Request,
    auction_id: int = Path(..., description="The ID of the auction to add images to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Endpoint simplifié pour le frontend qui accepte plusieurs images.
    Ne nécessite pas que les noms soient envoyés dans un format spécifique.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    from app.models.user import UserRole
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    if auction.creator_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des images à cette enchère"
        )
    
    # Traiter le formulaire manuellement
    form = await request.form()
    images = []
    names = []
    
    # Extraire les images et les noms du formulaire
    for key, value in form.items():
        if key == 'images':
            if isinstance(value, UploadFile):
                images.append(value)
        elif key == 'names':
            names.append(str(value))
    
    # Récupérer le nombre actuel d'images pour cet article
    _, total = image_crud.get_auction_images(db=db, auction_id=auction_id)
    
    # Créer une liste pour stocker les images créées
    created_images = []
    
    # Télécharger et créer chaque image
    for i, file in enumerate(images):
        # Enregistrer l'image téléchargée
        image_url = await save_uploaded_image(file=file, auction_id=auction_id)
        
        # Définir si c'est l'image principale (uniquement si c'est la première image et qu'il n'y a pas d'autres images)
        is_main = (i == 0 and total == 0)
        
        # Récupérer le nom de l'image si disponible
        image_name = None
        if i < len(names):
            image_name = names[i]
        
        # Utiliser le nom du fichier original comme légende si disponible, sinon utiliser un numéro générique
        caption = image_name if image_name else f"Image {i+1}"
        
        # Créer l'enregistrement dans la base de données
        image_data = AuctionImageCreate(
            auctionId=auction_id,
            imageUrl=image_url,
            caption=caption,
            isMain=is_main,
            displayOrder=i + total  # Ordre d'affichage basé sur l'index
        )
        
        # Ajouter l'image créée à la liste
        created_image = image_crud.create_image(db=db, image_data=image_data)
        created_images.append(created_image)
    
    return created_images
