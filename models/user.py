from sqlalchemy import Boolean, Column, String, Integer, Enum, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base

class UserRole(str, enum.Enum):
    """Énumération des rôles d'utilisateur possibles"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    TRIBUNAL = "tribunal"
    TRIBUNALMANAGER = "tribunalmanager"
    ORGACREDIT = "orgacredit"
    ENCHERISSEUR = "encherisseur"

class User(Base):
    """Modèle d'utilisateur"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)
    
    # Informations additionnelles
    phone_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    ville_etranger = Column(String, nullable=True)  # Pour les utilisateurs dont le pays n'est pas le Maroc
    registre_commerce = Column(String, nullable=True)
    denomination_societe = Column(String, nullable=True)
    cin = Column(String, nullable=True)
    
    # Relations avec les nouvelles tables
    tribunal_id = Column(Integer, ForeignKey("tribunaux.id"), nullable=True)
    pays_id = Column(Integer, ForeignKey("pays.id"), nullable=True)
    ville_id = Column(Integer, ForeignKey("villes.id"), nullable=True)
    organism_credit_id = Column(Integer, ForeignKey("organism_credit.id"), nullable=True)
    
    # Relations (ORM)
    tribunal = relationship("Tribunal", back_populates="users")
    pays = relationship("Pays", back_populates="users")
    ville = relationship("Ville", back_populates="users")
    organism_credit = relationship("OrganismCredit", back_populates="users")
    
    # Champs d'audit
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
