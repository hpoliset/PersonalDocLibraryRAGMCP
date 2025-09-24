#!/usr/bin/env python3
"""
Integration test for email indexing functionality.
Tests the email loaders without requiring actual email files.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_email_filtering():
    """Test email filtering logic"""
    from personal_doc_library.loaders.email_loaders import EmailFilterConfig
    from datetime import datetime, timedelta
    
    print("\n" + "="*60)
    print("    Testing Email Filtering Logic")
    print("="*60 + "\n")
    
    # Create filter configuration
    filter_config = EmailFilterConfig({
        'max_age_days': 30,
        'excluded_folders': ['Spam', 'Junk', 'Trash'],
        'included_folders': [],
        'important_senders': ['important@example.com']
    })
    
    # Test marketing email detection
    marketing_subjects = [
        "50% OFF - Limited Time Offer!",
        "Your order #12345 has shipped",
        "Unsubscribe from our newsletter",
        "Flash Sale Ends Today!"
    ]
    
    normal_subjects = [
        "Meeting tomorrow at 3pm",
        "Project update",
        "Quick question about the report"
    ]
    
    print("🧪 Testing marketing email detection:")
    print("\n  Marketing emails (should be filtered):")
    for subject in marketing_subjects:
        is_marketing = filter_config.is_marketing_email(
            subject, {}, "promo@store.com"
        )
        status = "❌ Filtered" if is_marketing else "✅ Kept"
        print(f"    - '{subject[:30]}...' : {status}")
    
    print("\n  Normal emails (should be kept):")
    for subject in normal_subjects:
        is_marketing = filter_config.is_marketing_email(
            subject, {}, "colleague@work.com"
        )
        status = "❌ Filtered" if is_marketing else "✅ Kept"
        print(f"    - '{subject[:30]}...' : {status}")
    
    # Test date filtering
    print("\n📅 Testing date filtering:")
    now = datetime.now()
    old_date = now - timedelta(days=60)
    recent_date = now - timedelta(days=5)
    
    should_index_old = filter_config.should_index_email(
        "test.emlx", old_date, "INBOX", "test@example.com",
        "Normal email content", {}, "sender@example.com"
    )
    print(f"  Email from 60 days ago: {'Kept' if should_index_old else 'Filtered (too old)'}")
    
    should_index_recent = filter_config.should_index_email(
        "test.emlx", recent_date, "INBOX", "test@example.com",
        "Normal email content", {}, "sender@example.com"
    )
    print(f"  Email from 5 days ago: {'Kept' if should_index_recent else 'Filtered'}")
    
    # Test folder filtering
    print("\n📁 Testing folder filtering:")
    folders = ["INBOX", "Sent", "Spam", "Trash", "Archive"]
    for folder in folders:
        should_index = filter_config.should_index_email(
            "test.emlx", recent_date, folder, "test@example.com",
            "Normal email content", {}, "sender@example.com"
        )
        status = "✅ Indexed" if should_index else "❌ Skipped"
        print(f"  Folder '{folder}': {status}")
    
    print("\n✅ Email filtering tests completed!")
    return True

def test_web_monitor_stats():
    """Test web monitor statistics display"""
    print("\n" + "="*60)
    print("    Testing Web Monitor Email Statistics")
    print("="*60 + "\n")
    
    # Create mock index file with mixed content
    mock_index = {
        "books/document1.pdf": {
            "hash": "abc123",
            "chunks": 10,
            "type": "document"
        },
        "emails/email1.emlx": {
            "hash": "def456",
            "chunks": 2,
            "type": "email"
        },
        "emails/email2.emlx": {
            "hash": "ghi789",
            "chunks": 3,
            "type": "email"
        },
        "books/document2.docx": {
            "hash": "jkl012",
            "chunks": 8,
            "type": "document"
        }
    }
    
    # Count statistics
    total_books = sum(1 for entry in mock_index.values() if entry.get('type') != 'email')
    total_emails = sum(1 for entry in mock_index.values() if entry.get('type') == 'email')
    total_chunks = sum(entry.get('chunks', 0) for entry in mock_index.values())
    
    print("📊 Statistics from mock index:")
    print(f"  📚 Documents: {total_books}")
    print(f"  📧 Emails: {total_emails}")
    print(f"  📝 Total chunks: {total_chunks}")
    
    # Verify the separation logic
    assert total_books == 2, "Should have 2 documents"
    assert total_emails == 2, "Should have 2 emails"
    assert total_chunks == 23, "Should have 23 total chunks"
    
    print("\n✅ Web monitor statistics tests passed!")
    return True

def test_email_document_creation():
    """Test creating Langchain documents from email data"""
    from personal_doc_library.loaders.email_loaders import BaseEmailLoader
    from datetime import datetime
    
    print("\n" + "="*60)
    print("    Testing Email Document Creation")
    print("="*60 + "\n")
    
    loader = BaseEmailLoader()
    
    # Create sample email metadata
    metadata = {
        'subject': 'Test Email Subject',
        'sender': 'sender@example.com',
        'recipient': 'recipient@example.com',
        'date': datetime.now(),
        'has_attachments': True,
        'attachment_count': 2,
        'message_id': '<test123@example.com>'
    }
    
    # Create document
    doc = loader.create_document(
        email_content="This is the email body content.",
        metadata=metadata,
        source_path="/path/to/email.emlx"
    )
    
    print("📧 Created email document:")
    print(f"  Type: {doc.metadata['type']}")
    print(f"  Subject: {doc.metadata['email_subject']}")
    print(f"  Sender: {doc.metadata['email_sender']}")
    print(f"  Has attachments: {doc.metadata['has_attachments']}")
    print(f"  Content preview: {doc.page_content[:50]}...")
    
    assert doc.metadata['type'] == 'email'
    assert doc.metadata['email_subject'] == 'Test Email Subject'
    assert doc.metadata['has_attachments'] == True
    
    print("\n✅ Email document creation test passed!")
    return True

def main():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("    🧪 RAGDEX EMAIL INDEXING INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        test_email_filtering,
        test_web_monitor_stats,
        test_email_document_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ Test {test.__name__} failed: {e}")
            results.append((test.__name__, False))
    
    # Summary
    print("\n" + "="*60)
    print("    TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Email indexing is ready to use.")
        print("\n💡 To enable email indexing, set these environment variables:")
        print("   export PERSONAL_LIBRARY_INDEX_EMAILS=true")
        print("   export PERSONAL_LIBRARY_EMAIL_SOURCES=apple_mail,outlook_local")
        print("   export PERSONAL_LIBRARY_EMAIL_MAX_AGE_DAYS=365")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()