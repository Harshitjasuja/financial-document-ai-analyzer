import pickle
import json
from pathlib import Path

def validate_real_data():
    """Verify we're working with real SEC data - FIXED VERSION"""
    print("🔍 VALIDATING REAL DATA QUALITY")
    print("=" * 40)
    
    # Check 1: Raw documents - Debug structure first
    with open("data/processed/raw_documents.pkl", 'rb') as f:
        docs = pickle.load(f)
    
    print(f"📊 Raw Documents: {len(docs)} items loaded")
    print(f"🔧 Debug - First item type: {type(docs[0])}")
    
    # Handle nested structure
    if isinstance(docs[0], list):
        print("📋 Data is nested - flattening...")
        flat_docs = []
        for item in docs:
            if isinstance(item, list):
                flat_docs.extend(item)
            else:
                flat_docs.append(item)
        docs = flat_docs
        print(f"📊 Flattened to: {len(docs)} documents")
    
    # Sample first document
    sample_doc = docs[0]
    print(f"\n📄 Sample Document (first 200 chars):")
    print(f"Type: {type(sample_doc)}")
    
    if hasattr(sample_doc, 'metadata'):
        print(f"Company: {sample_doc.metadata.get('company', 'Unknown')}")
        print(f"Content: {sample_doc.page_content[:200]}...")
        print(f"File: {sample_doc.metadata.get('source_file', 'Unknown')}")
    else:
        print("❌ Document doesn't have expected metadata structure")
        print(f"Available attributes: {dir(sample_doc)}")
        return
    
    # Check 2: Chunks
    print(f"\n📦 Loading chunks...")
    try:
        with open("data/processed/document_chunks.pkl", 'rb') as f:
            chunks = pickle.load(f)
        
        print(f"📊 Chunks: {len(chunks)} created")
        
        # Sample chunks from different companies
        companies = list(set(chunk.metadata['company'] for chunk in chunks if hasattr(chunk, 'metadata')))
        print(f"\n🏢 Companies found: {sorted(companies)}")
        
        print(f"\n📝 Sample chunks from each company:")
        for company in sorted(companies)[:3]:  # First 3 companies
            company_chunks = [c for c in chunks if hasattr(c, 'metadata') and c.metadata.get('company') == company]
            if company_chunks:
                sample_chunk = company_chunks[0]
                
                print(f"\n🏢 {company}:")
                print(f"   Chunk ID: {sample_chunk.metadata.get('chunk_id', 'N/A')}")
                print(f"   Page: {sample_chunk.metadata.get('page_number', 'N/A')}")
                print(f"   Content: {sample_chunk.page_content[:150]}...")
                print(f"   Length: {len(sample_chunk.page_content)} chars")
        
        # Check 3: Financial content validation
        print(f"\n💰 FINANCIAL CONTENT VALIDATION:")
        financial_keywords = ['revenue', 'income', 'profit', 'sales', 'earnings', 'cash flow', 'billion', 'million']
        
        for company in ['APPLE', 'MICROSOFT', 'TESLA']:
            company_chunks = [c for c in chunks if hasattr(c, 'metadata') and c.metadata.get('company') == company]
            financial_chunks = []
            
            for chunk in company_chunks[:50]:  # Check first 50 chunks
                content_lower = chunk.page_content.lower()
                if any(keyword in content_lower for keyword in financial_keywords):
                    financial_chunks.append(chunk)
            
            print(f"   {company}: {len(financial_chunks)}/{len(company_chunks[:50])} chunks contain financial data")
            
            if financial_chunks:
                sample = financial_chunks[0]
                snippet = sample.page_content[:120].replace('\n', ' ') + "..."
                print(f"      Sample: {snippet}")
    
    except FileNotFoundError:
        print("❌ Chunks file not found - run text chunker first")
        return
    
    print(f"\n✅ DATA VALIDATION COMPLETE")
    print(f"📊 Summary: {len(docs)} pages → {len(chunks)} chunks from {len(companies)} companies")
    
    # Quick content samples to verify real data
    print(f"\n📋 REAL DATA VERIFICATION:")
    sample_texts = []
    for company in ['APPLE', 'TESLA', 'MICROSOFT']:
        company_chunks = [c for c in chunks if hasattr(c, 'metadata') and c.metadata.get('company') == company]
        if company_chunks:
            # Look for chunks with company-specific info
            for chunk in company_chunks[:10]:
                content = chunk.page_content.lower()
                if company.lower() in content and any(word in content for word in ['business', 'products', 'operations']):
                    sample_texts.append(f"{company}: {chunk.page_content[:100]}...")
                    break
    
    for sample in sample_texts:
        print(f"   {sample}")

if __name__ == "__main__":
    validate_real_data()
