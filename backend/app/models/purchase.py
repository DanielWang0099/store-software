"""
Purchase model for tracking customer purchases and loyalty points
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base
from app.models.customer import GUID

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=True)
    receipt_number = Column(String(50), nullable=True)
    receipt_text = Column(Text, nullable=True)
    amount_cents = Column(Integer, nullable=False)  # Amount in cents
    points_awarded = Column(Integer, default=0)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    cashier_station = Column(String(20), nullable=True)
    receipt_hash = Column(String(64), nullable=True)  # For duplicate detection
    
    # Relationship to customer
    customer = relationship("Customer", back_populates="purchases")
    
    @property
    def amount_dollars(self):
        """Get amount in dollars"""
        return self.amount_cents / 100.0
    
    @amount_dollars.setter
    def amount_dollars(self, value):
        """Set amount from dollars"""
        self.amount_cents = int(value * 100)
    
    def calculate_points(self, points_per_dollar=1):
        """Calculate loyalty points for this purchase"""
        base_points = int(self.amount_dollars * points_per_dollar)
        
        # Bonus points for larger purchases
        if self.amount_dollars >= 500:
            bonus_points = 50
        elif self.amount_dollars >= 250:
            bonus_points = 25
        elif self.amount_dollars >= 100:
            bonus_points = 10
        else:
            bonus_points = 0
            
        self.points_awarded = base_points + bonus_points
        return self.points_awarded
    
    def to_dict(self):
        """Convert purchase to dictionary"""
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "receipt_number": self.receipt_number,
            "amount_dollars": self.amount_dollars,
            "points_awarded": self.points_awarded,
            "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            "cashier_station": self.cashier_station,
            "receipt_hash": self.receipt_hash
        }
    
    def __repr__(self):
        return f"<Purchase(id={self.id}, amount=${self.amount_dollars:.2f}, points={self.points_awarded})>"
