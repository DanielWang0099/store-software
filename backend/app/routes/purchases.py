"""
Purchase management API routes
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from app.models.database import get_db
from app.models.purchase import Purchase
from app.models.customer import Customer
from app.models.scan_event import ScanEvent

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class PurchaseCreate(BaseModel):
    customer_id: UUID
    receipt_id: Optional[str] = None
    amount: float
    receipt_text: Optional[str] = None
    items_count: Optional[int] = 0

class PurchaseResponse(BaseModel):
    id: str
    customer_id: str
    receipt_id: Optional[str]
    timestamp: Optional[str]
    amount: float
    points_awarded: int
    items_count: int
    processed_at: Optional[str]

class CustomerPurchaseStats(BaseModel):
    customer_id: str
    total_purchases: int
    total_spent: float
    total_points: int
    first_purchase: Optional[str]
    last_purchase: Optional[str]

@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    purchase_data: PurchaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new purchase and award loyalty points"""
    try:
        # Verify customer exists
        result = await db.execute(select(Customer).where(Customer.id == purchase_data.customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Create purchase record
        purchase = Purchase(
            customer_id=purchase_data.customer_id,
            receipt_id=purchase_data.receipt_id,
            amount=purchase_data.amount,
            receipt_text=purchase_data.receipt_text,
            items_count=purchase_data.items_count or 0
        )
        
        # Calculate and award points
        points_awarded = purchase.calculate_points()
        
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        
        logger.info(f"Created purchase for customer {customer.name}: ${purchase.amount}, {points_awarded} points")
        
        return PurchaseResponse(**purchase.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating purchase"
        )

@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get purchase by ID"""
    try:
        result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
        purchase = result.scalar_one_or_none()
        
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )
        
        return PurchaseResponse(**purchase.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase {purchase_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving purchase"
        )

@router.get("/customer/{customer_id}", response_model=List[PurchaseResponse])
async def get_customer_purchases(
    customer_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all purchases for a customer"""
    try:
        # Verify customer exists
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get purchases
        query = select(Purchase).where(Purchase.customer_id == customer_id)\
                                .order_by(Purchase.timestamp.desc())\
                                .offset(skip).limit(limit)
        
        result = await db.execute(query)
        purchases = result.scalars().all()
        
        return [PurchaseResponse(**purchase.to_dict()) for purchase in purchases]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer purchases {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer purchases"
        )

@router.get("/stats/{customer_id}", response_model=CustomerPurchaseStats)
async def get_customer_purchase_stats(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get purchase statistics for a customer"""
    try:
        # Verify customer exists
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get purchase statistics
        stats_query = select(
            func.count(Purchase.id).label('total_purchases'),
            func.sum(Purchase.amount).label('total_spent'),
            func.sum(Purchase.points_awarded).label('total_points'),
            func.min(Purchase.timestamp).label('first_purchase'),
            func.max(Purchase.timestamp).label('last_purchase')
        ).where(Purchase.customer_id == customer_id)
        
        result = await db.execute(stats_query)
        stats = result.first()
        
        return CustomerPurchaseStats(
            customer_id=str(customer_id),
            total_purchases=stats.total_purchases or 0,
            total_spent=float(stats.total_spent or 0),
            total_points=stats.total_points or 0,
            first_purchase=stats.first_purchase.isoformat() if stats.first_purchase else None,
            last_purchase=stats.last_purchase.isoformat() if stats.last_purchase else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer stats {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving customer statistics"
        )

@router.get("/", response_model=List[PurchaseResponse])
async def list_purchases(
    skip: int = 0,
    limit: int = 100,
    customer_id: Optional[UUID] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List purchases with optional filters"""
    try:
        query = select(Purchase)
        
        # Apply filters
        filters = []
        
        if customer_id:
            filters.append(Purchase.customer_id == customer_id)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                filters.append(Purchase.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format."
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                filters.append(Purchase.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format."
                )
        
        if filters:
            query = query.where(and_(*filters))
        
        # Add ordering and pagination
        query = query.order_by(Purchase.timestamp.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        purchases = result.scalars().all()
        
        return [PurchaseResponse(**purchase.to_dict()) for purchase in purchases]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing purchases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing purchases"
        )

@router.post("/process-barcode-purchase")
async def process_barcode_purchase(
    barcode: str,
    receipt_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Process a purchase based on customer barcode scan and receipt data"""
    try:
        # Find customer by barcode
        result = await db.execute(select(Customer).where(Customer.barcode_data == barcode))
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found for barcode"
            )
        
        # Create scan event
        scan_event = ScanEvent(
            customer_id=customer.id,
            barcode_data=barcode,
            is_matched=True
        )
        db.add(scan_event)
        
        # Create purchase
        purchase = Purchase(
            customer_id=customer.id,
            receipt_id=receipt_data.get('receipt_id'),
            amount=receipt_data.get('total', 0),
            receipt_text=receipt_data.get('raw_text'),
            items_count=receipt_data.get('items_count', 0)
        )
        
        # Calculate points
        points_awarded = purchase.calculate_points()
        
        db.add(purchase)
        await db.commit()
        await db.refresh(purchase)
        await db.refresh(scan_event)
        
        logger.info(f"Processed barcode purchase: {customer.name}, ${purchase.amount}, {points_awarded} points")
        
        return {
            "purchase": purchase.to_dict(),
            "customer": customer.to_dict(),
            "points_awarded": points_awarded
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing barcode purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing purchase"
        )
