import logging
import os
import sys
from datetime import datetime

def setup_logging():
    """Setup logging for production and development"""
    
    # Configure basic logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # In production, just use stdout
    if os.getenv('ENVIRONMENT') == 'production':
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    else:
        # Local development - file and console
        os.makedirs('logs', exist_ok=True)
        log_file = f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    # Quiet down some loggers
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")