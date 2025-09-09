import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Lark Configuration
    LARK_WEBHOOK_URL = os.getenv('LARK_WEBHOOK_URL', '').strip()
    
    # Server Configuration  
    SERVER_PORT = int(os.getenv('PORT', os.getenv('SERVER_PORT', 8000)))
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook/lark-mail').strip()
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip()
    TEST_EMAIL = os.getenv('TEST_EMAIL', 'utosabu.adhikari@allagi.jp').strip()
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.LARK_WEBHOOK_URL:
            errors.append('LARK_WEBHOOK_URL is required')
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    @classmethod 
    def is_production(cls):
        return cls.ENVIRONMENT.lower() == 'production'