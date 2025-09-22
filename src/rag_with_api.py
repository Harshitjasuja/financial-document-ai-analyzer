# src/rag_with_api_fixed.py
import os
import time
import logging
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try imports with better error handling
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError as e:
    genai = None
    GENAI_AVAILABLE = False
    logger.warning(f"Google Generative AI not available: {e}")

try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    FAISS = None
    HuggingFaceEmbeddings = None
    LANGCHAIN_AVAILABLE = False
    logger.warning(f"LangChain Community not available: {e}")

class RAGWithGemini:
    def __init__(self):
        """Initialize RAG system with comprehensive error handling"""
        self.init_errors = []
        self.warnings = []
        
        # Initialize components
        self.embeddings = None
        self.vectorstore = None
        self.gemini_model = None
        self.gemini_ready = False
        self.companies = []
        
        # Company aliases for better detection
        self.company_aliases = {
            'GOOGLE': ['ALPHABET', 'GOOGL', 'GOOGLE INC'],
            'CRM': ['SALESFORCE', 'SALESFORCE.COM', 'SALESFORCE INC'],
            'TESLA': ['TSLA', 'TESLA INC', 'TESLA MOTORS'],
            'APPLE': ['AAPL', 'APPLE INC'],
            'MICROSOFT': ['MSFT', 'MICROSOFT CORP'],
            'AMAZON': ['AMZN', 'AMAZON.COM', 'AMAZON INC'],
            'NETFLIX': ['NFLX', 'NETFLIX INC'],
            'NVIDIA': ['NVDA', 'NVIDIA CORP'],
            'INTEL': ['INTC', 'INTEL CORP'],
            'ORACLE': ['ORCL', 'ORACLE CORP']
        }
        
        logger.info("🤖 Initializing RAG System...")
        
        # Initialize in order
        self._load_environment()
        self._init_embeddings()
        self._load_vectorstore()
        self._init_gemini()
        
        # Set demo companies if no vector store
        if not self.companies:
            self.companies = ['APPLE', 'MICROSOFT', 'TESLA', 'GOOGLE', 'AMAZON', 'NETFLIX']
            self.warnings.append("Running with demo companies (no vector store loaded)")
        
        logger.info("✅ RAG System initialization complete!")
        if self.init_errors:
            logger.error(f"❌ Initialization errors: {len(self.init_errors)}")
            for error in self.init_errors:
                logger.error(f"  - {error}")
        if self.warnings:
            logger.warning(f"⚠️ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

    def _load_environment(self):
        """Load environment variables"""
        try:
            # Try to load .env from current directory and parent
            env_paths = [Path(".env"), Path("../.env"), Path("../../.env")]
            loaded = False
            
            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"✅ Loaded .env from {env_path}")
                    loaded = True
                    break
            
            if not loaded:
                self.warnings.append("No .env file found - using environment variables")
                logger.warning("⚠️ No .env file found")
            
            # Check for API key
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key:
                self.init_errors.append("GOOGLE_API_KEY not found in environment")
            else:
                logger.info("✅ GOOGLE_API_KEY found")
                
        except Exception as e:
            self.init_errors.append(f"Environment loading failed: {str(e)}")
            logger.exception("❌ Environment loading failed")

    def _init_embeddings(self):
        """Initialize embeddings model"""
        try:
            if not LANGCHAIN_AVAILABLE:
                self.warnings.append("LangChain not available - embeddings disabled")
                return
            
            logger.info("🔤 Loading embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            logger.info("✅ Embeddings model loaded successfully")
            
        except Exception as e:
            self.init_errors.append(f"Embeddings initialization failed: {str(e)}")
            logger.exception("❌ Embeddings initialization failed")

    def _load_vectorstore(self):
        """Load vector store if available"""
        try:
            if not LANGCHAIN_AVAILABLE or not self.embeddings:
                self.warnings.append("Cannot load vector store - missing dependencies")
                return
            
            vector_dir = Path("data/processed/vectorstore")
            info_path = Path("data/processed/vectordb_info.json")
            
            if not vector_dir.exists():
                self.warnings.append(f"Vector store directory not found: {vector_dir}")
                return
            
            logger.info("📚 Loading vector store...")
            self.vectorstore = FAISS.load_local(
                str(vector_dir),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("✅ Vector store loaded successfully")
            
            # Load company info
            if info_path.exists():
                import json
                with open(info_path, "r") as f:
                    info = json.load(f)
                    self.companies = info.get("companies", [])
                    logger.info(f"✅ Loaded {len(self.companies)} companies")
            else:
                self.warnings.append("Vector DB info file not found")
                
        except Exception as e:
            self.init_errors.append(f"Vector store loading failed: {str(e)}")
            logger.exception("❌ Vector store loading failed")

    def _init_gemini(self):
        """Initialize Gemini AI model"""
        try:
            if not GENAI_AVAILABLE:
                self.warnings.append("Google Generative AI not available")
                return
            
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key:
                self.warnings.append("GOOGLE_API_KEY not available for Gemini")
                return
            
            logger.info("🧠 Initializing Gemini model...")
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            self.gemini_ready = True
            logger.info("✅ Gemini model initialized successfully")
            
        except Exception as e:
            self.init_errors.append(f"Gemini initialization failed: {str(e)}")
            logger.exception("❌ Gemini initialization failed")

    def get_system_status(self):
        """Get comprehensive system status"""
        return {
            "system_ready": bool(self.vectorstore and self.gemini_ready),
            "vectorstore_loaded": bool(self.vectorstore),
            "gemini_configured": bool(self.gemini_ready),
            "embeddings_loaded": bool(self.embeddings),
            "dependencies": {
                "langchain_available": LANGCHAIN_AVAILABLE,
                "genai_available": GENAI_AVAILABLE
            },
            "total_companies": len(self.companies),
            "companies": sorted(self.companies),
            "errors": self.init_errors,
            "warnings": self.warnings,
            "mode": "ready" if (self.vectorstore and self.gemini_ready) else "demo"
        }

    def detect_company_from_query(self, query: str):
        """Detect company mentioned in query"""
        if not query:
            return None
            
        q = query.upper()
        
        # Direct company match
        for company in self.companies:
            if company.upper() in q:
                return company
        
        # Alias match
        for main_company, aliases in self.company_aliases.items():
            for alias in aliases:
                if alias.upper() in q:
                    return main_company
        
        return None

    def enhanced_search(self, query: str, company_filter=None, k: int = 3):
        """Enhanced search with fallback to demo mode"""
        start_time = time.time()
        
        try:
            if not company_filter:
                company_filter = self.detect_company_from_query(query)
            
            if not self.vectorstore:
                return self._demo_search(query, company_filter, k, start_time)
            
            # Real vector search
            results = self.vectorstore.similarity_search(query, k=k*2)
            
            # Filter by company if specified
            if company_filter:
                filtered = []
                for result in results:
                    result_company = result.metadata.get('company', '').upper()
                    if result_company == company_filter.upper():
                        filtered.append(result)
                results = filtered[:k]
            else:
                results = results[:k]
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append({
                    "rank": i,
                    "company": result.metadata.get("company", "Unknown"),
                    "page": result.metadata.get("page_number", 1),
                    "chunk_id": result.metadata.get("chunk_id", f"chunk_{i}"),
                    "content": result.page_content,
                    "content_preview": result.page_content[:300] + "..." if len(result.page_content) > 300 else result.page_content,
                    "relevance_score": "High" if i <= 2 else "Medium"
                })
            
            return {
                "query": query,
                "company_filter": company_filter,
                "results": formatted_results,
                "search_time": time.time() - start_time,
                "total_results": len(formatted_results),
                "mode": "vectorstore"
            }
            
        except Exception as e:
            logger.exception("Search failed, falling back to demo mode")
            return self._demo_search(query, company_filter, k, start_time)

    def _demo_search(self, query: str, company_filter=None, k: int = 3, start_time=None):
        """Demo search when vector store is not available"""
        if start_time is None:
            start_time = time.time()
        
        companies = [company_filter] if company_filter else self.companies[:k]
        results = []
        
        for i, company in enumerate(companies[:k], 1):
            results.append({
                "rank": i,
                "company": company,
                "page": i,
                "chunk_id": f"demo_{i}",
                "content": f"This is demo content for {company} related to your query about: {query}. In a real system, this would contain actual SEC filing data.",
                "content_preview": f"Demo content for {company} about {query[:50]}...",
                "relevance_score": "Demo" if i <= 2 else "Demo"
            })
        
        return {
            "query": query,
            "company_filter": company_filter,
            "results": results,
            "search_time": time.time() - start_time,
            "total_results": len(results),
            "mode": "demo"
        }

    def enhanced_query_with_ai(self, query: str, k: int = 3):
        """Enhanced query with AI response"""
        start_time = time.time()
        
        try:
            # Get search results
            search_result = self.enhanced_search(query, k=k)
            docs = search_result.get("results", [])
            
            # Generate AI response
            ai_answer = self._generate_ai_response(query, docs)
            
            return {
                "query": query,
                "ai_answer": ai_answer,
                "search_results": [{
                    "company": doc.get("company", "Unknown"),
                    "content_preview": doc.get("content_preview", ""),
                    "page": doc.get("page", 1),
                    "relevance_score": doc.get("relevance_score", "Medium"),
                } for doc in docs],
                "search_time": time.time() - start_time,
                "company_detected": search_result.get("company_filter", "General Search"),
                "mode": search_result.get("mode", "demo")
            }
            
        except Exception as e:
            logger.exception("Enhanced query failed")
            return {
                "query": query,
                "ai_answer": f"❌ Error processing query: {str(e)}",
                "search_results": [],
                "search_time": time.time() - start_time,
                "company_detected": "Error",
                "mode": "error"
            }

    def _generate_ai_response(self, query: str, docs: list):
        """Generate AI response using Gemini or fallback"""
        if not self.gemini_ready or not self.gemini_model:
            return self._fallback_response(query, docs)
        
        if not docs:
            return "No relevant documents found in the database. Please ensure SEC filings have been processed and indexed."
        
        # Prepare context
        context_parts = []
        total_chars = 0
        max_chars = 4000
        
        for doc in docs:
            company = doc.get("company", "Unknown")
            page = doc.get("page", "Unknown")
            content = doc.get("content", doc.get("content_preview", ""))[:600]
            
            part = f"Company: {company} (Page {page})\nContent: {content}\n---\n"
            if total_chars + len(part) > max_chars:
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        context = "".join(context_parts)
        
        prompt = f"""You are a financial analyst assistant specializing in SEC filings analysis.

Please answer the following question based ONLY on the provided context from SEC filings. 
Be precise, factual, and cite specific information from the documents when possible.

Question: {query}

Context from SEC Filings:
{context}

Instructions:
- Answer based only on the provided context
- If the context doesn't contain enough information, clearly state this
- Be concise but thorough
- Highlight key financial metrics, dates, and company-specific information
- If comparing companies, use the data provided

Answer:"""

        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text or "No response generated from AI model."
        except Exception as e:
            logger.exception("Gemini generation failed")
            return f"AI generation failed: {str(e)}. Falling back to document summary: {self._fallback_response(query, docs)}"

    def _fallback_response(self, query: str, docs: list):
        """Fallback response when AI is not available"""
        if not docs:
            return "No relevant documents found. The system is running in demo mode - please configure GOOGLE_API_KEY and ensure SEC documents are processed."
        
        summary = f"Found {len(docs)} relevant documents for your query about: {query}\n\n"
        
        for i, doc in enumerate(docs, 1):
            company = doc.get("company", "Unknown")
            preview = doc.get("content_preview", "No preview available")[:200]
            summary += f"{i}. {company}: {preview}...\n\n"
        
        summary += "Note: AI analysis is not available. Please configure GOOGLE_API_KEY for enhanced responses."
        return summary

    # Legacy compatibility methods
    def hybrid_search(self, query: str, k: int = 3):
        """Legacy method for backward compatibility"""
        result = self.enhanced_search(query, k=k)
        return result["results"]