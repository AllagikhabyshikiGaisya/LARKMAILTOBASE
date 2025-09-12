import os
import re
import base64
import pickle
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Gmail API settings
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GMAIL_CREDENTIALS_FILE = 'credentials.json'
GMAIL_TOKEN_FILE = 'token.pickle'

# Lark API settings from environment variables
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
LARK_BASE_TOKEN = os.getenv('LARK_BASE_TOKEN')
LARK_TABLE_ID = os.getenv('LARK_TABLE_ID')


class EmailProcessor:
    def __init__(self):
        self.gmail_service = None
        self.lark_access_token = None
        print("🔧 Initializing Email Processor...")
        self.initialize_gmail()
        self.get_lark_access_token()

    def initialize_gmail(self):
        """Initialize Gmail API service"""
        print("📧 Setting up Gmail API...")

        # Handle production deployment - load token from environment variable
        token_base64 = os.getenv('GMAIL_TOKEN_BASE64')
        if token_base64 and not os.path.exists(GMAIL_TOKEN_FILE):
            print("🌐 Loading Gmail token from environment for production...")
            try:
                token_data = base64.b64decode(token_base64)
                with open(GMAIL_TOKEN_FILE, 'wb') as token_file:
                    token_file.write(token_data)
                print("✅ Gmail token loaded from environment successfully")
            except Exception as e:
                print(f"❌ Failed to load token from environment: {e}")

        try:
            creds = None

            # Load existing token if available
            if os.path.exists(GMAIL_TOKEN_FILE):
                print("📄 Loading existing Gmail token...")
                with open(GMAIL_TOKEN_FILE, 'rb') as token:
                    creds = pickle.load(token)

            # If there are no valid credentials available, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 Refreshing Gmail token...")
                    creds.refresh(Request())
                else:
                    print("🌐 Starting Gmail OAuth flow...")
                    print("⚠️  A browser window will open. Please authorize the application.")

                    if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                        print("❌ credentials.json file not found!")
                        print("Please download it from Google Cloud Console")
                        return

                    flow = InstalledAppFlow.from_client_secrets_file(
                        GMAIL_CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                    print("✅ Gmail authorization completed!")

                # Save the credentials for next time
                with open(GMAIL_TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
                    print("💾 Gmail token saved")

            self.gmail_service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail service initialized successfully!")

        except Exception as e:
            print(f"❌ Failed to initialize Gmail: {str(e)}")

    def get_lark_access_token(self):
        """Get Lark access token"""
        print("🏢 Getting Lark access token...")

        if not LARK_APP_ID or not LARK_APP_SECRET:
            print("❌ Lark credentials missing in .env file!")
            return

        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}

        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if result.get('code') == 0:
                self.lark_access_token = result['app_access_token']
                print("✅ Lark access token obtained!")
            else:
                print(f"❌ Failed to get Lark token: {result}")
        except Exception as e:
            print(f"❌ Error getting Lark token: {str(e)}")

    def parse_customer_info(self, email_body):
        """Extract customer information from email body"""
        print("🔍 Parsing customer information...")

        # Patterns to extract information from Japanese email
        patterns = {
            'event_name': r'イベント名\s*[:\uff1a]\s*(.+?)(?=\n|開催日)',
            'event_date': r'開催日\s*[:\uff1a]\s*(.+?)(?=\n|時間)',
            'event_time': r'時間\s*[:\uff1a]\s*(.+?)(?=\n|会場)',
            'venue': r'会場\s*[:\uff1a]\s*(.+?)(?=\n|URL)',
            'url': r'URL\s*[:\uff1a]\s*(https?://[^\s]+)',
            'reservation_date': r'ご希望日\s*[：:\uff1a]\s*(.+?)(?=\n|ご希望時間)',
            'reservation_time': r'ご希望時間\s*[：:\uff1a]\s*(.+?)(?=\n)',
            'name': r'お名前\s*[:\uff1a]\s*(.+?)(?=\n|フリガナ)',
            'furigana': r'フリガナ\s*[:\uff1a]\s*(.+?)(?=\n|メール)',
            'email': r'メールアドレス\s*[:\uff1a]\s*(.+?)(?=\n|電話)',
            'phone': r'電話番号\s*[:\uff1a]\s*(.+?)(?=\n|年齢)',
            'age': r'年齢\s*[:\uff1a]\s*(.+?)(?=\n|毎月)',
            'monthly_rent': r'毎月の家賃\s*[:\uff1a]\s*(.+?)(?=\n|月々)',
            'monthly_payment': r'月々の返済額\s*[:\uff1a]\s*(.+?)(?=\n|郵便)',
            'postal_code': r'郵便番号\s*[:\uff1a]\s*(.+?)(?=\n|ご住所)',
            'address': r'ご住所\s*[:\uff1a]\s*(.+?)(?=\n|ご意見)',
            'comments': r'ご意見・ご質問等\s*[:\uff1a]\s*(.+?)(?=\n|ご予約のきっかけ)',
            'trigger': r'ご予約のきっかけ\s*[:\uff1a]\s*(.+?)(?=\n|=)',
            'store_name': r'展示場名\s*[:\uff1a]\s*(.+?)(?=\n|所在地)',
            'store_address': r'所在地\s*[:\uff1a]\s*(.+?)(?=\n|営業時間)',
            'business_hours': r'営業時間\s*[:\uff1a]\s*(.+?)(?=\n|定休日)',
            'closed_days': r'定休日\s*[:\uff1a]\s*(.+?)(?=\n)'
        }

        customer_data = {}
        extracted_count = 0

        for key, pattern in patterns.items():
            match = re.search(pattern, email_body, re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                customer_data[key] = re.sub(r'\s+', ' ', value).strip()
                if customer_data[key]:
                    extracted_count += 1
                    print(f"  ✅ {key}: {customer_data[key]}")
            else:
                customer_data[key] = ""

        print(f"📊 Extracted {extracted_count}/{len(patterns)} fields")
        return customer_data

    def store_in_lark_base(self, customer_data):
        """Store customer data in Lark Base"""
        print("💾 Storing data in Lark Base...")

        if not self.lark_access_token:
            print("❌ No Lark access token available")
            return False

        if not LARK_BASE_TOKEN or not LARK_TABLE_ID:
            print("❌ Lark Base Token or Table ID missing")
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{LARK_BASE_TOKEN}/tables/{LARK_TABLE_ID}/records"
        headers = {
            "Authorization": f"Bearer {self.lark_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        record_data = {
            "fields": {
                "イベント名": customer_data.get('event_name', ''),
                "開催日": customer_data.get('event_date', ''),
                "時間": customer_data.get('event_time', ''),
                "会場": customer_data.get('venue', ''),
                "URL": customer_data.get('url', ''),
                "ご希望日": customer_data.get('reservation_date', ''),
                "ご希望時間": customer_data.get('reservation_time', ''),
                "お名前": customer_data.get('name', ''),
                "フリガナ": customer_data.get('furigana', ''),
                "メールアドレス": customer_data.get('email', ''),
                "電話番号": customer_data.get('phone', ''),
                "年齢": customer_data.get('age', ''),
                "毎月の家賃": customer_data.get('monthly_rent', ''),
                "月々の返済額": customer_data.get('monthly_payment', ''),
                "郵便番号": customer_data.get('postal_code', ''),
                "ご住所": customer_data.get('address', ''),
                "ご意見・ご質問等": customer_data.get('comments', ''),
                "ご予約のきっかけ": customer_data.get('trigger', ''),
                "展示場名": customer_data.get('store_name', ''),
                "店舗所在地": customer_data.get('store_address', ''),
                "営業時間": customer_data.get('business_hours', ''),
                "定休日": customer_data.get('closed_days', ''),
                "処理日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        try:
            response = requests.post(url, headers=headers, json=record_data)
            result = response.json()

            if response.status_code == 200:
                print("✅ Data successfully stored in Lark Base!")
                return True
            else:
                print(f"❌ Failed to store data: {result}")
                return False
        except Exception as e:
            print(f"❌ Error storing data: {str(e)}")
            return False

    def get_recent_emails(self, hours_back=24):
        """Get recent emails from Gmail"""
        print(f"📬 Looking for emails from last {hours_back} hours...")

        if not self.gmail_service:
            print("❌ Gmail service not available")
            return []

        try:
            query = 'subject:"イベントの参加お申し込みがありました"'

            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=10
            ).execute()

            messages = results.get('messages', [])
            print(f"📧 Found {len(messages)} matching emails")

            processed_emails = []
            for i, message in enumerate(messages):
                print(f"📨 Processing email {i+1}/{len(messages)}...")

                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id']
                ).execute()

                email_body = self.extract_email_body(msg)
                if email_body:
                    customer_data = self.parse_customer_info(email_body)
                    if customer_data.get('name'):
                        processed_emails.append({
                            'message_id': message['id'],
                            'customer_data': customer_data,
                            'email_body': email_body
                        })
                        print(f"✅ Email processed for: {customer_data.get('name')}")

            return processed_emails

        except Exception as e:
            print(f"❌ Error retrieving emails: {str(e)}")
            return []

    def extract_email_body(self, message):
        """Extract text content from email message"""
        try:
            payload = message['payload']
            body = ""

            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            else:
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            return body
        except Exception as e:
            print(f"⚠️  Error extracting email body: {str(e)}")
            return ""


# Initialize the email processor
print("🚀 Starting Email Parser Application...")
email_processor = EmailProcessor()


# Flask routes (web endpoints)
@app.route('/')
def home():
    return jsonify({
        "status": "✅ Email Parser is running!",
        "timestamp": datetime.now().isoformat(),
        "available_endpoints": {
            "/health": "Check system status",
            "/process-emails": "Process recent emails",
            "/test-parse": "Test parsing with sample data"
        }
    })


@app.route('/health')
def health_check():
    status = {"status": "healthy", "timestamp": datetime.now().isoformat()}

    if email_processor.gmail_service:
        status["gmail"] = "✅ Connected"
    else:
        status["gmail"] = "❌ Not connected"
        status["status"] = "unhealthy"

    if email_processor.lark_access_token:
        status["lark"] = "✅ Connected"
    else:
        status["lark"] = "❌ Not connected"
        status["status"] = "unhealthy"

    return jsonify(status)


@app.route('/process-emails', methods=['GET', 'POST'])
def process_emails():
    print("\n" + "="*50)
    print("🔄 PROCESSING EMAILS")
    print("="*50)

    try:
        recent_emails = email_processor.get_recent_emails(hours_back=24)

        if not recent_emails:
            return jsonify({
                "status": "success",
                "message": "No new emails found to process",
                "processed_count": 0
            })

        results = []
        success_count = 0

        for email_data in recent_emails:
            customer_data = email_data['customer_data']
            success = email_processor.store_in_lark_base(customer_data)
            if success:
                success_count += 1

            results.append({
                "customer_name": customer_data.get('name', 'Unknown'),
                "customer_email": customer_data.get('email', 'Unknown'),
                "stored_successfully": success
            })

        print(f"✅ Processing complete: {success_count}/{len(results)} stored successfully")

        return jsonify({
            "status": "success",
            "processed_emails": len(results),
            "successful_stores": success_count,
            "results": results
        })

    except Exception as e:
        print(f"❌ Error processing emails: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/test-parse', methods=['POST'])
def test_parse():
    try:
        data = request.get_json()
        if not data or 'email_body' not in data:
            return jsonify({"error": "Please provide 'email_body' in JSON"}), 400

        print("\n" + "="*50)
        print("🧪 TESTING EMAIL PARSING")
        print("="*50)

        customer_data = email_processor.parse_customer_info(data['email_body'])

        return jsonify({
            "status": "success",
            "parsed_data": customer_data,
            "non_empty_fields": len([v for v in customer_data.values() if v])
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🌐 Starting web server on port {port}")
    print("Press Ctrl+C to stop")
    app.run(debug=False, host='0.0.0.0', port=port)  # debug=False for production
