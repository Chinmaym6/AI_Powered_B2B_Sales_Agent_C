"""
Email Monitor Service - Checks inbox for replies and processes them
Supports both MailHog (testing) and real IMAP (Gmail/Outlook)
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from ..config import settings
from ..models.database import SessionLocal
from ..models.tables import Email, Lead
from .sentiment_service import SentimentService


class EmailMonitorService:
    """Monitor inbox for email replies and process them"""
    
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.use_mailhog = not getattr(settings, 'IMAP_USER', None)
    
    async def check_for_replies(self) -> Dict:
        """
        Check inbox for new replies and process them
        
        Returns statistics about what was found
        """
        
        if self.use_mailhog:
            return await self._check_mailhog()
        else:
            return await self._check_imap()
    
    async def _check_mailhog(self) -> Dict:
        """Check MailHog HTTP API for replies"""
        
        try:
            mailhog_api = getattr(settings, 'MAILHOG_API_URL', 'http://localhost:8025')
            
            # Fetch messages from MailHog API
            response = requests.get(f"{mailhog_api}/api/v2/messages", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get('items', [])
            
            stats = {
                'total_checked': len(messages),
                'replies_found': 0,
                'processed': 0,
                'auto_labeled': 0,
                'errors': 0
            }
            
            db = SessionLocal()
            
            try:
                for msg in messages:
                    try:
                        # Extract email details
                        from_addr = msg.get('From', {}).get('Mailbox', '') + '@' + msg.get('From', {}).get('Domain', '')
                        subject = msg.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]
                        body = self._extract_mailhog_body(msg)
                        
                        # Check if this is a reply to our sent email
                        sent_email = db.query(Email).filter(
                            Email.lead.has(email=from_addr)
                        ).first()
                        
                        if sent_email and not sent_email.processed_for_sentiment:
                            stats['replies_found'] += 1
                            
                            # Process the reply
                            await self._process_reply(
                                db=db,
                                email_record=sent_email,
                                reply_text=body,
                                replied_at=datetime.now ()
                            )
                            
                            stats['processed'] += 1
                            
                            # Check if auto-labeled
                            lead = sent_email.lead
                            if lead and lead.auto_labeled:
                                stats['auto_labeled'] += 1
                    
                    except Exception as e:
                        print(f"Error processing MailHog message: {e}")
                        stats['errors'] += 1
            
            finally:
                db.close()
            
            return stats
            
        except requests.exceptions.ConnectionError:
            # MailHog not running - silently skip (normal for production without MailHog)
            return {'total_checked': 0, 'info': 'MailHog not running (use real IMAP for production)'}
        except Exception as e:
            # Only log unexpected errors
            if 'Connection refused' not in str(e):
                print(f"MailHog check error: {e}")
            return {'error': str(e)}
    
    async def _check_imap(self) -> Dict:
        """Check real email via IMAP (Gmail, Outlook, etc.)"""
        
        try:
            imap_host = getattr(settings, 'IMAP_HOST', 'imap.gmail.com')
            imap_port = getattr(settings, 'IMAP_PORT', 993)
            imap_user = getattr(settings, 'IMAP_USER', '')
            imap_pass = getattr(settings, 'IMAP_PASS', '')
            
            if not imap_user or not imap_pass:
                print("⚠️ IMAP credentials not configured")
                return {'error': 'IMAP not configured'}
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_host, imap_port)
            mail.login(imap_user, imap_pass)
            mail.select('INBOX')
            
            # Search for unread emails from last 7 days
            since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            status, messages = mail.search(None, f'(UNSEEN SINCE {since_date})')
            
            email_ids = messages[0].split()
            
            stats = {
                'total_checked': len(email_ids),
                'replies_found': 0,
                'processed': 0,
                'auto_labeled': 0,
                'errors': 0
            }
            
            db = SessionLocal()
            
            try:
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                
                                # Extract details
                                from_addr = self._extract_email_address(msg.get('From', ''))
                                subject = self._decode_header(msg.get('Subject', ''))
                                body = self._extract_email_body(msg)
                                message_id = msg.get('Message-ID', '')
                                in_reply_to = msg.get('In-Reply-To', '')
                                
                                # Find matching sent email
                                sent_email = db.query(Email).filter(
                                    Email.lead.has(email=from_addr),
                                    Email.processed_for_sentiment == False
                                ).first()
                                
                                if sent_email:
                                    stats['replies_found'] += 1
                                    
                                    # Process the reply
                                    await self._process_reply(
                                        db=db,
                                        email_record=sent_email,
                                        reply_text=body,
                                        replied_at=datetime.now()
                                    )
                                    
                                    stats['processed'] += 1
                                    
                                    # Check if auto-labeled
                                    lead = sent_email.lead
                                    if lead and lead.auto_labeled:
                                        stats['auto_labeled'] += 1
                    
                    except Exception as e:
                        print(f"Error processing IMAP message {email_id}: {e}")
                        stats['errors'] += 1
            
            finally:
                db.close()
                mail.close()
                mail.logout()
            
            return stats
            
        except Exception as e:
            print(f"IMAP check error: {e}")
            return {'error': str(e)}
    
    async def _process_reply(
        self, 
        db: SessionLocal, 
        email_record: Email, 
        reply_text: str,
        replied_at: datetime
    ):
        """Process a reply: analyze sentiment and update database"""
        
        # Get the lead
        lead = email_record.lead
        if not lead:
            return
        
        # Analyze sentiment
        sentiment_result = await self.sentiment_service.analyze_reply(
            reply_text=reply_text,
            original_email=email_record.body or ""
        )
        
        # Update email record
        email_record.reply_text = reply_text
        email_record.replied_at = replied_at
        email_record.reply_sentiment = sentiment_result['sentiment']
        email_record.reply_intent = sentiment_result['intent']
        email_record.reply_confidence = sentiment_result['confidence']
        email_record.processed_for_sentiment = True
        
        # Update lead record
        lead.reply_received = True
        lead.replied_at = replied_at
        lead.reply_sentiment = sentiment_result['sentiment']
        lead.reply_intent = sentiment_result['intent']
        lead.reply_confidence = sentiment_result['confidence']
        
        # Auto-label if confident enough
        if sentiment_result['should_auto_label'] and sentiment_result['suggested_outcome'] is not None:
            lead.actual_outcome = sentiment_result['suggested_outcome']
            lead.auto_labeled = True
            lead.needs_manual_review = False
            
            print(f"✅ Auto-labeled {lead.company_name}: outcome={sentiment_result['suggested_outcome']} (sentiment={sentiment_result['sentiment']}, confidence={sentiment_result['confidence']:.2f})")
        else:
            lead.needs_manual_review = True
            print(f"⚠️ {lead.company_name} needs manual review (confidence={sentiment_result['confidence']:.2f})")
        
        # Update status
        if sentiment_result['sentiment'] == 'positive':
            lead.status = 'interested'
        elif sentiment_result['sentiment'] == 'negative':
            lead.status = 'closed'
        else:
            lead.status = 'follow_up'
        
        db.commit()
        
        print(f"📧 Processed reply from {lead.company_name}: {sentiment_result['sentiment']} ({sentiment_result['confidence']:.0%})")
    
    def _extract_mailhog_body(self, msg: Dict) -> str:
        """Extract body from MailHog message format"""
        try:
            body = msg.get('Content', {}).get('Body', '')
            # MailHog stores body as plain text
            return body
        except:
            return ""
    
    def _extract_email_address(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+', from_header)
        return match.group(0) if match else from_header
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
        if not header:
            return ""
        decoded = decode_header(header)
        decoded_str = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += part
        return decoded_str
    
    def _extract_email_body(self, msg) -> str:
        """Extract plain text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body
