from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserResponseAllFrontend
from app.schemas.token import Token, TokenCustomResponse, LoginRequest
from app.utils.security import verify_password, create_access_token, get_current_user
from app.utils.email import send_verification_email
from app.crud.user import get_user_by_email, create_user, update_last_login, verify_user,create_user_new
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register_user(
#     user: UserCreate, 
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """
#     Inscription d'un nouvel utilisateur avec envoi d'email de confirmation
#     """
#     # Créer l'utilisateur
#     print("user : -------------")
#     print(user)
#     db_user = create_user(db, user, send_verification=True, is_active=False, is_verified=False)
    
#     # Envoyer l'email de vérification en arrière-plan
#     if settings.ENABLE_EMAIL_NOTIFICATIONS and db_user.verification_token:
#         background_tasks.add_task(
#             send_verification_email,
#             email=db_user.email,
#             token=db_user.verification_token
#         )
    
#     return db_user





@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserResponseAllFrontend,
    db: Session = Depends(get_db)
):
    """
    Met à jour l'utilisateur (admin uniquement)
    """
    print("user_data : -----11--------")
    print(user_data)
    print("user_data : -----11--------")
    db_user = create_user_new(db, user_data)



    """
    Inscription d'un nouvel utilisateur avec envoi d'email de confirmation
    """
    
    # Créer l'utilisateur
    #db_user = create_user(db, user, send_verification=True, is_active=False, is_verified=False)
    
    # Envoyer l'email de vérification en arrière-plan
    # if settings.ENABLE_EMAIL_NOTIFICATIONS and db_user.verification_token:
    #     background_tasks.add_task(
    #         send_verification_email,
    #         email=db_user.email,
    #         token=db_user.verification_token
    #     )
    
    return db_user






# @router.post("/login", response_model=Token)
# async def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     """
#     Authentification d'un utilisateur et génération d'un token JWT (format form-urlencoded)
#     """
#     # Vérifier l'email et le mot de passe
#     user = get_user_by_email(db, form_data.username)  # username est en fait l'email dans OAuth2PasswordRequestForm
#     
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Email ou mot de passe incorrect",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     
#     # Vérifier que l'utilisateur est actif
#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Compte utilisateur inactif"
#         )
#     
#     # Créer le token d'accès
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         subject=user.id, expires_delta=access_token_expires
#     )
#     
#     # Mettre à jour la date de dernière connexion
#     update_last_login(db, user.id)
#     
#     # Retourner le token
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user_id": user.id,
#         "email": user.email,
#         "role": user.role
#     }

import logging

# Configuration du logger
logger = logging.getLogger("auth_debug")
logger.setLevel(logging.DEBUG)

from fastapi import Request, Body
import json

@router.post("/login-json", response_model=TokenCustomResponse)
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authentification d'un utilisateur et génération d'un token JWT (format JSON)
    Renvoie le nom complet de l'utilisateur sans l'email
    """
    # Log des données reçues pour le débogage
    body = await request.json()
    headers = dict(request.headers)
    
    logger.debug(f"Headers de la requête: {headers}")
    logger.debug(f"Body de la requête: {body}")
    logger.debug(f"Tentative de connexion avec email: {login_data.email}")
    logger.debug(f"Password fourni (longueur): {len(login_data.password) if login_data.password else 0}")
    
    # Vérifier l'email et le mot de passe
    user = get_user_by_email(db, login_data.email)
    logger.debug(f"Utilisateur trouvé: {user is not None}")
    
    if user:
        logger.debug(f"Utilisateur actif: {user.is_active}")
        logger.debug(f"Vérification mot de passe: {verify_password(login_data.password, user.hashed_password) if login_data.password else False}")
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Ajouter des détails sur la raison de l'échec
        reason = "Utilisateur non trouvé" if not user else "Mot de passe incorrect"
        logger.debug(f"Authentification échouée: {reason}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب المستخدم غير نشط"
        )
    
    # Créer le token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Mettre à jour la date de dernière connexion
    update_last_login(db, user.id)
    
    # Créer le nom complet à partir du prénom et du nom
    user_full_name = f"{user.first_name} {user.last_name}"
    
    # Retourner le token avec le nom complet mais sans l'email
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "user_full_name": user_full_name
    }

@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_account(token: str, db: Session = Depends(get_db)):
    """
    Vérification du compte utilisateur via le token envoyé par email
    """
    user = verify_user(db, token)
    return {"detail": "تم التحقق من الحساب بنجاح"}

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    email: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Renvoie l'email de vérification à un utilisateur
    """
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يتم العثور على المستخدم"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="الحساب تم التحقق منه مسبقاً"
        )
    
    # Si le token est None, en générer un nouveau
    if not user.verification_token:
        from app.utils.email import generate_verification_token
        user.verification_token = generate_verification_token()
        db.commit()
        db.refresh(user)
    
    # Envoyer l'email de vérification en arrière-plan
    if settings.ENABLE_EMAIL_NOTIFICATIONS:
        background_tasks.add_task(
            send_verification_email,
            email=user.email,
            token=user.verification_token
        )
    
    return {"detail": "تم إرسال بريد إلكتروني للتحقق"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur actuellement connecté
    """
    return current_user

# Endpoint de débogage désactivé
# @router.post("/debug-login")
# async def debug_login(request: Request):
#     """
#     Endpoint de diagnostic pour tester les problèmes d'authentification
#     """
#     try:
#         # Lire et enregistrer la totalité de la requête
#         body = await request.body()
#         headers = dict(request.headers)
#         
#         # Enregistrer les informations de débogage
#         with open("login_debug.log", "a") as f:
#             f.write("\n--- NOUVELLE TENTATIVE DE CONNEXION ---\n")
#             f.write(f"Date: {datetime.now()}\n")
#             f.write(f"Headers: {json.dumps(headers, indent=2)}\n")
#             f.write(f"Body (raw): {body}\n")
#             
#             # Essayer de parser le JSON
#             try:
#                 parsed_body = json.loads(body)
#                 f.write(f"Body (parsed): {json.dumps(parsed_body, indent=2)}\n")
#             except Exception as e:
#                 f.write(f"Erreur de parsing JSON: {str(e)}\n")
#         
#         # Répondre avec les données reçues
#         return {
#             "message": "Données de débogage enregistrées",
#             "headers_received": headers,
#             "body_received": body.decode() if body else None
#         }
#     except Exception as e:
#         return {"error": str(e)}
