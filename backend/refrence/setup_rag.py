import json
import os
import uuid
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import time

class RAGSystem:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', persist_directory: str = 'data/vectors/chroma'):
        """Initialize the RAG system"""
        try:
            print("Initializing RAG system...")
            
            # Initialize the embedding model
            self.model = SentenceTransformer(model_name)
            print("Embedding model loaded successfully")
            
            # Ensure persist directory exists and is absolute
            self.persist_directory = os.path.abspath(persist_directory)
            os.makedirs(self.persist_directory, exist_ok=True)
            print(f"Using persist directory: {self.persist_directory}")
            
            # Initialize ChromaDB with settings
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
            
            # Create ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=settings
            )

            # Delete existing collection if it exists
            try:
                self.client.delete_collection("study_abroad_docs")
                print("Deleted existing collection")
                time.sleep(1)  # Give it time to clean up
            except:
                pass

            # Create new collection
            self.collection = self.client.create_collection(
                name="study_abroad_docs",
                metadata={"hnsw:space": "cosine"}
            )
            print("Created new collection: study_abroad_docs")
            
            self.is_initialized = True
            print("RAG system initialized successfully")
            
        except Exception as e:
            print(f"Error initializing RAG system: {e}")
            self.is_initialized = False
            raise

    def load_documents(self, json_path: str) -> bool:
        """Load documents into ChromaDB"""
        if not self.is_initialized:
            print("RAG system not properly initialized")
            return False

        try:
            print(f"\nLoading documents from {json_path}")
            
            # Load and validate JSON
            if not os.path.isfile(json_path):
                raise FileNotFoundError(f"Document file not found: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process documents
            documents = []
            metadatas = []
            ids = []
            
            # Flatten the nested structure
            for category, subcategories in data.items():
                for subcategory, items in subcategories.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                # Create document text combining question and answer
                                doc_text = f"{item['question']} {item['answer']}"
                                
                                # Create metadata
                                metadata = {
                                    'question': item['question'],
                                    'answer': item['answer'],
                                    'category': category,
                                    'subcategory': subcategory,
                                    'section': item.get('section', ''),
                                    'document': item.get('document', '')
                                }
                                
                                # Generate unique ID
                                doc_id = item.get('chunk_id', str(uuid.uuid4()))
                                
                                documents.append(doc_text)
                                metadatas.append(metadata)
                                ids.append(doc_id)
                                print(f"Processed document: {item['question']}")
            
            if not documents:
                print("No valid documents found to process")
                return False
            
            # Generate embeddings
            print(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.model.encode(documents).tolist()
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"Successfully loaded {len(documents)} documents into ChromaDB")
            return True
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False

    def update_documents(self, json_path: str) -> bool:
        """Update documents in ChromaDB without recreating the entire collection"""
        if not self.is_initialized:
            print("RAG system not properly initialized")
            return False

        try:
            print(f"\nUpdating documents from {json_path}")
            
            # Load and validate JSON
            if not os.path.isfile(json_path):
                raise FileNotFoundError(f"Document file not found: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Process new documents
            documents = []
            metadatas = []
            ids = []
            
            # Flatten the nested structure
            for category, subcategories in data.items():
                for subcategory, items in subcategories.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict) and 'question' in item and 'answer' in item:
                                doc_text = f"{item['question']} {item['answer']}"
                                metadata = {
                                    'question': item['question'],
                                    'answer': item['answer'],
                                    'category': category,
                                    'subcategory': subcategory,
                                    'section': item.get('section', ''),
                                    'document': item.get('document', '')
                                }
                                doc_id = item.get('chunk_id', str(uuid.uuid4()))
                                
                                documents.append(doc_text)
                                metadatas.append(metadata)
                                ids.append(doc_id)
            
            # Get existing documents
            existing_ids = set()
            results = self.collection.get()
            if results['ids']:
                existing_ids = set(results['ids'])
            
            # Find new documents to add
            new_docs = []
            new_metadatas = []
            new_ids = []
            for i, doc_id in enumerate(ids):
                if doc_id not in existing_ids:
                    new_docs.append(documents[i])
                    new_metadatas.append(metadatas[i])
                    new_ids.append(doc_id)
            
            # Add only new documents if any
            if new_docs:
                embeddings = self.model.encode(new_docs)
                self.collection.add(
                    documents=new_docs,
                    embeddings=embeddings.tolist(),
                    metadatas=new_metadatas,
                    ids=new_ids
                )
                print(f"Added {len(new_docs)} new documents")
            else:
                print("No new documents to add")
            
            return True
            
        except Exception as e:
            print(f"Error updating documents: {e}")
            return False

    def search(self, query: str, k: int = 3) -> List[dict]:
        """Search for relevant documents"""
        if not self.is_initialized:
            print("RAG system not properly initialized")
            return []
        
        try:
            print(f"\nProcessing search query: '{query}'")
            
            # Clean and normalize the query
            query = query.strip().lower()
            
            # Generate query embedding
            print("Generating query embedding...")
            query_embedding = self.model.encode([query]).tolist()[0]
            
            # Search with more results initially for better matching
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k * 3,  # Get more candidates for better matching
                include=['metadatas', 'documents', 'distances']
            )
            
            print("\nInitial ChromaDB Results:")
            for i in range(min(3, len(results['metadatas'][0]))):
                print(f"Result {i+1}:")
                print(f"Question: {results['metadatas'][0][i]['question']}")
                print(f"Distance: {results['distances'][0][i]}")
            
            if not results['ids'][0]:
                print("No results found")
                return []
            
            # Process results with improved scoring
            documents = []
            for i, (meta, doc, distance) in enumerate(zip(
                results['metadatas'][0],
                results['documents'][0],
                results['distances'][0]
            )):
                # Base score from cosine similarity (convert to 0-1 range)
                score = 1.0 - distance  # distance is cosine distance
                
                # Get query and question words
                query_words = set(query.split())
                question_words = set(meta['question'].lower().split())
                
                # Boost score based on exact matches and word overlap
                if query in meta['question'].lower():
                    # Perfect match gets maximum boost
                    score += 0.4
                elif query_words.intersection(question_words):
                    # Partial word overlap gets proportional boost
                    overlap_score = len(query_words.intersection(question_words)) / len(query_words)
                    score += 0.3 * overlap_score
                    
                    # Additional boost for matching word order
                    query_words_list = query.split()
                    question_words_list = meta['question'].lower().split()
                    for i in range(len(query_words_list) - 1):
                        if i < len(question_words_list) - 1:
                            if query_words_list[i:i+2] == question_words_list[i:i+2]:
                                score += 0.1
                
                # Category-based scoring with context
                if meta.get('category'):
                    # Strong boost for category match with scholarship terms
                    if meta['category'] == 'scholarships' and query_words.intersection({'scholarship', 'scholarships', 'financial', 'aid', 'funding'}):
                        score += 0.3
                    # Partial boost for subcategory match
                    elif meta.get('subcategory') and any(word in meta['subcategory'].lower() for word in query_words):
                        score += 0.2
                
                # Create result object
                result = {
                    **meta,
                    'score': round(score, 4),
                    'rank': i + 1,
                    'raw_text': doc
                }
                
                print(f"Match {i+1}:")
                print(f"  Question: {meta['question']}")
                print(f"  Category: {meta.get('category', 'N/A')}")
                print(f"  Score: {score}")
                print(f"  Distance: {distance}")
                
                documents.append(result)
            
            # Sort by score and filter results with low scores
            documents = sorted(documents, key=lambda x: x['score'], reverse=True)
            
            # Additional debug output
            print("\nScoring Details:")
            for doc in documents[:k]:
                print(f"Question: {doc['question']}")
                print(f"Score: {doc['score']}")
                print(f"Category: {doc.get('category', 'N/A')}")
                print("---")
            
            # Only return results with good enough scores
            # Increased threshold for better precision
            good_matches = [doc for doc in documents if doc['score'] > 0.25]
            print(f"Found {len(good_matches)} good matches out of {len(documents)} total")
            return good_matches[:k]  # Return top k good matches
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    @classmethod
    def load(cls, directory: str):
        """Load a RAG system with existing vectors"""
        return cls(persist_directory=directory + '/chroma')

if __name__ == '__main__':
    # Test the system
    rag = RAGSystem()
    success = rag.load_documents('data/documents/education_faq.json')
    print(f"Documents loaded successfully: {success}")
    
    if success:
        test_query = "Why study abroad?"
        results = rag.search(test_query)
        print(f"\nTest Query: {test_query}")
        print("\nTop relevant documents:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.2f}")
            print(f"Q: {result['question']}")
            print(f"A: {result['answer']}")
