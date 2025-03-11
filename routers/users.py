from fastapi import APIRouter, Depends, HTTPException, status, Query,Path, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate, UserUpdateRole, UserUpdatePassword, UserList,UserUpdateState, DetailedUserResponse,UserUpdateResponse,DetailedUserResponseAll,UserCreate,UserResponseAllFrontend,UserResponseAllFrontendUpdate
from app.crud.user import (
    get_user, get_users, update_user, update_user_role, 
    update_user_password, deactivate_user, activate_user,update_user_state,get_user_detailed,update_user_arabic,get_users_all_detailed
    ,create_user_new
)
from app.utils.security import get_current_user, get_admin_user, get_superadmin_user, get_current_user_or_none

# Classes qui étaient dans arabic_user.py, désormais intégrées directement
class ArabicUserRole:
    """Mapping des rôles utilisateur vers des textes en arabe"""
    @staticmethod
    def get_role_text_and_class(role: UserRole) -> Dict[str, str]:
        if role == UserRole.ENCHERISSEUR:
            return {"text": "متزايد", "class": "bg-info"}
        elif role == UserRole.TRIBUNAL:
            return {"text": "المحكمة", "class": "bg-info"}
        elif role == UserRole.TRIBUNALMANAGER:
            return {"text": "الوزارة", "class": "bg-info"}
        elif role == UserRole.ORGACREDIT:
            return {"text": "شركة القروض", "class": "bg-info"}
        elif role == UserRole.ADMIN:
            return {"text": "مدير", "class": "bg-danger"}
        elif role == UserRole.SUPERADMIN:
            return {"text": "مدير عام", "class": "bg-danger"}
        else:
            return {"text": "غير معروف", "class": "bg-secondary"}

class ArabicUserStatus:
    """Mapping des statuts utilisateur vers des textes en arabe"""
    @staticmethod
    def get_status_text_and_class(is_active: bool, is_blocked: Optional[bool] = None) -> Dict[str, str]:
        # Si is_blocked n'est pas encore dans la BDD, on le traite comme False
        if is_blocked is True:  # Vérification explicite de True pour éviter les problèmes avec None
            return {"text": "محظور", "class": "bg-danger"}
        elif not is_active:
            return {"text": "معلق", "class": "bg-warning"}
        else:
            return {"text": "نشط", "class": "bg-success"}

class ArabicUserResponse(BaseModel):
    """Schéma pour la réponse utilisateur en format arabe"""
    id: int
    avatar: str = "https://www.claudeusercontent.com/api/placeholder/40/40"
    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    role: Dict[str, str]
    regDate: str
    status: Dict[str, str]

class ArabicUsersList(BaseModel):
    """Schéma pour la liste des utilisateurs en format arabe"""
    users: List[ArabicUserResponse]
    total: int

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("", response_model=UserList)
async def read_users(
    skip: int = 0,
    limit: int = 10,
    role: Optional[UserRole] = None,
    search: Optional[str] = Query(None, description="Recherche par nom, prénom ou email"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des utilisateurs (admin uniquement)
    """
    users, total = get_users(db, skip=skip, limit=limit, role=role, search=search)
    return {"users": users, "total": total}





@router.get("/detail")
async def read_users_details(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    search: Optional[str] = Query(None, description="Recherche par nom, prénom ou email"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Route publique pour récupérer la liste des utilisateurs"""
    from app.crud.user import get_users
    from app.models.user import UserRole
    # Convertir role en UserRole enum si nécessaire
    role_enum = None
    if role:
        try:
            role_enum = UserRole(role)
        except ValueError:
            pass
    users, total = get_users(db, skip=skip, limit=limit, role=role_enum, search=search)
    # Reformater les objets utilisateurs selon le format souhaité
    formatted_users = []
    for user in users:

        if user.role == UserRole.ENCHERISSEUR:
            role_text_map = {"text": "متزايد", "class": "bg-primary"}
        elif user.role == UserRole.TRIBUNAL:
            role_text_map =  {"text": "المحكمة", "class": "bg-secondary"}
        elif user.role == UserRole.TRIBUNALMANAGER:
            role_text_map =  {"text": "الوزارة", "class": "bg-success"}
        elif user.role == UserRole.ORGACREDIT:
            role_text_map =  {"text": "شركة القروض", "class": "bg-info"}
        elif user.role == UserRole.ADMIN:
            role_text_map =  {"text": "مدير", "class": "bg-dark"}
        elif user.  role == UserRole.SUPERADMIN:
            role_text_map =  {"text": "مدير عام", "class": "bg-warning"}
        else:
            role_text_map =  {"text": "غير معروف", "class": "bg-danger"}


        
        if user.is_blocked is True and user.is_active is False:
            status_text = {"text": "محظور", "class": "bg-danger"}
        elif user.is_verified is False:
            status_text = {"text": "معلق", "class": "bg-warning"}
        elif user.is_blocked is False and user.is_active is True:
            status_text = {"text": "نشط", "class": "bg-success"}
        else:
            status_text = {"text": "محظور", "class": "bg-success"}




        # Format de la date d'inscription (created_at) au format JJ/MM/AAAA
        reg_date = user.created_at.strftime("%d/%m/%Y") if user.created_at else ""
        
        formatted_users.append({
            "id": user.id,
            "avatar": "https://www.claudeusercontent.com/api/placeholder/40/40",
            "firstName": user.first_name,
            "lastName": user.last_name,
            "email": user.email,
            "phone": user.phone_number or "",
            "role": role_text_map,
            "regDate": reg_date,
            "status": status_text,
            "cin": user.cin or "",
            "ville_etranger": user.ville_etranger or "",
            "registre_commerce": user.registre_commerce or "",
            "denomination_societe": user.denomination_societe or "",
            "tribunal_id": user.tribunal_id or None,
            "pays_id": user.pays_id or None,
            "ville_id": user.ville_id or None,
            "organism_credit_id": user.organism_credit_id or None,
            "address": user.address or None,
        })
    
    return formatted_users



# @public_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register_user_new(
#     user_data: UserResponseAllFrontend,
#     db: Session = Depends(get_db)
# ):
#     """
#     Met à jour l'utilisateur (admin uniquement)
#     """
    
#     db_user = create_user_new(db, user_data)



#     """
#     Inscription d'un nouvel utilisateur avec envoi d'email de confirmation
#     """
    
#     # Créer l'utilisateur
#     #db_user = create_user(db, user, send_verification=True, is_active=False, is_verified=False)
    
#     # Envoyer l'email de vérification en arrière-plan
#     # if settings.ENABLE_EMAIL_NOTIFICATIONS and db_user.verification_token:
#     #     background_tasks.add_task(
#     #         send_verification_email,
#     #         email=db_user.email,
#     #         token=db_user.verification_token
#     #     )
    
#     return db_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les informations d'un utilisateur spécifique
    """
    # Vérifier les permissions (un utilisateur ne peut voir que son propre profil, sauf les admins)
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك الصلاحيات اللازمة"
        )
    
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لم يتم العثور على المستخدم"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour les informations d'un utilisateur
    """
    # Vérifier les permissions (un utilisateur ne peut modifier que son propre profil, sauf les admins)
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك الصلاحيات اللازمة لتحديث بيانات هذا المستخدم"
        )
    
    return update_user(db, user_id, user_data)



@router.put("/{user_id}/password", response_model=UserResponse)
async def update_user_password_endpoint(
    user_id: int,
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le mot de passe d'un utilisateur
    """
    # Vérifier les permissions (un utilisateur ne peut modifier que son propre mot de passe, sauf les admins)
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك الصلاحيات اللازمة لتغيير كلمة المرور لهذا المستخدم"
        )
    
    return update_user_password(db, user_id, password_data.current_password,password_data.new_password)




@router.put("/{user_id}/state", response_model=UserResponse)
async def update_user_state_endpoint(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le bloc d'un utilisateur (admin uniquement)
    """
    
    return update_user_state(db, user_id)




@router.put("/{user_id}/update", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_data: UserResponseAllFrontendUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour l'utilisateur (admin uniquement)
    """
    
    return update_user_arabic(db, user_id,user_data)

# @router.get("/{user_id}/details", response_model=DetailedUserResponse)
# async def read_user_detailed(
#     user_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Récupère les informations détaillées d'un utilisateur spécifique
#     """
#     db_user = get_user_detailed(db, user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
#     # Vérifier les permissions (seul l'admin peut voir tous les utilisateurs)
#     if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
#         raise HTTPException(status_code=403, detail="لا يمكنك عرض معلومات هذا المستخدم")
    
#     # Formater le rôle selon le format arabe
#     # if db_user.role == UserRole.ENCHERISSEUR:
#     #     role_text_map = {"text": "متزايد", "class": "bg-primary", "value": "bidder"}
#     # elif db_user.role == UserRole.TRIBUNAL:
#     #     role_text_map = {"text": "المحكمة", "class": "bg-secondary", "value": "tribunal"}
#     # elif db_user.role == UserRole.TRIBUNALMANAGER:
#     #     role_text_map = {"text": "الوزارة", "class": "bg-success", "value": "manager"}
#     # elif db_user.role == UserRole.ORGACREDIT:
#     #     role_text_map = {"text": "شركة القروض", "class": "bg-info", "value": "credit"}
#     # elif db_user.role == UserRole.ADMIN:
#     #     role_text_map = {"text": "مدير", "class": "bg-dark", "value": "admin"}
#     # else:
#     #     role_text_map = {"text": "مدير عام", "class": "bg-warning", "value": "superadmin"}



#     if db_user.role == UserRole.ENCHERISSEUR:
#         role_text_map = "متزايد"
#     elif db_user.role == UserRole.TRIBUNAL:
#         role_text_map = "المحكمة"
#     elif db_user.role == UserRole.TRIBUNALMANAGER:
#         role_text_map = "الوزارة"
#     elif db_user.role == UserRole.ORGACREDIT:
#         role_text_map = "شركة القروض"
#     elif db_user.role == UserRole.ADMIN:
#         role_text_map = "مدير"
#     else:
#         role_text_map = "مدير عام"


    
    
    
#     # Formater le statut
#     if db_user.is_blocked is True and db_user.is_active is False:
#         status_text = "banned"
#     elif db_user.is_verified is False:
#         status_text = "pending"
#     elif db_user.is_blocked is False and db_user.is_active is True:
#         status_text = "active"
#     else:
#         status_text = "banned"
    
#     # Formater les dates
#     reg_date = db_user.created_at.strftime("%d/%m/%Y") if db_user.created_at else ""
#     last_login = db_user.last_login.strftime("%d/%m/%Y %H:%M") if db_user.last_login else ""
    
#     # Créer la réponse
#     return DetailedUserResponse(
#         id=db_user.id,
#         firstName=db_user.first_name,
#         lastName=db_user.last_name,
#         email=db_user.email,
#         phone=db_user.phone_number,
#         avatar=f"https://www.claudeusercontent.com/api/placeholder/120/120",  # URL statique basée sur l'ID
#         regDate=reg_date,
#         role=role_text_map,
#         status=status_text,
#         # Statistiques factices (statiques)
#         statistics={
#             "createdAuctions": 0,
#             "wonAuctions": 0,
#             "bidsPlaced": 0,
#             "spentAmount": 0
#         },
#         address=db_user.address or "شارع محمد الخامس، رقم 45، الدار البيضاء",
#         city="الدار البيضاء", #db_user.city or "الدار البيضاء",
#         country="المغرب",
#         preferredLanguage="ar",
#         lastLogin=last_login,
#         # Statut de vérification statique
#         verificationStatus={
#             "email": True,
#             "phone": True,
#             "identity": db_user.is_verified
#         }
#     )


# @router.get("/details", response_model=DetailedUserResponseAll)
# async def read_user_detailed(
#     current_user: User = Depends(get_admin_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Récupère les informations détaillées d'un utilisateur spécifique
#     """
#     db_user = get_users_all_detailed(db)
#     if not db_users:
#         raise HTTPException(status_code=404, detail="Aucun utilisateur trouvé")
    
#     detailed_users = []
#     for db_user in db_users:
#         # Formater le rôle selon le format arabe
#         if db_user.role == UserRole.ENCHERISSEUR:
#             role_text_map = {"text": "متزايد", "class": "bg-primary", "value": "bidder"}
#         elif db_user.role == UserRole.TRIBUNAL:
#             role_text_map = {"text": "المحكمة", "class": "bg-secondary", "value": "tribunal"}
#         elif db_user.role == UserRole.TRIBUNALMANAGER:
#             role_text_map = {"text": "الوزارة", "class": "bg-success", "value": "manager"}
#         elif db_user.role == UserRole.ORGACREDIT:
#             role_text_map = {"text": "شركة القروض", "class": "bg-info", "value": "credit"}
#         elif db_user.role == UserRole.ADMIN:
#             role_text_map = {"text": "مدير", "class": "bg-dark", "value": "admin"}
#         else:
#             role_text_map = {"text": "مدير عام", "class": "bg-warning", "value": "superadmin"}

#         # Formater le statut
#         if db_user.is_blocked is True:  
#             status_text = {"text": "محظور", "class": "bg-danger"}
#         elif not db_user.is_active:
#             status_text = {"text": "معلق", "class": "bg-warning"}
#         else:
#             status_text = {"text": "نشط", "class": "bg-success"}
        
#         # Formater les dates
#         reg_date = db_user.created_at.strftime("%d/%m/%Y") if db_user.created_at else ""
#         last_login = db_user.last_login.strftime("%d/%m/%Y %H:%M") if db_user.last_login else ""
        
#         # Créer la réponse pour chaque utilisateur
#         detailed_user = DetailedUserResponseAll(
#             id=db_user.id,
#             firstName=db_user.first_name,
#             lastName=db_user.last_name,
#             email=db_user.email,
#             phone=db_user.phone_number,
#             avatar=f"https://www.claudeusercontent.com/api/placeholder/120/120",
#             regDate=reg_date,
#             role=role_text_map,
#             status=status_text,
#             address=db_user.address,
#             city="الدار البيضاء",
#             country="المغرب",
#             lastLogin=last_login,
#         )
#         detailed_users.append(detailed_user)
    
#     return detailed_users




# @router.put("/{user_id}/deactivate", response_model=UserResponse)
# async def deactivate_user_endpoint(
#     user_id: int,
#     current_user: User = Depends(get_admin_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Désactive un utilisateur (admin uniquement)
#     """
#     return deactivate_user(db, user_id)


#------------------------------------ 



# @router.put("/{user_id}/activate", response_model=UserResponse)
# async def activate_user_endpoint(
#     user_id: int,
#     current_user: User = Depends(get_admin_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Active un utilisateur (admin uniquement)
#     """
#     return activate_user(db, user_id)


#------------------------------------

# Nouvelle route optimisée pour remplacer les routes supprimées - Rendue publique
# Créer un routeur public distinct sans dépendance d'authentification

# @public_router.get("/allusers")
# async def read_all_users(
#     skip: Optional[int] = Query(0, description="Nombre d'utilisateurs à sauter"),
#     limit: Optional[int] = Query(100, description="Nombre d'utilisateurs à récupérer"),
#     db: Session = Depends(get_db)
# ):
#     """Endpoint public pour récupérer la liste des utilisateurs
    
#     - Supporte uniquement les paramètres de pagination (skip et limit)
#     - Retourne les informations de base des utilisateurs
#     - Accessible sans authentification
#     """
#     # Récupérer les utilisateurs avec pagination simple
#     users, total = get_users(db, skip=skip, limit=limit)
    
#     # Convertir les utilisateurs au format simplifié
#     result = []
#     for user in users:
#         # Format de base pour tous les utilisateurs
#         user_data = {
#             "id": user.id,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#             "role": user.role.value,  # Envoyer la valeur de l'enum plutôt que l'objet
#             "created_at": user.created_at.strftime("%d/%m/%Y") if user.created_at else "",
#             "is_blocked": user.is_blocked if hasattr(user, 'is_blocked') else False,
#             "is_active": user.is_active
#         }
#         result.append(user_data)
    
#     # Structure de réponse simplifiée
#     response = {
#         "users": result,
#         "total": total,
#         "success": True,
#         "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#     }
    
#     return response




#----------------------------------- my


# @router.get("/usersall")  # Route publique
# async def read_formatted_users(
#     skip: int = 0,
#     limit: int = 10,
#     current_user: User = Depends(get_admin_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Récupère la liste des utilisateurs formatée pour le frontend (admin uniquement)
#     """
#     users, total = get_users(db, skip=skip, limit=limit, role=role, search=search)
#     print("-----------------****")
#     # Reformater les objets utilisateurs selon le format souhaité
#     formatted_users = []
#     for user in users:
#         # Détermine la classe et le texte du statut
#         status_text = "نشط" if user.is_active else "غير نشط"
#         status_class = "bg-success" if user.is_active else "bg-danger"
#         
#         # Détermine la classe et le texte du rôle
#         role_text_map = {
#             "superadmin": "مدير عام",
#             "admin": "مدير",
#             "encherisseur": "مزايد"
#             # Ajoutez d'autres rôles au besoin
#         }
#         role_text = role_text_map.get(user.role, user.role)
#         role_class = "bg-danger" if user.role in ["superadmin", "admin"] else "bg-primary"
#         
#         # Format de la date d'inscription (created_at) au format JJ/MM/AAAA
#         reg_date = user.created_at.strftime("%d/%m/%Y") if user.created_at else ""
#         
#         formatted_users.append({
#             "id": user.id,
#             "avatar": "https://www.claudeusercontent.com/api/placeholder/40/40",
#             "firstName": user.first_name,
#             "lastName": user.last_name,
#             "email": user.email,
#             "phone": user.phone_number or "",
#             "role": {"text": role_text, "class": role_class},
#             "regDate": reg_date,
#             "status": {"text": status_text, "class": status_class}
#         })
#     
#     return {"users": formatted_users}


#------------------------------------



# @router.put("/{user_id}/role", response_model=UserResponse)
# async def update_user_role_endpoint(
#     user_id: int,
#     role_data: UserUpdateRole,
#     current_user: User = Depends(get_admin_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Met à jour le rôle d'un utilisateur (admin uniquement)
#     """
#     return update_user_role(db, user_id, role_data.role)


#------------------------------------