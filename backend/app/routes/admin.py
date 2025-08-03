"""
Admin and system management API routes
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.models.database import get_db
from app.models.customer import Customer
from app.models.purchase import Purchase
from app.models.scan_event import ScanEvent

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for admin responses
class SystemStats(BaseModel):
    total_customers: int
    total_purchases: int
    total_revenue: float
    total_points_awarded: int
    total_scan_events: int
    avg_purchase_amount: float

class TestReceiptRequest(BaseModel):
    receipt_text: str

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """Get overall system statistics"""
    try:
        # Get customer count
        customer_count_result = await db.execute(select(func.count(Customer.id)))
        total_customers = customer_count_result.scalar() or 0
        
        # Get purchase statistics
        purchase_stats_result = await db.execute(
            select(
                func.count(Purchase.id),
                func.sum(Purchase.amount),
                func.sum(Purchase.points_awarded),
                func.avg(Purchase.amount)
            )
        )
        purchase_stats = purchase_stats_result.first()
        
        total_purchases = purchase_stats[0] or 0
        total_revenue = float(purchase_stats[1] or 0)
        total_points_awarded = purchase_stats[2] or 0
        avg_purchase_amount = float(purchase_stats[3] or 0)
        
        # Get scan event count
        scan_count_result = await db.execute(select(func.count(ScanEvent.id)))
        total_scan_events = scan_count_result.scalar() or 0
        
        return SystemStats(
            total_customers=total_customers,
            total_purchases=total_purchases,
            total_revenue=total_revenue,
            total_points_awarded=total_points_awarded,
            total_scan_events=total_scan_events,
            avg_purchase_amount=avg_purchase_amount
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving system statistics"
        )

@router.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "service": "admin",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/connection-status")
async def get_connection_status():
    """Get WebSocket connection status"""
    # This would be injected from the WebSocket manager in a real implementation
    return {
        "tablet_connected": False,
        "electron_connected": False,
        "tablet_state": "idle",
        "current_customer_scan": None
    }

@router.post("/test-receipt")
async def test_receipt_parsing(request: TestReceiptRequest):
    """Test receipt parsing functionality"""
    try:
        from app.utils.receipt_parser import ReceiptParser
        
        parser = ReceiptParser()
        parsed_data = parser.parse_receipt(request.receipt_text)
        
        return {
            "success": True,
            "parsed_data": parsed_data,
            "is_valid": parser.is_valid_receipt(request.receipt_text)
        }
        
    except Exception as e:
        logger.error(f"Error testing receipt parsing: {e}")
        return {
            "success": False,
            "error": str(e),
            "parsed_data": None
        }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get recent system activity"""
    try:
        # Get recent purchases
        recent_purchases_result = await db.execute(
            select(Purchase)
            .order_by(Purchase.purchase_date.desc())
            .limit(limit)
        )
        recent_purchases = recent_purchases_result.scalars().all()
        
        # Get recent scan events
        recent_scans_result = await db.execute(
            select(ScanEvent)
            .order_by(ScanEvent.scanned_at.desc())
            .limit(limit)
        )
        recent_scans = recent_scans_result.scalars().all()
        
        # Get recent customers
        recent_customers_result = await db.execute(
            select(Customer)
            .order_by(Customer.joined_at.desc())
            .limit(limit)
        )
        recent_customers = recent_customers_result.scalars().all()
        
        return {
            "recent_purchases": [purchase.to_dict() for purchase in recent_purchases],
            "recent_scans": [scan.to_dict() for scan in recent_scans],
            "recent_customers": [customer.to_dict() for customer in recent_customers]
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving recent activity"
        )

@router.post("/broadcast-message")
async def broadcast_system_message(message: dict):
    """Broadcast a message to all connected clients"""
    try:
        # This would use the WebSocket manager to broadcast
        # For now, just return success
        logger.info(f"Broadcasting message: {message}")
        
        return {
            "success": True,
            "message": "Message broadcasted",
            "recipients": ["tablet", "electron"]
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error broadcasting message"
        )

@router.post("/reset-tablet")
async def reset_tablet():
    """Reset tablet to idle state"""
    try:
        # This would use the WebSocket manager to reset tablet
        logger.info("Resetting tablet to idle state")
        
        return {
            "success": True,
            "message": "Tablet reset to idle state"
        }
        
    except Exception as e:
        logger.error(f"Error resetting tablet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting tablet"
        )

@router.get("/export-data")
async def export_system_data(
    format: str = "json",
    include_customers: bool = True,
    include_purchases: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Export system data for backup or analysis"""
    try:
        export_data = {}
        
        if include_customers:
            customers_result = await db.execute(select(Customer))
            customers = customers_result.scalars().all()
            export_data["customers"] = [customer.to_dict() for customer in customers]
        
        if include_purchases:
            purchases_result = await db.execute(select(Purchase))
            purchases = purchases_result.scalars().all()
            export_data["purchases"] = [purchase.to_dict() for purchase in purchases]
        
        export_data["exported_at"] = "2024-01-01T00:00:00Z"
        export_data["format"] = format
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting system data"
        )
