#!/usr/bin/env python3
"""
Apple Mail EMLX file loader for ragdex.
Processes locally stored Apple Mail emails and attachments.
"""

import os
import glob
import logging
import plistlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import email
from email.parser import BytesParser
from email import policy
from langchain.schema import Document

try:
    import emlx
    EMLX_AVAILABLE = True
except ImportError:
    EMLX_AVAILABLE = False
    logging.warning("emlx library not available. Install with: pip install emlx")

from .email_loaders import BaseEmailLoader, EmailFilterConfig

logger = logging.getLogger(__name__)


class EMLXLoader(BaseEmailLoader):
    """Loader for Apple Mail EMLX files"""
    
    def __init__(self, mail_directory: Optional[str] = None, 
                 filter_config: Optional[EmailFilterConfig] = None):
        super().__init__(filter_config)
        
        # Default Apple Mail directory
        if mail_directory:
            self.mail_directory = Path(mail_directory)
        else:
            # Try common Apple Mail locations
            possible_locations = [
                Path.home() / "Library" / "Mail",
                Path.home() / "Library" / "Containers" / "com.apple.mail" / "Data" / "Library" / "Mail"
            ]
            
            for location in possible_locations:
                if location.exists():
                    self.mail_directory = location
                    logger.info(f"Found Apple Mail directory: {location}")
                    break
            else:
                self.mail_directory = Path.home() / "Library" / "Mail"
                logger.warning(f"Apple Mail directory not found, using default: {self.mail_directory}")
        
        self.documents = []
        self.stats = {
            'total_emails_found': 0,
            'emails_processed': 0,
            'emails_skipped': 0,
            'marketing_emails_skipped': 0,
            'attachments_processed': 0,
            'errors': 0
        }
    
    def find_emlx_files(self) -> List[Path]:
        """Find all EMLX files in the mail directory"""
        emlx_files = []
        
        # Search patterns for EMLX files
        patterns = [
            "V*/MailData/Messages/**/*.emlx",
            "V*/MailData/**/*.emlx",
            "V*/**/*.mbox/Messages/*.emlx",
            "**/*.emlx"  # Fallback pattern
        ]
        
        for pattern in patterns:
            search_path = self.mail_directory / pattern
            found_files = glob.glob(str(search_path), recursive=True)
            emlx_files.extend([Path(f) for f in found_files])
        
        # Remove duplicates
        emlx_files = list(set(emlx_files))
        
        logger.info(f"Found {len(emlx_files)} EMLX files in {self.mail_directory}")
        self.stats['total_emails_found'] = len(emlx_files)
        
        return emlx_files
    
    def extract_folder_and_mailbox(self, file_path: Path) -> tuple[str, str]:
        """Extract folder and mailbox information from file path"""
        path_parts = file_path.parts
        
        folder = "Unknown"
        mailbox = "Unknown"
        
        # Try to extract folder name (usually the .mbox directory name)
        for i, part in enumerate(path_parts):
            if part.endswith('.mbox'):
                folder = part[:-5]  # Remove .mbox extension
                # Try to get mailbox/account from previous parts
                if i > 0:
                    for j in range(i-1, -1, -1):
                        if '@' in path_parts[j] or 'MailData' not in path_parts[j]:
                            mailbox = path_parts[j]
                            break
                break
        
        # Alternative pattern for newer Mail versions
        if 'MailData' in str(file_path):
            # Extract from path like: MailData/Library/Mail/V8/[account]/[folder].mbox/
            try:
                mail_data_idx = path_parts.index('MailData')
                if mail_data_idx + 3 < len(path_parts):
                    potential_account = path_parts[mail_data_idx + 3]
                    if '@' in potential_account:
                        mailbox = potential_account
            except (ValueError, IndexError):
                pass
        
        return folder, mailbox
    
    def parse_emlx_file(self, file_path: Path) -> Optional[Dict]:
        """Parse an EMLX file and extract email data"""
        try:
            if EMLX_AVAILABLE:
                # Use emlx library if available
                msg = emlx.read(str(file_path))
                
                # Extract metadata
                metadata = self.extract_email_metadata(msg)
                
                # Extract body
                body = self.extract_email_body(msg)
                
                # Get folder and mailbox info
                folder, mailbox = self.extract_folder_and_mailbox(file_path)
                
                # Extract attachments
                attachments = self.extract_attachments(msg, str(file_path))
                
                return {
                    'message': msg,
                    'metadata': metadata,
                    'body': body,
                    'folder': folder,
                    'mailbox': mailbox,
                    'attachments': attachments,
                    'file_path': file_path
                }
            
            else:
                # Fallback: Parse EMLX file manually
                with open(file_path, 'rb') as f:
                    # EMLX files have a length indicator at the beginning
                    # Read the first line to get the message length
                    length_line = f.readline()
                    try:
                        message_length = int(length_line.strip())
                    except ValueError:
                        logger.warning(f"Could not parse EMLX length indicator: {file_path}")
                        return None
                    
                    # Read the email message
                    email_data = f.read(message_length)
                    
                    # Parse the email
                    msg = BytesParser(policy=policy.default).parsebytes(email_data)
                    
                    # Extract metadata
                    metadata = self.extract_email_metadata(msg)
                    
                    # Extract body
                    body = self.extract_email_body(msg)
                    
                    # Get folder and mailbox info
                    folder, mailbox = self.extract_folder_and_mailbox(file_path)
                    
                    # Extract attachments
                    attachments = self.extract_attachments(msg, str(file_path))
                    
                    # The rest of the file contains XML plist with flags
                    # We can parse this for additional metadata if needed
                    remaining_data = f.read()
                    if remaining_data:
                        try:
                            plist_data = plistlib.loads(remaining_data)
                            metadata['flags'] = plist_data.get('flags', [])
                        except:
                            pass
                    
                    return {
                        'message': msg,
                        'metadata': metadata,
                        'body': body,
                        'folder': folder,
                        'mailbox': mailbox,
                        'attachments': attachments,
                        'file_path': file_path
                    }
        
        except Exception as e:
            logger.error(f"Error parsing EMLX file {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_attachments(self, attachments: List[Dict], parent_metadata: Dict) -> List[Document]:
        """Process email attachments and create documents"""
        attachment_docs = []
        
        # Import document loaders for attachments
        from ..core.shared_rag import (
            PyPDFLoader, 
            UnstructuredWordDocumentLoader,
            UnstructuredPowerPointLoader
        )
        
        import tempfile
        
        for attachment in attachments:
            try:
                filename = attachment['filename']
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Check if this is a supported document type
                supported_extensions = ('.pdf', '.docx', '.doc', '.pptx', '.ppt')
                if file_ext not in supported_extensions:
                    continue
                
                # Save attachment to temp file
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
                    tmp_file.write(attachment['data'])
                    tmp_path = tmp_file.name
                
                try:
                    # Load attachment based on type
                    if file_ext == '.pdf':
                        loader = PyPDFLoader(tmp_path)
                    elif file_ext in ['.docx', '.doc']:
                        loader = UnstructuredWordDocumentLoader(tmp_path)
                    elif file_ext in ['.pptx', '.ppt']:
                        loader = UnstructuredPowerPointLoader(tmp_path)
                    else:
                        continue
                    
                    # Load the document
                    docs = loader.load()
                    
                    # Add email metadata to attachment documents
                    for doc in docs:
                        doc.metadata.update({
                            'type': 'email_attachment',
                            'parent_email_subject': parent_metadata.get('subject', ''),
                            'parent_email_sender': parent_metadata.get('sender', ''),
                            'parent_email_date': parent_metadata.get('date').isoformat() if parent_metadata.get('date') else '',
                            'attachment_filename': filename
                        })
                        attachment_docs.append(doc)
                    
                    self.stats['attachments_processed'] += 1
                    
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            except Exception as e:
                logger.warning(f"Error processing attachment {attachment.get('filename')}: {e}")
        
        return attachment_docs
    
    def load(self) -> List[Document]:
        """Load and process all EMLX files"""
        
        # Find all EMLX files
        emlx_files = self.find_emlx_files()
        
        if not emlx_files:
            logger.warning("No EMLX files found")
            return []
        
        # Process each EMLX file
        for file_path in emlx_files:
            try:
                # Parse the EMLX file
                email_data = self.parse_emlx_file(file_path)
                
                if not email_data:
                    continue
                
                # Check if we should index this email
                should_index = self.filter_config.should_index_email(
                    email_path=str(file_path),
                    email_date=email_data['metadata'].get('date'),
                    folder=email_data['folder'],
                    mailbox=email_data['mailbox'],
                    email_content=email_data['body'],
                    headers=dict(email_data['message'].items()) if email_data['message'] else {},
                    sender=email_data['metadata'].get('sender')
                )
                
                if not should_index:
                    self.stats['emails_skipped'] += 1
                    
                    # Check if it was a marketing email
                    if self.filter_config.is_marketing_email(
                        email_data['body'],
                        dict(email_data['message'].items()) if email_data['message'] else {},
                        email_data['metadata'].get('sender')
                    ):
                        self.stats['marketing_emails_skipped'] += 1
                    continue
                
                # Create document from email
                doc = self.create_document(
                    email_content=email_data['body'],
                    metadata=email_data['metadata'],
                    source_path=str(file_path)
                )
                
                if doc:
                    # Add folder and mailbox to metadata
                    doc.metadata['email_folder'] = email_data['folder']
                    doc.metadata['email_mailbox'] = email_data['mailbox']
                    
                    self.documents.append(doc)
                    self.stats['emails_processed'] += 1
                    
                    # Process attachments if any
                    if email_data['attachments']:
                        attachment_docs = self.process_attachments(
                            email_data['attachments'],
                            email_data['metadata']
                        )
                        self.documents.extend(attachment_docs)
            
            except Exception as e:
                logger.error(f"Error processing EMLX file {file_path}: {e}")
                self.stats['errors'] += 1
                continue
        
        # Log statistics
        logger.info(f"Email processing complete:")
        logger.info(f"  Total found: {self.stats['total_emails_found']}")
        logger.info(f"  Processed: {self.stats['emails_processed']}")
        logger.info(f"  Skipped: {self.stats['emails_skipped']}")
        logger.info(f"  Marketing skipped: {self.stats['marketing_emails_skipped']}")
        logger.info(f"  Attachments: {self.stats['attachments_processed']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        return self.documents