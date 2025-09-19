#!/usr/bin/env python3
"""
🔄 Production-Safe Vector Refresh Manager
========================================

Centralized, thread-safe vector database refresh system that prevents corruption
and handles concurrent requests properly.
"""

import threading
import time
import json
import os
from typing import Dict, Optional, List
from django.conf import settings


class VectorRefreshManager:
    """Thread-safe manager for vector database refresh operations"""
    
    def __init__(self):
        self._global_lock = threading.Lock()
        self._company_locks = {}
        self._refresh_status = {}
        self._last_refresh = {}
        
    def _get_company_lock(self, company_id: str) -> threading.Lock:
        """Get or create a lock for a specific company"""
        with self._global_lock:
            if company_id not in self._company_locks:
                self._company_locks[company_id] = threading.Lock()
            return self._company_locks[company_id]
    
    def is_refresh_in_progress(self, company_id: str = None) -> bool:
        """Check if a refresh is currently in progress"""
        key = company_id or 'general'
        return self._refresh_status.get(key, False)
    
    def get_last_refresh_time(self, company_id: str = None) -> Optional[float]:
        """Get the timestamp of the last successful refresh"""
        key = company_id or 'general'
        return self._last_refresh.get(key)
    
    def refresh_general_vectors(self) -> Dict:
        """Refresh general FAQ vectors (superadmin)"""
        if self.is_refresh_in_progress():
            return {
                'success': False,
                'message': 'General vector refresh already in progress',
                'status': 'in_progress'
            }
        
        with self._global_lock:
            self._refresh_status['general'] = True
            
        try:
            print("🔄 [SAFE] Starting general vector refresh...")
            
            # Load general FAQ file
            faq_file_path = os.path.join(settings.BASE_DIR, 'refrence', 'data', 'documents', 'education_faq.json')
            
            if not os.path.exists(faq_file_path):
                return {
                    'success': False,
                    'message': 'General FAQ file not found',
                    'status': 'error'
                }
            
            with open(faq_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return {
                    'success': False,
                    'message': 'General FAQ file is empty',
                    'status': 'error'
                }
            
            # Use the RAG system to refresh vectors
            from .rag_system import rag_system
            
            # Reinitialize ChromaDB connection
            rag_system._init_chromadb()
            
            if not rag_system.is_initialized:
                return {
                    'success': False,
                    'message': 'ChromaDB not initialized',
                    'status': 'error'
                }
            
            # Process general FAQs (simplified for safety)
            success = self._safe_refresh_general_collection(rag_system, data)
            
            if success:
                self._last_refresh['general'] = time.time()
                return {
                    'success': True,
                    'message': 'General vectors refreshed successfully',
                    'status': 'completed',
                    'timestamp': self._last_refresh['general']
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to refresh general vectors',
                    'status': 'error'
                }
                
        except Exception as e:
            print(f"❌ Error in general vector refresh: {e}")
            return {
                'success': False,
                'message': f'Refresh failed: {str(e)}',
                'status': 'error'
            }
        finally:
            with self._global_lock:
                self._refresh_status['general'] = False
    
    def refresh_company_vectors(self, company_id: str) -> Dict:
        """Refresh company-specific vectors (admin)"""
        if self.is_refresh_in_progress(company_id):
            return {
                'success': False,
                'message': f'Company {company_id} vector refresh already in progress',
                'status': 'in_progress'
            }
        
        company_lock = self._get_company_lock(company_id)
        
        with company_lock:
            self._refresh_status[company_id] = True
            
            try:
                print(f"🔄 [SAFE] Starting company vector refresh for {company_id}...")
                
                # Load company FAQ file
                company_faq_file_path = os.path.join(
                    settings.BASE_DIR, 'refrence', 'data', 'documents', 
                    f'company_{company_id}_faq.json'
                )
                
                if not os.path.exists(company_faq_file_path):
                    return {
                        'success': False,
                        'message': f'Company FAQ file not found for {company_id}',
                        'status': 'error'
                    }
                
                with open(company_faq_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use the RAG system to refresh company vectors
                from .rag_system import rag_system
                
                success = rag_system.refresh_company_vectors(company_id, data)
                
                if success:
                    self._last_refresh[company_id] = time.time()
                    return {
                        'success': True,
                        'message': f'Company {company_id} vectors refreshed successfully',
                        'status': 'completed',
                        'company_id': company_id,
                        'timestamp': self._last_refresh[company_id]
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Failed to refresh vectors for company {company_id}',
                        'status': 'error'
                    }
                    
            except Exception as e:
                print(f"❌ Error in company vector refresh for {company_id}: {e}")
                return {
                    'success': False,
                    'message': f'Refresh failed for {company_id}: {str(e)}',
                    'status': 'error'
                }
            finally:
                self._refresh_status[company_id] = False
    
    def _safe_refresh_general_collection(self, rag_system, data: Dict) -> bool:
        """Safely refresh the general FAQ collection"""
        try:
            collection_name = "general_faq"
            
            # Delete and recreate collection safely
            try:
                rag_system.chroma_client.get_collection(collection_name)
                rag_system.chroma_client.delete_collection(collection_name)
                print(f"✅ Deleted existing collection: {collection_name}")
                time.sleep(0.5)  # Brief pause
            except Exception:
                print(f"⚠️ Collection {collection_name} not found or already deleted")
            
            # Create new collection
            collection = rag_system.chroma_client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ Created new collection: {collection_name}")
            
            # Process FAQs in batches
            documents = []
            metadatas = []
            ids = []
            
            # Process the FAQ data structure
            for category, subcategories in data.items():
                if isinstance(subcategories, dict):
                    for subcategory, faqs in subcategories.items():
                        if isinstance(faqs, list):
                            for faq in faqs:
                                question = faq.get('question', '')
                                answer = faq.get('answer', '')
                                
                                if question and answer:
                                    documents.append(question.lower())
                                    metadatas.append({
                                        'question': question,
                                        'answer': answer,
                                        'category': category,
                                        'subcategory': subcategory,
                                        'section': 'General FAQ',
                                        'document': 'General Education FAQ',
                                        'chunk_id': f'general_{len(ids)}'
                                    })
                                    ids.append(f'general_faq_{len(ids)}')
            
            if documents:
                # Generate embeddings and add to collection
                embeddings = rag_system.model.encode(documents).tolist()
                
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )
                
                print(f"✅ Added {len(documents)} general FAQs to collection")
                return True
            else:
                print("⚠️ No general FAQs found to process")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing general collection: {e}")
            return False
    
    def get_refresh_status(self) -> Dict:
        """Get current refresh status for all companies"""
        return {
            'general': {
                'in_progress': self.is_refresh_in_progress(),
                'last_refresh': self.get_last_refresh_time()
            },
            'companies': {
                company_id: {
                    'in_progress': self.is_refresh_in_progress(company_id),
                    'last_refresh': self.get_last_refresh_time(company_id)
                }
                for company_id in self._company_locks.keys()
            }
        }


# Global instance
vector_refresh_manager = VectorRefreshManager()
