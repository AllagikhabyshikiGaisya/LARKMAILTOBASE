import schedule
import time
import requests
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_emails():
    """Automatically process emails every 15 minutes"""
    try:
        # Get the base URL from environment or use localhost for testing
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        
        logger.info(f"🔄 Starting automatic email processing...")
        response = requests.get(f'{base_url}/process-emails', timeout=60)
        
        logger.info(f"📊 Processing status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            processed_count = result.get('processed_emails', 0)
            success_count = result.get('successful_stores', 0)
            
            logger.info(f"✅ SUCCESS: Processed {processed_count} emails, stored {success_count} successfully")
            
            # Log details of processed emails
            if result.get('results'):
                for email_result in result['results']:
                    customer_name = email_result.get('customer_name', 'Unknown')
                    stored = '✅' if email_result.get('stored_successfully') else '❌'
                    logger.info(f"  {stored} Customer: {customer_name}")
        else:
            logger.error(f"❌ Processing failed with status {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Request timed out - email processing took too long")
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Connection error - unable to reach email processing service")
    except Exception as e:
        logger.error(f"💥 Unexpected error during email processing: {str(e)}")

def health_check():
    """Check system health every hour"""
    try:
        base_url = os.getenv('BASE_URL', 'http://localhost:5000')
        response = requests.get(f'{base_url}/health', timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            gmail_status = result.get('gmail', 'unknown')
            lark_status = result.get('lark', 'unknown')
            
            logger.info(f"❤️  Health check: {status} | Gmail: {gmail_status} | Lark: {lark_status}")
            
            if status != 'healthy':
                logger.warning(f"⚠️  System not healthy: {result}")
        else:
            logger.warning(f"⚠️  Health check failed: {response.status_code}")
            
    except Exception as e:
        logger.error(f"💔 Health check error: {str(e)}")

def main():
    logger.info("🚀 Email Processing Scheduler Started")
    logger.info("📅 Schedule: Process emails every 15 minutes")
    logger.info("❤️  Schedule: Health check every hour")
    logger.info("🛑 Press Ctrl+C to stop")
    
    # Schedule tasks
    schedule.every(15).minutes.do(process_emails)  # Process emails every 15 minutes
    schedule.every(1).hours.do(health_check)      # Health check every hour
    
    # Run initial health check
    health_check()
    
    # Main scheduling loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler crashed: {str(e)}")
        # Wait before potentially restarting
        time.sleep(300)  # Wait 5 minutes before exit

if __name__ == "__main__":
    main()