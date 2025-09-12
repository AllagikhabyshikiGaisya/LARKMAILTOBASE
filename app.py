import os
import re
import base64
import pickle
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Config (from environment) ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'token.pickle')

# Google Cloud Pub/Sub topic for Gmail push notifications
PUBSUB_TOPIC_NAME = os.getenv('PUBSUB_TOPIC_NAME')  # e.g., "projects/your-project/topics/gmail-topic"

# Your Lark webhook URL
AUTOMATION_WEBHOOK_URL = 'https://y8xp2r4oy7i.jp.larksuite.com/base/automation/webhook/event/PUAmanwDgwlW3GhK7FyjGFF3pJb'

# --- Helpers for env-to-file convenience ---
def write_file_from_base64_env(env_var_name, filepath):
    """If env_var present and file missing, write decoded file to filepath."""
    b64 = os.getenv(env_var_name)
    if b64 and not os.path.exists(filepath):
        try:
            dec = base64.b64decode(b64)
            with open(filepath, 'wb') as f:
                f.write(dec)
            print(f"✅ Wrote {filepath} from env var {env_var_name}")
        except Exception as e:
            print(f"❌ Failed to write {filepath} from {env_var_name}: {e}")

def safe_b64decode(s):
    """URL-safe and padding-safe base64 decode for Gmail data pieces."""
    if not s:
        return b''
    s = s.replace('-', '+').replace('_', '/')
    padding = len(s) % 4
    if padding:
        s += '=' * (4 - padding)
    try:
        return base64.b64decode(s)
    except Exception:
        return base64.urlsafe_b64decode(s + '===')

# Try to write credentials and token from environment (if provided)
write_file_from_base64_env('GMAIL_CREDENTIALS_JSON_BASE64', GMAIL_CREDENTIALS_FILE)
write_file_from_base64_env('GMAIL_TOKEN_BASE64', GMAIL_TOKEN_FILE)

class EmailProcessor:
    def __init__(self):
        self.gmail_service = None
        self.processed_messages = set()
        self.history_id = None
        print("🔧 Initializing Email Processor...")
        self.initialize_gmail()
        # Load history ID if exists
        if os.path.exists('gmail_history.txt'):
            with open('gmail_history.txt', 'r') as f:
                self.history_id = f.read().strip()
        # Set up Gmail watch on startup
        time.sleep(1)
        self.setup_gmail_watch()

    def initialize_gmail(self):
        """Initialize Gmail API service"""
        print("📧 Setting up Gmail API...")
        try:
            creds = None
            if os.path.exists(GMAIL_TOKEN_FILE):
                with open(GMAIL_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)
                    print("📄 Loaded token from file")

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 Refreshing token...")
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(GMAIL_TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
                else:
                    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                        print("❌ credentials.json not found. Provide GMAIL_CREDENTIALS_JSON_BASE64 or upload credentials.json.")
                        return
                    print("🌐 Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(GMAIL_TOKEN_FILE, 'wb') as token:
                        pickle.dump(creds, token)
                        print("💾 Saved new token.pickle")

            self.gmail_service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            print("✅ Gmail service initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize Gmail: {e}")

    def setup_gmail_watch(self):
        """Set up Gmail push notifications via Pub/Sub"""
        if not self.gmail_service:
            print("⚠️  Gmail service not ready; skipping watch setup.")
            return
        if not PUBSUB_TOPIC_NAME:
            print("⚠️  PUBSUB_TOPIC_NAME not configured; Gmail push notifications disabled.")
            print("💡 Without Pub/Sub, the app will still work but won't be instant.")
            return
        
        try:
            print("👁️ Setting up Gmail watch for instant notifications...")
            body = {
                'topicName': PUBSUB_TOPIC_NAME,
                'labelIds': ['INBOX'],
                'labelFilterAction': 'include'
            }
            resp = self.gmail_service.users().watch(userId='me', body=body).execute()
            self.history_id = resp.get('historyId')
            expiration = resp.get('expiration')
            print(f"✅ Gmail watch active! (historyId={self.history_id}, expires={expiration})")
            
            # Save history ID for future use
            with open('gmail_history.txt', 'w') as f:
                f.write(str(self.history_id or ''))
                
        except Exception as e:
            print(f"⚠️  Could not set up Gmail watch: {e}")
            print("💡 The app will still work but without instant notifications.")

    def renew_watch(self):
        """Renew Gmail watch (watches expire after 7 days)"""
        self.setup_gmail_watch()

    def _extract_text_from_payload(self, payload):
        """Extract plain text from email payload"""
        collected_plain = []
        collected_html = []

        def walk(part):
            mime = part.get('mimeType', '')
            body = part.get('body', {})
            data = body.get('data')
            if data:
                try:
                    decoded = safe_b64decode(data).decode('utf-8', errors='ignore')
                except Exception:
                    decoded = ''
                if mime == 'text/plain':
                    collected_plain.append(decoded)
                elif mime == 'text/html':
                    collected_html.append(decoded)
            for sub in part.get('parts', []):
                walk(sub)

        walk(payload)
        
        if collected_plain:
            return "\n".join(collected_plain).strip()
        if collected_html:
            # Remove HTML tags
            html_text = "\n".join(collected_html)
            text = re.sub(r'<script.*?>.*?</script>', '', html_text, flags=re.DOTALL|re.IGNORECASE)
            text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL|re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        # Sometimes body.data is at top level
        top_data = payload.get('body', {}).get('data')
        if top_data:
            try:
                return safe_b64decode(top_data).decode('utf-8', errors='ignore')
            except:
                return ''
        return ''

    def extract_email_body(self, message):
        """Extract text content from Gmail message"""
        try:
            payload = message.get('payload', {})
            body_text = self._extract_text_from_payload(payload)
            return body_text
        except Exception as e:
            print(f"⚠️  Error extracting email body: {e}")
            return ""

    def parse_customer_info(self, email_body):
        """Extract customer information from email body"""
        # Clean up the email body first
        email_body = email_body.replace('\r', '').strip()
        
        # Enhanced patterns for better matching
        patterns = {
            'event_name': r'イベント名\s*[:：]?\s*(.+?)(?=\n|開催日|$)',
            'event_date': r'開催日\s*[:：]?\s*(.+?)(?=\n|時間|$)',
            'event_time': r'時間\s*[:：]?\s*(.+?)(?=\n|会場|$)',
            'venue': r'会場\s*[:：]?\s*(.+?)(?=\n|URL|$)',
            'url': r'URL\s*[:：]?\s*(https?://[^\s\n]+)',
            'reservation_date': r'ご希望日\s*[:：]?\s*(.+?)(?=\n|ご希望時間|$)',
            'reservation_time': r'ご希望時間\s*[:：]?\s*(.+?)(?=\n|=|$)',
            'name': r'お名前\s*[:：]?\s*(.+?)(?=\n|フリガナ|$)',
            'furigana': r'フリガナ\s*[:：]?\s*(.+?)(?=\n|メール|$)',
            'email': r'メールアドレス\s*[:：]?\s*([^\s\n]+@[^\s\n]+?)(?=\n|電話|$)',
            'phone': r'電話番号\s*[:：]?\s*(\d+?)(?=\n|年齢|$)',
            'age': r'年齢\s*[:：]?\s*(.+?)(?=\n|毎月|$)',
            'monthly_rent': r'毎月の家賃\s*[:：]?\s*(.+?)(?=\n|月々|$)',
            'monthly_payment': r'月々の返済額\s*[:：]?\s*(.+?)(?=\n|郵便|$)',
            'postal_code': r'郵便番号\s*[:：]?\s*(.+?)(?=\n|ご住所|$)',
            'address': r'ご住所\s*[:：]?\s*(.+?)(?=\n|ご意見|$)',
            'comments': r'ご意見・ご質問等\s*[:：]?\s*(.+?)(?=\n|ご予約のきっかけ|$)',
            'trigger': r'ご予約のきっかけ\s*[:：]?\s*(.+?)(?=\n|=|取り扱い|$)',
            'store_name': r'展示場名\s*[:：]?\s*(.+?)(?=\n|所在地|$)',
            'store_address': r'所在地\s*[:：]?\s*(.+?)(?=\n|営業時間|$)',
            'business_hours': r'営業時間\s*[:：]?\s*(.+?)(?=\n|定休日|$)',
            'closed_days': r'定休日\s*[:：]?\s*(.+?)(?=\n|=|$)'
        }

        customer_data = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, email_body, flags=re.MULTILINE | re.DOTALL)
            if m and m.group(1):
                value = m.group(1).strip()
                # Clean up the value
                value = re.sub(r'\s+', ' ', value)  # Replace multiple spaces with single space
                value = value.replace('：', ':').replace('　', ' ')  # Normalize characters
                customer_data[key] = value
            else:
                customer_data[key] = ""
        
        print(f"📊 Parsed data: {customer_data.get('name', 'Unknown')} - {customer_data.get('email', 'No email')}")
        return customer_data

    def send_to_automation_webhook(self, customer_data, raw_body=None, message_id=None, subject=None):
        """Send parsed data to Lark webhook in JSON format"""
        # Prepare the JSON payload
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_id": message_id,
            "subject": subject,
            "customer_info": {
                "name": customer_data.get('name', ''),
                "furigana": customer_data.get('furigana', ''),
                "email": customer_data.get('email', ''),
                "phone": customer_data.get('phone', ''),
                "age": customer_data.get('age', ''),
                "postal_code": customer_data.get('postal_code', ''),
                "address": customer_data.get('address', ''),
                "monthly_rent": customer_data.get('monthly_rent', ''),
                "monthly_payment": customer_data.get('monthly_payment', ''),
                "comments": customer_data.get('comments', ''),
                "trigger": customer_data.get('trigger', '')
            },
            "reservation_info": {
                "date": customer_data.get('reservation_date', ''),
                "time": customer_data.get('reservation_time', '')
            },
            "event_info": {
                "name": customer_data.get('event_name', ''),
                "date": customer_data.get('event_date', ''),
                "time": customer_data.get('event_time', ''),
                "venue": customer_data.get('venue', ''),
                "url": customer_data.get('url', '')
            },
            "store_info": {
                "name": customer_data.get('store_name', ''),
                "address": customer_data.get('store_address', ''),
                "business_hours": customer_data.get('business_hours', ''),
                "closed_days": customer_data.get('closed_days', '')
            }
        }

        try:
            print(f"📤 Sending to webhook: {AUTOMATION_WEBHOOK_URL}")
            resp = requests.post(AUTOMATION_WEBHOOK_URL, json=payload, timeout=15)
            if 200 <= resp.status_code < 300:
                print(f"✅ Successfully sent data to Lark webhook! Status: {resp.status_code}")
                return True
            else:
                print(f"❌ Webhook returned {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Error posting to webhook: {e}")
            return False

    def process_specific_email(self, message_id):
        """Process a single email by ID"""
        if message_id in self.processed_messages:
            print(f"⏭️  Already processed {message_id}")
            return False
        
        if not self.gmail_service:
            print("❌ Gmail service unavailable")
            return False

        try:
            print(f"📧 Processing email {message_id}...")
            msg = self.gmail_service.users().messages().get(userId='me', id=message_id).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            subject = headers.get('Subject', '')
            from_email = headers.get('From', '')
            date = headers.get('Date', '')
            
            print(f"📨 Subject: {subject}")
            print(f"👤 From: {from_email}")
            
            # Check if this is the target email
            if 'イベントの参加お申し込みがありました' not in subject:
                print(f"📪 Skipping - not a registration email")
                return False

            # Extract body
            body = self.extract_email_body(msg)
            if not body:
                print("⚠️  No body content found")
                return False

            # Parse customer info
            customer_data = self.parse_customer_info(body)
            
            # Check if we got valid data
            if not customer_data.get('name') and not customer_data.get('email'):
                print("⚠️  Could not extract customer information")
                # Still try to send what we have
            
            # Send to webhook immediately
            success = self.send_to_automation_webhook(
                customer_data, 
                raw_body=body[:4000],  # Limit size
                message_id=message_id, 
                subject=subject
            )
            
            if success:
                self.processed_messages.add(message_id)
                print(f"✅ Successfully processed and sent email {message_id}")
                print(f"👤 Customer: {customer_data.get('name', 'Unknown')}")
                return True
            
            return False

        except Exception as e:
            print(f"❌ Error processing email {message_id}: {e}")
            return False

    def process_history_changes(self, start_history_id):
        """Process emails from history changes (used for push notifications)"""
        if not self.gmail_service or not start_history_id:
            return []
        
        try:
            print(f"📜 Checking history from ID: {start_history_id}")
            history = self.gmail_service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                labelId='INBOX',
                historyTypes=['messageAdded']
            ).execute()
            
            changes = history.get('history', [])
            processed = []
            
            for change in changes:
                added_messages = change.get('messagesAdded', [])
                for msg_added in added_messages:
                    message_id = msg_added['message']['id']
                    if self.process_specific_email(message_id):
                        processed.append(message_id)
            
            # Update history ID
            new_history_id = history.get('historyId')
            if new_history_id:
                self.history_id = new_history_id
                with open('gmail_history.txt', 'w') as f:
                    f.write(str(new_history_id))
            
            return processed
            
        except Exception as e:
            print(f"⚠️  Error processing history: {e}")
            # Fall back to recent emails
            return self.get_recent_emails(minutes_back=5)

    def get_recent_emails(self, minutes_back=5):
        """Fallback: Search for recent emails"""
        if not self.gmail_service:
            print("❌ Gmail service not available")
            return []
        
        try:
            query = f'subject:"イベントの参加お申し込みがありました" newer_than:{minutes_back}m'
            print(f"🔍 Searching for emails from last {minutes_back} minutes...")
            
            res = self.gmail_service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=10
            ).execute()
            
            messages = res.get('messages', [])
            processed_ids = []
            
            print(f"📧 Found {len(messages)} matching emails")
            
            for m in messages:
                mid = m.get('id')
                if self.process_specific_email(mid):
                    processed_ids.append(mid)
            
            return processed_ids
            
        except Exception as e:
            print(f"❌ Error retrieving messages: {e}")
            return []

# Initialize the email processor
email_processor = EmailProcessor()

# --- Flask Routes ---
@app.route('/')
def home():
    return jsonify({
        "status": "✅ Automatic Gmail Parser Active",
        "timestamp": datetime.now().isoformat(),
        "webhook_url": AUTOMATION_WEBHOOK_URL,
        "processed_count": len(email_processor.processed_messages),
        "endpoints": {
            "/": "This page",
            "/health": "Health check",
            "/webhook": "Gmail push notification endpoint (POST)",
            "/process-now": "Manually trigger email processing",
            "/renew-watch": "Renew Gmail watch subscription"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    gmail_status = "✅ Connected" if email_processor.gmail_service else "❌ Not connected"
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gmail": gmail_status,
        "processed_emails": len(email_processor.processed_messages),
        "webhook_configured": bool(AUTOMATION_WEBHOOK_URL),
        "pubsub_configured": bool(PUBSUB_TOPIC_NAME)
    })

@app.route('/webhook', methods=['POST'])
def gmail_webhook():
    """
    Main webhook endpoint for Gmail push notifications via Pub/Sub
    This is where the magic happens - instant email processing!
    """
    print("\n" + "="*50)
    print("🔔 INSTANT NOTIFICATION RECEIVED!")
    print("="*50)
    
    try:
        data = request.get_json(silent=True)
        if not data:
            print("❌ No JSON in request")
            return "Bad Request", 400
        
        # Log the notification
        print(f"📬 Notification received at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Pub/Sub message format
        if 'message' in data:
            message = data['message']
            
            # Decode the message data
            if 'data' in message:
                raw_data = message['data']
                decoded = base64.b64decode(raw_data).decode('utf-8')
                
                try:
                    gmail_data = json.loads(decoded)
                    print(f"📨 Gmail notification data: {gmail_data}")
                    
                    # Get history ID from the notification
                    history_id = gmail_data.get('historyId')
                    if history_id and email_processor.history_id:
                        # Process only new messages since last history ID
                        processed = email_processor.process_history_changes(email_processor.history_id)
                    else:
                        # Fallback to recent emails
                        processed = email_processor.get_recent_emails(minutes_back=2)
                    
                except json.JSONDecodeError:
                    # If not JSON, still process recent emails
                    processed = email_processor.get_recent_emails(minutes_back=2)
            else:
                # No data in message, process recent
                processed = email_processor.get_recent_emails(minutes_back=2)
            
            # Acknowledge the Pub/Sub message
            return jsonify({
                "status": "success",
                "processed": len(processed),
                "timestamp": datetime.now().isoformat()
            }), 200
        
        # Not a Pub/Sub message format, but still try to process
        processed = email_processor.get_recent_emails(minutes_back=5)
        return jsonify({
            "status": "processed",
            "count": len(processed)
        }), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        # Even on error, try to process emails
        try:
            email_processor.get_recent_emails(minutes_back=5)
        except:
            pass
        return jsonify({"error": str(e)}), 500

@app.route('/process-now', methods=['GET', 'POST'])
def manual_process():
    """Manually trigger email processing (useful for testing)"""
    print("\n📧 Manual processing triggered...")
    processed = email_processor.get_recent_emails(minutes_back=60)
    return jsonify({
        "status": "success",
        "processed_count": len(processed),
        "processed_ids": list(processed),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/renew-watch', methods=['POST'])
def renew_watch():
    """Renew Gmail watch subscription (watches expire after 7 days)"""
    print("\n🔄 Renewing Gmail watch...")
    email_processor.renew_watch()
    return jsonify({
        "status": "success",
        "message": "Gmail watch renewed",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test-parse', methods=['POST'])
def test_parse():
    """Test endpoint for parsing email body"""
    data = request.get_json(silent=True)
    if not data or 'email_body' not in data:
        return jsonify({"error": "Please POST JSON with 'email_body' field"}), 400
    
    parsed = email_processor.parse_customer_info(data['email_body'])
    
    # Test sending to webhook if requested
    if data.get('send_to_webhook'):
        success = email_processor.send_to_automation_webhook(
            parsed,
            raw_body=data['email_body'],
            message_id="test",
            subject="Test Parse"
        )
        return jsonify({
            "parsed": parsed,
            "webhook_sent": success
        })
    
    return jsonify({"parsed": parsed})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*50)
    print(f"🚀 Starting Automatic Gmail Parser on port {port}")
    print(f"📮 Webhook URL: {AUTOMATION_WEBHOOK_URL}")
    print(f"🔔 Push notifications: {'Enabled' if PUBSUB_TOPIC_NAME else 'Disabled'}")
    print("="*50 + "\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)