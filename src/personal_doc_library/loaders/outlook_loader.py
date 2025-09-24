#!/usr/bin/env python3
"""
Outlook local storage loader for ragdex.
Processes locally stored Outlook emails from OLM files or local cache.
"""

import os
import zipfile
import xml.etree.ElementTree as ET
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import email
from email.parser import BytesParser
from email import policy
from langchain.schema import Document

from .email_loaders import BaseEmailLoader, EmailFilterConfig

logger = logging.getLogger(__name__)


class OutlookLocalLoader(BaseEmailLoader):
    """Loader for Outlook local storage (OLM files)"""
    
    def __init__(self, olm_path: Optional[str] = None,
                 filter_config: Optional[EmailFilterConfig] = None):
        super().__init__(filter_config)
        
        self.olm_path = olm_path
        self.temp_dir = None
        self.documents = []
        self.stats = {
            'total_emails_found': 0,
            'emails_processed': 0,
            'emails_skipped': 0,
            'marketing_emails_skipped': 0,
            'attachments_processed': 0,
            'errors': 0
        }
    
    def find_olm_files(self) -> List[Path]:
        """Find OLM files in common locations or use provided path"""
        if self.olm_path:
            if os.path.exists(self.olm_path):
                return [Path(self.olm_path)]
            else:
                logger.warning(f"Specified OLM file not found: {self.olm_path}")
                return []
        
        # Look for OLM files in common locations
        common_locations = [
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
            Path.home() / "Library" / "Group Containers" / "UBF8T346G9.Office" / "Outlook"
        ]
        
        olm_files = []
        for location in common_locations:
            if location.exists():
                olm_files.extend(location.glob("*.olm"))
        
        if olm_files:
            logger.info(f"Found {len(olm_files)} OLM files")
        else:
            logger.warning("No OLM files found. Please export from Outlook: File > Export")
        
        return olm_files
    
    def extract_olm(self, olm_path: Path) -> Optional[Path]:
        """Extract OLM archive to temporary directory"""
        try:
            # Create temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="outlook_olm_")
            temp_path = Path(self.temp_dir)
            
            # OLM files are essentially ZIP archives
            with zipfile.ZipFile(olm_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            logger.info(f"Extracted OLM file to {temp_path}")
            return temp_path
        
        except Exception as e:
            logger.error(f"Error extracting OLM file: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return None
    
    def parse_olm_structure(self, extracted_path: Path) -> Dict:
        """Parse the OLM file structure to find emails"""
        structure = {
            'folders': {},
            'emails': []
        }
        
        # Look for email files in the extracted directory
        # OLM structure typically includes:
        # - com.microsoft.outlook.email/
        # - Local/
        # - Messages/
        
        email_dirs = [
            extracted_path / "com.microsoft.outlook.email",
            extracted_path / "Local",
            extracted_path / "Messages"
        ]
        
        for email_dir in email_dirs:
            if email_dir.exists():
                # Find all email files (usually .eml or similar)
                for email_file in email_dir.rglob("*"):
                    if email_file.is_file():
                        # Try to determine if it's an email file
                        if email_file.suffix.lower() in ['.eml', '.msg', '.xml', '']:
                            structure['emails'].append(email_file)
        
        logger.info(f"Found {len(structure['emails'])} potential email files")
        self.stats['total_emails_found'] = len(structure['emails'])
        
        return structure
    
    def parse_email_file(self, file_path: Path) -> Optional[Dict]:
        """Parse an individual email file from OLM"""
        try:
            # Try to parse as EML format first
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            
            # Extract metadata
            metadata = self.extract_email_metadata(msg)
            
            # Extract body
            body = self.extract_email_body(msg)
            
            # Try to determine folder from path
            folder = "Inbox"  # Default
            path_parts = file_path.parts
            for part in ['Inbox', 'Sent', 'Drafts', 'Deleted', 'Archive']:
                if part.lower() in str(file_path).lower():
                    folder = part
                    break
            
            # Extract attachments
            attachments = self.extract_attachments(msg, str(file_path))
            
            return {
                'message': msg,
                'metadata': metadata,
                'body': body,
                'folder': folder,
                'mailbox': 'Outlook',
                'attachments': attachments,
                'file_path': file_path
            }
        
        except Exception as e:
            # Try XML format (some OLM files use XML)
            try:
                return self.parse_xml_email(file_path)
            except:
                logger.debug(f"Could not parse email file {file_path}: {e}")
                return None
    
    def parse_xml_email(self, file_path: Path) -> Optional[Dict]:
        """Parse XML-formatted email from OLM"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract email data from XML
            # This is a simplified parser - actual OLM XML structure may vary
            metadata = {}
            body = ""
            
            # Look for common email fields
            for field in ['Subject', 'From', 'To', 'Date', 'Body']:
                element = root.find(f".//{field}")
                if element is not None:
                    if field == 'Body':
                        body = element.text or ""
                    else:
                        metadata[field.lower()] = element.text or ""
            
            # Parse date if present
            if 'date' in metadata:
                try:
                    from email.utils import parsedate_to_datetime
                    metadata['date'] = parsedate_to_datetime(metadata['date'])
                except:
                    metadata['date'] = None
            
            return {
                'message': None,
                'metadata': metadata,
                'body': body,
                'folder': 'Inbox',
                'mailbox': 'Outlook',
                'attachments': [],
                'file_path': file_path
            }
        
        except Exception as e:
            logger.debug(f"Could not parse XML email {file_path}: {e}")
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
        """Load and process Outlook emails"""
        
        # Find OLM files
        olm_files = self.find_olm_files()
        
        if not olm_files:
            logger.warning("No OLM files found. Please export from Outlook: File > Export")
            return []
        
        # Process each OLM file
        for olm_file in olm_files:
            try:
                logger.info(f"Processing OLM file: {olm_file}")
                
                # Extract OLM archive
                extracted_path = self.extract_olm(olm_file)
                if not extracted_path:
                    continue
                
                # Parse OLM structure
                structure = self.parse_olm_structure(extracted_path)
                
                # Process each email
                for email_path in structure['emails']:
                    try:
                        # Parse the email file
                        email_data = self.parse_email_file(email_path)
                        
                        if not email_data:
                            continue
                        
                        # Check if we should index this email
                        should_index = self.filter_config.should_index_email(
                            email_path=str(email_path),
                            email_date=email_data['metadata'].get('date'),
                            folder=email_data['folder'],
                            mailbox=email_data['mailbox'],
                            email_content=email_data['body'],
                            headers=dict(email_data['message'].items()) if email_data['message'] else {},
                            sender=email_data['metadata'].get('sender', email_data['metadata'].get('from', ''))
                        )
                        
                        if not should_index:
                            self.stats['emails_skipped'] += 1
                            
                            # Check if it was a marketing email
                            if self.filter_config.is_marketing_email(
                                email_data['body'],
                                dict(email_data['message'].items()) if email_data['message'] else {},
                                email_data['metadata'].get('sender', email_data['metadata'].get('from', ''))
                            ):
                                self.stats['marketing_emails_skipped'] += 1
                            continue
                        
                        # Create document from email
                        doc = self.create_document(
                            email_content=email_data['body'],
                            metadata=email_data['metadata'],
                            source_path=str(email_path)
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
                        logger.error(f"Error processing email {email_path}: {e}")
                        self.stats['errors'] += 1
                        continue
            
            except Exception as e:
                logger.error(f"Error processing OLM file {olm_file}: {e}")
                self.stats['errors'] += 1
                continue
            
            finally:
                # Clean up temp directory
                if self.temp_dir and os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    self.temp_dir = None
        
        # Log statistics
        logger.info(f"Outlook email processing complete:")
        logger.info(f"  Total found: {self.stats['total_emails_found']}")
        logger.info(f"  Processed: {self.stats['emails_processed']}")
        logger.info(f"  Skipped: {self.stats['emails_skipped']}")
        logger.info(f"  Marketing skipped: {self.stats['marketing_emails_skipped']}")
        logger.info(f"  Attachments: {self.stats['attachments_processed']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        return self.documents