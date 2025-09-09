import logging
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, Any

# Simple logging setup for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import Flask (pure Python, no compilation)
try:
    from flask import Flask, request, jsonify
    import requests
    from dotenv import load_dotenv
    logger.info("All dependencies imported successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Simple Configuration
class Config:
    LARK_WEBHOOK_URL = os.getenv('LARK_WEBHOOK_URL', '').strip()
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip()
    TEST_EMAIL = os.getenv('TEST_EMAIL', 'utosabu.adhikari@allagi.jp').strip()
    
    @classmethod
    def is_valid(cls):
        return bool(cls.LARK_WEBHOOK_URL)

# Email Parser Class
class EmailParser:
    def __init__(self):
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
    
    def parse_email(self, email_content: str) -> Dict[str, Any]:
        extracted_data = {'timestamp': datetime.now().isoformat()}
        
        for field_name, pattern in self.patterns.items():
            try:
                match = re.search(pattern, email_content, re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    value = re.sub(r'\s+', ' ', value).strip()
                    extracted_data[field_name] = value
                    logger.debug(f"Extracted {field_name}: {value}")
                else:
                    extracted_data[field_name] = ""
            except Exception as e:
                logger.error(f"Error extracting {field_name}: {e}")
                extracted_data[field_name] = ""
        
        # Special handling for age
        if extracted_data.get('Customer Age'):
            age_match = re.search(r'(\d+)', extracted_data['Customer Age'])
            if age_match:
                extracted_data['Customer Age'] = int(age_match.group(1))
        
        logger.info(f"Email parsing completed. Extracted {len(extracted_data)} fields.")
        return extracted_data
    
    def validate_required_fields(self, data: Dict[str, Any]) -> bool:
        required_fields = ['Customer Name', 'Customer Email', 'Customer Phone']
        
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == "":
                logger.error(f"Missing required field: {field}")
                return False
        
        return True

# Webhook Client Class
class WebhookClient:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_to_lark_base(self, data: Dict[str, Any]) -> bool:
        try:
            # Prepare data for Lark Base
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
            
            logger.info(f"Sending {len(webhook_data)} fields to Lark Base webhook")
            
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                headers={'Content-Type': 'application/json'},
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
        try:
            test_data = {
                "test": True,
                "timestamp": datetime.now().isoformat(),
                "customer_name": "Test Connection"
            }
            
            response = requests.post(
                self.webhook_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Webhook test failed: {str(e)}")
            return False

# Initialize Flask app
app = Flask(__name__)

# Initialize components
email_parser = EmailParser()
webhook_client = None

# Initialize webhook client if config is valid
if Config.is_valid():
    webhook_client = WebhookClient(Config.LARK_WEBHOOK_URL)
    logger.info("Webhook client initialized")
else:
    logger.warning("No valid webhook URL configured")

@app.route('/', methods=['GET'])
def root():
    """Health check and service info"""
    return jsonify({
        "service": "Lark Mail to Base Automation",
        "status": "running",
        "version": "1.0.0",
        "framework": "Flask",
        "environment": Config.ENVIRONMENT,
        "webhook_configured": bool(webhook_client),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Detailed health check"""
    webhook_ok = False
    webhook_error = None
    
    if webhook_client:
        try:
            webhook_ok = webhook_client.test_connection()
        except Exception as e:
            webhook_error = str(e)
    
    return jsonify({
        "status": "healthy" if webhook_ok else "degraded",
        "webhook_connection": webhook_ok,
        "webhook_error": webhook_error,
        "config_valid": Config.is_valid(),
        "environment": Config.ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook/lark-mail', methods=['POST'])
def handle_lark_mail_webhook():
    """Handle incoming webhook from Lark Mail"""
    if not webhook_client:
        return jsonify({"error": "Webhook client not initialized"}), 503
    
    try:
        logger.info("Received webhook request from Lark Mail")
        
        # Get JSON data
        webhook_data = request.get_json()
        if not webhook_data:
            logger.warning("No JSON data received")
            return jsonify({"error": "No JSON data"}), 400
        
        logger.info(f"Webhook data keys: {list(webhook_data.keys())}")
        
        # Handle webhook verification
        if webhook_data.get('type') == 'url_verification':
            challenge = webhook_data.get('challenge', '')
            logger.info("Webhook verification request received")
            return jsonify({"challenge": challenge})
        
        # Handle mail events
        if webhook_data.get('type') != 'event_callback':
            logger.info(f"Ignoring webhook type: {webhook_data.get('type')}")
            return jsonify({"status": "ignored", "message": "Not a mail event"})
        
        # Extract email content
        event_data = webhook_data.get('event', {})
        email_content = event_data.get('content', '') or event_data.get('mail_content', '')
        sender = event_data.get('sender', '') or event_data.get('from', '')
        
        if not email_content:
            logger.error("No email content found in webhook")
            return jsonify({"error": "No email content"}), 400
        
        logger.info(f"Processing email from: {sender}")
        logger.info(f"Email content length: {len(email_content)} characters")
        
        # Parse email content
        extracted_data = email_parser.parse_email(email_content)
        
        # Validate required fields
        if not email_parser.validate_required_fields(extracted_data):
            logger.error("Email validation failed - missing required fields")
            return jsonify({
                "error": "Missing required fields",
                "extracted_data": extracted_data
            }), 400
        
        # Send data to Lark Base webhook
        success = webhook_client.send_to_lark_base(extracted_data)
        
        if success:
            customer_name = extracted_data.get('Customer Name', 'Unknown')
            logger.info(f"Successfully processed email for customer: {customer_name}")
            return jsonify({
                "status": "success",
                "message": "Email processed and data sent to Lark Base successfully",
                "customer_name": customer_name,
                "fields_extracted": len(extracted_data)
            })
        else:
            logger.error("Failed to send data to Lark Base webhook")
            return jsonify({
                "error": "Failed to send data to Lark Base webhook"
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/test/parse', methods=['POST'])
def test_parse_email():
    """Test endpoint for parsing email content"""
    try:
        email_content = request.get_data(as_text=True)
        
        if not email_content:
            return jsonify({"error": "No email content provided"}), 400
        
        logger.info("Testing email parsing...")
        extracted_data = email_parser.parse_email(email_content)
        
        return jsonify({
            "status": "success",
            "message": "Email parsed successfully",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data)
        })
        
    except Exception as e:
        logger.error(f"Error in test parse: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test/full', methods=['POST'])
def test_full_workflow():
    """Test complete workflow: parse email and send to Lark Base"""
    if not webhook_client:
        return jsonify({"error": "Webhook client not initialized"}), 503
    
    try:
        email_content = request.get_data(as_text=True)
        
        if not email_content:
            return jsonify({"error": "No email content provided"}), 400
        
        logger.info("Testing complete workflow...")
        
        # Parse email
        extracted_data = email_parser.parse_email(email_content)
        
        # Validate
        if not email_parser.validate_required_fields(extracted_data):
            return jsonify({
                "status": "validation_failed",
                "message": "Missing required fields",
                "extracted_data": extracted_data
            }), 400
        
        # Send to Lark Base
        success = webhook_client.send_to_lark_base(extracted_data)
        
        return jsonify({
            "status": "success" if success else "error",
            "message": "Complete workflow tested successfully" if success else "Failed to send to Lark Base",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data),
            "sent_to_lark": success
        })
        
    except Exception as e:
        logger.error(f"Error in full workflow test: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)