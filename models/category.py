from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Category(Base):
    """Modèle pour les catégories d'enchères"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Category {self.name}>"
