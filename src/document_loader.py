from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
import json
from typing import List, Dict
import pickle

class DocumentLoader:
    def __init__(self, pdf_directory="data/raw"):
        self.pdf_directory = Path(pdf_directory)
        self.documents = []
        
    def load_all_pdfs(self) -> List[Dict]:
        """Load all PDFs and extract text with metadata"""
        print("📚 Loading PDF documents...")
        
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        all_documents = []
        
        for pdf_path in pdf_files:
            try:
                #extract company name 
                company = self._extract_company_name_fixed(pdf_path.stem)
                
                print(f"Loading {company}...")
                
                #load PDF
                loader = PyPDFLoader(str(pdf_path))
                pages = loader.load()
                
                #add metadata
                for i, page in enumerate(pages):
                    page.metadata.update({
                        'company': company,
                        'source_file': pdf_path.name,
                        'page_number': i + 1,
                        'document_type': 'SEC_10K',
                        'file_size': pdf_path.stat().st_size
                    })
                
                all_documents.extend(pages)
                print(f"  ✅ {company}: {len(pages)} pages loaded")
                
            except Exception as e:
                print(f"  ❌ Error loading {pdf_path.name}: {e}")
                continue  # Continue with next file
        
        # Save raw documents
        if all_documents:
            self._save_documents(all_documents)
        
        return all_documents
    
    def _extract_company_name_fixed(self, filename_stem) -> str:
        """Extract company name from filename stem - FIXED VERSION"""
        try:
            # Convert to string
            filename_str = str(filename_stem)
            
            # Split on underscore
            parts = filename_str.split('_')
            
            # Get first part
            first_part = parts[0]
            
            # Convert to uppercase
            company = first_part.upper()
            
            return company
            
        except Exception as e:
            print(f"Error extracting company name from '{filename_stem}': {e}")
            return "UNKNOWN"
    
    def _save_documents(self, documents: List):
        """Save loaded documents for later use"""
        Path("data/processed").mkdir(exist_ok=True)
        
        # Save documents
        with open("data/processed/raw_documents.pkl", 'wb') as f:
            pickle.dump(documents, f)
        
        # Save metadata summary
        companies = []
        if documents:
            companies = list(set(doc.metadata['company'] for doc in documents))
        
        metadata_summary = {
            'total_documents': len(documents),
            'companies': companies,
            'total_pages': len(documents)
        }
        
        with open("data/processed/document_summary.json", 'w') as f:
            json.dump(metadata_summary, f, indent=2)
        
        print(f"💾 Saved {len(documents)} documents to data/processed/")

if __name__ == "__main__":
    loader = DocumentLoader()
    docs = loader.load_all_pdfs()
    print(f"🎉 Loaded {len(docs)} total pages from SEC filings")

