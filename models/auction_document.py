from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

class AuctionDocument(Base):
    """Modèle pour les documents d'une enchère"""
    __tablename__ = "auction_documents"

    id = Column(Integer, primary_key=True, index=True)
    auctionId = Column(Integer, ForeignKey("auctions.id"), nullable=False, index=True)
    documentType = Column(String, nullable=False)
    documentUrl = Column(String, nullable=False)
    documentName = Column(String, nullable=True)
    isPublic = Column(Boolean, default=True)
    uploadedAt = Column(DateTime(timezone=True), default=func.now())
    
    # Relations
    auction = relationship("Auction", back_populates="documents")
    
    def __repr__(self):
        return f"<AuctionDocument {self.documentType} for Auction {self.auctionId}>"
