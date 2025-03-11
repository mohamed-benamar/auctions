from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base

class AuctionType(str, enum.Enum):
    """Types d'enchères disponibles"""
    NORMAL = "normal"
    FLASH = "flash"
    RESERVED = "reserved"
    PRIVATE = "private"

class AuctionStatus(str, enum.Enum):
    """Statuts possibles d'une enchère"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    SOLD = "sold"

class Auction(Base):
    """Modèle d'enchère"""
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    startingPrice = Column(Float, nullable=False)
    reservePrice = Column(Float, nullable=True)
    incrementAmount = Column(Float, nullable=False, default=1.0)
    location = Column(String, nullable=True)
    sellerName = Column(String, nullable=False)
    termsConditions = Column(Text, nullable=True)
    productHistory = Column(Text, nullable=True)
    
    # Champs de planification
    startDate = Column(DateTime, nullable=False)
    endDate = Column(DateTime, nullable=False)
    startTime = Column(String, nullable=True)  # Format HH:MM
    endTime = Column(String, nullable=True)    # Format HH:MM
    auctionType = Column(Enum(AuctionType), nullable=False, default=AuctionType.NORMAL)
    auctionStatus = Column(Enum(AuctionStatus), nullable=False, default=AuctionStatus.DRAFT)
    featuredAuction = Column(Boolean, default=False)
    
    # Champs d'audit
    createdAt = Column(DateTime(timezone=True), default=func.now())
    updatedAt = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relations
    category = relationship("Category", backref="auctions")
    creator = relationship("User", backref="auctions")
    images = relationship("AuctionImage", back_populates="auction", cascade="all, delete-orphan")
    specifications = relationship("AuctionSpecification", back_populates="auction", cascade="all, delete-orphan")
    documents = relationship("AuctionDocument", back_populates="auction", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")
    deposits = relationship('Deposit', back_populates='auction')


    def __repr__(self):
        return f"<Auction {self.title} ({self.auctionStatus})>"
