from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base

class OrganismCredit(Base):
    """Modèle pour les organismes de crédit"""
    __tablename__ = "organism_credit"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    nom_ar = Column(String, nullable=True)
    adresse = Column(Text, nullable=True)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    site_web = Column(String, nullable=True)
    
    # Relations
    users = relationship("User", back_populates="organism_credit")
    
    def __repr__(self):
        return f"<OrganismCredit {self.nom}>"
