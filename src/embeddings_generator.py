from langchain_community.embeddings import HuggingFaceEmbeddings
import pickle
import numpy as np
import json
from pathlib import Path
from typing import List
import time

class EmbeddingGenerator:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        print("🧠 Initializing embedding model...")
        self.model_name = model_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"✅ Loaded embedding model: {model_name}")
        
    def load_chunks(self):
        """Load chunks from step 2"""
        print("📂 Loading chunks from step 2...")
        with open("data/processed/document_chunks.pkl", 'rb') as f:
            chunks = pickle.load(f)
        print(f"✅ Loaded {len(chunks)} chunks")
        return chunks
    
    def generate_embeddings(self, chunks=None) -> tuple:
        """Generate vector embeddings for all chunks"""
        if chunks is None:
            chunks = self.load_chunks()
        
        print(f"🔢 Generating embeddings for {len(chunks)} chunks...")
        start_time = time.time()
        
        # Extract texts for embedding
        texts = [chunk.page_content for chunk in chunks]
        
        # Generate embeddings in batches for memory efficiency
        batch_size = 50  # Smaller batches for stability
        all_embeddings = []
        
        print("Processing in batches:")
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            print(f"  📦 Batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}: Processing {len(batch_texts)} chunks...")
            
            batch_embeddings = self.embeddings.embed_documents(batch_texts)
            all_embeddings.extend(batch_embeddings)
            
            # Progress update
            processed = min(i + batch_size, len(texts))
            print(f"     ✅ Processed {processed}/{len(texts)} chunks")
        
        # Convert to numpy array
        embedding_matrix = np.array(all_embeddings)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n🎉 Embedding generation complete!")
        print(f"   📊 Shape: {embedding_matrix.shape}")
        print(f"   ⏱️  Time: {duration:.1f} seconds")
        print(f"   📈 Rate: {len(chunks)/duration:.1f} chunks/second")
        
        # Save embeddings and metadata
        self._save_embeddings(embedding_matrix, chunks, duration)
        
        return embedding_matrix, chunks
    
    def _save_embeddings(self, embeddings: np.ndarray, chunks: List, duration: float):
        """Save embeddings and metadata"""
        Path("data/processed").mkdir(exist_ok=True)
        
        # Save embeddings as numpy array
        np.save("data/processed/embeddings.npy", embeddings)
        print(f"💾 Saved embeddings to data/processed/embeddings.npy")
        
        # Save chunk metadata separately (lighter than full chunks)
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                'index': i,
                'content_preview': chunk.page_content[:100] + "...",
                'metadata': chunk.metadata,
                'content_length': len(chunk.page_content)
            })
        
        with open("data/processed/chunk_metadata.pkl", 'wb') as f:
            pickle.dump(chunk_metadata, f)
        print(f"💾 Saved chunk metadata")
        
        # Save embedding information - FIXED
        embedding_info = {
            'embedding_shape': list(embeddings.shape),
            'model_name': self.model_name,
            'total_chunks': len(chunks),
            'embedding_dimension': embeddings.shape[1],  # FIXED: was [2], now [1]
            'generation_time': duration,
            'chunks_per_second': len(chunks) / duration,
            'companies': list(set(chunk.metadata['company'] for chunk in chunks))
        }
        
        with open("data/processed/embedding_info.json", 'w') as f:
            json.dump(embedding_info, f, indent=2)
        print(f"💾 Saved embedding info")

if __name__ == "__main__":
    print("🚀 Starting Embedding Generation Process")
    print("=" * 45)
    
    generator = EmbeddingGenerator()
    embeddings, chunks = generator.generate_embeddings()
    
    print(f"\n✅ Embedding generation complete!")
    print(f"Generated {embeddings.shape[0]} embeddings of dimension {embeddings.shape[1]}")

