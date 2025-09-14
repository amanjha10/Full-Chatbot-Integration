#!/usr/bin/env python3
"""
🔍 RAG System Debug Test
========================

Test the RAG system to see what's happening with vector search
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/amanjha/Documents/Consultancy_ChatBot/Full-Chatbot-Integration/ChatBot_DRF_Api')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_system.settings')
django.setup()

def test_rag_system():
    """Test the RAG system with debug output"""
    try:
        from chatbot.utils.rag_system import rag_system
        
        print("🔍 Testing RAG System")
        print("=" * 50)
        
        # Test queries
        test_queries = [
            "what are the visa requirements",
            "visa requirements",
            "student visa",
            "what kind of universities has Growth wings successfully placed students in",
            "Growth wings universities",
            "headphones"  # This should not match anything
        ]
        
        company_id = "NHS001"
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            print("-" * 40)
            
            # Test the search method directly
            results = rag_system.search(query, k=3, company_id=company_id)
            print(f"📊 Search returned {len(results)} results")
            
            for i, result in enumerate(results):
                print(f"  Result {i+1}:")
                print(f"    Question: {result.get('question', 'N/A')[:80]}...")
                print(f"    Answer: {result.get('answer', 'N/A')[:80]}...")
                print(f"    Similarity: {result.get('similarity', 0):.3f}")
                print(f"    Source: {result.get('source_type', 'N/A')}")
                print(f"    Company: {result.get('company_id', 'N/A')}")
            
            # Test get_best_answer
            best_answer = rag_system.get_best_answer(query, min_score=0.2, company_id=company_id)
            if best_answer:
                print(f"✅ Best answer found:")
                print(f"    Question: {best_answer.get('question', 'N/A')[:80]}...")
                print(f"    Answer: {best_answer.get('answer', 'N/A')[:80]}...")
                print(f"    Similarity: {best_answer.get('similarity', 0):.3f}")
                print(f"    Source: {best_answer.get('source_type', 'N/A')}")
            else:
                print("❌ No best answer found")
            
            print()
        
        # Test ChromaDB connection
        print("\n🗄️ Testing ChromaDB Connection")
        print("-" * 40)
        
        if rag_system.is_initialized:
            print("✅ RAG system is initialized")
            
            # Test collections
            try:
                collections = rag_system.chroma_client.list_collections()
                print(f"📚 Found {len(collections)} collections:")
                for collection in collections:
                    count = collection.count()
                    print(f"  - {collection.name}: {count} documents")
            except Exception as e:
                print(f"❌ Error listing collections: {e}")
        else:
            print("❌ RAG system not initialized")
            
        # Test specific collections
        print("\n📚 Testing Specific Collections")
        print("-" * 40)
        
        # Test company collection
        try:
            company_collection = rag_system.chroma_client.get_collection(f"company_{company_id}_faq")
            company_count = company_collection.count()
            print(f"✅ Company collection (company_{company_id}_faq): {company_count} documents")
            
            # Test a simple query on company collection
            if company_count > 0:
                test_results = company_collection.query(
                    query_texts=["location"],
                    n_results=3,
                    include=['documents', 'metadatas', 'distances']
                )
                print(f"  Sample query results: {len(test_results['documents'][0]) if test_results['documents'] else 0}")
                
        except Exception as e:
            print(f"❌ Company collection error: {e}")
        
        # Test general collection
        try:
            general_collection = rag_system.chroma_client.get_collection("general_faq")
            general_count = general_collection.count()
            print(f"✅ General collection (general_faq): {general_count} documents")
            
            # Test a simple query on general collection
            if general_count > 0:
                test_results = general_collection.query(
                    query_texts=["visa requirements"],
                    n_results=3,
                    include=['documents', 'metadatas', 'distances']
                )
                print(f"  Sample query results: {len(test_results['documents'][0]) if test_results['documents'] else 0}")
                
        except Exception as e:
            print(f"❌ General collection error: {e}")
            
    except Exception as e:
        print(f"❌ Error testing RAG system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_system()
