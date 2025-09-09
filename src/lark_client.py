import requests
import logging
from datetime import datetime
from typing import Dict, Optional
from .config import Config

logger = logging.getLogger(__name__)

class LarkWebhookClient:
    """Simplified client that sends data to Lark Base webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_to_lark_base(self, data: Dict[str, str]) -> bool:
        """
        Send data to Lark Base via webhook
        
        Args:
            data: Dictionary containing the parsed email data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare the data for Lark Base
            webhook_data = {
                "timestamp": datetime.now().isoformat(),
                "event_name": data.get('Event Name', ''),
                "event_date": data.get('Event Date', ''),
                "event_time": data.get('Event Time', ''),
                "event_venue": data.get('Event Venue', ''),
                "event_url": data.get('Event URL', ''),
                "customer_name": data.get('Customer Name', ''),
                "customer_furigana": data.get('Customer Furigana', ''),
                "customer_email": data.get('Customer Email', ''),
                "customer_phone": data.get('Customer Phone', ''),
                "customer_age": data.get('Customer Age', ''),
                "monthly_rent": data.get('Monthly Rent', ''),
                "monthly_payment": data.get('Monthly Payment', ''),
                "postal_code": data.get('Postal Code', ''),
                "address": data.get('Address', ''),
            }
            
            # Remove empty fields
            webhook_data = {k: v for k, v in webhook_data.items() if v}
            
            logger.info(f"Sending data to Lark Base webhook: {len(webhook_data)} fields")
            logger.debug(f"Webhook data: {webhook_data}")
            
            # Send to Lark Base webhook
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Webhook response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Successfully sent data to Lark Base webhook")
                return True
            else:
                logger.error(f"Webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send data to webhook: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """Test webhook connection with sample data"""
        try:
            test_data = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "customer_name": "Test User",
                "customer_email": "test@example.com"
            }
            
            response = requests.post(
                self.webhook_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Webhook test failed: {str(e)}")
            return False