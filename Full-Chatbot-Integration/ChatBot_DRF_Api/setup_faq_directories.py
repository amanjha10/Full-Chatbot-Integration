#!/usr/bin/env python3
"""
📁 FAQ DIRECTORIES SETUP SCRIPT
===============================

This script ensures all necessary directories exist for the FAQ system.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

from django.conf import settings

def setup_faq_directories():
    """Create necessary directories for FAQ system"""
    
    print("📁 SETTING UP FAQ DIRECTORIES")
    print("=" * 40)
    
    # Base directories
    base_dir = settings.BASE_DIR
    refrence_dir = os.path.join(base_dir, 'refrence')
    data_dir = os.path.join(refrence_dir, 'data')
    documents_dir = os.path.join(data_dir, 'documents')
    vectors_dir = os.path.join(data_dir, 'vectors')
    chroma_dir = os.path.join(vectors_dir, 'chroma')
    
    directories = [
        refrence_dir,
        data_dir,
        documents_dir,
        vectors_dir,
        chroma_dir
    ]
    
    # Create directories
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")
    
    # Create general FAQ file if it doesn't exist
    general_faq_path = os.path.join(documents_dir, 'education_faq.json')
    if not os.path.exists(general_faq_path):
        general_faq_data = {
            "general_info": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "description": "General FAQ for study abroad consulting"
            },
            "study_abroad": {
                "general": [
                    {
                        "chunk_id": "general_001",
                        "question": "What services do you offer for study abroad?",
                        "answer": "We offer comprehensive study abroad consulting services including university selection, application assistance, visa guidance, and pre-departure support.",
                        "section": "General FAQ",
                        "document": "General FAQ",
                        "page": 1
                    },
                    {
                        "chunk_id": "general_002",
                        "question": "Which countries do you provide services for?",
                        "answer": "We provide study abroad services for popular destinations including USA, UK, Canada, Australia, Germany, and many other countries.",
                        "section": "General FAQ",
                        "document": "General FAQ",
                        "page": 1
                    },
                    {
                        "chunk_id": "general_003",
                        "question": "How can I contact you for more information?",
                        "answer": "You can contact us through our website contact form, email, or phone. Our consultants are available to help you with your study abroad journey.",
                        "section": "General FAQ",
                        "document": "General FAQ",
                        "page": 1
                    }
                ]
            }
        }
        
        with open(general_faq_path, 'w', encoding='utf-8') as f:
            json.dump(general_faq_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Created general FAQ file: {general_faq_path}")
    else:
        print(f"✅ General FAQ file exists: {general_faq_path}")
    
    # Create sample company FAQ for testing
    sample_company_faq_path = os.path.join(documents_dir, 'company_TEST001_faq.json')
    if not os.path.exists(sample_company_faq_path):
        sample_company_data = {
            "company_info": {
                "company_id": "TEST001",
                "company_name": "Test Company",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "company_faqs": {
                "Services": [
                    {
                        "chunk_id": "company_TEST001_001",
                        "question": "What services does Test Company offer?",
                        "answer": "Test Company offers premium consulting services including business strategy, digital transformation, and market analysis.",
                        "section": "Company FAQ",
                        "document": "TEST001 Company FAQ",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                ],
                "Contact": [
                    {
                        "chunk_id": "company_TEST001_002",
                        "question": "How can I contact Test Company?",
                        "answer": "You can reach Test Company through our 24/7 support hotline or email us at support@testcompany.com.",
                        "section": "Company FAQ",
                        "document": "TEST001 Company FAQ",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                ]
            }
        }
        
        with open(sample_company_faq_path, 'w', encoding='utf-8') as f:
            json.dump(sample_company_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Created sample company FAQ file: {sample_company_faq_path}")
    else:
        print(f"✅ Sample company FAQ file exists: {sample_company_faq_path}")
    
    print(f"\n🎉 FAQ directories setup completed!")
    print("=" * 40)
    
    # List all FAQ files
    print(f"\n📋 FAQ Files Found:")
    for file in os.listdir(documents_dir):
        if file.endswith('.json'):
            file_path = os.path.join(documents_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size} bytes)")

if __name__ == '__main__':
    try:
        setup_faq_directories()
    except Exception as e:
        print(f"❌ Error setting up directories: {e}")
        import traceback
        traceback.print_exc()
