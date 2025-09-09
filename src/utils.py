import logging
import os
import sys
from datetime import datetime
from .config import Config

def setup_logging():
    """Setup logging configuration for both local and production"""
    
    # Create logs directory if running locally
    if not Config.is_production():
        os.makedirs('logs', exist_ok=True)
        log_filename = f"logs/lark_mail_automation_{datetime.now().strftime('%Y%m%d')}.log"
        handlers = [
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    else:
        # In production, just use stdout (Render will capture this)
        handlers = [logging.StreamHandler(sys.stdout)]
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Set specific loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    
    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized for environment: {Config.ENVIRONMENT}")