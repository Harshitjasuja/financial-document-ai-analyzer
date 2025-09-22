from langchain.text_splitter import RecursiveCharacterTextSplitter
import pickle
import json
from typing import List
from pathlib import Path

class TextChunker:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
    def load_documents(self):
        """Load raw documents from step 1"""
        print("📂 Loading documents from step 1...")
        with open("data/processed/raw_documents.pkl", 'rb') as f:
            documents = pickle.load(f)
        print(f"✅ Loaded {len(documents)} documents")
        return documents
    
    def chunk_documents(self, documents=None) -> List:
        """Convert documents into manageable chunks"""
        if documents is None:
            documents = self.load_documents()
        
        print(f"✂️  Chunking {len(documents)} documents...")
        
        all_chunks = []
        company_stats = {}
        
        for doc in documents:
            company = doc.metadata['company']
            
            # Split document into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk-specific metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_id': f"{company}_chunk_{len(all_chunks) + i}",
                    'chunk_index': i,
                    'total_chunks_in_doc': len(chunks),
                    'char_count': len(chunk.page_content)
                })
            
            all_chunks.extend(chunks)
            
            # Track statistics
            if company not in company_stats:
                company_stats[company] = {'pages': 0, 'chunks': 0}
            company_stats[company]['pages'] += 1
            company_stats[company]['chunks'] += len(chunks)
        
        # Display statistics
        print("\n📊 Chunking Statistics:")
        total_chunks = 0
        for company, stats in sorted(company_stats.items()):
            print(f"  {company}: {stats['pages']} pages → {stats['chunks']} chunks")
            total_chunks += stats['chunks']
        
        print(f"\n🎯 Total chunks created: {total_chunks}")
        
        # Save chunks and statistics
        self._save_chunks(all_chunks, company_stats)
        return all_chunks
    
    def _save_chunks(self, chunks: List, stats: dict):
        """Save chunks and statistics"""
        Path("data/processed").mkdir(exist_ok=True)
        
        # Save chunks
        with open("data/processed/document_chunks.pkl", 'wb') as f:
            pickle.dump(chunks, f)
        
        # Save chunking statistics
        chunk_summary = {
            'total_chunks': len(chunks),
            'company_statistics': stats,
            'chunk_size': self.text_splitter._chunk_size,
            'chunk_overlap': self.text_splitter._chunk_overlap,
            'avg_chunk_length': sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
        }
        
        with open("data/processed/chunk_summary.json", 'w') as f:
            json.dump(chunk_summary, f, indent=2)
        
        print(f"💾 Saved {len(chunks)} chunks to data/processed/")

if __name__ == "__main__":
    print("🚀 Starting Text Chunking Process")
    print("=" * 40)
    
    chunker = TextChunker()
    chunks = chunker.chunk_documents()
    
    print(f"\n✅ Chunking complete! Created {len(chunks)} total chunks")
