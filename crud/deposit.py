# app/crud/deposit.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from datetime import datetime
from typing import List, Optional, Tuple

from app.models.deposit import Deposit, DepositStatus
from app.models.user import User
from app.models.auction import Auction
from app.schemas.deposit import DepositCreate, DepositUpdate, DepositFilter

class CRUDDeposit:
    @staticmethod
    def create(db: Session, deposit_create: DepositCreate) -> Deposit:
        """Créer un nouveau dépôt de caution"""
        db_deposit = Deposit(
            userId=deposit_create.userId,
            auctionId=deposit_create.auctionId,
            amount=deposit_create.amount,
            depositMethod=deposit_create.depositMethod,
            receiptFile=deposit_create.receiptFile,
            status=DepositStatus.PENDING,
            submittedAt=datetime.now()
        )
        db.add(db_deposit)
        db.commit()
        db.refresh(db_deposit)
        return db_deposit
    
    @staticmethod
    def get(db: Session, deposit_id: int) -> Optional[Deposit]:
        """Récupérer un dépôt par son ID"""
        return db.query(Deposit).filter(Deposit.id == deposit_id).first()
    
    @staticmethod
    def get_multi(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[DepositFilter] = None
    ) -> Tuple[List[Deposit], int]:
        """Récupérer plusieurs dépôts avec filtrage et pagination"""
        query = db.query(Deposit)
        
        if filters:
            if filters.status:
                query = query.filter(Deposit.status == filters.status)
            if filters.userId:
                query = query.filter(Deposit.userId == filters.userId)
            if filters.auctionId:
                query = query.filter(Deposit.auctionId == filters.auctionId)
            if filters.searchTerm:
                # Join avec les tables nécessaires pour la recherche
                query = query.join(Deposit.auction).join(Deposit.user)
                # Recherche sur les champs pertinents
                search_term = f"%{filters.searchTerm}%"
                query = query.filter(
                    or_(
                        cast(Deposit.id, String).like(search_term),
                        User.username.like(search_term),
                        cast(Auction.id, String).like(search_term),
                        Auction.title.like(search_term)
                    )
                )
        
        # Compter le nombre total d'éléments
        total = query.count()
        
        # Récupérer les éléments paginés
        items = query.order_by(Deposit.submittedAt.desc()).offset(skip).limit(limit).all()
        
        return items, total
    
    @staticmethod
    def get_by_auction(db: Session, auction_id: int) -> List[Deposit]:
        """Récupérer tous les dépôts pour une enchère spécifique"""
        return db.query(Deposit).filter(Deposit.auctionId == auction_id).all()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int) -> List[Deposit]:
        """Récupérer tous les dépôts d'un utilisateur spécifique"""
        return db.query(Deposit).filter(Deposit.userId == user_id).all()
    
    @staticmethod
    def update(db: Session, deposit_id: int, deposit_update: DepositUpdate) -> Optional[Deposit]:
        """Mettre à jour un dépôt"""
        db_deposit = CRUDDeposit.get(db, deposit_id)
        
        if not db_deposit:
            return None
        
        update_data = deposit_update.dict(exclude_unset=True)
        
        # Si le statut est mis à jour, mettre à jour la date de révision
        if "status" in update_data:
            update_data["reviewedAt"] = datetime.now()
        
        for key, value in update_data.items():
            setattr(db_deposit, key, value)
        
        db.commit()
        db.refresh(db_deposit)
        return db_deposit
    
    @staticmethod
    def remove(db: Session, deposit_id: int) -> bool:
        """Supprimer un dépôt"""
        db_deposit = CRUDDeposit.get(db, deposit_id)
        
        if not db_deposit:
            return False
        
        db.delete(db_deposit)
        db.commit()
        return True
    
    @staticmethod
    def count_by_status(db: Session) -> dict:
        """Compter le nombre de dépôts par statut"""
        total = db.query(Deposit).count()
        pending = db.query(Deposit).filter(Deposit.status == DepositStatus.PENDING).count()
        confirmed = db.query(Deposit).filter(Deposit.status == DepositStatus.CONFIRMED).count()
        rejected = db.query(Deposit).filter(Deposit.status == DepositStatus.REJECTED).count()
        
        return {
            "total": total,
            "pending": pending,
            "confirmed": confirmed,
            "rejected": rejected
        }