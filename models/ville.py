from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class Ville(Base):
    """Modèle pour les villes (avec noms en français et arabe)"""
    __tablename__ = "villes"

    id = Column(Integer, primary_key=True, index=True)
    nom_fr = Column(String, nullable=False, index=True)
    nom_ar = Column(String, nullable=False)
    pays_id = Column(Integer, ForeignKey("pays.id"), nullable=False)
    
    # Relations
    pays = relationship("Pays", back_populates="villes")
    users = relationship("User", back_populates="ville")
    
    def __repr__(self):
        return f"<Ville {self.nom_fr}>"
