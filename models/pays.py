from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

class Pays(Base):
    """Modèle pour les pays (avec noms en français et arabe)"""
    __tablename__ = "pays"

    id = Column(Integer, primary_key=True, index=True)
    nom_fr = Column(String, nullable=False, index=True)
    nom_ar = Column(String, nullable=False)
    code = Column(String(2), nullable=True)  # Code ISO du pays (e.g., MA pour Maroc)
    
    # Relations
    users = relationship("User", back_populates="pays")
    villes = relationship("Ville", back_populates="pays")
    
    def __repr__(self):
        return f"<Pays {self.code}: {self.nom_fr}>"
