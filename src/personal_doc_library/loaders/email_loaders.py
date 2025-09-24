#!/usr/bin/env python3
"""
Email loaders for indexing local email storage from Apple Mail and Outlook.
Supports filtering by marketing emails, folders, mailboxes, and date ranges.
"""

import os
import re
import logging
import json
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
from langchain.schema import Document
import hashlib

logger = logging.getLogger(__name__)

class EmailFilterConfig:
    """Configuration for email filtering during indexing"""
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        # Marketing email detection patterns
        self.marketing_patterns = config.get('marketing_patterns', [
            # Common unsubscribe patterns
            r'unsubscribe',
            r'opt.?out',
            r'remove\s+from\s+(mailing|email)\s+list',
            r'email\s+preferences',
            r'manage\s+subscriptions',
            r'update\s+your\s+preferences',
            # Marketing keywords in headers
            r'list-unsubscribe',
            r'bulk',
            r'newsletter',
            r'promotional',
            # Common marketing sender patterns
            r'noreply@',
            r'no-reply@',
            r'donotreply@',
            r'marketing@',
            r'newsletter@',
            r'notifications@',
            r'updates@',
            r'info@',
            r'news@',
            r'promo@',
            # Shopping and e-commerce patterns
            r'order\s+confirmation',
            r'order\s+#\d+',
            r'your\s+order\s+(has|is)',
            r'shipment\s+tracking',
            r'delivery\s+confirmation',
            r'package\s+delivered',
            r'invoice\s+#',
            r'receipt\s+for',
            r'payment\s+received',
            r'transaction\s+confirmation',
            r'shopping\s+cart',
            r'items?\s+in\s+your\s+cart',
            r'complete\s+your\s+purchase',
            r'abandoned\s+cart',
            r'sale\s+ends',
            r'limited\s+time\s+offer',
            r'special\s+offer',
            r'exclusive\s+deal',
            r'discount\s+code',
            r'coupon',
            r'save\s+\d+%',
            r'free\s+shipping',
            r'flash\s+sale',
            r'clearance',
            r'black\s+friday',
            r'cyber\s+monday',
            # Promotional patterns
            r'act\s+now',
            r'don\'t\s+miss\s+out',
            r'hurry',
            r'expires\s+soon',
            r'last\s+chance',
            r'today\s+only',
            r'deal\s+of\s+the\s+day',
            r'weekly\s+deals',
            r'new\s+arrivals',
            r'back\s+in\s+stock',
            r'recommended\s+for\s+you',
            r'you\s+might\s+like',
            r'similar\s+items',
        ])
        
        # Mailboxes/accounts to exclude (e.g., 'marketing@company.com')
        self.excluded_mailboxes = set(config.get('excluded_mailboxes', []))
        
        # Folders to exclude (e.g., 'Promotions', 'Spam', 'Trash')
        self.excluded_folders = set(config.get('excluded_folders', [
            'Spam', 'Junk', 'Trash', 'Deleted Items', 'Drafts',
            'Promotions', 'Social', 'Forums', 'Updates'
        ]))
        
        # Folders to include (if specified, only these folders will be indexed)
        self.included_folders = set(config.get('included_folders', []))
        
        # Maximum email age in days (None = no limit)
        self.max_age_days = config.get('max_age_days', 365)
        
        # Minimum email age in days (to avoid indexing very recent emails)
        self.min_age_days = config.get('min_age_days', 0)
        
        # Marketing sender domains to exclude
        self.marketing_domains = set(config.get('marketing_domains', [
            'mailchimp.com', 'sendgrid.net', 'amazonaws.com',
            'salesforce.com', 'hubspot.com', 'constantcontact.com',
            'mailgun.org', 'sendgrid.com', 'mandrillapp.com',
            # E-commerce and shopping domains
            'amazon.com', 'amazonses.com', 'shopify.com', 'ebay.com',
            'etsy.com', 'paypal.com', 'stripe.com', 'square.com',
            'woocommerce.com', 'bigcommerce.com', 'magento.com',
            # Delivery and logistics
            'ups.com', 'fedex.com', 'dhl.com', 'usps.com',
            'shipstation.com', 'stamps.com',
            # Common retailers and brands
            'walmart.com', 'target.com', 'bestbuy.com', 'homedepot.com',
            'lowes.com', 'costco.com', 'apple.com', 'nike.com',
            'adidas.com', 'nordstrom.com', 'macys.com', 'gap.com',
            'oldnavy.com', 'zara.com', 'hm.com', 'ikea.com',
            # Food delivery and restaurants
            'doordash.com', 'ubereats.com', 'grubhub.com', 'postmates.com',
            'instacart.com', 'seamless.com', 'deliveroo.com',
            # Travel and hospitality
            'booking.com', 'expedia.com', 'hotels.com', 'airbnb.com',
            'tripadvisor.com', 'priceline.com', 'kayak.com',
            'marriott.com', 'hilton.com', 'hyatt.com',
            # Subscription services
            'netflix.com', 'spotify.com', 'hulu.com', 'disney.com',
            'hbomax.com', 'paramount.com', 'peacocktv.com',
            'adobe.com', 'microsoft.com', 'dropbox.com',
        ]))
        
        # Important senders to always include (whitelist)
        self.important_senders = set(config.get('important_senders', []))
        
        # Filter by email size (skip very large emails)
        self.max_email_size_mb = config.get('max_email_size_mb', 50)
        
        # Whether to index emails with attachments
        self.include_attachments = config.get('include_attachments', True)
        
        # File extensions to exclude from attachment processing
        self.excluded_attachment_types = set(config.get('excluded_attachment_types', [
            '.exe', '.dll', '.bat', '.cmd', '.scr', '.zip', '.rar'
        ]))

    def is_marketing_email(self, email_content: str, headers: Dict, sender: str = None) -> bool:
        """Detect if an email is likely marketing/promotional"""
        
        # Check if sender is in important senders (whitelist)
        if sender and sender.lower() in self.important_senders:
            return False
        
        # Check sender domain
        if sender:
            domain = sender.split('@')[-1].lower() if '@' in sender else ''
            if any(marketing_domain in domain for marketing_domain in self.marketing_domains):
                logger.debug(f"Marketing email detected: sender domain {domain}")
                return True
        
        # Check for marketing patterns in content
        content_lower = email_content.lower() if email_content else ''
        for pattern in self.marketing_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                logger.debug(f"Marketing email detected: pattern '{pattern}' found")
                return True
        
        # Check headers for marketing indicators
        headers_str = json.dumps(headers).lower() if headers else ''
        if 'list-unsubscribe' in headers_str or 'bulk' in headers_str:
            logger.debug("Marketing email detected: list headers found")
            return True
        
        # Check for multiple recipients (common in marketing emails)
        if headers:
            to_field = headers.get('To', '').lower()
            if 'undisclosed-recipients' in to_field:
                logger.debug("Marketing email detected: undisclosed recipients")
                return True
        
        return False
    
    def should_index_email(self, email_path: str, email_date: datetime, 
                          folder: str, mailbox: str, email_content: str,
                          headers: Dict, sender: str = None) -> bool:
        """Determine if an email should be indexed based on filters"""
        
        # Check mailbox exclusion
        if mailbox and mailbox.lower() in self.excluded_mailboxes:
            logger.debug(f"Skipping email from excluded mailbox: {mailbox}")
            return False
        
        # Check folder inclusion/exclusion
        if self.included_folders:
            # If included_folders is specified, only index those
            if folder and folder not in self.included_folders:
                logger.debug(f"Skipping email from non-included folder: {folder}")
                return False
        elif self.excluded_folders:
            # Otherwise check excluded folders
            if folder and folder in self.excluded_folders:
                logger.debug(f"Skipping email from excluded folder: {folder}")
                return False
        
        # Check email age
        if email_date:
            now = datetime.now()
            email_age_days = (now - email_date).days
            
            if self.max_age_days and email_age_days > self.max_age_days:
                logger.debug(f"Skipping email older than {self.max_age_days} days")
                return False
            
            if self.min_age_days and email_age_days < self.min_age_days:
                logger.debug(f"Skipping email newer than {self.min_age_days} days")
                return False
        
        # Check if it's a marketing email
        if self.is_marketing_email(email_content, headers, sender):
            logger.debug(f"Skipping marketing email from {sender}")
            return False
        
        # Check email size
        if email_path and os.path.exists(email_path):
            size_mb = os.path.getsize(email_path) / (1024 * 1024)
            if size_mb > self.max_email_size_mb:
                logger.debug(f"Skipping email larger than {self.max_email_size_mb}MB")
                return False
        
        return True


class BaseEmailLoader:
    """Base class for email loaders"""
    
    def __init__(self, filter_config: Optional[EmailFilterConfig] = None):
        self.filter_config = filter_config or EmailFilterConfig()
        self.processed_hashes = set()
    
    def extract_email_metadata(self, msg) -> Dict:
        """Extract metadata from email message"""
        metadata = {}
        
        # Basic headers
        metadata['subject'] = msg.get('Subject', 'No Subject')
        metadata['sender'] = msg.get('From', '')
        metadata['recipient'] = msg.get('To', '')
        metadata['cc'] = msg.get('Cc', '')
        metadata['date_str'] = msg.get('Date', '')
        
        # Parse date
        try:
            from email.utils import parsedate_to_datetime
            if metadata['date_str']:
                metadata['date'] = parsedate_to_datetime(metadata['date_str'])
            else:
                metadata['date'] = None
        except Exception as e:
            logger.warning(f"Could not parse date: {e}")
            metadata['date'] = None
        
        # Message ID for deduplication
        metadata['message_id'] = msg.get('Message-ID', '')
        
        # Check for attachments
        metadata['has_attachments'] = False
        metadata['attachment_count'] = 0
        metadata['attachment_names'] = []
        
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')
            if 'attachment' in content_disposition:
                metadata['has_attachments'] = True
                metadata['attachment_count'] += 1
                filename = part.get_filename()
                if filename:
                    metadata['attachment_names'].append(filename)
        
        return metadata
    
    def extract_email_body(self, msg) -> str:
        """Extract text body from email message"""
        body_parts = []
        
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition', '')
            
            # Skip attachments
            if 'attachment' in content_disposition:
                continue
            
            # Extract text parts
            if content_type == 'text/plain':
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or 'utf-8'
                        body_parts.append(body.decode(charset, errors='ignore'))
                except Exception as e:
                    logger.warning(f"Error extracting text body: {e}")
            
            elif content_type == 'text/html' and not body_parts:
                # Use HTML only if no plain text is available
                try:
                    html_body = part.get_payload(decode=True)
                    if html_body:
                        charset = part.get_content_charset() or 'utf-8'
                        # Simple HTML to text conversion
                        import re
                        text = html_body.decode(charset, errors='ignore')
                        # Remove HTML tags
                        text = re.sub(r'<[^>]+>', ' ', text)
                        # Clean up whitespace
                        text = re.sub(r'\s+', ' ', text)
                        body_parts.append(text.strip())
                except Exception as e:
                    logger.warning(f"Error extracting HTML body: {e}")
        
        return '\n\n'.join(body_parts)
    
    def extract_attachments(self, msg, email_path: str) -> List[Dict]:
        """Extract attachments from email message"""
        attachments = []
        
        if not self.filter_config.include_attachments:
            return attachments
        
        for part in msg.walk():
            content_disposition = part.get('Content-Disposition', '')
            
            if 'attachment' in content_disposition:
                filename = part.get_filename()
                if filename:
                    # Check if attachment type is excluded
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext in self.filter_config.excluded_attachment_types:
                        logger.debug(f"Skipping excluded attachment type: {filename}")
                        continue
                    
                    try:
                        data = part.get_payload(decode=True)
                        if data:
                            attachments.append({
                                'filename': filename,
                                'size': len(data),
                                'content_type': part.get_content_type(),
                                'data': data
                            })
                    except Exception as e:
                        logger.warning(f"Error extracting attachment {filename}: {e}")
        
        return attachments
    
    def create_document(self, email_content: str, metadata: Dict, source_path: str) -> Document:
        """Create a Langchain Document from email content"""
        
        # Generate a unique hash for deduplication
        content_hash = hashlib.md5(
            (metadata.get('message_id', '') + email_content).encode()
        ).hexdigest()
        
        if content_hash in self.processed_hashes:
            logger.debug(f"Skipping duplicate email: {metadata.get('subject')}")
            return None
        
        self.processed_hashes.add(content_hash)
        
        # Prepare document metadata
        doc_metadata = {
            'source': source_path,
            'type': 'email',
            'email_subject': metadata.get('subject', ''),
            'email_sender': metadata.get('sender', ''),
            'email_recipient': metadata.get('recipient', ''),
            'email_date': metadata.get('date').isoformat() if metadata.get('date') else '',
            'has_attachments': metadata.get('has_attachments', False),
            'attachment_count': metadata.get('attachment_count', 0),
            'message_id': metadata.get('message_id', ''),
            'content_hash': content_hash
        }
        
        # Create document with email content
        document = Document(
            page_content=email_content,
            metadata=doc_metadata
        )
        
        return document
    
    def load(self) -> List[Document]:
        """Load emails - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement the load method")