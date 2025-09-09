import os
from dotenv import load_dotenv

# Load environment variables (works locally and on Render)
load_dotenv()

class Config:
    # Lark Webhook Configuration
    LARK_WEBHOOK_URL = os.getenv('LARK_WEBHOOK_URL')
    
    # Server Configuration
    SERVER_PORT = int(os.getenv('PORT', os.getenv('SERVER_PORT', 8000)))  # Render uses PORT
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook/lark-mail')
    
    # Test Configuration
    TEST_EMAIL = os.getenv('TEST_EMAIL', 'utosabu.adhikari@allagi.jp')
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_configs = ['LARK_WEBHOOK_URL']
        
        missing_configs = []
        for config in required_configs:
            value = getattr(cls, config)
            if not value or value.strip() == '':
                missing_configs.append(config)
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
    
    @classmethod
    def is_production(cls):
        """Check if running in production"""
        return cls.ENVIRONMENT.lower() == 'production'
    
    @classmethod
    def get_base_url(cls):
        """Get base URL for the application"""
        if cls.is_production():
            return os.getenv('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')
        else:
            return f'http://localhost:{cls.SERVER_PORT}'