#!/usr/bin/env python3
"""
Test email indexing functionality for ragdex.
Tests Apple Mail EMLX files and shows statistics.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_indexing():
    """Test email indexing with sample emails"""
    
    # Set environment variables for email indexing
    os.environ['PERSONAL_LIBRARY_INDEX_EMAILS'] = 'true'
    os.environ['PERSONAL_LIBRARY_EMAIL_SOURCES'] = 'apple_mail'
    os.environ['PERSONAL_LIBRARY_EMAIL_MAX_AGE_DAYS'] = '365'
    os.environ['PERSONAL_LIBRARY_EMAIL_EXCLUDED_FOLDERS'] = 'Spam,Junk,Trash,Deleted Items,Drafts'
    
    # Look for iCloud email specifically
    os.environ['PERSONAL_LIBRARY_EMAIL_INCLUDED_FOLDERS'] = 'INBOX,Sent'
    
    # Import the loaders
    from personal_doc_library.loaders.emlx_loader import EMLXLoader
    from personal_doc_library.loaders.email_loaders import EmailFilterConfig
    
    print("\n" + "="*60)
    print("    📧 Email Indexing Test for ragdex")
    print("="*60 + "\n")
    
    # Create filter configuration
    filter_config = EmailFilterConfig({
        'max_age_days': 365,
        'excluded_folders': ['Spam', 'Junk', 'Trash', 'Deleted Items', 'Drafts'],
        'included_folders': ['INBOX', 'Sent'],
        # Focus on iCloud email
        'important_senders': ['hpoliset@icloud.com']
    })
    
    # Check for Apple Mail directory
    mail_locations = [
        Path.home() / "Library" / "Mail",
        Path.home() / "Library" / "Containers" / "com.apple.mail" / "Data" / "Library" / "Mail"
    ]
    
    mail_dir = None
    for location in mail_locations:
        if location.exists():
            mail_dir = location
            print(f"✅ Found Apple Mail directory: {mail_dir}")
            break
    
    if not mail_dir:
        print("❌ Apple Mail directory not found")
        print("\nChecked locations:")
        for loc in mail_locations:
            print(f"  - {loc}")
        return
    
    # Look for iCloud email folders
    print("\n📂 Searching for iCloud email folders...")
    icloud_patterns = [
        "*iCloud*",
        "*@icloud.com*",
        "*hpoliset@icloud*"
    ]
    
    found_folders = []
    for pattern in icloud_patterns:
        folders = list(mail_dir.rglob(pattern))
        found_folders.extend(folders)
    
    if found_folders:
        print(f"\nFound {len(set(found_folders))} potential iCloud folders:")
        for folder in set(found_folders):
            print(f"  📁 {folder.relative_to(mail_dir)}")
    
    # Initialize the EMLX loader
    print("\n🔄 Initializing email loader...")
    loader = EMLXLoader(mail_directory=str(mail_dir), filter_config=filter_config)
    
    # Find EMLX files
    print("\n🔍 Searching for EMLX files...")
    emlx_files = loader.find_emlx_files()
    
    if not emlx_files:
        print("❌ No EMLX files found")
        return
    
    print(f"\n✅ Found {len(emlx_files)} EMLX files")
    
    # Show sample of found files
    print("\n📋 Sample of found EMLX files (first 5):")
    for i, file_path in enumerate(emlx_files[:5]):
        try:
            relative_path = file_path.relative_to(mail_dir)
            print(f"  {i+1}. {relative_path}")
        except:
            print(f"  {i+1}. {file_path.name}")
    
    # Load and process emails
    print("\n⚙️  Processing emails (this may take a few moments)...")
    documents = loader.load()
    
    # Show statistics
    print("\n" + "="*60)
    print("    📊 Email Indexing Statistics")
    print("="*60)
    print(f"\n📧 Total emails found: {loader.stats['total_emails_found']}")
    print(f"✅ Emails processed: {loader.stats['emails_processed']}")
    print(f"⏭️  Emails skipped: {loader.stats['emails_skipped']}")
    print(f"🛍️  Marketing emails skipped: {loader.stats['marketing_emails_skipped']}")
    print(f"📎 Attachments processed: {loader.stats['attachments_processed']}")
    print(f"❌ Errors: {loader.stats['errors']}")
    
    # Show sample of processed emails
    if documents:
        print(f"\n📝 Sample of processed emails (first 3):")
        for i, doc in enumerate(documents[:3]):
            meta = doc.metadata
            print(f"\n  {i+1}. Subject: {meta.get('email_subject', 'No Subject')}")
            print(f"     From: {meta.get('email_sender', 'Unknown')}")
            print(f"     Date: {meta.get('email_date', 'Unknown')[:10] if meta.get('email_date') else 'Unknown'}")
            print(f"     Type: {meta.get('type', 'email')}")
            if meta.get('has_attachments'):
                print(f"     📎 Has {meta.get('attachment_count', 0)} attachments")
    
    # Check for specific iCloud emails
    print("\n🔍 Checking for hpoliset@icloud.com emails...")
    icloud_emails = [
        doc for doc in documents 
        if 'hpoliset@icloud.com' in doc.metadata.get('email_sender', '').lower() or
           'hpoliset@icloud.com' in doc.metadata.get('email_recipient', '').lower()
    ]
    
    if icloud_emails:
        print(f"✅ Found {len(icloud_emails)} emails related to hpoliset@icloud.com")
    else:
        print("❌ No emails found for hpoliset@icloud.com")
        print("   This could be due to:")
        print("   - Emails being filtered as marketing/shopping")
        print("   - Emails being in excluded folders")
        print("   - Emails being older than the age limit")
    
    print("\n" + "="*60)
    print("    ✅ Email Indexing Test Complete")
    print("="*60 + "\n")
    
    return documents

if __name__ == "__main__":
    test_email_indexing()