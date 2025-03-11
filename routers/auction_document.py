from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models.user import User
from app.crud import auction as auction_crud
from app.crud import auction_document as document_crud
from app.utils.file_utils import save_uploaded_document, delete_file_from_url
from app.schemas.auction_document import (
    AuctionDocumentCreate, 
    AuctionDocumentUpdate, 
    AuctionDocumentResponse, 
    AuctionDocumentPaginatedResponse
)
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import get_current_user_from_token

router = APIRouter(
    prefix="/auction-documents",
    tags=["Auction Documents"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload/{auction_id}", response_model=AuctionDocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_document(
    auction_id: int = Path(..., description="The ID of the auction to add a document to"),
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    is_public: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Télécharge un nouveau document pour une enchère.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des documents à cette enchère"
        )
    
    # Enregistrer le document téléchargé
    document_url = await save_uploaded_document(file=file, auction_id=auction_id)
    
    # Créer l'enregistrement dans la base de données
    document_data = AuctionDocumentCreate(
        auctionId=auction_id,
        documentUrl=document_url,
        documentName=document_name,
        documentType=document_type,
        isPublic=is_public
    )
    
    return document_crud.create_document(db=db, document_data=document_data)

@router.get("/auction/{auction_id}", response_model=AuctionDocumentPaginatedResponse)
def read_auction_documents(
    auction_id: int = Path(..., description="The ID of the auction to get documents for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token)
):
    """
    Récupère tous les documents publics pour une enchère spécifique.
    Si l'utilisateur est authentifié et est le créateur de l'enchère ou un administrateur,
    récupère également les documents privés.
    """
    # Récupérer l'enchère
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Récupérer les documents
    documents, total = document_crud.get_auction_documents(db=db, auction_id=auction_id, skip=skip, limit=limit)
    
    # Filtrer les documents privés si l'utilisateur n'est pas autorisé
    if current_user is None or (auction.creator_id != current_user.id and not current_user.is_admin):
        documents = [doc for doc in documents if doc.isPublic]
        total = len(documents)
    
    return {
        "items": documents,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.get("/{document_id}", response_model=AuctionDocumentResponse)
def read_document(
    document_id: int = Path(..., description="The ID of the document to get"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token)
):
    """
    Récupère un document spécifique par son ID.
    Les documents privés ne sont accessibles qu'au créateur de l'enchère et aux administrateurs.
    """
    db_document = document_crud.get_document(db=db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Vérifier si l'utilisateur peut accéder au document privé
    if not db_document.isPublic:
        # Récupérer l'enchère associée
        auction = auction_crud.get_auction(db=db, auction_id=db_document.auctionId)
        
        # Vérifier si l'utilisateur est authentifié et autorisé
        if current_user is None or (auction.creator_id != current_user.id and not current_user.is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à accéder à ce document"
            )
    
    return db_document

@router.put("/{document_id}", response_model=AuctionDocumentResponse, dependencies=[Depends(JWTBearer())])
def update_document(
    document_id: int,
    document_data: AuctionDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Met à jour un document existant.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer le document existant
    db_document = document_crud.get_document(db=db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_document.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier ce document"
        )
    
    # Mettre à jour le document
    return document_crud.update_document(db=db, document_id=document_id, document_data=document_data)

@router.delete("/{document_id}", response_model=Dict[str, bool], dependencies=[Depends(JWTBearer())])
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Supprime un document.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Récupérer le document existant
    db_document = document_crud.get_document(db=db, document_id=document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Récupérer l'enchère associée
    auction = auction_crud.get_auction(db=db, auction_id=db_document.auctionId)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    # Vérifier les autorisations
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer ce document"
        )
    
    # Supprimer le document
    result = document_crud.delete_document(db=db, document_id=document_id)
    
    # Supprimer le fichier physique
    if result:
        delete_file_from_url(db_document.documentUrl)
    
    return {"success": result}

@router.post("/frontend-upload/{auction_id}", response_model=List[AuctionDocumentResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_documents_from_frontend(
    auction_id: int = Path(..., description="L'ID de l'enchère à laquelle ajouter des documents"),
    documents: List[UploadFile] = File(..., description="Les documents à télécharger"),
    names: List[str] = Form(..., description="Les noms des documents"),
    document_type: str = Form("document", description="Le type de document"),
    is_public: bool = Form(True, description="Indique si le document est public"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Télécharge plusieurs documents pour une enchère avec des noms spécifiés.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    Spécialement conçu pour correspondre à l'approche frontend qui envoie des documents et leurs noms sous forme de listes distinctes.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des documents à cette enchère"
        )
    
    # Vérifier que le nombre de noms correspond au nombre de documents
    if len(documents) != len(names):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de noms doit correspondre au nombre de documents"
        )
    
    created_documents = []
    
    # Traiter chaque document avec son nom correspondant
    for i, document in enumerate(documents):
        # Enregistrer le document téléchargé
        document_url = await save_uploaded_document(file=document, auction_id=auction_id)
        
        # Créer l'enregistrement dans la base de données
        document_data = AuctionDocumentCreate(
            auctionId=auction_id,
            documentUrl=document_url,
            documentName=names[i] if i < len(names) else document.filename,
            documentType=document_type,
            isPublic=is_public
        )
        
        created_document = document_crud.create_document(db=db, document_data=document_data)
        created_documents.append(created_document)
    
    return created_documents

@router.post("/frontend-simple/{auction_id}", response_model=List[AuctionDocumentResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(JWTBearer())])
async def upload_documents_simple_frontend(
    request: Request,
    auction_id: int = Path(..., description="L'ID de l'enchère à laquelle ajouter des documents"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Télécharge plusieurs documents pour une enchère avec des noms spécifiés.
    Traite manuellement le formulaire pour permettre plusieurs champs avec le même nom.
    Vérifie les doublons de noms et extrait le type de document depuis le nom du fichier.
    Nécessite d'être authentifié et d'être le créateur de l'enchère ou un administrateur.
    """
    # Vérifier si l'enchère existe et si l'utilisateur est autorisé
    auction = auction_crud.get_auction(db=db, auction_id=auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Enchère non trouvée")
    
    if auction.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à ajouter des documents à cette enchère"
        )
    
    # Récupérer le formulaire
    form_data = await request.form()
    
    # Extraire les documents et leurs noms
    documents = form_data.getlist("documents")
    names = form_data.getlist("names")
    
    # Visibilité par défaut
    is_public = form_data.get("is_public", "True").lower() in ["true", "1", "yes"]
    
    # Vérifier que des documents ont été fournis
    if not documents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun document fourni"
        )
    
    # Récupérer les documents existants pour cette enchère pour vérifier les doublons
    existing_docs, _ = document_crud.get_auction_documents(db=db, auction_id=auction_id, skip=0, limit=1000)
    existing_names = [doc.documentName for doc in existing_docs]
    
    created_documents = []
    
    # Traiter chaque document avec son nom correspondant
    for i, document in enumerate(documents):
        # Utiliser le nom correspondant ou le nom du fichier si non disponible
        document_name = names[i] if i < len(names) else document.filename
        
        # Vérifier si un document avec le même nom existe déjà
        if document_name in existing_names:
            # Ajouter un suffixe numérique pour éviter les duplicats
            base_name, extension = os.path.splitext(document_name)
            count = 1
            while f"{base_name}_{count}{extension}" in existing_names:
                count += 1
            document_name = f"{base_name}_{count}{extension}"
        
        # Extraire le type de document depuis le nom/extension du fichier
        _, extension = os.path.splitext(document_name)
        extension = extension.lower().lstrip('.')
        
        # Mapper les extensions à des types de documents
        document_type_map = {
            'pdf': 'PDF',
            'doc': 'Word',
            'docx': 'Word',
            'xls': 'Excel',
            'xlsx': 'Excel',
            'ppt': 'PowerPoint',
            'pptx': 'PowerPoint',
            'txt': 'Texte',
            'jpg': 'Image',
            'jpeg': 'Image',
            'png': 'Image',
            'gif': 'Image'
        }
        
        document_type = document_type_map.get(extension, 'Document')
        
        # Enregistrer le document téléchargé
        document_url = await save_uploaded_document(file=document, auction_id=auction_id)
        
        # Ajouter le nom à la liste des existants pour éviter les doublons dans le même lot
        existing_names.append(document_name)
        
        # Créer l'enregistrement dans la base de données
        document_data = AuctionDocumentCreate(
            auctionId=auction_id,
            documentUrl=document_url,
            documentName=document_name,
            documentType=document_type,
            isPublic=is_public
        )
        
        created_document = document_crud.create_document(db=db, document_data=document_data)
        created_documents.append(created_document)
    
    return created_documents
