from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class AuctionSpecification(Base):
    """Modèle pour les spécifications d'une enchère"""
    __tablename__ = "auction_specifications"

    id = Column(Integer, primary_key=True, index=True)
    auctionId = Column(Integer, ForeignKey("auctions.id"), nullable=False, index=True)
    property = Column(String, nullable=False)
    value = Column(String, nullable=False)
    
    # Relations
    auction = relationship("Auction", back_populates="specifications")
    
    def __repr__(self):
        return f"<AuctionSpec {self.property}: {self.value} for Auction {self.auctionId}>"
