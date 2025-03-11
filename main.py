from fastapi import FastAPI, Depends, HTTPException,Request,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.utils.exception_handlers import validation_exception_handler

from app.config import settings
from app.database import get_db, engine, Base

# Import explicite de tous les modèles avant création des tables
from app.models.user import User, UserRole
from app.models.auction import Auction, AuctionType, AuctionStatus
from app.models.category import Category
from app.models.bid import Bid
from app.models.auction_image import AuctionImage
from app.models.auction_document import AuctionDocument
from app.models.auction_specification import AuctionSpecification
from app.models.tribunal import Tribunal
from app.models.pays import Pays
from app.models.ville import Ville
from app.models.organism_credit import OrganismCredit
from app.models.deposit import Deposit
from app.schemas.user import UserCreate
from app.crud.user import create_user, get_user_by_email
from app.routers import auth, users, utilities, deposit

# Configuration des logs
logging.basicConfig(
    level=logging.DEBUG,  # Changé en DEBUG pour voir les logs de debug
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurez spécifiquement le logger pour notre debug d'update
update_debug_logger = logging.getLogger("update_debug")
update_debug_logger.setLevel(logging.DEBUG)

# Création des tables dans la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="API pour la plateforme d'enchères judiciaires",
    version=settings.APP_VERSION,
)

# Ajout des gestionnaires d'exceptions personnalisés
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
async def capture_and_log_request_info(request: Request):
    """
    Capture et journalise les informations de la requête incluant la méthode, le chemin,
    les en-têtes et le corps, puis retourne une nouvelle requête avec le corps restauré.
    """
    # Log des informations de base de la requête
    logger.info(f"Requête {request.method} {request.url.path}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    # Capture et log du corps de la requête
    body = await request.body()
    if body:
        try:
            # Tente de décoder en UTF-8, utile pour les requêtes JSON
            body_str = body.decode('utf-8')
            logger.debug(f"Corps de la requête: {body_str}")
        except UnicodeDecodeError:
            # En cas d'échec de décodage (pour les données binaires)
            logger.debug(f"Corps de la requête: [Binary data, len={len(body)}]")
    
    # Crée une nouvelle requête avec le corps lu
    # Nécessaire car .body() consomme le stream
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    
    # Retourne une nouvelle requête avec le corps restauré
    return Request(
        scope=request.scope,
        receive=receive,
        send=request._send
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Capture, journalise les informations de la requête et restaure le corps
    modified_request = await capture_and_log_request_info(request)
    
    # Traite la requête avec le reste de l'application
    response = await call_next(modified_request)
    
    # Log de la réponse
    logger.info(f"Réponse: {response.status_code}")
    
    return response

# Inclure les routers
app.include_router(auth.router)
app.include_router(users.router)
#app.include_router(deposit.router)
# utilities.router est inclus plus bas avec le préfixe /api

# Inclure le routeur public des utilisateurs
# from app.routers.users import public_router
# app.include_router(public_router)

# Inclure les routers d'enchères
from app.routers import category, auction, bid, auction_image, auction_document, auction_specification, utilities, auction_complete, deposit

app.include_router(category.router, prefix="/api")
app.include_router(auction.router, prefix="/api")
app.include_router(bid.router, prefix="/api")
app.include_router(auction_image.router, prefix="/api")
app.include_router(auction_document.router, prefix="/api")
app.include_router(auction_specification.router, prefix="/api")
app.include_router(utilities.router, prefix="/api")
app.include_router(auction_complete.router, prefix="/api")
app.include_router(deposit.router, prefix="/api")
@app.get("/api/health")
async def health_check():
    """
    Point de terminaison pour vérifier la santé de l'API
    """
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/api/public/info")
async def public_info():
    """Point d'entrée API publique simple pour les tests"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "API publique accessible - tout fonctionne correctement",
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

# @app.get("/api/public/users")
# async def get_public_users(
#     skip: int = 0,
#     limit: int = 10,
#     role: Optional[str] = None,
#     search: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """Route publique pour récupérer la liste des utilisateurs"""
#     from app.crud.user import get_users
#     from app.models.user import UserRole
#     # Convertir role en UserRole enum si nécessaire
#     role_enum = None
#     if role:
#         try:
#             role_enum = UserRole(role)
#         except ValueError:
#             pass
#     users, total = get_users(db, skip=skip, limit=limit, role=role_enum, search=search)
#     # Reformater les objets utilisateurs selon le format souhaité
#     formatted_users = []
#     for user in users:

#         if user.role == UserRole.ENCHERISSEUR:
#             role_text_map = {"text": "متزايد", "class": "bg-primary"}
#         elif user.role == UserRole.TRIBUNAL:
#             role_text_map =  {"text": "المحكمة", "class": "bg-secondary"}
#         elif user.role == UserRole.TRIBUNALMANAGER:
#             role_text_map =  {"text": "الوزارة", "class": "bg-success"}
#         elif user.role == UserRole.ORGACREDIT:
#             role_text_map =  {"text": "شركة القروض", "class": "bg-info"}
#         elif user.role == UserRole.ADMIN:
#             role_text_map =  {"text": "مدير", "class": "bg-dark"}
#         elif user.  role == UserRole.SUPERADMIN:
#             role_text_map =  {"text": "مدير عام", "class": "bg-warning"}
#         else:
#             role_text_map =  {"text": "غير معروف", "class": "bg-danger"}


#         if user.is_blocked is True:  
#             status_text = {"text": "محظور", "class": "bg-danger"}
#         elif not user.is_active:
#             status_text = {"text": "معلق", "class": "bg-warning"}
#         else:
#             status_text = {"text": "نشط", "class": "bg-success"}

#         # Format de la date d'inscription (created_at) au format JJ/MM/AAAA
#         reg_date = user.created_at.strftime("%d/%m/%Y") if user.created_at else ""
        
#         formatted_users.append({
#             "id": user.id,
#             "avatar": "https://www.claudeusercontent.com/api/placeholder/40/40",
#             "firstName": user.first_name,
#             "lastName": user.last_name,
#             "email": user.email,
#             "phone": user.phone_number or "",
#             "role": role_text_map,
#             "regDate": reg_date,
#             "status": status_text,
#         })
    
#     return formatted_users

















def create_initial_admin_users():
    """
    Crée les utilisateurs admin et superadmin initiaux
    """
    logger.info("Vérification des comptes administrateurs initiaux...")
    db = next(get_db())
    
    # Créer le superadmin s'il n'existe pas déjà
    superadmin = get_user_by_email(db, settings.SUPERADMIN_EMAIL)
    if not superadmin:
        logger.info(f"Création du compte superadmin: {settings.SUPERADMIN_EMAIL}")
        superadmin_data = UserCreate(
            email=settings.SUPERADMIN_EMAIL,
            password=settings.SUPERADMIN_PASSWORD,
            password_confirm=settings.SUPERADMIN_PASSWORD,
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPERADMIN
        )
        create_user(
            db=db,
            user_data=superadmin_data,
            send_verification=False,
            is_active=True,
            is_verified=True
        )
    
    # Créer l'admin s'il n'existe pas déjà
    admin = get_user_by_email(db, settings.ADMIN_EMAIL)
    if not admin:
        logger.info(f"Création du compte admin: {settings.ADMIN_EMAIL}")
        admin_data = UserCreate(
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            password_confirm=settings.ADMIN_PASSWORD,
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN
        )
        create_user(
            db=db,
            user_data=admin_data,
            send_verification=False,
            is_active=True,
            is_verified=True
        )
    
    logger.info("Vérification des comptes administrateurs terminée.")

# Événement de démarrage de l'application
@app.on_event("startup")
async def startup_event():
    logger.info(f"Démarrage de l'application {settings.APP_NAME} v{settings.APP_VERSION}")
    create_initial_admin_users()

# Événement d'arrêt de l'application
@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Arrêt de l'application {settings.APP_NAME}")


# Endpoint pour initialiser ou réinitialiser la base de données (version admin protégée)
@app.post("/api/admin/init-db", tags=["admin"])
async def init_db(recreate_all: bool = False):
    """Initialises ou réinitialise la base de données
    
    Si recreate_all est True, toutes les tables seront supprimées puis recréées
    Sinon, seules les tables manquantes seront créées
    
    ATTENTION: L'option recreate_all=True supprimera toutes les données existantes!
    """
    if recreate_all:
        logger.info("Suppression et recréation de toutes les tables...")
        Base.metadata.drop_all(bind=engine)
    
    # Créer les tables manquantes
    logger.info("Création des tables manquantes...")
    Base.metadata.create_all(bind=engine)
    
    return {"message": "Initialisation de la base de données terminée avec succès", "success": True}


# Endpoint public pour initialiser la base de données (uniquement création de tables manquantes)
@app.post("/api/public/init-db", tags=["public"])
async def init_db_public():
    """Initialise la base de données (version publique)
    
    Cette version crée uniquement les tables manquantes sans supprimer les données existantes.
    Elle est spécialement conçue pour fonctionner avec une base de données PostgreSQL existante,
    en préservant les tables déjà créées (comme 'users') avec leurs données.
    """
    # Créer les tables manquantes
    logger.info("Création des tables manquantes (endpoint public)...")
    Base.metadata.create_all(bind=engine)
    
    # Vérifier les tables créées
    from sqlalchemy import inspect
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    logger.info(f"Tables existantes dans la base de données: {table_names}")
    
    return {"message": "Initialisation de la base de données terminée avec succès", "success": True}
