# chatbot/utils/rag_system.py
"""
RAG (Retrieval-Augmented Generation) System for Django
Based on the Flask reference implementation
"""
import json
import os
from typing import List, Dict, Optional
from django.conf import settings
from chatbot.models import RAGDocument

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system"""
        self.is_initialized = False
        self.documents = []
        
    def load_documents_from_json(self, json_path: str) -> bool:
        """Load documents from JSON file and save to database"""
        try:
            if not os.path.exists(json_path):
                print(f"Warning: Document file not found at {json_path}")
                return False
                
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing documents
            RAGDocument.objects.all().delete()
            
            # Process the JSON structure
            documents_added = 0
            for category, subcategories in data.items():
                if isinstance(subcategories, dict):
                    for subcategory, documents in subcategories.items():
                        if isinstance(documents, list):
                            for doc in documents:
                                self._save_document(doc)
                                documents_added += 1
                                
            print(f"Loaded {documents_added} documents to database")
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
    
    def _save_document(self, doc_data: dict):
        """Save a single document to database"""
        try:
            RAGDocument.objects.update_or_create(
                chunk_id=doc_data.get('chunk_id', ''),
                defaults={
                    'question': doc_data.get('question', ''),
                    'answer': doc_data.get('answer', ''),
                    'section': doc_data.get('section', ''),
                    'document': doc_data.get('document', ''),
                    'page': doc_data.get('page', 0),
                    'is_active': True
                }
            )
        except Exception as e:
            print(f"Error saving document: {e}")
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Search for relevant documents based on query"""
        try:
            # Simple text-based search (in production, use vector search)
            query_lower = query.lower()
            
            # Search in questions and answers
            results = []
            documents = RAGDocument.objects.filter(is_active=True)
            
            for doc in documents:
                score = 0.0
                
                # Check question match
                if query_lower in doc.question.lower():
                    score += 1.0
                
                # Check answer match
                if query_lower in doc.answer.lower():
                    score += 0.8
                
                # Check word overlap with higher weights for important terms
                query_words = set(query_lower.split())
                question_words = set(doc.question.lower().split())
                answer_words = set(doc.answer.lower().split())
                
                # Higher scoring for education-related terms
                education_terms = {'study', 'studying', 'education', 'university', 'college', 'course', 'program', 'degree', 'requirements', 'australia', 'usa', 'uk', 'canada', 'application', 'admission'}
                
                question_overlap = len(query_words.intersection(question_words))
                answer_overlap = len(query_words.intersection(answer_words))
                education_overlap = len(query_words.intersection(education_terms))
                
                if question_overlap > 0:
                    score += 0.6 * (question_overlap / len(query_words))
                if answer_overlap > 0:
                    score += 0.4 * (answer_overlap / len(query_words))
                if education_overlap > 0:
                    score += 0.3 * education_overlap
                
                if score > 0:
                    results.append({
                        'question': doc.question,
                        'answer': doc.answer,
                        'section': doc.section,
                        'document': doc.document,
                        'score': score,
                        'chunk_id': doc.chunk_id
                    })
            
            # Sort by score and return top k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            print(f"Error in RAG search: {e}")
            return []
    
    def get_best_answer(self, query: str, min_score: float = 0.3) -> Optional[Dict]:
        """Get the best answer for a query"""
        results = self.search(query, k=1)
        if results and results[0]['score'] >= min_score:
            return results[0]
        return None

# Global RAG instance
rag_system = RAGSystem()
