import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from rag_with_api import RAGWithGemini
except ImportError:
    st.error("❌ Could not import RAG system. Make sure all files are in the correct location.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="SEC Filings RAG Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
    st.session_state.system_loaded = False

@st.cache_resource
def initialize_rag_system():
    """Initialize RAG system - cached to avoid reloading"""
    try:
        with st.spinner("🤖 Initializing RAG System..."):
            rag_system = RAGWithGemini()
            return rag_system, True
    except Exception as e:
        st.error(f"❌ Error initializing RAG system: {str(e)}")
        return None, False

def main():
    # Header
    st.title("📊 SEC Filings RAG Assistant")
    st.markdown("*Intelligent Financial Document Analysis with AI*")
    
    # Sidebar - System Status
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Initialize system
        if not st.session_state.system_loaded:
            if st.button("🚀 Initialize RAG System"):
                rag_system, success = initialize_rag_system()
                st.session_state.rag_system = rag_system
                st.session_state.system_loaded = success
                
                if success:
                    st.success("✅ System Ready!")
                    st.rerun()
        else:
            st.success("✅ System Ready!")
            
        # System Info
        if st.session_state.system_loaded and st.session_state.rag_system:
            st.markdown("---")
            st.subheader("📈 System Info")
            try:
                companies = st.session_state.rag_system.companies
                st.write(f"**Companies:** {len(companies)}")
                st.write(f"**Vector Database:** FAISS")
                st.write(f"**AI Model:** Gemini 2.0 Flash")
                
                with st.expander("View Companies"):
                    for company in sorted(companies):
                        st.write(f"• {company}")
            except:
                st.write("System info unavailable")

    # Main content
    if not st.session_state.system_loaded:
        st.info("👈 Please initialize the RAG system using the sidebar")
        
        # Show sample queries while waiting
        st.subheader("🔍 Sample Queries You Can Try:")
        sample_queries = [
            "What was Apple's revenue in 2024?",
            "How did Tesla perform financially?",
            "What are Microsoft's key risk factors?",
            "Compare Netflix's growth strategy",
            "What AI investments is Google making?",
            "Which company has the highest profit margins?"
        ]
        
        for i, query in enumerate(sample_queries, 1):
            st.write(f"{i}. {query}")
            
    else:
        # MAIN QUERY SECTION - FULL WIDTH
        st.subheader("💬 Ask Your Question")
        
        # Query input - FULL WIDTH
        user_query = st.text_area(
            "Enter your question about SEC filings:",
            placeholder="e.g., What was Apple's revenue in 2024?",
            height=100,
            key="user_query"
        )
        
        # Query options in columns
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            num_results = st.selectbox("Number of results:", [3, 5, 7], index=0)
        with col_b:
            query_type = st.radio("Search type:", ["Auto-detect", "General search"], horizontal=True)
        with col_c:
            st.write("") # Empty space
        
        # Search button
        if st.button("🔍 Search & Analyze", type="primary", disabled=not user_query.strip()):
            if user_query.strip():
                process_and_display_query(user_query.strip(), num_results)
        
        # QUICK ACTIONS SECTION - FULL WIDTH
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        st.write("**Click any button to get instant analysis:**")
        
        # Quick action buttons in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Apple's 2024 revenue", key="apple_revenue"):
                process_and_display_query("What was Apple's total revenue in 2024?", 3)
            
            if st.button("🚗 Tesla financial performance", key="tesla_finance"):
                process_and_display_query("How did Tesla perform financially in 2024?", 3)
        
        with col2:
            if st.button("⚠️ Microsoft risk factors", key="msft_risks"):
                process_and_display_query("What are Microsoft's key risk factors?", 3)
            
            if st.button("🎬 Netflix content strategy", key="netflix_strategy"):
                process_and_display_query("What is Netflix's content strategy and growth plan?", 3)
        
        with col3:
            if st.button("🤖 Google AI investments", key="google_ai"):
                process_and_display_query("What AI investments and developments is Google making?", 3)
            
            if st.button("💰 Highest revenue company", key="revenue_compare"):
                process_and_display_query("Which company has the highest revenue in 2024?", 5)
        
        # Additional comparison buttons
        st.write("**Comparison Queries:**")
        col_comp1, col_comp2 = st.columns(2)
        
        with col_comp1:
            if st.button("⚡ Tech sector risks", key="tech_risks"):
                process_and_display_query("What are the main risks facing technology companies?", 5)
        
        with col_comp2:
            if st.button("🔬 AI investment comparison", key="ai_comparison"):
                process_and_display_query("Compare AI investments across technology companies", 5)

def process_and_display_query(query: str, k: int):
    """Process query and display results BELOW the main interface"""
    
    # Show processing status
    with st.spinner("🔍 Searching documents and generating AI response..."):
        try:
            # Get AI-powered response
            result = st.session_state.rag_system.enhanced_query_with_ai(query, k=k)
            
            # Display results immediately below
            display_results_below(result)
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.write("Please check your API key and try again.")

def display_results_below(result: dict):
    """Display results BELOW the main interface - FIXED FONT CONSISTENCY"""
    
    # RESULTS SECTION - FULL WIDTH
    st.markdown("---")
    st.markdown("# 📋 Analysis Results")
    
    # Query header
    st.markdown(f"### 🔍 Query: *{result['query']}*")
    
    # Simple, clean status line - NO COMPRESSED METRICS
    company = result.get('company_detected', 'General Search')
    st.write(f"**✅ Analysis Complete** | ⚡ Search Time: **{result['search_time']:.3f} seconds** | 🏢 Company Focus: **{company}** | 📄 Sources Analyzed: **{len(result['search_results'])}**")
    
    # AI ANALYSIS - CONSISTENT FONT WITH BEST FIX
    st.markdown("---")
    st.markdown("## 🤖 AI Analysis")
    
    # BEST FIX: Clean info box with consistent formatting
    with st.container():
        st.markdown(
            f"""
            <div style="
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 16px;
                line-height: 1.6;
                color: #155724;
                white-space: pre-wrap;
                word-wrap: break-word;
            ">
                {result['ai_answer']}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # SOURCE DOCUMENTS - CLEAN LAYOUT
    st.markdown("---")
    st.markdown("## 📚 Source Documents")
    st.write(f"*Analysis based on excerpts from {len(result['search_results'])} SEC filing pages*")
    
    # Display sources in clean expandable sections
    for i, source in enumerate(result['search_results'], 1):
        with st.expander(
            f"📄 **{source['company']}** - Page {source['page']} ({source['relevance_score']} Relevance)",
            expanded=(i == 1)  # Expand first result
        ):
            # Clean source info
            st.write(f"**📋 Document:** {source['company']} SEC 10-K Filing")
            st.write(f"**📄 Page Number:** {source['page']}")
            st.write(f"**🎯 Relevance:** {source['relevance_score']}")
            st.write(f"**🔗 Chunk ID:** {source['chunk_id']}")
            
            st.markdown("---")
            st.markdown("**📝 Document Content:**")
            
            # Display content in clean text format
            content = source['content'][:1200] + "..." if len(source['content']) > 1200 else source['content']
            
            # Use text area for better formatting
            st.text_area(
                f"Content from {source['company']} (Page {source['page']})",
                value=content,
                height=180,
                key=f"source_{i}",
                disabled=True
            )
    
    # Clean separator and next action prompt
    st.markdown("---")
    st.info("🔄 **Ready for your next question!** Use the query box above or click any Quick Action button.")

def add_sidebar_features():
    """Add additional features to sidebar"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🛠️ Advanced Options")
        
        if st.button("🧪 Run System Tests"):
            run_system_tests()
        
        if st.button("📊 Show Statistics"):
            show_system_stats()
        
        st.markdown("---")
        st.subheader("ℹ️ About This System")
        st.write("**RAG Technology Stack:**")
        st.write("• **Documents:** 1,349 SEC pages")
        st.write("• **Chunks:** 6,541 searchable segments")
        st.write("• **Embeddings:** sentence-transformers")
        st.write("• **Vector DB:** FAISS")
        st.write("• **AI Model:** Google Gemini 2.0")
        st.write("• **Frontend:** Streamlit")
        
        st.markdown("---")
        st.write("**📈 Performance:**")
        st.write("• Search: <0.1 seconds")
        st.write("• AI Response: 2-5 seconds")
        st.write("• Total Analysis: <10 seconds")

def run_system_tests():
    """Run basic system tests"""
    st.markdown("---")
    st.subheader("🧪 System Tests")
    
    test_queries = [
        "What is Apple's main business?",
        "How did Tesla perform?", 
        "Microsoft risk factors"
    ]
    
    progress_bar = st.progress(0)
    test_results = []
    
    for i, query in enumerate(test_queries):
        st.write(f"**Testing Query {i+1}:** {query}")
        
        try:
            result = st.session_state.rag_system.enhanced_search(query, k=1)
            
            test_results.append({
                'query': query,
                'status': '✅ Passed',
                'time': result['search_time']
            })
            st.success(f"✅ Test {i+1} **PASSED** - {result['search_time']:.3f} seconds")
            
        except Exception as e:
            test_results.append({
                'query': query,
                'status': '❌ Failed',
                'error': str(e)[:100]
            })
            st.error(f"❌ Test {i+1} **FAILED**: {str(e)[:100]}...")
        
        progress_bar.progress((i + 1) / len(test_queries))
    
    # Test summary
    st.markdown("---")
    st.subheader("📊 Test Results Summary")
    
    passed = sum(1 for r in test_results if '✅' in r['status'])
    total = len(test_results)
    
    if passed == total:
        st.success(f"🎉 **ALL TESTS PASSED** ({passed}/{total})")
    else:
        st.warning(f"⚠️ **{passed}/{total} Tests Passed**")
    
    # Detailed results
    with st.expander("📋 Detailed Test Results"):
        for i, test in enumerate(test_results, 1):
            if '✅' in test['status']:
                st.write(f"**Test {i}:** {test['query']} - {test['status']} ({test['time']:.3f}s)")
            else:
                st.write(f"**Test {i}:** {test['query']} - {test['status']}")
                st.write(f"   Error: {test['error']}")

def show_system_stats():
    """Show comprehensive system statistics"""
    st.markdown("---")
    st.subheader("📊 Comprehensive System Statistics")
    
    try:
        # Data Processing Stats
        st.markdown("### 📄 Data Processing")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("SEC Documents Processed", "1,349 pages", help="Total pages from SEC 10-K filings")
            st.metric("Text Chunks Generated", "6,541 chunks", help="Intelligent text segments for search")
            st.metric("Companies Covered", "10 companies", help="Major technology companies")
        
        with col2:
            st.metric("Vector Dimensions", "384 dimensions", help="Embedding vector size")
            st.metric("Database Technology", "FAISS", help="Facebook AI Similarity Search")
            st.metric("AI Model", "Gemini 2.0 Flash", help="Google's latest language model")
        
        # Performance Metrics
        st.markdown("### ⚡ Performance Benchmarks")
        
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.write("**🔍 Search Performance:**")
            st.write("• Vector similarity search: < 0.05 seconds")
            st.write("• Document retrieval: < 0.1 seconds") 
            st.write("• Company auto-detection: Instant")
            st.write("• Result ranking & filtering: < 0.01 seconds")
        
        with perf_col2:
            st.write("**🤖 AI Response Generation:**")
            st.write("• Context preparation: < 0.1 seconds")
            st.write("• Gemini API call: 2-5 seconds")
            st.write("• Response formatting: < 0.1 seconds")
            st.write("• **Total end-to-end: < 10 seconds**")
        
        # Data Quality Metrics
        st.markdown("### 📈 Data Quality & Coverage")
        
        st.write("**📋 Document Coverage:**")
        companies_info = [
            "APPLE - Consumer electronics, services",
            "MICROSOFT - Cloud computing, productivity software", 
            "GOOGLE - Search, advertising, cloud services",
            "TESLA - Electric vehicles, energy storage",
            "AMAZON - E-commerce, cloud computing",
            "NETFLIX - Streaming entertainment",
            "NVIDIA - Graphics processing, AI chips",
            "INTEL - Semiconductors, processors",
            "ORACLE - Database software, cloud services",
            "SALESFORCE - Customer relationship management"
        ]
        
        for company_info in companies_info:
            st.write(f"• {company_info}")
        
        st.markdown("---")
        st.write("**✅ Data Quality Assurance:**")
        st.write("• All documents from official SEC EDGAR database")
        st.write("• 2024 fiscal year 10-K filings")
        st.write("• Complete document processing (no truncation)")
        st.write("• Validated company name extraction")
        st.write("• Cross-referenced financial data")
        
    except Exception as e:
        st.error(f"Error loading comprehensive statistics: {e}")

if __name__ == "__main__":
    main()
    add_sidebar_features()