"""
Scan event model for tracking customer barcode scans
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base
from app.models.customer import GUID

class ScanEvent(Base):
    __tablename__ = "scan_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID(), ForeignKey("customers.id"), nullable=True)
    barcode_data = Column(String(50), nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    is_matched = Column(Boolean, default=False)  # Whether matched to a purchase
    cashier_station = Column(String(20), nullable=True)  # Which station scanned
    
    # Relationship to customer
    customer = relationship("Customer", back_populates="scan_events")
    
    def to_dict(self):
        """Convert scan event to dictionary"""
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "barcode_data": self.barcode_data,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
            "is_matched": self.is_matched,
            "cashier_station": self.cashier_station
        }
    
    def __repr__(self):
        return f"<ScanEvent(id={self.id}, barcode='{self.barcode_data}', matched={self.is_matched})>"
