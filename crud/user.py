from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from datetime import datetime
import secrets
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserUpdateRole, UserUpdateState,UserUpdateResponse,UserResponseAllFrontend,UserResponseAllFrontendUpdate
from app.utils.security import get_password_hash, verify_password
from app.utils.email import generate_verification_token

def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Récupère un utilisateur par son ID
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Récupère un utilisateur par son email
    """
    return db.query(User).filter(User.email == email).first()

def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    role: Optional[UserRole] = None,
    search: Optional[str] = None
) -> Tuple[List[User], int]:
    """
    Récupère une liste d'utilisateurs avec pagination et filtrage
    """
    query = db.query(User)
    
    # Filtrer par rôle si spécifié
    if role:
        query = query.filter(User.role == role)
    
    # Recherche sur le nom, l'email
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )
        
    #supp admin et superadmin
    query = query.filter(User.role.notin_([UserRole.ADMIN, UserRole.SUPERADMIN]))


    # Compter le nombre total avant pagination
    total = query.count()
    
    # Appliquer la pagination
    users = query.offset(skip).limit(limit).all()
    
    return users, total




def get_usersall(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
) -> Tuple[List[User]]:
    """
    Récupère une liste d'utilisateurs avec pagination et filtrage
    """
    query = db.query(User)

    # Appliquer la pagination
    users = query.offset(skip).limit(limit).all()
    
    return users

def create_user(db: Session, user_data: UserCreate, send_verification: bool = True, is_active: bool = False, is_verified: bool = False) -> User:
    """
    Crée un nouvel utilisateur
    """
    # Vérifier si l'email existe déjà
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email est déjà utilisé"
        )
    
    # Générer un token de vérification si nécessaire
    verification_token = generate_verification_token() if send_verification else None
    
    # Créer l'utilisateur avec mot de passe hashé
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        phone_number=user_data.phone_number,
        address=user_data.address,
        is_active=is_active,
        is_verified=is_verified,
        verification_token=verification_token,
        ville_id=user_data.ville_id,    
        pays_id=user_data.pays_id,
        organism_credit_id=user_data.organism_credit_id,
        cin=user_data.cin,
        ville_etranger=user_data.ville_etranger,
        registre_commerce=user_data.registre_commerce,
        denomination_societe=user_data.denomination_societe
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_new(db: Session, user_data: UserResponseAllFrontend, send_verification: bool = True, is_active: bool = False, is_verified: bool = False) -> User:
    """
    Crée un nouvel utilisateur
    """
    # Vérifier si l'email existe déjà
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'email est déjà utilisé"
        )
    
    # Générer un token de vérification si nécessaire
    verification_token = generate_verification_token() if send_verification else None
    print("-----------user_data------------")
    print(user_data)
    print("-----------user_data------------")
    # Convertir la chaîne de rôle en énumération UserRole
    try:
        role_enum = UserRole(user_data.role.lower())
    except ValueError:
        # Par défaut, utiliser ENCHERISSEUR
        role_enum = UserRole.ENCHERISSEUR
    
    # Convertir les IDs en entiers si nécessaire
    try:
        ville_id = int(user_data.ville_id) if user_data.ville_id else None
    except (ValueError, TypeError):
        ville_id = None
        
    try:
        pays_id = int(user_data.pays_id) if user_data.pays_id else None
    except (ValueError, TypeError):
        pays_id = None
        
    try:
        organism_credit_id = int(user_data.organism_credit_id) if user_data.organism_credit_id else None
    except (ValueError, TypeError):
        organism_credit_id = None
    
    # Créer l'utilisateur avec mot de passe hashé
    db_user = User(
        email=user_data.email,
        first_name=user_data.firstName,
        last_name=user_data.lastName,
        role=role_enum,
        hashed_password=get_password_hash(user_data.password),
        phone_number=user_data.phone,
        address=user_data.address,
        is_active=is_active,
        is_verified=is_verified,
        verification_token=verification_token,
        ville_id=ville_id,    
        pays_id=pays_id,
        organism_credit_id=organism_credit_id,
        cin=user_data.cin,
        ville_etranger=user_data.ville_etranger or None,
        registre_commerce=user_data.registre_commerce or None,
        denomination_societe=user_data.denomination_societe or None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

import logging

# Configuration du logger pour le debugging
debug_logger = logging.getLogger("update_debug")
debug_logger.setLevel(logging.DEBUG)

def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    """
    Met à jour les informations d'un utilisateur
    """
    # Log des données reçues pour le debugging
    debug_logger.debug(f"Données de mise à jour reçues: {user_data.model_dump()}")
    debug_logger.debug(f"Type de l'objet user_data: {type(user_data)}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # Log de l'utilisateur avant modification
    debug_logger.debug(f"Utilisateur avant modification: ID={db_user.id}, Email={db_user.email}, "  
                     f"Prénom={db_user.first_name}, Nom={db_user.last_name}, "  
                     f"Téléphone={db_user.phone_number}, Adresse={db_user.address}")
    
    # La vérification de l'email a été supprimée car l'email n'est plus modifiable
    # Le champ email a été supprimé du schéma UserUpdate
    
    # Mettre à jour les champs modifiables
    update_data = user_data.model_dump(exclude_unset=True)
    debug_logger.debug(f"Données à mettre à jour après model_dump: {update_data}")
    
    for key, value in update_data.items():
        debug_logger.debug(f"Mise à jour du champ {key} avec la valeur: {value}")
        setattr(db_user, key, value)
    
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_user_role(db: Session, user_id: int, role_data: UserUpdateRole) -> User:
    """
    Met à jour le rôle d'un utilisateur (réservé aux administrateurs)
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    db_user.role = role_data.role
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user



def update_user_state(db: Session, user_id: int) -> User:
    """
    Met à jour le bloc d'un utilisateur (réservé aux administrateurs)
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    db_user.is_blocked = not db_user.is_blocked
    db_user.is_active = not db_user.is_blocked
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_arabic(db: Session, user_id: int, user_data: UserResponseAllFrontendUpdate) -> User:
    """
    Met à jour le bloc d'un utilisateur (réservé aux administrateurs).
    Ne met à jour que les champs explicitement présents dans la requête.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Obtenir uniquement les champs explicitement fournis dans la requête JSON
    # exclude_unset=True est crucial ici - il exclut les champs non fournis dans la requête
    user_dict = user_data.dict(exclude_unset=True)
    print("Champs explicitement fournis dans la requête:", user_dict)

    # Dictionnaire de correspondance entre les champs Pydantic et les champs SQLAlchemy
    field_mapping = {
        "firstName": "first_name",
        "lastName": "last_name",
        # "email" est omis intentionnellement pour éviter les mises à jour d'email accidentelles
        "phone": "phone_number",
        "address": "address",
        "tribunal_id": "tribunal_id",  # Réactivé pour permettre les mises à jour explicites
        "pays_id": "pays_id",
        "ville_id": "ville_id",
        "ville_etranger": "ville_etranger",
        "organism_credit_id": "organism_credit_id",
        "registre_commerce": "registre_commerce",
        "denomination_societe": "denomination_societe",
        "cin": "cin"
    }
    
    # Cas spécial: mise à jour du mot de passe
    if "password" in user_dict and user_dict["password"] is not None:
        if "password_confirm" in user_dict and user_dict["password_confirm"] == user_dict["password"]:
            db_user.hashed_password = get_password_hash(user_dict["password"])
            print("Mot de passe mis à jour")
        else:
            print("Les mots de passe ne correspondent pas - mot de passe non mis à jour")
    
    # Mise à jour uniquement des champs qui sont explicitement fournis dans la requête
    for pydantic_field, db_field in field_mapping.items():
        if pydantic_field in user_dict:  # Seulement si le champ est explicitement présent
            value = user_dict[pydantic_field]  # Peut être None (c'est OK pour NULL explicite)
            
            # Traitement spécial pour les champs ID
            if db_field.endswith("_id"):
                if value == "":  # Traiter les chaînes vides comme None
                    value = None
                    print(f"{db_field} chaîne vide convertie en NULL")
                elif value is not None:  # Convertir en entier si la valeur n'est pas None
                    try:
                        value = int(value)
                        print(f"{db_field} converti en entier: {value}")
                    except (ValueError, TypeError):
                        print(f"Erreur de conversion pour {db_field} (valeur: {value}) - utilisé None")
                        value = None
                elif value is None:  # Cas explicite de NULL
                    print(f"{db_field} explicitement défini à NULL")
            
            # Appliquer la mise à jour
            print(f"Mise à jour de {db_field} avec valeur: {value}")
            setattr(db_user, db_field, value)

    # Gestion du statut d'utilisateur - si le champ status est fourni
    if "status" in user_dict:
        status_value = user_dict["status"]
        if status_value:
            if status_value.lower() == "active":
                db_user.is_active = True
                db_user.is_verified = True
                db_user.is_blocked = False
                print("Statut défini à ACTIVE - utilisateur activé et vérifié")
            elif status_value.lower() == "pending":
                db_user.is_active = False
                db_user.is_blocked = True
                print("Statut défini à PENDING - utilisateur désactivé et bloqué")
            elif status_value.lower() == "banned":
                db_user.is_blocked = True
                print("Statut défini à BANNED - utilisateur bloqué")
            else:
                print(f"Valeur de statut non reconnue: {status_value}")

    # Gestion du rôle - seulement s'il est explicitement fourni dans la requête
    if "role" in user_dict:
        role_value = user_dict["role"]
        if role_value is None:
            print("Rôle explicit null reçu - mais non modifié (le rôle ne peut pas être null)")
        else:
            # Support des rôles en arabe
            role_map = {
                # Rôles en arabe
                "متزايد": UserRole.ENCHERISSEUR,
                "المحكمة": UserRole.TRIBUNAL,
                "مدير عام": UserRole.SUPERADMIN,
                "مدير": UserRole.ADMIN,
                "الوزارة": UserRole.TRIBUNALMANAGER,
                "شركة القروض": UserRole.ORGACREDIT,
                
                # Rôles en français/anglais
                "encherisseur": UserRole.ENCHERISSEUR,
                "tribunal": UserRole.TRIBUNAL,
                "superadmin": UserRole.SUPERADMIN,
                "admin": UserRole.ADMIN,
                "tribunalmanager": UserRole.TRIBUNALMANAGER,
                "orgacredit": UserRole.ORGACREDIT
            }
            
            try:
                # D'abord essayer dans la table de correspondance
                if role_value in role_map:
                    db_user.role = role_map[role_value]
                    print(f"Rôle mis à jour vers: {db_user.role}")
                # Essayer la conversion directe
                else:
                    # Essayer de convertir directement en UserRole
                    db_user.role = UserRole(str(role_value).lower())
                    print(f"Rôle mis à jour vers: {db_user.role}")
            except (ValueError, KeyError):
                print(f"Rôle invalide ignoré: {role_value}")

    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user_id: int, current_password: str, new_password: str) -> User:
    """
    Met à jour le mot de passe d'un utilisateur
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    # Vérifier que le mot de passe actuel est correct
    if not verify_password(current_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة"
        )
    
    # Mettre à jour le mot de passe
    db_user.hashed_password = get_password_hash(new_password)
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def verify_user(db: Session, token: str) -> User:
    """
    Vérifie un utilisateur en utilisant son token de vérification
    """
    db_user = db.query(User).filter(User.verification_token == token).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="رمز التحقق غير صالح"
        )
    
    db_user.is_verified = True
    db_user.is_active = True
    db_user.verification_token = None
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def deactivate_user(db: Session, user_id: int) -> User:
    """
    Désactive un utilisateur
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    db_user.is_active = False
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def activate_user(db: Session, user_id: int) -> User:
    """
    Active un utilisateur
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    
    db_user.is_active = True
    db_user.updated_at = datetime.now()
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_last_login(db: Session, user_id: int) -> None:
    """
    Met à jour la date de dernière connexion de l'utilisateur
    """
    db.query(User).filter(User.id == user_id).update(
        {"last_login": datetime.now()}
    )
    db.commit()

# -------------

def get_user_detailed(db: Session, user_id: int) -> Optional[User]:
    """
    Récupère un utilisateur avec toutes ses informations détaillées
    """
    return db.query(User).filter(User.id == user_id).first()




def get_users_all_detailed(db: Session) ->List[User]:
    """
    Récupère un utilisateur avec toutes ses informations détaillées
    """
    return db.query(User).all()

