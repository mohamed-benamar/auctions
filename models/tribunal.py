from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

class Tribunal(Base):
    """Modèle pour les tribunaux du Maroc"""
    __tablename__ = "tribunaux"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    nom_ar = Column(String, nullable=True)  # Nom en arabe
    ville = Column(String, nullable=False)
    type = Column(String, nullable=True)  # Type de tribunal (e.g., première instance, appel, etc.)
    
    # Relations
    users = relationship("User", back_populates="tribunal")
    
    def __repr__(self):
        return f"<Tribunal {self.nom} ({self.ville})>"
