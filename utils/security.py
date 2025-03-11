from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole

# Contexte de hachage de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration pour l'authentification OAuth2
# Nous avons désactivé la route form-urlencoded et utilisons maintenant la route JSON
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login-json")

# Version optionnelle du schéma OAuth2 pour les routes qui autorisent l'accès anonyme
class OAuth2PasswordBearerOptional(OAuth2PasswordBearer):
    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        return param

oauth2_scheme_optional = OAuth2PasswordBearerOptional(tokenUrl="/api/auth/login-json")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si un mot de passe en clair correspond au hash stocké
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Génère un hash sécurisé pour un mot de passe en clair
    """
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un JWT (JSON Web Token) pour l'authentification
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur courant à partir du token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="فشل في التحقق من الهوية",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Décoder le token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (jwt.JWTError, ValidationError):
        raise credentials_exception
    
    # Récupérer l'utilisateur dans la base de données
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur inactif"
        )
    
    return user

async def get_current_user_or_none(
    token: Optional[str] = Depends(oauth2_scheme_optional), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Récupère l'utilisateur courant à partir du token JWT, ou retourne None si pas de token valide
    Utile pour les routes qui autorisent l'accès anonyme
    """
    if not token:
        return None
        
    try:
        # Décoder le token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except (jwt.JWTError, ValidationError):
        return None
    
    # Récupérer l'utilisateur dans la base de données
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None
    
    return user

def get_current_active_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur courant est actif et vérifié
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur inactif"
        )
    
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لم يتم التحقق من حساب المستخدم"
        )
        
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur courant est un administrateur
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الوصول مقتصر على المشرفين"
        )
    return current_user

def get_superadmin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Vérifie que l'utilisateur courant est un super administrateur
    """
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="الوصول مقتصر على المشرفين العامين"
        )
    return current_user
