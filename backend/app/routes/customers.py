"""
Customer management API routes
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.models.database import get_db
from app.models.customer import Customer

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    barcode: Optional[str]
    total_points: int
    total_spent: int
    joined_at: Optional[str]
    last_visit: Optional[str]
    notes: Optional[str]

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer"""
    try:
        # Create new customer
        customer = Customer(
            name=customer_data.name,
            email=customer_data.email,
            phone=customer_data.phone,
            notes=customer_data.notes
        )
        
        # Generate barcode for new customer
        customer.generate_barcode()
        
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
        logger.info(f"Created new customer: {customer.name} ({customer.barcode})")
        
        return CustomerResponse(**customer.to_dict())
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating customer"
        )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get customer by ID"""
    try:
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return CustomerResponse(**customer.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer"
        )

@router.get("/barcode/{barcode}", response_model=CustomerResponse)
async def get_customer_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db)
):
    """Get customer by barcode"""
    try:
        result = await db.execute(select(Customer).where(Customer.barcode == barcode))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        return CustomerResponse(**customer.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer by barcode {barcode}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer"
        )

@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List customers with optional search"""
    try:
        query = select(Customer)
        
        # Add search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                Customer.name.ilike(search_filter) |
                Customer.email.ilike(search_filter) |
                Customer.phone.ilike(search_filter)
            )
        
        # Add pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        customers = result.scalars().all()
        
        return [CustomerResponse(**customer.to_dict()) for customer in customers]
        
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing customers"
        )

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update customer information"""
    try:
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Update fields if provided
        if customer_data.name is not None:
            customer.name = customer_data.name
        if customer_data.email is not None:
            customer.email = customer_data.email
        if customer_data.phone is not None:
            customer.phone = customer_data.phone
        if customer_data.notes is not None:
            customer.notes = customer_data.notes
        
        await db.commit()
        await db.refresh(customer)
        
        logger.info(f"Updated customer: {customer.name} ({customer.barcode})")
        
        return CustomerResponse(**customer.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating customer"
        )

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete customer"""
    try:
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        await db.delete(customer)
        await db.commit()
        
        logger.info(f"Deleted customer: {customer.name} ({customer.barcode})")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting customer"
        )
