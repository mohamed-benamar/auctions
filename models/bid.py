from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class Bid(Base):
    """Modèle pour les enchères placées"""
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    auctionId = Column(Integer, ForeignKey("auctions.id"), nullable=False, index=True)
    bidderId = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    
    # Relations
    auction = relationship("Auction", back_populates="bids")
    bidder = relationship("User", backref="bids")
    
    def __repr__(self):
        return f"<Bid {self.id} - {self.amount} on Auction {self.auctionId}>"
