import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Lark Configuration
    LARK_APP_ID = os.getenv('LARK_APP_ID')
    LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
    LARK_BASE_TOKEN = os.getenv('LARK_BASE_TOKEN')
    LARK_TABLE_ID = os.getenv('LARK_TABLE_ID')
    
    # Gmail Configuration
    GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
    TARGET_EMAIL = os.getenv('TARGET_EMAIL')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Gmail API Scopes
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.modify']