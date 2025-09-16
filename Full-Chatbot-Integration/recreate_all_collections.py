#!/usr/bin/env python3
"""
# UNUSED - VECTOR RECREATION COMPLETED - Safe to remove if not required
#
# 🔄 Recreate All Vector Collections
# ==================================
#
# Load all FAQ data from JSON files into ChromaDB collections
#
# STATUS: ✅ COMPLETED - Vector collections successfully recreated
# LAST USED: During RAG system restoration
# SAFE TO REMOVE: Yes, collections are now properly populated
"""

import os
import sys
import json
import django

# Add the project directory to Python path
sys.path.append('/Users/amanjha/Documents/Consultancy_ChatBot/Full-Chatbot-Integration/ChatBot_DRF_Api')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

def recreate_general_collection():
    """Recreate the general FAQ collection from education_faq.json"""
    try:
        from chatbot.utils.vector_refresh_manager import vector_refresh_manager
        
        print("🌐 Recreating General FAQ Collection")
        print("=" * 50)
        
        result = vector_refresh_manager.refresh_general_vectors()
        
        if result['success']:
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error recreating general collection: {e}")
        import traceback
        traceback.print_exc()
        return False

def recreate_company_collections():
    """Recreate all company-specific collections"""
    try:
        from chatbot.utils.vector_refresh_manager import vector_refresh_manager
        
        print("\n🏢 Recreating Company FAQ Collections")
        print("=" * 50)
        
        # Find all company FAQ files
        documents_dir = '/Users/amanjha/Documents/Consultancy_ChatBot/Full-Chatbot-Integration/ChatBot_DRF_Api/refrence/data/documents'
        
        company_files = []
        for filename in os.listdir(documents_dir):
            if filename.startswith('company_') and filename.endswith('_faq.json'):
                # Extract company ID from filename: company_NHS001_faq.json -> NHS001
                company_id = filename.replace('company_', '').replace('_faq.json', '')
                company_files.append((company_id, filename))
        
        print(f"📁 Found {len(company_files)} company FAQ files:")
        for company_id, filename in company_files:
            print(f"   - {filename} → Company ID: {company_id}")
        
        success_count = 0
        for company_id, filename in company_files:
            print(f"\n🔄 Processing company {company_id}...")
            
            result = vector_refresh_manager.refresh_company_vectors(company_id)
            
            if result['success']:
                print(f"✅ {result['message']}")
                success_count += 1
            else:
                print(f"❌ {result['message']}")
        
        print(f"\n📊 Summary: {success_count}/{len(company_files)} company collections created successfully")
        return success_count == len(company_files)
        
    except Exception as e:
        print(f"❌ Error recreating company collections: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_collections():
    """Verify that all collections were created successfully"""
    try:
        from chatbot.utils.rag_system import rag_system
        
        print("\n🔍 Verifying Collections")
        print("=" * 50)
        
        if not rag_system.is_initialized:
            print("❌ RAG system not initialized")
            return False
        
        # List all collections
        collections = rag_system.chroma_client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        
        total_documents = 0
        for collection in collections:
            count = collection.count()
            total_documents += count
            print(f"   - {collection.name}: {count} documents")
        
        print(f"\n📊 Total documents across all collections: {total_documents}")
        
        # Test a sample query
        print("\n🧪 Testing Sample Queries")
        print("-" * 30)
        
        test_queries = [
            ("visa requirements", "NHS001"),
            ("Growth wings universities", None),
            ("company location", "NHS001")
        ]
        
        for query, company_id in test_queries:
            print(f"\n🔍 Query: '{query}' (Company: {company_id or 'General'})")
            
            result = rag_system.get_best_answer(query, min_score=0.2, company_id=company_id)
            if result:
                print(f"✅ Found answer:")
                print(f"   Question: {result.get('question', 'N/A')[:60]}...")
                print(f"   Answer: {result.get('answer', 'N/A')[:60]}...")
                print(f"   Similarity: {result.get('similarity', 0):.3f}")
                print(f"   Source: {result.get('source_type', 'N/A')}")
            else:
                print("❌ No answer found")
        
        return total_documents > 0
        
    except Exception as e:
        print(f"❌ Error verifying collections: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to recreate all collections"""
    print("🔄 Recreating All Vector Collections")
    print("=" * 60)
    
    # Step 1: Recreate general collection
    general_success = recreate_general_collection()
    
    # Step 2: Recreate company collections
    company_success = recreate_company_collections()
    
    # Step 3: Verify collections
    verification_success = verify_collections()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL SUMMARY")
    print("=" * 60)
    
    if general_success:
        print("✅ General FAQ collection created successfully")
    else:
        print("❌ General FAQ collection failed")
    
    if company_success:
        print("✅ Company FAQ collections created successfully")
    else:
        print("❌ Some company FAQ collections failed")
    
    if verification_success:
        print("✅ Collections verified and working")
    else:
        print("❌ Collection verification failed")
    
    if general_success and company_success and verification_success:
        print("\n🎉 ALL COLLECTIONS RECREATED SUCCESSFULLY!")
        print("   Your RAG system should now work properly.")
    else:
        print("\n⚠️ Some issues occurred. Check the logs above.")

if __name__ == "__main__":
    main()
