import os
from dotenv import load_dotenv

def check_env_config():
    """Check if .env configuration is properly loaded"""
    print("=== Checking Environment Configuration ===")
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✓ .env file found")
        
        # Read and display .env contents (without secrets)
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        print("\n.env file contents:")
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'SECRET' in key:
                        print(f"  {key}=***hidden***")
                    else:
                        print(f"  {key}={value}")
        
        # Check individual environment variables
        print("\n=== Environment Variables Check ===")
        
        required_vars = [
            'LARK_APP_ID',
            'LARK_APP_SECRET', 
            'LARK_BASE_ID',
            'LARK_TABLE_ID'
        ]
        
        all_present = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if 'SECRET' in var:
                    print(f"✓ {var}: ***hidden*** (length: {len(value)})")
                else:
                    print(f"✓ {var}: {value}")
            else:
                print(f"✗ {var}: NOT SET")
                all_present = False
        
        if all_present:
            print("\n✅ All required environment variables are set!")
            return True
        else:
            print("\n❌ Some environment variables are missing!")
            return False
    else:
        print("✗ .env file not found!")
        print("\nPlease create a .env file with the following format:")
        print("""
# Lark App Configuration
LARK_APP_ID=your_app_id_here
LARK_APP_SECRET=your_app_secret_here

# Lark Base Configuration  
LARK_BASE_ID=your_base_id_here
LARK_TABLE_ID=your_table_id_here

# Server Configuration
SERVER_PORT=8000
WEBHOOK_PATH=/webhook/lark-mail

# Test Email
TEST_EMAIL=utosabu.adhikari@allagi.jp
        """)
        return False

if __name__ == "__main__":
    check_env_config()