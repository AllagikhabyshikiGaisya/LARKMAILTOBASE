import requests
import json
import time

def test_server_endpoints():
    """Test all server endpoints"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Server Endpoints ===")
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ Server is running")
            print(f"Response: {response.json()}")
        else:
            print(f"✗ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to server: {str(e)}")
        print("Make sure the server is running with: python run.py")
        return False
    
    # Test 2: Detailed health check
    print("\n2. Testing detailed health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Health check response: {health_data}")
            if health_data.get('lark_connection'):
                print("✓ Lark connection is working")
            else:
                print("✗ Lark connection failed")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {str(e)}")
    
    # Test 3: Email parsing endpoint
    print("\n3. Testing email parsing endpoint...")
    try:
        # Read sample email
        with open('test_sample_email.txt', 'r', encoding='utf-8') as f:
            email_content = f.read()
        
        response = requests.post(
            f"{base_url}/test/parse-email",
            data=email_content.encode('utf-8'),
            headers={'Content-Type': 'text/plain; charset=utf-8'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Email parsing endpoint works")
            print(f"Extracted {result.get('field_count', 0)} fields")
            
            # Show some extracted data
            extracted = result.get('extracted_data', {})
            print("\nSample extracted data:")
            for key in ['Customer Name', 'Customer Email', 'Event Name']:
                if key in extracted and extracted[key]:
                    print(f"  {key}: {extracted[key]}")
                    
            return True
        else:
            print(f"✗ Email parsing failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Email parsing test error: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_server_endpoints()
    if result:
        print("\n✅ ALL ENDPOINT TESTS PASSED!")
    else:
        print("\n❌ ENDPOINT TESTS FAILED!")