from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Union
from datetime import datetime

from app.models.user import UserRole

class UserBase(BaseModel):
    """Schéma de base pour les utilisateurs"""
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    
class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    role: UserRole = UserRole.ENCHERISSEUR
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tribunal_id: Optional[int] = None
    pays_id: Optional[int] = None
    ville_id: Optional[int] = None
    ville_etranger: Optional[str] = None
    organism_credit_id: Optional[int] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v

class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # email: Optional[EmailStr] = None  # Email supprimé des champs modifiables
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tribunal_id: Optional[int] = None
    pays_id: Optional[int] = None
    ville_id: Optional[int] = None
    ville_etranger: Optional[str] = None
    organism_credit_id: Optional[int] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None

class UserUpdateRole(BaseModel):
    """Schéma pour la mise à jour du rôle d'un utilisateur (admin uniquement)"""
    role: UserRole


class UserUpdateState(BaseModel):
    """Schéma pour la mise à jour du rôle d'un utilisateur (admin uniquement)"""
    is_blocked: Optional[bool] = None

class UserUpdatePassword(BaseModel):
    """Schéma pour la mise à jour du mot de passe"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str = Field(..., min_length=8)
    
    @validator('new_password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('كلمات المرور الجديدة غير متطابقة')
        return v

class UserInDB(UserBase):
    """Schéma représentant un utilisateur en base de données"""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tribunal_id: Optional[int] = None
    pays_id: Optional[int] = None
    ville_id: Optional[int] = None
    ville_etranger: Optional[str] = None
    organism_credit_id: Optional[int] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """Schéma pour la réponse d'un utilisateur"""
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tribunal_id: Optional[int] = None
    pays_id: Optional[int] = None
    ville_id: Optional[int] = None
    ville_etranger: Optional[str] = None
    organism_credit_id: Optional[int] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    """Schéma pour la liste des utilisateurs"""
    users: List[UserResponse]
    total: int

class UserUpdateResponse(BaseModel):
    """Schéma modifie utilisateur en format arabe"""
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email:Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class DetailedUserResponse(BaseModel):
    """Schéma détaillé pour la réponse utilisateur en format arabe"""
    id: int
    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    avatar: str = "https://exemple.com/avatars/default.jpg"
    regDate: str
    role: str
    status: str
    statistics: dict[str, int] = {
        "createdAuctions": 0,
        "wonAuctions": 0,
        "bidsPlaced": 0,
        "spentAmount": 0
    }
    address: Optional[str] = None
    city: Optional[dict] = None
    country: Optional[dict] = None
    tribunal: Optional[dict] = None
    ville_etranger: Optional[str] = None
    preferredLanguage: str = "ar"
    lastLogin: Optional[str] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None
    verificationStatus: dict[str, bool] = {
        "email": True,
        "phone": True,
        "identity": False
    }




class DetailedUserResponseAll(BaseModel):
    """Schéma détaillé pour la réponse utilisateur en format arabe"""
    id: int
    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    avatar: str = "https://exemple.com/avatars/default.jpg"
    regDate: str
    role: dict[str, str]
    status: dict[str, str]
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "المغرب"
    lastLogin: Optional[str] = None
    tribunal_id: Optional[int] = None
    pays_id: Optional[int] = None
    ville_id: Optional[int] = None
    ville_etranger: Optional[str] = None
    registre_commerce: Optional[str] = None
    denomination_societe: Optional[str] = None
    cin: Optional[str] = None
    

# forma mounir frontend

class UserResponseAllFrontend(BaseModel):
    """Schéma pour la création d'un utilisateur"""
    firstName: str = Field(..., description="Prénom de l'utilisateur")
    lastName: str = Field(..., description="Nom de famille de l'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")
    password: str = Field(..., min_length=8, description="Mot de passe (minimum 8 caractères)")
    password_confirm: str = Field(..., min_length=8, description="Confirmation du mot de passe")
    role: str = Field("encherisseur", description="Rôle de l'utilisateur")
    phone: Optional[str] = Field(None, description="Numéro de téléphone")
    address: Optional[str] = Field(None, description="Adresse postale")
    tribunal_id: Optional[int] = Field(None, description="ID du tribunal associé")
    pays_id: Optional[int] = Field(None, description="ID du pays")
    ville_id: Optional[int] = Field(None, description="ID de la ville")
    ville_etranger: Optional[str] = Field(None, description="Nom de ville étrangère")
    organism_credit_id: Optional[int] = Field(None, description="ID de l'organisme de crédit")
    registre_commerce: Optional[str] = Field(None, description="Numéro de registre de commerce")
    denomination_societe: Optional[str] = Field(None, description="Nom de la société")
    cin: Optional[str] = Field(None, description="Numéro de carte d'identité nationale")
    
    class Config:
        schema_extra = {
            "example": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "role": "encherisseur",
                "phone": "+212600000000",
                "address": "123 Rue Example",
                "cin": "AB123456"
            }
        }
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v



class UserResponseAllFrontendUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur - tous les champs sont optionnels"""
    firstName: Optional[str] = Field(None, description="Prénom de l'utilisateur")
    lastName: Optional[str] = Field(None, description="Nom de famille de l'utilisateur")
    email: Optional[str] = Field(None, description="Adresse e-mail de l'utilisateur")
    password: Optional[str] = Field(None, description="Mot de passe (minimum 8 caractères)")
    password_confirm: Optional[str] = Field(None, description="Confirmation du mot de passe")
    role: Optional[str] = Field(None, description="Rôle de l'utilisateur")
    phone: Optional[str] = Field(None, description="Numéro de téléphone")
    address: Optional[str] = Field(None, description="Adresse postale")
    # Champ de status pour gérer l'état de l'utilisateur
    status: Optional[str] = Field(None, description="Statut de l'utilisateur (active, pending, banned)")
    # Les IDs peuvent être des entiers, None, ou des chaînes
    tribunal_id: Optional[Union[int, str, None]] = Field(default=None, description="ID du tribunal associé")
    pays_id: Optional[Union[int, str, None]] = Field(default=None, description="ID du pays")
    ville_id: Optional[Union[int, str, None]] = Field(default=None, description="ID de la ville")
    ville_etranger: Optional[str] = Field(None, description="Nom de ville étrangère")
    organism_credit_id: Optional[Union[int, str, None]] = Field(default=None, description="ID de l'organisme de crédit")
    registre_commerce: Optional[str] = Field(None, description="Numéro de registre de commerce")
    denomination_societe: Optional[str] = Field(None, description="Nom de la société")
    cin: Optional[str] = Field(None, description="Numéro de carte d'identité nationale")
    
    # Validateurs pour convertir les chaînes vides en None pour les IDs
    @validator('tribunal_id', 'pays_id', 'ville_id', 'organism_credit_id', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        # Vérification uniquement si les deux champs sont fournis
        if v is not None and 'password' in values and values['password'] is not None:
            if v != values['password']:
                raise ValueError('Les mots de passe ne correspondent pas')
        return v
        
    class Config:
        extra = 'ignore'  # Ignore les champs supplémentaires
        validate_assignment = False  # Ne pas valider lors de l'assignation
        validate_all = False  # Ne pas valider tous les champs

