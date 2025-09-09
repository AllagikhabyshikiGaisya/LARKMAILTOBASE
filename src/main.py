import logging
import json
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from .config import Config
from .email_parser import EmailParser
from .lark_client import LarkWebhookClient
from .utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Lark Mail to Base Automation",
    version="1.0.0",
    description="Automatically process Japanese event registration emails and send to Lark Base"
)

# Initialize components
email_parser = EmailParser()
lark_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global lark_client
    try:
        logger.info("Starting Lark Mail Automation Service...")
        logger.info(f"Environment: {Config.ENVIRONMENT}")
        logger.info(f"Server Port: {Config.SERVER_PORT}")
        logger.info(f"Webhook Path: {Config.WEBHOOK_PATH}")
        
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize webhook client
        lark_client = LarkWebhookClient(Config.LARK_WEBHOOK_URL)
        
        # Test webhook connection (only log warning if fails, don't crash)
        try:
            if lark_client.test_connection():
                logger.info("Lark webhook connection test successful")
            else:
                logger.warning("Lark webhook connection test failed - but continuing startup")
        except Exception as e:
            logger.warning(f"Webhook test failed: {str(e)} - but continuing startup")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

@app.get("/")
async def root():
    """Health check and service info"""
    return {
        "service": "Lark Mail to Base Automation",
        "status": "running",
        "version": "1.0.0",
        "environment": Config.ENVIRONMENT,
        "webhook_path": Config.WEBHOOK_PATH,
        "timestamp": datetime.now().isoformat(),
        "base_url": Config.get_base_url()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        webhook_connected = False
        webhook_error = None
        
        if lark_client:
            try:
                webhook_connected = lark_client.test_connection()
            except Exception as e:
                webhook_error = str(e)
        
        return {
            "status": "healthy" if webhook_connected else "degraded",
            "webhook_connection": webhook_connected,
            "webhook_error": webhook_error,
            "environment": Config.ENVIRONMENT,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post(Config.WEBHOOK_PATH)
async def handle_lark_mail_webhook(request: Request):
    """Handle incoming webhook from Lark Mail"""
    try:
        logger.info("Received webhook request from Lark Mail")
        
        # Get request body
        body = await request.body()
        if not body:
            logger.warning("Received empty webhook body")
            return {"status": "error", "message": "Empty request body"}
        
        # Parse JSON data
        try:
            webhook_data = json.loads(body)
            logger.debug(f"Webhook data keys: {list(webhook_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook JSON: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Handle different webhook types
        webhook_type = webhook_data.get('type', 'unknown')
        logger.info(f"Webhook type: {webhook_type}")
        
        # For mail received events
        if webhook_type == 'url_verification':
            # Lark webhook verification
            challenge = webhook_data.get('challenge', '')
            logger.info("Webhook verification request received")
            return {"challenge": challenge}
        
        if webhook_type != 'event_callback':
            logger.info(f"Ignoring webhook type: {webhook_type}")
            return {"status": "ignored", "message": f"Webhook type {webhook_type} not handled"}
        
        # Extract email content from event
        event_data = webhook_data.get('event', {})
        email_content = event_data.get('content', '') or event_data.get('mail_content', '')
        sender_email = event_data.get('sender_email', '') or event_data.get('from', '')
        
        if not email_content:
            logger.error("No email content found in webhook")
            logger.debug(f"Event data: {event_data}")
            raise HTTPException(status_code=400, detail="No email content found")
        
        logger.info(f"Processing email from: {sender_email}")
        logger.info(f"Email content length: {len(email_content)} characters")
        
        # Parse email content
        extracted_data = email_parser.parse_email(email_content)
        logger.info(f"Extracted {len(extracted_data)} fields from email")
        
        # Validate required fields
        if not email_parser.validate_required_fields(extracted_data):
            logger.error("Email validation failed - missing required fields")
            return {
                "status": "error", 
                "message": "Missing required fields in email"
            }
        
        # Send data to Lark Base webhook
        success = lark_client.send_to_lark_base(extracted_data)
        
        if success:
            customer_name = extracted_data.get('Customer Name', 'Unknown')
            logger.info(f"Successfully processed email for customer: {customer_name}")
            return {
                "status": "success",
                "message": "Email processed and data sent to Lark Base successfully",
                "customer_name": customer_name,
                "fields_extracted": len(extracted_data)
            }
        else:
            logger.error("Failed to send data to Lark Base webhook")
            return {
                "status": "error",
                "message": "Failed to send data to Lark Base webhook"
            }
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/test/parse-email")
async def test_parse_email(request: Request):
    """Test endpoint for parsing email content"""
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        if not email_content:
            raise HTTPException(status_code=400, detail="No email content provided")
        
        logger.info("Testing email parsing...")
        extracted_data = email_parser.parse_email(email_content)
        
        return {
            "status": "success",
            "message": "Email parsed successfully",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data)
        }
        
    except Exception as e:
        logger.error(f"Error in test parse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/full-workflow")
async def test_full_workflow(request: Request):
    """Test complete workflow: parse email and send to Lark Base"""
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        if not email_content:
            raise HTTPException(status_code=400, detail="No email content provided")
        
        logger.info("Testing complete workflow...")
        
        # Parse email
        extracted_data = email_parser.parse_email(email_content)
        
        # Validate
        if not email_parser.validate_required_fields(extracted_data):
            return {
                "status": "error",
                "message": "Validation failed - missing required fields",
                "extracted_data": extracted_data
            }
        
        # Send to Lark Base
        success = lark_client.send_to_lark_base(extracted_data)
        
        return {
            "status": "success" if success else "error",
            "message": "Complete workflow tested successfully" if success else "Failed to send to Lark Base",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data),
            "sent_to_lark": success
        }
        
    except Exception as e:
        logger.error(f"Error in full workflow test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add CORS middleware for development
if not Config.is_production():
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )