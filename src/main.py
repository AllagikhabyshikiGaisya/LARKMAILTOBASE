import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    logger.info("FastAPI imported successfully")
except ImportError as e:
    logger.error(f"Failed to import FastAPI: {e}")
    sys.exit(1)

# Simple imports without complex dependencies
try:
    from dotenv import load_dotenv
    import requests
    logger.info("Basic dependencies imported successfully")
except ImportError as e:
    logger.error(f"Failed to import basic dependencies: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Simple configuration
class SimpleConfig:
    LARK_WEBHOOK_URL = os.getenv('LARK_WEBHOOK_URL', '').strip()
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip()
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook/lark-mail').strip()
    TEST_EMAIL = os.getenv('TEST_EMAIL', 'utosabu.adhikari@allagi.jp').strip()
    
    @classmethod
    def is_valid(cls):
        return bool(cls.LARK_WEBHOOK_URL)

# Simple Email Parser
class SimpleEmailParser:
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
        import re
        extracted_data = {'timestamp': datetime.now().isoformat()}
        
        for field_name, pattern in self.patterns.items():
            try:
                match = re.search(pattern, email_content, re.MULTILINE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    value = re.sub(r'\s+', ' ', value).strip()
                    extracted_data[field_name] = value
                else:
                    extracted_data[field_name] = ""
            except Exception as e:
                logger.error(f"Error extracting {field_name}: {e}")
                extracted_data[field_name] = ""
        
        # Handle age
        if extracted_data.get('Customer Age'):
            age_match = re.search(r'(\d+)', extracted_data['Customer Age'])
            if age_match:
                extracted_data['Customer Age'] = int(age_match.group(1))
        
        return extracted_data
    
    def validate_required_fields(self, data: Dict[str, Any]) -> bool:
        required_fields = ['Customer Name', 'Customer Email', 'Customer Phone']
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == "":
                return False
        return True

# Simple Webhook Client
class SimpleWebhookClient:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_to_lark_base(self, data: Dict[str, Any]) -> bool:
        try:
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
            
            response = requests.post(
                self.webhook_url,
                json=webhook_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            logger.info(f"Webhook response: {response.status_code}")
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            response = requests.post(
                self.webhook_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

# Initialize FastAPI
app = FastAPI(title="Lark Mail Automation", version="1.0.0")

# Global components
email_parser = SimpleEmailParser()
webhook_client = None

@app.on_event("startup")
async def startup_event():
    global webhook_client
    logger.info("Starting Lark Mail Automation Service...")
    
    if SimpleConfig.is_valid():
        webhook_client = SimpleWebhookClient(SimpleConfig.LARK_WEBHOOK_URL)
        logger.info("Webhook client initialized")
        
        try:
            if webhook_client.test_connection():
                logger.info("Webhook test successful")
            else:
                logger.warning("Webhook test failed - continuing anyway")
        except Exception as e:
            logger.warning(f"Webhook test error: {e}")
    else:
        logger.error("Invalid configuration - webhook not initialized")
    
    logger.info("Startup complete")

@app.get("/")
async def root():
    return {
        "service": "Lark Mail to Base Automation",
        "status": "running",
        "version": "1.0.0",
        "environment": SimpleConfig.ENVIRONMENT,
        "webhook_configured": bool(webhook_client),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    webhook_ok = False
    if webhook_client:
        try:
            webhook_ok = webhook_client.test_connection()
        except:
            pass
    
    return {
        "status": "healthy" if webhook_ok else "degraded",
        "webhook_connection": webhook_ok,
        "config_valid": SimpleConfig.is_valid(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhook/lark-mail")
async def handle_webhook(request: Request):
    if not webhook_client:
        raise HTTPException(status_code=503, detail="Webhook client not initialized")
    
    try:
        body = await request.body()
        if not body:
            return {"status": "error", "message": "Empty body"}
        
        webhook_data = json.loads(body)
        
        # Handle verification
        if webhook_data.get('type') == 'url_verification':
            return {"challenge": webhook_data.get('challenge', '')}
        
        # Handle mail events
        if webhook_data.get('type') != 'event_callback':
            return {"status": "ignored", "message": "Not a mail event"}
        
        event_data = webhook_data.get('event', {})
        email_content = event_data.get('content', '') or event_data.get('mail_content', '')
        
        if not email_content:
            return {"status": "error", "message": "No email content"}
        
        # Parse email
        extracted_data = email_parser.parse_email(email_content)
        
        if not email_parser.validate_required_fields(extracted_data):
            return {"status": "error", "message": "Missing required fields"}
        
        # Send to webhook
        success = webhook_client.send_to_lark_base(extracted_data)
        
        if success:
            return {
                "status": "success",
                "message": "Email processed successfully",
                "customer_name": extracted_data.get('Customer Name', 'Unknown')
            }
        else:
            return {"status": "error", "message": "Failed to send to Lark Base"}
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/parse")
async def test_parse(request: Request):
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        if not email_content:
            raise HTTPException(status_code=400, detail="No content")
        
        extracted_data = email_parser.parse_email(email_content)
        
        return {
            "status": "success",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/full")
async def test_full(request: Request):
    if not webhook_client:
        raise HTTPException(status_code=503, detail="Webhook not configured")
    
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        extracted_data = email_parser.parse_email(email_content)
        
        if not email_parser.validate_required_fields(extracted_data):
            return {
                "status": "validation_failed",
                "extracted_data": extracted_data
            }
        
        success = webhook_client.send_to_lark_base(extracted_data)
        
        return {
            "status": "success" if success else "error",
            "message": "Test completed",
            "extracted_data": extracted_data,
            "sent_to_lark": success
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)