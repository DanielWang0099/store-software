"""
Receipt parsing utilities for extracting transaction data
"""
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List
from decimal import Decimal

logger = logging.getLogger(__name__)

class ReceiptParser:
    """Parse receipt text to extract transaction information"""
    
    # Common receipt patterns
    TOTAL_PATTERNS = [
        r'TOTAL\s*:?\s*\$?(\d+\.\d{2})',
        r'Total\s*:?\s*\$?(\d+\.\d{2})',
        r'AMOUNT\s*:?\s*\$?(\d+\.\d{2})',
        r'Grand Total\s*:?\s*\$?(\d+\.\d{2})',
    ]
    
    RECEIPT_ID_PATTERNS = [
        r'Receipt\s*#?\s*:?\s*([A-Z0-9]+)',
        r'Transaction\s*#?\s*:?\s*([A-Z0-9]+)',
        r'REF\s*#?\s*:?\s*([A-Z0-9]+)',
        r'Invoice\s*#?\s*:?\s*([A-Z0-9]+)',
    ]
    
    DATE_PATTERNS = [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}-\d{2}-\d{4})',
    ]
    
    TIME_PATTERNS = [
        r'(\d{1,2}:\d{2}:\d{2})',
        r'(\d{1,2}:\d{2}\s*[AP]M)',
    ]
    
    def parse_receipt(self, receipt_text: str) -> Dict:
        """
        Parse receipt text and extract key information
        
        Args:
            receipt_text: Raw receipt text
            
        Returns:
            Dictionary with parsed receipt data
        """
        try:
            parsed_data = {
                'raw_text': receipt_text,
                'total': self._extract_total(receipt_text),
                'receipt_id': self._extract_receipt_id(receipt_text),
                'date': self._extract_date(receipt_text),
                'time': self._extract_time(receipt_text),
                'items': self._extract_items(receipt_text),
                'items_count': 0,
                'parsed_at': datetime.utcnow()
            }
            
            # Count items
            if parsed_data['items']:
                parsed_data['items_count'] = len(parsed_data['items'])
            
            logger.info(f"Parsed receipt - Total: ${parsed_data['total']}, Items: {parsed_data['items_count']}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing receipt: {e}")
            return {
                'raw_text': receipt_text,
                'total': 0.0,
                'receipt_id': None,
                'error': str(e),
                'parsed_at': datetime.utcnow()
            }
    
    def _extract_total(self, text: str) -> float:
        """Extract total amount from receipt"""
        for pattern in self.TOTAL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return 0.0
    
    def _extract_receipt_id(self, text: str) -> Optional[str]:
        """Extract receipt ID from receipt"""
        for pattern in self.RECEIPT_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from receipt"""
        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_items(self, text: str) -> List[Dict]:
        """Extract individual items from receipt"""
        items = []
        
        # Common item line patterns
        item_patterns = [
            r'(\w+.*?)\s+(\d+\.\d{2})',  # Item name followed by price
            r'(\w+.*?)\s+\$(\d+\.\d{2})',  # Item name followed by $price
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
                
            for pattern in item_patterns:
                match = re.search(pattern, line)
                if match:
                    item_name = match.group(1).strip()
                    item_price = float(match.group(2))
                    
                    # Skip if it looks like a total line
                    if any(keyword in item_name.lower() for keyword in ['total', 'subtotal', 'tax', 'change']):
                        continue
                        
                    items.append({
                        'name': item_name,
                        'price': item_price,
                        'line': line
                    })
                    break
        
        return items
    
    def is_valid_receipt(self, receipt_text: str) -> bool:
        """Check if text appears to be a valid receipt"""
        if not receipt_text or len(receipt_text.strip()) < 20:
            return False
            
        # Check for receipt indicators
        receipt_indicators = [
            'total', 'receipt', 'thank you', 'transaction',
            'subtotal', 'tax', 'change', 'payment'
        ]
        
        text_lower = receipt_text.lower()
        indicators_found = sum(1 for indicator in receipt_indicators if indicator in text_lower)
        
        # Must have at least 2 receipt indicators and a valid total
        return indicators_found >= 2 and self._extract_total(receipt_text) > 0
