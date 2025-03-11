from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import pwd_context, oauth2_scheme, oauth2_scheme_optional

# Fonction pour vérifier un token JWT
def verify_jwt_token(token: str) -> bool:
    """
    Vérifie la validité d'un token JWT.
    
    Args:
        token (str): Le token JWT à vérifier
        
    Returns:
        bool: True si le token est valide, False sinon
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        # Vérifier que le token n'est pas expiré
        return payload.get("exp") > datetime.utcnow().timestamp()
    except (JWTError, ValidationError):
        return False

# Fonction pour décoder un token JWT
def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Décode le contenu d'un token JWT.
    
    Args:
        token (str): Le token JWT à décoder
        
    Returns:
        Dict: Le contenu du token décodé
        
    Raises:
        HTTPException: Si le token est invalide
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        return payload
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token invalide"
        )

# Fonction pour récupérer l'utilisateur à partir du token
def get_current_user_from_token(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur courant à partir du token JWT.
    
    Args:
        token (str): Le token JWT
        db (Session): La session de base de données
        
    Returns:
        User: L'utilisateur courant
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    try:
        payload = decode_jwt_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    
    # Récupérer l'utilisateur depuis la base de données
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable"
        )
    
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur inactif"
        )
    
    return user

# Fonction pour récupérer l'utilisateur optionnellement (routes publiques)
def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Récupère l'utilisateur courant à partir du token JWT, ou retourne None si pas de token valide.
    Utile pour les routes qui autorisent l'accès anonyme.
    
    Args:
        token (Optional[str]): Le token JWT ou None
        db (Session): La session de base de données
        
    Returns:
        Optional[User]: L'utilisateur courant ou None
    """
    if token is None:
        return None
    
    try:
        user = get_current_user_from_token(token, db)
        return user
    except HTTPException:
        return None

# Fonction pour vérifier si l'utilisateur est un admin
def verify_admin(user: User) -> bool:
    """
    Vérifie si l'utilisateur est un administrateur.
    
    Args:
        user (User): L'utilisateur à vérifier
        
    Returns:
        bool: True si l'utilisateur est un administrateur, False sinon
    """
    return user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]

# Fonction pour vérifier si l'utilisateur est un super-admin
def verify_superadmin(user: User) -> bool:
    """
    Vérifie si l'utilisateur est un super-administrateur.
    
    Args:
        user (User): L'utilisateur à vérifier
        
    Returns:
        bool: True si l'utilisateur est un super-administrateur, False sinon
    """
    return user.role == UserRole.SUPERADMIN
