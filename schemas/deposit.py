# app/schemas/deposit.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.deposit import DepositStatus, DepositMethod

class DepositBase(BaseModel):
    amount: float
    auctionId: int
    userId: int
    depositMethod: DepositMethod

class DepositCreate(DepositBase):
    receiptFile: Optional[str] = None

class DepositUpdate(BaseModel):
    status: Optional[DepositStatus] = None
    adminMessage: Optional[str] = None
    reviewedBy: Optional[str] = None
    
    @validator('adminMessage')
    def validate_admin_message(cls, v, values):
        if values.get('status') == DepositStatus.REJECTED and not v:
            raise ValueError('Admin message is required when rejecting a deposit')
        return v

class DepositResponse(DepositBase):
    id: int
    status: DepositStatus
    adminMessage: Optional[str] = None
    receiptFile: Optional[str] = None
    submittedAt: datetime
    reviewedAt: Optional[datetime] = None
    reviewedBy: Optional[str] = None
    
    class Config:
        orm_mode = True

class DepositWithAuctionInfo(DepositResponse):
    auctionTitle: str
    
    class Config:
        orm_mode = True

class DepositFilter(BaseModel):
    status: Optional[DepositStatus] = None
    userId: Optional[int] = None
    auctionId: Optional[int] = None
    searchTerm: Optional[str] = None

# Schema pour la pagination
class PaginatedDeposits(BaseModel):
    items: List[DepositWithAuctionInfo]
    total: int
    page: int
    size: int
    pages: int