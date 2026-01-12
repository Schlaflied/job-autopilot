# Job Autopilot - Gmail Service
# Gmail API integration for creating drafts and detecting replies

import os
import pickle
from typing import Optional, List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from datetime import datetime
from dotenv import load_dotenv
from modules.logger_config import gmail_logger

load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.compose', 
          'https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    """Gmail API service for email automation"""
    
    def __init__(self):
        self.creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./data/credentials/gmail_credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "./data/credentials/gmail_token.json")
        self.service = None
        self.authenticated = False
        
        gmail_logger.info("Gmail service initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0
        
        Returns:
            bool: True if authentication successful
        """
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
                gmail_logger.info("Loaded existing Gmail token")
            except Exception as e:
                gmail_logger.warning(f"Failed to load token: {e}")
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    gmail_logger.info("Refreshed Gmail credentials")
                except Exception as e:
                    gmail_logger.error(f"Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                # New OAuth flow
                if not os.path.exists(self.creds_path):
                    gmail_logger.error(f"Credentials file not found: {self.creds_path}")
                    raise FileNotFoundError(f"Gmail credentials not found at {self.creds_path}")
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.creds_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    gmail_logger.info("Completed OAuth flow")
                except Exception as e:
                    gmail_logger.error(f"OAuth flow failed: {e}", exc_info=True)
                    return False
            
            # Save credentials
            try:
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                gmail_logger.info(f"Saved Gmail token to {self.token_path}")
            except Exception as e:
                gmail_logger.warning(f"Failed to save token: {e}")
        
        # Build service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            gmail_logger.info("Gmail API service built successfully")
            return True
        except Exception as e:
            gmail_logger.error(f"Failed to build Gmail service: {e}", exc_info=True)
            return False
    
    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Create a Gmail draft
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)
            attachments: List of file paths to attach
        
        Returns:
            dict: Draft info or None if failed
        """
        if not self.authenticated:
            gmail_logger.warning("Not authenticated. Call authenticate() first.")
            if not self.authenticate():
                return None
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            message.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            gmail_logger.info(f"Created draft: {subject} → {to}")
            return {
                "id": draft['id'],
                "subject": subject,
                "to": to,
                "created_at": datetime.now().isoformat()
            }
        
        except HttpError as e:
            gmail_logger.error(f"Gmail API error: {e}", exc_info=True)
            return None
        except Exception as e:
            gmail_logger.error(f"Failed to create draft: {e}", exc_info=True)
            return None
    
    def get_user_email(self) -> Optional[str]:
        """Get authenticated user's email address"""
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress')
            gmail_logger.info(f"User email: {email}")
            return email
        except Exception as e:
            gmail_logger.error(f"Failed to get user email: {e}")
            return None
    
    def test_connection(self) -> Dict:
        """
        Test Gmail API connection
        
        Returns:
            dict: Test results
        """
        results = {
            "credentials_found": os.path.exists(self.creds_path),
            "token_found": os.path.exists(self.token_path),
            "authenticated": False,
            "user_email": None,
            "error": None
        }
        
        if not results["credentials_found"]:
            results["error"] = f"Credentials not found at {self.creds_path}"
            gmail_logger.error(results["error"])
            return results
        
        try:
            if self.authenticate():
                results["authenticated"] = True
                results["user_email"] = self.get_user_email()
                gmail_logger.info("✅ Gmail API connection successful!")
            else:
                results["error"] = "Authentication failed"
        except Exception as e:
            results["error"] = str(e)
            gmail_logger.error(f"Connection test failed: {e}", exc_info=True)
        
        return results

# Global Gmail service instance
gmail_service = GmailService()

if __name__ == "__main__":
    # Test Gmail API
    print("Testing Gmail API connection...")
    print("-" * 50)
    
    results = gmail_service.test_connection()
    
    print(f"Credentials found: {results['credentials_found']}")
    print(f"Token found: {results['token_found']}")
    print(f"Authenticated: {results['authenticated']}")
    print(f"User email: {results['user_email']}")
    
    if results['error']:
        print(f"❌ Error: {results['error']}")
    else:
        print("✅ Gmail API connection successful!")
