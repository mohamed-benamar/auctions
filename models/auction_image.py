from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class AuctionImage(Base):
    """Modèle pour les images d'une enchère"""
    __tablename__ = "auction_images"

    id = Column(Integer, primary_key=True, index=True)
    auctionId = Column(Integer, ForeignKey("auctions.id"), nullable=False, index=True)
    imageUrl = Column(String, nullable=False)
    caption = Column(String, nullable=True)
    isMain = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    # Relations
    auction = relationship("Auction", back_populates="images")
    
    def __repr__(self):
        return f"<AuctionImage {self.id} for Auction {self.auctionId}>"
