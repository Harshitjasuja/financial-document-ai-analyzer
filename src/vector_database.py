from langchain.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import pickle
import numpy as np
import json
from pathlib import Path
from typing import List, Dict
import time

class VectorDatabase:
    def __init__(self):
        print("🗄️  Initializing Vector Database...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        print("✅ Vector Database initialized")
    
    def create_vector_database(self):
        """Create FAISS vector database from processed chunks"""
        print("🔧 Creating FAISS vector database...")
        
        # Load chunks from step 2
        print("📂 Loading chunks...")
        with open("data/processed/document_chunks.pkl", 'rb') as f:
            chunks = pickle.load(f)
        print(f"✅ Loaded {len(chunks)} chunks")
        
        start_time = time.time()
        
        # Create FAISS vector store
        print("🔄 Building vector store with embeddings...")
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save vector store
        print("💾 Saving vector store...")
        self.vectorstore.save_local("data/processed/vectorstore")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Save database info
        companies = list(set(chunk.metadata['company'] for chunk in chunks))
        db_info = {
            'total_vectors': len(chunks),
            'vector_dimension': 384,  # all-MiniLM-L6-v2 dimension
            'companies': companies,
            'database_type': 'FAISS',
            'creation_time': duration,
            'index_file': 'data/processed/vectorstore'
        }
        
        with open("data/processed/vectordb_info.json", 'w') as f:
            json.dump(db_info, f, indent=2)
        
        print(f"\n🎉 Vector database created successfully!")
        print(f"   📊 Vectors: {len(chunks)}")
        print(f"   🏢 Companies: {len(companies)}")
        print(f"   ⏱️  Time: {duration:.1f} seconds")
        print(f"   📁 Location: data/processed/vectorstore/")
        
        return self.vectorstore
    
    def load_vector_database(self):
        """Load existing vector database"""
        vectorstore_path = "data/processed/vectorstore"
        
        if Path(vectorstore_path).exists():
            print("📂 Loading existing vector database...")
            try:
                self.vectorstore = FAISS.load_local(
                    vectorstore_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                print("✅ Vector database loaded successfully!")
                return True
            except Exception as e:
                print(f"❌ Error loading vector database: {e}")
                return False
        else:
            print("❌ Vector database not found at", vectorstore_path)
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if Path("data/processed/vectordb_info.json").exists():
            with open("data/processed/vectordb_info.json", 'r') as f:
                return json.load(f)
        return {"error": "Database info not found"}
    
    def test_similarity_search(self, queries=None, k=3):
        """Test the vector database with sample queries"""
        if not self.vectorstore:
            print("❌ Vector database not loaded!")
            return None
        
        if queries is None:
            queries = [
                "What is Apple's main business model?",
                "How did Tesla perform financially?",
                "What are Microsoft's key risk factors?",
                "What is Intel's manufacturing strategy?",
                "How does Google make revenue?",
                "What are Amazon's main revenue sources?",
                "What is Netflix's content strategy?",
                "What are NVIDIA's AI products?",
                "How does Oracle compete in cloud computing?",
                "What is Salesforce's growth strategy?"
            ]
        
        print(f"\n🧪 Testing similarity search with {len(queries)} queries...")
        
        all_results = {}
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            
            start_time = time.time()
            results = self.vectorstore.similarity_search(query, k=k)
            search_time = time.time() - start_time
            
            query_results = []
            for j, result in enumerate(results, 1):
                company = result.metadata.get('company', 'Unknown')
                page = result.metadata.get('page_number', '?')
                chunk_id = result.metadata.get('chunk_id', 'unknown')
                preview = result.page_content[:120].replace('\n', ' ') + "..."
                
                result_info = {
                    'company': company,
                    'page': page,
                    'chunk_id': chunk_id,
                    'preview': preview
                }
                query_results.append(result_info)
                
                print(f"   📄 {j}. {company} (Page {page}): {preview}")
            
            all_results[query] = {
                'results': query_results,
                'search_time': search_time
            }
            
            print(f"   ⚡ Search time: {search_time:.3f} seconds")
        
        return all_results
    
    def run_database_creation(self):
        """Complete database creation process"""
        print("🚀 Starting Vector Database Creation")
        print("=" * 45)
        
        # Try to load existing, otherwise create new
        if not self.load_vector_database():
            print("\n🔧 Creating new vector database...")
            vectorstore = self.create_vector_database()
        else:
            print("\n✅ Using existing vector database")
        
        # Show database stats
        stats = self.get_database_stats()
        if "error" not in stats:
            print(f"\n📊 Database Statistics:")
            for key, value in stats.items():
                if key == 'companies':
                    print(f"   {key}: {', '.join(sorted(value))}")
                else:
                    print(f"   {key}: {value}")
        
        # Test the database
        print(f"\n🧪 Testing database functionality...")
        test_results = self.test_similarity_search()
        
        if test_results:
            # Summary of test results
            avg_search_time = sum(result['search_time'] for result in test_results.values()) / len(test_results)
            print(f"\n📈 Performance Summary:")
            print(f"   Average search time: {avg_search_time:.3f} seconds")
            print(f"   Total queries tested: {len(test_results)}")
            
            # Show companies found in results
            companies_found = set()
            for result in test_results.values():
                for res in result['results']:
                    companies_found.add(res['company'])
            
            print(f"   Companies found in results: {', '.join(sorted(companies_found))}")
        
        print(f"\n✅ Vector database ready for RAG queries!")
        print(f"🎯 Your RAG system can now answer questions about SEC filings!")

if __name__ == "__main__":
    db = VectorDatabase()
    db.run_database_creation()
