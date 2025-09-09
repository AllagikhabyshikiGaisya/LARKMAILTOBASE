import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
except ImportError as e:
    print(f"Failed to import FastAPI: {e}")
    sys.exit(1)

try:
    from src.config import Config
    from src.email_parser import EmailParser
    from src.lark_client import LarkWebhookClient
    from src.utils import setup_logging
except ImportError as e:
    print(f"Failed to import local modules: {e}")
    # Try alternative import method
    try:
        from config import Config
        from email_parser import EmailParser
        from lark_client import LarkWebhookClient
        from utils import setup_logging
    except ImportError as e2:
        print(f"Failed alternative import: {e2}")
        sys.exit(1)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Lark Mail to Base Automation",
    version="1.0.0",
    description="Automatically process Japanese event registration emails and send to Lark Base"
)

# Global variables
email_parser = None
lark_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global email_parser, lark_client
    
    try:
        logger.info("Starting Lark Mail Automation Service...")
        
        # Initialize components
        email_parser = EmailParser()
        logger.info("Email parser initialized")
        
        # Validate configuration
        try:
            Config.validate()
            logger.info("Configuration validated successfully")
        except Exception as config_error:
            logger.error(f"Configuration validation failed: {config_error}")
            logger.info("App will start but webhook functionality may not work")
        
        # Initialize webhook client if config is valid
        if hasattr(Config, 'LARK_WEBHOOK_URL') and Config.LARK_WEBHOOK_URL:
            try:
                lark_client = LarkWebhookClient(Config.LARK_WEBHOOK_URL)
                logger.info("Webhook client initialized")
                
                # Test connection (don't fail startup if this fails)
                try:
                    if lark_client.test_connection():
                        logger.info("Webhook connection test successful")
                    else:
                        logger.warning("Webhook connection test failed - continuing anyway")
                except Exception as test_error:
                    logger.warning(f"Webhook test error: {test_error} - continuing anyway")
            except Exception as webhook_error:
                logger.error(f"Failed to initialize webhook client: {webhook_error}")
        else:
            logger.warning("No webhook URL configured")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Don't fail startup completely - let the health endpoint show the issue

@app.get("/")
async def root():
    """Health check and service info"""
    try:
        return {
            "service": "Lark Mail to Base Automation",
            "status": "running",
            "version": "1.0.0",
            "environment": getattr(Config, 'ENVIRONMENT', 'unknown'),
            "webhook_configured": bool(lark_client),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "error"}
        )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "email_parser": bool(email_parser),
                "webhook_client": bool(lark_client),
                "config_valid": False
            }
        }
        
        # Check configuration
        try:
            Config.validate()
            health_data["components"]["config_valid"] = True
        except Exception as e:
            health_data["components"]["config_error"] = str(e)
        
        # Check webhook if available
        if lark_client:
            try:
                webhook_ok = lark_client.test_connection()
                health_data["components"]["webhook_connection"] = webhook_ok
            except Exception as e:
                health_data["components"]["webhook_error"] = str(e)
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/webhook/lark-mail")
async def handle_lark_mail_webhook(request: Request):
    """Handle incoming webhook from Lark Mail"""
    if not email_parser or not lark_client:
        raise HTTPException(status_code=503, detail="Service not properly initialized")
    
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
            logger.info(f"Webhook data received with keys: {list(webhook_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook JSON: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Handle webhook verification
        if webhook_data.get('type') == 'url_verification':
            challenge = webhook_data.get('challenge', '')
            logger.info("Webhook verification request received")
            return {"challenge": challenge}
        
        # Handle mail events
        if webhook_data.get('type') != 'event_callback':
            logger.info(f"Ignoring webhook type: {webhook_data.get('type')}")
            return {"status": "ignored", "message": "Not a mail event"}
        
        # Extract email content
        event_data = webhook_data.get('event', {})
        email_content = event_data.get('content', '') or event_data.get('mail_content', '')
        sender = event_data.get('sender', '') or event_data.get('from', '')
        
        if not email_content:
            logger.error("No email content found in webhook")
            return {"status": "error", "message": "No email content"}
        
        logger.info(f"Processing email from: {sender}")
        
        # Parse email
        extracted_data = email_parser.parse_email(email_content)
        
        # Validate
        if not email_parser.validate_required_fields(extracted_data):
            logger.error("Email validation failed")
            return {"status": "error", "message": "Missing required fields"}
        
        # Send to Lark Base
        success = lark_client.send_to_lark_base(extracted_data)
        
        if success:
            customer_name = extracted_data.get('Customer Name', 'Unknown')
            logger.info(f"Successfully processed email for: {customer_name}")
            return {
                "status": "success",
                "message": "Email processed successfully",
                "customer_name": customer_name
            }
        else:
            logger.error("Failed to send data to Lark Base")
            return {"status": "error", "message": "Failed to send to Lark Base"}
            
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/parse")
async def test_parse(request: Request):
    """Test email parsing"""
    if not email_parser:
        raise HTTPException(status_code=503, detail="Email parser not initialized")
    
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        if not email_content:
            raise HTTPException(status_code=400, detail="No email content")
        
        extracted_data = email_parser.parse_email(email_content)
        
        return {
            "status": "success",
            "extracted_data": extracted_data,
            "field_count": len(extracted_data)
        }
        
    except Exception as e:
        logger.error(f"Test parse error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/full")
async def test_full_workflow(request: Request):
    """Test complete workflow"""
    if not email_parser or not lark_client:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    try:
        body = await request.body()
        email_content = body.decode('utf-8')
        
        if not email_content:
            raise HTTPException(status_code=400, detail="No email content")
        
        # Parse
        extracted_data = email_parser.parse_email(email_content)
        
        # Validate
        valid = email_parser.validate_required_fields(extracted_data)
        if not valid:
            return {
                "status": "validation_failed",
                "extracted_data": extracted_data,
                "message": "Missing required fields"
            }
        
        # Send to Lark Base
        success = lark_client.send_to_lark_base(extracted_data)
        
        return {
            "status": "success" if success else "error",
            "message": "Full workflow completed" if success else "Failed to send to Lark Base",
            "extracted_data": extracted_data,
            "sent_to_lark": success
        }
        
    except Exception as e:
        logger.error(f"Full workflow test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)