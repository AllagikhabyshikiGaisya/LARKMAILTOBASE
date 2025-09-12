import os
import pickle
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import re

class EmailProcessor:
    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.service = None
        self.initialize_service()
        
    def initialize_service(self):
        """Initialize Gmail API service"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
                
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
                
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Gmail API service initialized successfully")
        
    def get_unread_emails(self, target_email: str) -> List[Dict[str, Any]]:
        """Fetch unread emails sent to the target address"""
        try:
            # Search for unread emails to the target address
            query = f'to:{target_email} is:unread'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = self.get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
                    
            print(f"✓ Found {len(emails)} unread emails")
            return emails
            
        except Exception as e:
            print(f"✗ Error fetching emails: {e}")
            return []
            
    def get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an email"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            email_data = {
                'email_id': message_id,
                'sender': '',
                'recipient': '',
                'subject': '',
                'body': '',
                'received_date': '',
                'attachments': ''
            }
            
            # Parse headers
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                
                if name == 'from':
                    email_data['sender'] = self.extract_email_address(value)
                elif name == 'to':
                    email_data['recipient'] = self.extract_email_address(value)
                elif name == 'subject':
                    email_data['subject'] = value
                elif name == 'date':
                    email_data['received_date'] = self.parse_date(value)
                    
            # Extract body
            email_data['body'] = self.extract_body(message['payload'])
            
            # Check for attachments
            email_data['attachments'] = self.get_attachment_names(message['payload'])
            
            return email_data
            
        except Exception as e:
            print(f"✗ Error getting email details: {e}")
            return None
            
    def extract_email_address(self, email_string: str) -> str:
        """Extract email address from string like 'Name <email@domain.com>'"""
        match = re.search(r'[\w\.-]+@[\w\.-]+', email_string)
        return match.group(0) if match else email_string
        
    def parse_date(self, date_string: str) -> str:
        """Parse email date to ISO format"""
        try:
            # Remove timezone info for simplicity
            date_string = re.sub(r'\s*\([^)]*\)', '', date_string)
            date_string = re.sub(r'\s*[+-]\d{4}$', '', date_string)
            
            # Try multiple date formats
            formats = [
                '%a, %d %b %Y %H:%M:%S',
                '%d %b %Y %H:%M:%S',
                '%a, %d %b %Y %H:%M:%S %Z'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string.strip(), fmt)
                    return dt.isoformat()
                except:
                    continue
                    
            return datetime.now().isoformat()
            
        except Exception as e:
            print(f"Date parsing error: {e}")
            return datetime.now().isoformat()
            
    def extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ''
        
        def get_text_from_part(part):
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            return ''
            
        # Check if it's a simple message
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']).decode('utf-8', errors='ignore')
        
        # Check parts for multipart messages
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    body += get_text_from_part(part)
                elif 'parts' in part:
                    for subpart in part['parts']:
                        body += get_text_from_part(subpart)
                        
        # Truncate if too long
        if len(body) > 5000:
            body = body[:5000] + "... [truncated]"
            
        return body.strip()
        
    def get_attachment_names(self, payload: Dict) -> str:
        """Get list of attachment filenames"""
        attachments = []
        
        def check_part_for_attachment(part):
            filename = part.get('filename', '')
            if filename:
                attachments.append(filename)
                
        # Check main parts
        if 'parts' in payload:
            for part in payload['parts']:
                check_part_for_attachment(part)
                if 'parts' in part:
                    for subpart in part['parts']:
                        check_part_for_attachment(subpart)
                        
        return ', '.join(attachments) if attachments else 'None'
        
    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"✓ Marked email {message_id} as read")
            return True
            
        except Exception as e:
            print(f"✗ Error marking email as read: {e}")
            return False