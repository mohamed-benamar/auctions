import os
import shutil
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
import aiofiles

from app.config import settings

def create_directory_if_not_exists(directory: str) -> None:
    """Crée un répertoire s'il n'existe pas déjà."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def validate_file_size(file: UploadFile) -> None:
    """Valide la taille d'un fichier."""
    # Déplacer le pointeur de fichier au début
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Remettre le pointeur au début
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La taille du fichier dépasse la limite de {max_size_mb} Mo"
        )

def validate_image_type(file: UploadFile) -> None:
    """Valide le type MIME d'une image."""
    content_type = file.content_type
    
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        allowed_types = ", ".join(settings.ALLOWED_IMAGE_TYPES)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Type d'image non pris en charge. Types autorisés : {allowed_types}"
        )

def validate_document_type(file: UploadFile) -> None:
    """Valide le type MIME d'un document."""
    content_type = file.content_type
    
    if content_type not in settings.ALLOWED_DOCUMENT_TYPES:
        allowed_types = ", ".join(settings.ALLOWED_DOCUMENT_TYPES)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Type de document non pris en charge. Types autorisés : {allowed_types}"
        )

def generate_unique_filename(original_filename: str) -> str:
    """Génère un nom de fichier unique basé sur l'UUID et le timestamp."""
    # Extraire l'extension du fichier original
    filename, file_extension = os.path.splitext(original_filename)
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{timestamp}_{unique_id}{file_extension}"

async def save_uploaded_file(
    file: UploadFile, 
    destination_dir: str,
    auction_id: Optional[int] = None
) -> str:
    """
    Sauvegarde un fichier téléchargé sur le disque et retourne son chemin relatif.
    
    Args:
        file: Le fichier téléchargé
        destination_dir: Le répertoire de destination (IMAGES_DIR ou DOCUMENTS_DIR)
        auction_id: ID optionnel de l'enchère pour organiser les fichiers
        
    Returns:
        Le chemin relatif du fichier sauvegardé
    """
    # Créer le répertoire parent s'il n'existe pas
    base_dir = os.path.join(settings.STATIC_FILES_DIR, destination_dir)
    create_directory_if_not_exists(base_dir)
    
    # Si un ID d'enchère est fourni, créer un sous-répertoire
    if auction_id:
        base_dir = os.path.join(base_dir, str(auction_id))
        create_directory_if_not_exists(base_dir)
    
    # Générer un nom de fichier unique
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(base_dir, unique_filename)
    
    # Écrire le contenu du fichier
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Déterminer le chemin relatif pour l'URL
    if auction_id:
        relative_path = f"{destination_dir}/{auction_id}/{unique_filename}"
    else:
        relative_path = f"{destination_dir}/{unique_filename}"
    
    return relative_path

async def save_uploaded_image(file: UploadFile, auction_id: Optional[int] = None) -> str:
    """
    Valide et sauvegarde une image téléchargée.
    
    Args:
        file: Le fichier image téléchargé
        auction_id: ID optionnel de l'enchère
        
    Returns:
        L'URL de l'image sauvegardée
    """
    # Valider la taille et le type du fichier
    validate_file_size(file)
    validate_image_type(file)
    
    # Sauvegarder le fichier
    relative_path = await save_uploaded_file(file, settings.IMAGES_DIR, auction_id)
    
    # Construire l'URL complète
    image_url = f"{settings.MEDIA_BASE_URL}/{relative_path}"
    
    return image_url

async def save_uploaded_document(file: UploadFile, auction_id: Optional[int] = None) -> str:
    """
    Valide et sauvegarde un document téléchargé.
    
    Args:
        file: Le fichier document téléchargé
        auction_id: ID optionnel de l'enchère
        
    Returns:
        L'URL du document sauvegardé
    """
    # Valider la taille et le type du fichier
    validate_file_size(file)
    validate_document_type(file)
    
    # Sauvegarder le fichier
    relative_path = await save_uploaded_file(file, settings.DOCUMENTS_DIR, auction_id)
    
    # Construire l'URL complète
    document_url = f"{settings.MEDIA_BASE_URL}/{relative_path}"
    
    return document_url

async def save_multiple_uploaded_images(
    files: List[UploadFile], 
    auction_id: Optional[int] = None
) -> List[str]:
    """
    Valide et sauvegarde plusieurs images téléchargées.
    
    Args:
        files: Liste des fichiers image téléchargés
        auction_id: ID optionnel de l'enchère
        
    Returns:
        Liste des URLs des images sauvegardées
    """
    image_urls = []
    
    for file in files:
        image_url = await save_uploaded_image(file, auction_id)
        image_urls.append(image_url)
    
    return image_urls

def delete_file_from_url(url: str) -> bool:
    """
    Supprime un fichier à partir de son URL.
    
    Args:
        url: L'URL du fichier à supprimer
        
    Returns:
        True si le fichier a été supprimé, False sinon
    """
    try:
        # Extraire le chemin relatif de l'URL
        if url.startswith(settings.MEDIA_BASE_URL):
            relative_path = url[len(settings.MEDIA_BASE_URL) + 1:]  # +1 pour le slash
        else:
            return False
        
        # Construire le chemin absolu
        file_path = os.path.join(settings.STATIC_FILES_DIR, relative_path)
        
        # Vérifier si le fichier existe et le supprimer
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            return True
        
        return False
    except Exception:
        return False

def get_file_info(url: str) -> Tuple[str, int]:
    """
    Récupère des informations sur un fichier à partir de son URL.
    
    Args:
        url: L'URL du fichier
        
    Returns:
        Un tuple contenant le nom du fichier et sa taille en octets
    """
    try:
        # Extraire le chemin relatif de l'URL
        if url.startswith(settings.MEDIA_BASE_URL):
            relative_path = url[len(settings.MEDIA_BASE_URL) + 1:]  # +1 pour le slash
        else:
            return ("Fichier inconnu", 0)
        
        # Construire le chemin absolu
        file_path = os.path.join(settings.STATIC_FILES_DIR, relative_path)
        
        # Vérifier si le fichier existe
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            return (file_name, file_size)
        
        return ("Fichier non trouvé", 0)
    except Exception:
        return ("Erreur", 0)

def cleanup_auction_files(auction_id: int) -> None:
    """
    Supprime tous les fichiers associés à une enchère.
    
    Args:
        auction_id: L'ID de l'enchère
    """
    # Construire les chemins des répertoires
    image_dir = os.path.join(settings.STATIC_FILES_DIR, settings.IMAGES_DIR, str(auction_id))
    document_dir = os.path.join(settings.STATIC_FILES_DIR, settings.DOCUMENTS_DIR, str(auction_id))
    
    # Supprimer les répertoires s'ils existent
    for directory in [image_dir, document_dir]:
        if os.path.exists(directory) and os.path.isdir(directory):
            shutil.rmtree(directory)
            
#deposit ----------------  

async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Sauvegarde un fichier uploadé vers une destination spécifiée.
    
    Args:
        upload_file: Le fichier uploadé
        destination: Le chemin de destination
        
    Returns:
        Le chemin complet où le fichier a été sauvegardé
    """
    # Créer le répertoire de destination s'il n'existe pas
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Ouvrir le fichier de destination en mode écriture binaire
    with open(destination, "wb") as buffer:
        # Copier le contenu du fichier uploadé vers le fichier de destination
        shutil.copyfileobj(upload_file.file, buffer)
    
    return destination

async def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Génère un nom de fichier unique basé sur le nom de fichier original.
    
    Args:
        original_filename: Le nom de fichier original
        prefix: Un préfixe optionnel à ajouter
        
    Returns:
        Un nom de fichier unique
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}_{original_filename}"
    return f"{unique_id}_{original_filename}"

def get_file_extension(filename: str) -> str:
    """
    Récupère l'extension d'un fichier.
    
    Args:
        filename: Le nom du fichier
        
    Returns:
        L'extension du fichier (sans le point)
    """
    return os.path.splitext(filename)[1][1:].lower()

def delete_file(file_path: str) -> bool:
    """
    Supprime un fichier du système de fichiers.
    
    Args:
        file_path: Le chemin du fichier à supprimer
        
    Returns:
        True si le fichier a été supprimé, False sinon
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier {file_path}: {str(e)}")
        return False