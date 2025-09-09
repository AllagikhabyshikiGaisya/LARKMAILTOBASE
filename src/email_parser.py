import re
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class EmailParser:
    """Parse Japanese event registration emails and extract structured data"""
    
    def __init__(self):
        # Field mapping to match your Lark Base table exactly
        self.patterns = {
            'Event Name': r'イベント名\s*:\s*(.+?)(?=\n|開催日)',
            'Event Date': r'開催日\s*:\s*(.+?)(?=\n|時間)',
            'Event Time': r'時間\s*:\s*(.+?)(?=\n|会場)',
            'Event Venue': r'会場\s*:\s*(.+?)(?=\n|URL)',
            'Event URL': r'URL\s*:\s*(.+?)(?=\n|=)',
            'Customer Name': r'お名前\s*:\s*(.+?)(?=\n|フリガナ)',
            'Customer Furigana': r'フリガナ\s*:\s*(.+?)(?=\n|メールアドレス)',
            'Customer Email': r'メールアドレス\s*:\s*(.+?)(?=\n|電話番号)',
            'Customer Phone': r'電話番号\s*:\s*(.+?)(?=\n|年齢)',
            'Customer Age': r'年齢\s*:\s*(.+?)(?=\n|毎月の家賃)',
            'Monthly Rent': r'毎月の家賃\s*:\s*(.+?)(?=\n|月々の返済額)',
            'Monthly Payment': r'月々の返済額\s*:\s*(.+?)(?=\n|郵便番号)',
            'Postal Code': r'郵便番号\s*:\s*(.+?)(?=\n|ご住所)',
            'Address': r'ご住所\s*:\s*(.+?)(?=\n|ご意見)',
        }
    
    def parse_email(self, email_content: str) -> Dict[str, str]:
        """
        Parse email content and extract structured data
        
        Args:
            email_content: Raw email content in Japanese
            
        Returns:
            Dictionary with extracted data matching Lark Base fields
        """
        logger.info("Starting email parsing...")
        
        extracted_data = {}
        
        # Add timestamp
        extracted_data['timestamp'] = datetime.now().isoformat()
        
        # Extract each field using regex patterns
        for field_name, pattern in self.patterns.items():
            try:
                match = re.search(pattern, email_content, re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = self._clean_text(value)
                    extracted_data[field_name] = value
                    logger.debug(f"Extracted {field_name}: {value}")
                else:
                    extracted_data[field_name] = ""
                    logger.warning(f"Could not extract {field_name}")
            except Exception as e:
                logger.error(f"Error extracting {field_name}: {str(e)}")
                extracted_data[field_name] = ""
        
        # Special handling for age (extract number only)
        if extracted_data.get('Customer Age'):
            age_match = re.search(r'(\d+)', extracted_data['Customer Age'])
            if age_match:
                extracted_data['Customer Age'] = int(age_match.group(1))
        
        logger.info(f"Email parsing completed. Extracted {len(extracted_data)} fields.")
        return extracted_data
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and newlines"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def validate_required_fields(self, data: Dict[str, str]) -> bool:
        """
        Validate that required fields are present
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            True if all required fields are present
        """
        required_fields = [
            'Customer Name', 'Customer Email', 'Customer Phone'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == "":
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        
        return True