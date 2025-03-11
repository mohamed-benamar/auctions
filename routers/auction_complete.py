from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import tempfile
import os
from io import BytesIO

from app.database import get_db
from app.models.user import User
from app.models.auction import AuctionType, AuctionStatus
from app.crud import auction as auction_crud
from app.crud import auction_image as image_crud
from app.crud import auction_document as document_crud
from app.utils.file_utils import save_uploaded_image, save_uploaded_document
from app.schemas.auction import (
    AuctionCreate,
    AuctionResponse,
    AuctionCompleteResponse
)
from app.schemas.auction_image import AuctionImageCreate, AuctionImageResponse
from app.schemas.auction_document import AuctionDocumentCreate, AuctionDocumentResponse
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/auction-complete",
    tags=["Auction Complete"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=AuctionCompleteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def create_auction_with_files(
    auction_data: str = Form(...),
    images: List[UploadFile] = File([]),
    documents: List[UploadFile] = File([]),
    image_metadata: Optional[str] = Form(None),
    document_metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Crée une nouvelle enchère complète avec ses images et documents en une seule requête.
    
    - Les données de l'enchère sont fournies au format JSON dans le champ 'auction_data'
    - Les images sont téléchargées comme fichiers multipart
    - Les documents sont téléchargés comme fichiers multipart
    - Les métadonnées des images sont fournies au format JSON dans le champ 'image_metadata'
    - Les métadonnées des documents sont fournies au format JSON dans le champ 'document_metadata'
    
    Nécessite d'être authentifié.
    """
    try:
        # Parse des données JSON
        auction_data_dict = json.loads(auction_data)
        
        # Ajouter l'ID du créateur
        auction_data_dict["creator_id"] = current_user.id
        auction_create = AuctionCreate(**auction_data_dict)
        
        # Créer l'enchère
        auction = auction_crud.create_auction(db=db, auction_data=auction_create)
        
        # Parse des métadonnées
        image_metadata_list = json.loads(image_metadata) if image_metadata else [{"is_main": i == 0, "order": i} for i in range(len(images))]
        document_metadata_list = json.loads(document_metadata) if document_metadata else []
        
        # S'assurer que nous avons des métadonnées pour chaque document
        if len(document_metadata_list) < len(documents):
            for i in range(len(document_metadata_list), len(documents)):
                document_metadata_list.append({
                    "document_type": "general",
                    "document_name": f"Document {i+1}",
                    "is_public": True
                })
        
        # Traiter les images
        uploaded_images = []
        for idx, image_file in enumerate(images):
            metadata = image_metadata_list[idx] if idx < len(image_metadata_list) else {"is_main": False, "order": idx}
            
            # Télécharger l'image
            image_url = await save_uploaded_image(file=image_file, auction_id=auction.id)
            
            # Créer l'enregistrement dans la base de données
            image_data = AuctionImageCreate(
                auctionId=auction.id,
                imageUrl=image_url,
                isMain=metadata.get("is_main", False),
                order=metadata.get("order", idx),
                caption=metadata.get("caption", f"Image {idx+1}")
            )
            
            created_image = image_crud.create_image(db=db, image_data=image_data)
            uploaded_images.append(created_image)
        
        # Traiter les documents
        uploaded_documents = []
        for idx, doc_file in enumerate(documents):
            metadata = document_metadata_list[idx] if idx < len(document_metadata_list) else {}
            
            # Télécharger le document
            document_url = await save_uploaded_document(file=doc_file, auction_id=auction.id)
            
            # Créer l'enregistrement dans la base de données
            document_data = AuctionDocumentCreate(
                auctionId=auction.id,
                documentUrl=document_url,
                docType=metadata.get("document_type", "general"),
                documentName=metadata.get("document_name", f"Document {idx+1}"),
                isPublic=metadata.get("is_public", True)
            )
            
            created_document = document_crud.create_document(db=db, document_data=document_data)
            uploaded_documents.append(created_document)
        
        # Construire la réponse
        return {
            "auction": auction,
            "images": uploaded_images,
            "documents": uploaded_documents
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format JSON invalide pour les données d'enchère ou les métadonnées"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'enchère complète: {str(e)}"
        )
