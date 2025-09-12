import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
import time

class LarkClient:
    def __init__(self, app_id: str, app_secret: str, base_token: str, table_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_token = base_token
        self.table_id = table_id
        self.base_url = "https://open.larksuite.com/open-apis"
        self.access_token = None
        self.token_expiry = 0
        
    def get_tenant_access_token(self) -> str:
        """Get or refresh tenant access token"""
        current_time = time.time()
        
        # Check if token is still valid (with 5 minute buffer)
        if self.access_token and current_time < (self.token_expiry - 300):
            return self.access_token
            
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result["tenant_access_token"]
                # Token expires in 2 hours (7200 seconds)
                self.token_expiry = current_time + result.get("expire", 7200)
                print(f"✓ Tenant access token obtained successfully")
                return self.access_token
            else:
                raise Exception(f"Failed to get token: {result.get('msg')}")
                
        except Exception as e:
            print(f"✗ Error getting tenant access token: {e}")
            raise
            
    def create_record(self, record_data: Dict[str, Any]) -> Optional[str]:
        """Create a new record in Lark Base table"""
        token = self.get_tenant_access_token()
        
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Format the fields for Lark Base
        fields = {
            "email_id": record_data.get("email_id", ""),
            "sender": record_data.get("sender", ""),
            "recipient": record_data.get("recipient", ""),
            "subject": record_data.get("subject", ""),
            "body": record_data.get("body", ""),
            "received_date": record_data.get("received_date", ""),
            "attachments": record_data.get("attachments", ""),
            "processed_at": datetime.now().isoformat()
        }
        
        data = {"fields": fields}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                record_id = result["data"]["record"]["record_id"]
                print(f"✓ Record created successfully: {record_id}")
                return record_id
            else:
                print(f"✗ Failed to create record: {result.get('msg')}")
                return None
                
        except Exception as e:
            print(f"✗ Error creating record: {e}")
            return None
            
    def check_duplicate(self, email_id: str) -> bool:
        """Check if email already exists in the base"""
        token = self.get_tenant_access_token()
        
        url = f"{self.base_url}/bitable/v1/apps/{self.base_token}/tables/{self.table_id}/records/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Search for existing email_id
        data = {
            "filter": {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": "email_id",
                        "operator": "is",
                        "value": [email_id]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                has_duplicate = result["data"]["total"] > 0
                if has_duplicate:
                    print(f"⚠ Email {email_id} already exists in base")
                return has_duplicate
            else:
                print(f"✗ Error checking duplicate: {result.get('msg')}")
                return False
                
        except Exception as e:
            print(f"✗ Error checking duplicate: {e}")
            return False