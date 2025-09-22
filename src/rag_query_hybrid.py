from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import pickle
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class HybridRAGQuery:
    def __init__(self):
        print("🤖 Initializing Hybrid RAG Query System...")

        # Initialize basic properties first
        self.embeddings = None
        self.vectorstore = None
        self.companies = []
        self.company_aliases = {
            'GOOGLE': ['ALPHABET', 'GOOGL'],
            'CRM': ['SALESFORCE', 'SALESFORCE.COM'],
            'TESLA': ['TSLA'],
            'APPLE': ['AAPL'],
            'MICROSOFT': ['MSFT'],
            'AMAZON': ['AMZN'],
            'NETFLIX': ['NFLX'],
            'NVIDIA': ['NVDA'],
            'INTEL': ['INTC'],
            'ORACLE': ['ORCL']
        }

        try:
            # Initialize embeddings
            self._initialize_embeddings()
            # Try to load system (graceful if fails)
            self._load_system_safe()
            print("✅ Hybrid RAG System ready!")
        except Exception as e:
            print(f"⚠️ System initialized with limited functionality: {str(e)}")
            # Provide mock data for demo
            self.companies = ['APPLE', 'MICROSOFT', 'TESLA', 'GOOGLE', 'AMAZON']

    def _initialize_embeddings(self):
        """Initialize embeddings model safely"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            print("✅ Embeddings model loaded")
        except Exception as e:
            print(f"❌ Failed to load embeddings: {str(e)}")
            self.embeddings = None

    def _load_system_safe(self):
        """Load vector database and company info with error handling"""
        print("📂 Loading vector database...")

        vectorstore_path = Path("data/processed/vectorstore")
        info_path = Path("data/processed/vectordb_info.json")

        if vectorstore_path.exists() and self.embeddings:
            try:
                self.vectorstore = FAISS.load_local(
                    str(vectorstore_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Vector database loaded")

                # Load company list
                if info_path.exists():
                    with open(info_path, 'r') as f:
                        db_info = json.load(f)
                        self.companies = db_info.get('companies', [])
                        print(f"✅ Loaded database with {len(self.companies)} companies")

            except Exception as e:
                print(f"❌ Failed to load vector database: {str(e)}")
                self.vectorstore = None
                self.companies = ['APPLE', 'MICROSOFT', 'TESLA', 'GOOGLE', 'AMAZON']
        else:
            print("⚠️ Vector database not found. System running in demo mode.")
            self.companies = ['APPLE', 'MICROSOFT', 'TESLA', 'GOOGLE', 'AMAZON']

    def load_system(self):
        """Legacy method for compatibility"""
        return self._load_system_safe()

    def detect_company_from_query(self, query: str) -> Optional[str]:
        """Intelligently detect company from query"""
        query_upper = query.upper()

        # Direct company name detection
        for company in self.companies:
            if company in query_upper:
                return company

        # Check aliases
        for main_company, aliases in self.company_aliases.items():
            for alias in aliases:
                if alias in query_upper:
                    return main_company

        # Pattern matching for possessive forms
        patterns = [
            r"(\w+)'[Ss]\s+",  # "Apple's revenue"
            r"(\w+)\s+company",  # "Tesla company"
            r"(\w+)\s+corp",  # "Microsoft corp"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                match_upper = match.upper()
                if match_upper in self.companies:
                    return match_upper

                # Check aliases
                for main_company, aliases in self.company_aliases.items():
                    if match_upper in aliases:
                        return main_company

        return None

    def enhanced_search(self, query: str, company_filter: Optional[str] = None, k: int = 3) -> Dict:
        """Enhanced search with multiple strategies"""
        start_time = time.time()

        # Auto-detect company if not provided
        if not company_filter:
            company_filter = self.detect_company_from_query(query)

        print(f"🔍 Query: {query}")
        if company_filter:
            print(f"🏢 Detected/Filtered Company: {company_filter}")

        # If no vectorstore available, return mock results
        if not self.vectorstore:
            return self._mock_search_results(query, company_filter, k)

        try:
            # Strategy 1: Company-filtered search
            if company_filter:
                results = self._company_filtered_search(query, company_filter, k)
            else:
                # Strategy 2: General semantic search with ranking
                results = self._ranked_general_search(query, k)

            search_time = time.time() - start_time

            return {
                'query': query,
                'company_filter': company_filter,
                'results': results,
                'search_time': search_time,
                'total_results': len(results)
            }
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return self._mock_search_results(query, company_filter, k)

    def _company_filtered_search(self, query: str, company: str, k: int) -> List[Dict]:
        """Search within specific company documents"""
        if not self.vectorstore:
            return []

        try:
            # Get more results initially for filtering
            all_results = self.vectorstore.similarity_search(query, k=k*5)

            # Filter for specific company
            company_results = []
            for result in all_results:
                if result.metadata.get('company', '').upper() == company.upper():
                    company_results.append(result)
                    if len(company_results) >= k:
                        break

            return self._format_results(company_results)
        except Exception as e:
            logger.error(f"Company filtered search error: {str(e)}")
            return []

    def _ranked_general_search(self, query: str, k: int) -> List[Dict]:
        """General search with company diversity ranking"""
        if not self.vectorstore:
            return []

        try:
            # Get more results for ranking
            all_results = self.vectorstore.similarity_search(query, k=k*3)

            # Rank results to ensure company diversity
            ranked_results = []
            companies_used = set()

            # First pass: get best result from each company
            for result in all_results:
                company = result.metadata.get('company', 'Unknown')
                if company not in companies_used:
                    ranked_results.append(result)
                    companies_used.add(company)
                    if len(ranked_results) >= k:
                        break

            # Second pass: fill remaining slots with best overall
            if len(ranked_results) < k:
                for result in all_results:
                    if result not in ranked_results:
                        ranked_results.append(result)
                        if len(ranked_results) >= k:
                            break

            return self._format_results(ranked_results)
        except Exception as e:
            logger.error(f"Ranked search error: {str(e)}")
            return []

    def _format_results(self, results: List) -> List[Dict]:
        """Format results consistently"""
        formatted_results = []

        for i, result in enumerate(results, 1):
            formatted_result = {
                'rank': i,
                'company': result.metadata.get('company', 'Unknown'),
                'page': result.metadata.get('page_number', 'Unknown'),
                'chunk_id': result.metadata.get('chunk_id', 'Unknown'),
                'content': result.page_content,
                'content_preview': result.page_content[:200].replace('\n', ' ') + "...",
                'relevance_score': 'High' if i <= 2 else 'Medium'
            }
            formatted_results.append(formatted_result)

        return formatted_results

    def _mock_search_results(self, query: str, company_filter: Optional[str], k: int) -> Dict:
        """Return mock search results for demo mode"""
        mock_results = []

        companies = [company_filter] if company_filter else self.companies[:k]

        for i, company in enumerate(companies[:k], 1):
            mock_results.append({
                'rank': i,
                'company': company,
                'page': i,
                'chunk_id': f'mock_{i}',
                'content': f'This is mock content for {company} related to: {query}',
                'content_preview': f'Mock content preview for {company} regarding {query}...',
                'relevance_score': 'High' if i <= 2 else 'Medium'
            })

        return {
            'query': query,
            'company_filter': company_filter,
            'results': mock_results,
            'search_time': 0.1,
            'total_results': len(mock_results)
        }

    def hybrid_search(self, query: str, k: int = 3) -> list:
        """Simple search method for compatibility"""
        try:
            result = self.enhanced_search(query, k=k)
            return result['results']
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            return []

    def display_results(self, search_result: Dict):
        """Display search results in a user-friendly format"""
        print(f"\n{'='*60}")
        print(f"🔍 QUERY: {search_result['query']}")
        if search_result['company_filter']:
            print(f"🏢 COMPANY: {search_result['company_filter']}")
        print(f"⚡ SEARCH TIME: {search_result['search_time']:.3f} seconds")
        print(f"📊 RESULTS: {search_result['total_results']} found")
        print(f"{'='*60}")

        for result in search_result['results']:
            print(f"\n📄 RESULT {result['rank']}: {result['company']} (Page {result['page']})")
            print(f" 🎯 Relevance: {result['relevance_score']}")
            print(f" 📝 Content: {result['content_preview']}")

if __name__ == "__main__":
    # Test the system
    rag = HybridRAGQuery()

    # Test query
    test_query = "What is Apple's business model?"
    result = rag.enhanced_search(test_query, k=3)
    rag.display_results(result)
