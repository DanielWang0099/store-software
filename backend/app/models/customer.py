"""
Customer model for storing customer information and loyalty data
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, String as SQLString
import json

from app.models.database import Base

# Custom UUID type that works with both SQLite and PostgreSQL
class GUID(TypeDecorator):
    impl = SQLString
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(dialect.UUID())
        else:
            return dialect.type_descriptor(SQLString(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    barcode = Column(String(50), nullable=True, unique=True)
    total_points = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)  # in cents
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_visit = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="customer")
    scan_events = relationship("ScanEvent", back_populates="customer")
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "barcode": self.barcode,
            "total_points": self.total_points,
            "total_spent": self.total_spent,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_visit": self.last_visit.isoformat() if self.last_visit else None,
            "notes": self.notes
        }
    
    def generate_barcode(self):
        """Generate a unique barcode for the customer"""
        if not self.barcode:
            # Generate a simple numeric barcode based on timestamp and random
            import time
            import random
            timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            random_num = str(random.randint(1000, 9999))
            self.barcode = f"LOY{timestamp}{random_num}"
        return self.barcode
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', points={self.total_points})>"
