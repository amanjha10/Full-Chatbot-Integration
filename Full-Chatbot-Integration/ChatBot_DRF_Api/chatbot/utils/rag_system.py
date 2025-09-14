# chatbot/utils/rag_system.py
"""
RAG (Retrieval-Augmented Generation) System for Django
Based on the Flask reference implementation with ChromaDB integration
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
        self.chroma_client = None
        self.collection = None
        self.model = None

        # Try to initialize ChromaDB
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB connection with production-ready configuration"""
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            # Initialize the embedding model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

            # Production ChromaDB configuration
            # Try to connect to self-hosted ChromaDB server first, fallback to local
            try:
                # Try connecting to ChromaDB server on port 8002
                self.chroma_client = chromadb.HttpClient(host="localhost", port=8002)
                # Test the connection
                self.chroma_client.heartbeat()
                print("✅ Connected to ChromaDB server on port 8002")
            except Exception as server_error:
                print(f"⚠️ ChromaDB server not available: {server_error}")
                print("🔄 Falling back to local persistent client...")

                # Fallback to persistent client with production data directory
                vector_db_path = os.path.join(settings.BASE_DIR, 'chroma_data')
                os.makedirs(vector_db_path, exist_ok=True)

                self.chroma_client = chromadb.PersistentClient(
                    path=vector_db_path,
                    settings=chromadb.config.Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                print(f"✅ Using local ChromaDB at: {vector_db_path}")

            # Get or create the collection
            try:
                self.collection = self.chroma_client.get_collection("study_abroad_docs")
                self.is_initialized = True
                print("✅ ChromaDB RAG system initialized successfully")
            except Exception as e:
                print(f"⚠️ ChromaDB collection not found: {e}")
                try:
                    # Try to create the collection if it doesn't exist
                    self.collection = self.chroma_client.create_collection(
                        name="study_abroad_docs",
                        metadata={"hnsw:space": "cosine"}
                    )
                    print("✅ Created new ChromaDB collection")
                    self.is_initialized = True
                except Exception as create_error:
                    print(f"⚠️ Could not create ChromaDB collection: {create_error}")
                    print("Using fallback database search")
                    self.is_initialized = False

        except ImportError as e:
            print(f"⚠️ ChromaDB dependencies not available: {e}")
            print("Using fallback database search")
            self.is_initialized = False
        except Exception as e:
            print(f"⚠️ Error initializing ChromaDB: {e}")
            print("Using fallback database search")
            self.is_initialized = False

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
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better matching"""
        import re
        # Convert to lowercase
        normalized = query.lower().strip()
        # Remove extra punctuation but keep essential ones
        normalized = re.sub(r'[^\w\s\?]', '', normalized)
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return normalized

    def search(self, query: str, k: int = 3, company_id: str = None) -> List[Dict]:
        """
        Search for relevant documents based on query with company priority

        Args:
            query: Search query
            k: Number of results to return
            company_id: Company ID for prioritized search

        Returns:
            List of relevant documents with company-specific priority
        """
        try:
            # Normalize query for better matching
            normalized_query = self._normalize_query(query)
            print(f"🔍 Normalized query: '{query}' → '{normalized_query}'")

            # Use ChromaDB if available
            if self.is_initialized and self.model:
                return self._search_chromadb_with_priority(normalized_query, k, company_id)
            else:
                return self._search_database(normalized_query, k)

        except Exception as e:
            print(f"Error in RAG search: {e}")
            # Fallback to database search
            return self._search_database(query, k)

    def _search_chromadb_with_priority(self, query: str, k: int = 3, company_id: str = None) -> List[Dict]:
        """
        Search using ChromaDB with company-specific priority logic

        Priority:
        1. Company-specific FAQs (if company_id provided)
        2. General FAQs (fallback)
        3. Merge results with company priority
        """
        try:
            all_results = []

            # Step 1: Search company-specific collection first (if company_id provided)
            if company_id:
                company_results = self._search_company_collection(query, k, company_id)
                if company_results:
                    print(f"✅ Found {len(company_results)} company-specific results for {company_id}")
                    all_results.extend(company_results)

            # Step 2: Search general collection for fallback/additional results
            general_results = self._search_general_collection(query, k)
            if general_results:
                print(f"✅ Found {len(general_results)} general results")
                all_results.extend(general_results)

            # Step 3: Apply priority logic and return best results
            return self._apply_priority_logic(all_results, k, company_id)

        except Exception as e:
            print(f"Error in priority search: {e}")
            return self._search_database(query, k)

    def _search_company_collection(self, query: str, k: int, company_id: str) -> List[Dict]:
        """Search in company-specific collection"""
        try:
            company_collection_name = f"company_{company_id}_faq"
            print(f"DEBUG: Looking for collection: {company_collection_name}")

            # Get or create company collection
            try:
                company_collection = self.chroma_client.get_collection(company_collection_name)
                collection_count = company_collection.count()
                print(f"DEBUG: Found collection {company_collection_name} with {collection_count} documents")
            except Exception as e:
                # Collection doesn't exist, return empty
                print(f"DEBUG: Collection {company_collection_name} not found: {e}")
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query]).tolist()

            # Search in company collection
            results = company_collection.query(
                query_embeddings=query_embedding,
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0

                    # Calculate similarity (1 - distance for cosine)
                    similarity = max(0, 1 - distance)

                    formatted_results.append({
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'section': metadata.get('section', 'Company FAQ'),
                        'document': metadata.get('document', f'{company_id} Company FAQ'),
                        'similarity': similarity,
                        'source_type': 'company_faq',
                        'company_id': company_id,
                        'priority_score': similarity + 0.2  # Boost company results
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching company collection: {e}")
            return []

    def _search_general_collection(self, query: str, k: int) -> List[Dict]:
        """Search in general FAQ collection"""
        try:
            # Use the dedicated general_faq collection
            general_collection_name = "general_faq"
            print(f"DEBUG: Looking for general collection: {general_collection_name}")

            try:
                general_collection = self.chroma_client.get_collection(general_collection_name)
                collection_count = general_collection.count()
                print(f"DEBUG: Found general collection {general_collection_name} with {collection_count} documents")
            except Exception as e:
                print(f"DEBUG: General collection {general_collection_name} not found: {e}")
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query]).tolist()

            # Search in general collection
            results = general_collection.query(
                query_embeddings=query_embedding,
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0

                    # Calculate similarity (1 - distance for cosine)
                    similarity = max(0, 1 - distance)

                    formatted_results.append({
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'section': metadata.get('section', 'General FAQ'),
                        'document': metadata.get('document', 'General FAQ'),
                        'similarity': similarity,
                        'source_type': 'general_faq',
                        'company_id': None,
                        'priority_score': similarity  # No boost for general results
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching general collection: {e}")
            return []

    def _apply_priority_logic(self, all_results: List[Dict], k: int, company_id: str = None) -> List[Dict]:
        """
        Apply priority logic to merge and rank results

        Logic:
        1. Company results with similarity >= 0.7 get highest priority
        2. General results with similarity >= 0.7 get medium priority
        3. Sort by priority_score (company results get +0.2 boost)
        4. Return top k results
        """
        if not all_results:
            return []

        # Filter results by minimum similarity threshold
        filtered_results = [r for r in all_results if r.get('similarity', 0) >= 0.5]

        # Sort by priority score (descending)
        sorted_results = sorted(filtered_results, key=lambda x: x.get('priority_score', 0), reverse=True)

        # Return top k results
        final_results = sorted_results[:k]

        # Log the selection for debugging
        if company_id and final_results:
            company_count = sum(1 for r in final_results if r.get('source_type') == 'company_faq')
            general_count = sum(1 for r in final_results if r.get('source_type') == 'general_faq')
            print(f"🎯 Priority results for {company_id}: {company_count} company + {general_count} general")

            # Log details of top result
            if final_results:
                top_result = final_results[0]
                print(f"🏆 Top result: {top_result.get('source_type')} - Q: {top_result.get('question', '')[:50]}...")
                print(f"    Similarity: {top_result.get('similarity', 0):.3f}, Priority Score: {top_result.get('priority_score', 0):.3f}")

        return final_results

    def _search_chromadb(self, query: str, k: int = 3) -> List[Dict]:
        """Search using ChromaDB vector database"""
        try:
            # Check if collection is still valid, reinitialize if needed
            if not self.collection:
                self._init_chromadb()
                if not self.is_initialized:
                    return []

            # Generate query embedding
            query_embedding = self.model.encode([query]).tolist()

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )

            # Convert ChromaDB results to our format
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0

                    # Convert distance to similarity score (lower distance = higher similarity)
                    score = max(0.0, 1.0 - distance)

                    formatted_results.append({
                        'question': metadata.get('question', ''),
                        'answer': metadata.get('answer', ''),
                        'section': metadata.get('section', ''),
                        'document': metadata.get('document', ''),
                        'score': score,
                        'chunk_id': metadata.get('chunk_id', f'chroma_{i}')
                    })

            return formatted_results

        except Exception as e:
            print(f"Error in ChromaDB search: {e}")
            # Try to reinitialize ChromaDB once
            try:
                print("Attempting to reinitialize ChromaDB...")
                self._init_chromadb()
                if self.is_initialized and self.collection:
                    # Retry the search once
                    query_embedding = self.model.encode([query]).tolist()
                    results = self.collection.query(
                        query_embeddings=query_embedding,
                        n_results=k,
                        include=['documents', 'metadatas', 'distances']
                    )

                    # Convert results
                    formatted_results = []
                    if results['documents'] and results['documents'][0]:
                        for i, doc in enumerate(results['documents'][0]):
                            metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                            distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                            score = max(0.0, 1.0 - distance)

                            formatted_results.append({
                                'question': metadata.get('question', ''),
                                'answer': metadata.get('answer', ''),
                                'section': metadata.get('section', ''),
                                'document': metadata.get('document', ''),
                                'score': score,
                                'chunk_id': metadata.get('chunk_id', f'chroma_{i}')
                            })

                    return formatted_results
            except Exception as retry_error:
                print(f"ChromaDB retry failed: {retry_error}")

            return []

    def _search_database(self, query: str, k: int = 3) -> List[Dict]:
        """Fallback database search method"""
        try:
            # Simple text-based search (fallback when ChromaDB is not available)
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
            print(f"Error in database search: {e}")
            return []
    
    def get_best_answer(self, query: str, min_score: float = 0.3, company_id: str = None) -> Optional[Dict]:
        """Get the best answer for a query with smart company priority thresholds"""
        results = self.search(query, k=3, company_id=company_id)  # Get more results for better selection

        if not results:
            print(f"❌ No results found for query: {query}")
            return None

        # Smart threshold logic: Company FAQs get lower threshold, General FAQs get higher
        company_threshold = 0.3  # Lower threshold for company-specific FAQs (was 0.4)
        general_threshold = 0.5  # Higher threshold for general FAQs (was 0.6)

        print(f"🔍 Evaluating {len(results)} results with smart thresholds:")
        print(f"   Company threshold: {company_threshold}, General threshold: {general_threshold}")

        # First, look for company-specific results that meet the lower threshold
        for result in results:
            if result.get('source_type') == 'company_faq':
                score = result.get('similarity', result.get('score', 0))
                print(f"🏢 Company result: Score {score:.3f} - Q: {result.get('question', '')[:50]}...")

                if score >= company_threshold:
                    print(f"✅ Using company FAQ (score {score:.3f} >= {company_threshold})")
                    return result
                else:
                    print(f"⚠️ Company score {score:.3f} below threshold {company_threshold}")

        # If no company result meets threshold, look for general results
        for result in results:
            if result.get('source_type') == 'general_faq':
                score = result.get('similarity', result.get('score', 0))
                print(f"🌐 General result: Score {score:.3f} - Q: {result.get('question', '')[:50]}...")

                if score >= general_threshold:
                    print(f"✅ Using general FAQ (score {score:.3f} >= {general_threshold})")
                    return result
                else:
                    print(f"⚠️ General score {score:.3f} below threshold {general_threshold}")

        # If nothing meets thresholds, return the best company result if available, otherwise best general
        company_results = [r for r in results if r.get('source_type') == 'company_faq']
        if company_results:
            best_company = company_results[0]
            score = best_company.get('similarity', best_company.get('score', 0))
            print(f"🎯 Fallback: Using best company result with score {score:.3f}")
            return best_company

        # Last resort: return best general result
        if results:
            best_general = results[0]
            score = best_general.get('similarity', best_general.get('score', 0))
            print(f"🎯 Fallback: Using best general result with score {score:.3f}")
            return best_general

        return None

    def add_document(self, text: str, metadata: Dict, collection_name: str = None) -> bool:
        """
        Add a document to the vector database

        Args:
            text: Document text content
            metadata: Document metadata
            collection_name: Collection name (default: main collection)

        Returns:
            bool: Success status
        """
        try:
            if not self.is_initialized or not self.model:
                print("⚠️ RAG system not initialized")
                return False

            # Determine target collection
            if collection_name:
                # Get or create company-specific collection
                try:
                    target_collection = self.chroma_client.get_collection(collection_name)
                except:
                    # Create new collection
                    target_collection = self.chroma_client.create_collection(
                        name=collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    print(f"✅ Created new collection: {collection_name}")
            else:
                # Use main collection
                target_collection = self.collection
                if not target_collection:
                    print("⚠️ Main collection not available")
                    return False

            # Generate embedding
            embedding = self.model.encode([text]).tolist()[0]

            # Generate unique ID
            doc_id = metadata.get('chunk_id', f"doc_{len(text)}_{hash(text) % 10000}")

            # Add to collection
            target_collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )

            print(f"✅ Added document to {collection_name or 'main'} collection: {doc_id}")
            return True

        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return False

    def delete_company_collection(self, company_id: str) -> bool:
        """Delete all documents for a specific company"""
        try:
            collection_name = f"company_{company_id}_faq"

            try:
                self.chroma_client.delete_collection(collection_name)
                print(f"✅ Deleted collection: {collection_name}")
                return True
            except:
                print(f"⚠️ Collection {collection_name} not found or already deleted")
                return True  # Consider it success if already gone

        except Exception as e:
            print(f"❌ Error deleting company collection: {e}")
            return False

    def refresh_company_vectors(self, company_id: str, company_faqs: Dict) -> bool:
        """
        Production-safe refresh vectors for a specific company with proper locking and error handling

        Args:
            company_id: Company identifier
            company_faqs: Company FAQ data structure

        Returns:
            bool: Success status
        """
        import threading
        import time

        # Use a lock to prevent concurrent modifications
        if not hasattr(self, '_refresh_locks'):
            self._refresh_locks = {}

        if company_id not in self._refresh_locks:
            self._refresh_locks[company_id] = threading.Lock()

        with self._refresh_locks[company_id]:
            try:
                collection_name = f"company_{company_id}_faq"
                print(f"🔄 [SAFE] Refreshing vectors for company {company_id}")

                # Ensure ChromaDB is initialized
                if not self.chroma_client:
                    self._init_chromadb()
                    if not self.is_initialized:
                        print(f"❌ ChromaDB not initialized for company {company_id}")
                        return False

                # Delete existing collection safely with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        existing_collection = self.chroma_client.get_collection(collection_name)
                        self.chroma_client.delete_collection(collection_name)
                        print(f"✅ Deleted collection: {collection_name} (attempt {attempt + 1})")
                        time.sleep(0.5)  # Brief pause to ensure deletion is complete
                        break
                    except Exception as e:
                        if attempt == 0:
                            print(f"⚠️ Collection {collection_name} not found or already deleted")
                        elif attempt < max_retries - 1:
                            print(f"⚠️ Retry {attempt + 1} for deleting collection {collection_name}")
                            time.sleep(1)
                        else:
                            print(f"⚠️ Final attempt to delete collection {collection_name} failed: {e}")

                # Create new collection with retry logic
                company_collection = None
                for attempt in range(max_retries):
                    try:
                        company_collection = self.chroma_client.create_collection(
                            name=collection_name,
                            metadata={"hnsw:space": "cosine"}
                        )
                        print(f"✅ Created new collection: {collection_name}")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"⚠️ Retry {attempt + 1} for creating collection {collection_name}: {e}")
                            time.sleep(1)
                        else:
                            print(f"❌ Failed to create collection {collection_name}: {e}")
                            return False

                if not company_collection:
                    print(f"❌ Failed to create collection for company {company_id}")
                    return False

                # Prepare batch data
                documents = []
                metadatas = []
                ids = []

                # Process all company FAQs
                for category, questions in company_faqs.get('company_faqs', {}).items():
                    if isinstance(questions, list):
                        for faq in questions:
                            question = faq.get('question', '')
                            answer = faq.get('answer', '')

                            # Create multiple variations for better matching (like our working standalone script)
                            variations = [
                                question.lower(),
                                question,
                                question.lower().replace('?', '').strip(),
                                question.replace('?', '').strip(),
                            ]

                            # Add specific variations for common patterns
                            if 'location' in question.lower():
                                variations.extend([
                                    question.lower().replace('where is your location', 'company location'),
                                    question.lower().replace('location', 'where'),
                                    'company location',
                                    'location'
                                ])

                            # Remove duplicates and empty strings
                            variations = list(set([v for v in variations if v.strip()]))

                            for i, var in enumerate(variations):
                                documents.append(var)
                                metadatas.append({
                                    'chunk_id': faq.get('chunk_id', f'{company_id.lower()}_{len(ids)}'),
                                    'question': question,
                                    'answer': answer,
                                    'category': category,
                                    'section': faq.get('section', 'Company FAQ'),
                                    'document': faq.get('document', f'{company_id} Company FAQ'),
                                    'company_id': company_id,
                                    'source_type': 'company_faq'
                                })
                                ids.append(f'{company_id.lower()}_var_{len(ids)}_{i}')

                if not documents:
                    print(f"⚠️ No documents to process for {company_id}")
                    return False

                print(f"📝 Processing {len(documents)} document variations...")

                # Generate embeddings in batch
                embeddings = self.model.encode(documents).tolist()
                print(f"✅ Generated {len(embeddings)} embeddings")

                # Add all documents to collection in batch
                company_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )

                print(f"✅ Added {len(documents)} documents to {collection_name} collection")

                # Count unique FAQs processed
                unique_faqs = len(set(meta['chunk_id'] for meta in metadatas))
                print(f"✅ Refreshed {unique_faqs} company FAQs for {company_id}")

                return True

            except Exception as e:
                print(f"❌ Error refreshing company vectors: {e}")
                import traceback
                traceback.print_exc()
                return False

# Global RAG instance
rag_system = RAGSystem()
