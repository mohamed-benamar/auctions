# app/models/deposit.py
from sqlalchemy import Column, Integer, Float, ForeignKey, String, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from enum import Enum as PyEnum

class DepositStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class DepositMethod(str, PyEnum):
    BANK = "bank"
    CARD = "card"
    WALLET = "wallet"

class Deposit(Base):
    __tablename__ = 'deposits'

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    auctionId = Column(Integer, ForeignKey('auctions.id'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    depositMethod = Column(Enum(DepositMethod), nullable=False)
    receiptFile = Column(String, nullable=True)
    status = Column(Enum(DepositStatus), default=DepositStatus.PENDING)
    adminMessage = Column(Text, nullable=True)
    
    # Champs d'audit
    submittedAt = Column(DateTime(timezone=True), default=func.now())
    reviewedAt = Column(DateTime(timezone=True), nullable=True)
    reviewedBy = Column(String, nullable=True)
    
    # Relations
    auction = relationship('Auction', back_populates='deposits')
    user = relationship('User', foreign_keys=[userId], backref='deposits')

    def __repr__(self):
        return f"<Deposit {self.id} for Auction {self.auctionId} by User {self.userId} ({self.status})>"