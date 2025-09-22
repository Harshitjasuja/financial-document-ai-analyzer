# run.py - Fixed version with better error handling
import os
import sys
import logging
import time
# import method
import traceback
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, redirect, url_for

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Python path setup
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    logger.info(f"✅ Added {SRC_DIR} to Python path")

# Environment setup
def setup_environment():
    """Setup environment with better error handling"""
    env_paths = [
        PROJECT_ROOT / ".env",
        Path(".env"),
        Path("../.env")
    ]
    
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded environment from {env_path}")
            loaded = True
            break
    
    if not loaded:
        logger.warning("⚠️ No .env file found")
    
    # Set defaults
    os.environ.setdefault("FLASK_ENV", "development")
    os.environ.setdefault("FLASK_DEBUG", "1")
    os.environ.setdefault("SECRET_KEY", "change-this-in-production")
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if api_key:
        logger.info("✅ GOOGLE_API_KEY found")
    else:
        logger.warning("⚠️ GOOGLE_API_KEY not found - AI features will be limited")

# Create directories
def create_directories():
    """Create necessary directories"""
    dirs = [TEMPLATES_DIR, STATIC_DIR / "css", STATIC_DIR / "js", DATA_RAW, DATA_PROCESSED, SRC_DIR]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"📁 Ensured directory exists: {directory}")

# Setup
setup_environment()
create_directories()

# Flask app
app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-in-production")

# Global RAG system
rag_system = None

def initialize_rag():
    """Initialize RAG system with comprehensive error handling"""
    global rag_system
    
    if rag_system is not None:
        logger.info("📚 RAG system already initialized")
        return rag_system
    
    try:
        logger.info("🤖 Starting RAG system initialization...")
        
        # Try the fixed version first, then fallback to original
        try:
            from rag_with_api_fixed import RAGWithGemini
            logger.info("✅ Using fixed RAG system")
        except ImportError:
            try:
                from rag_with_api import RAGWithGemini
                logger.info("✅ Using original RAG system")
            except ImportError as e:
                logger.error(f"❌ Cannot import RAG system: {e}")
                raise
        
        rag_system = RAGWithGemini()
        
        # Log initialization status
        if hasattr(rag_system, 'init_errors') and rag_system.init_errors:
            for error in rag_system.init_errors:
                logger.error(f"❌ RAG Init Error: {error}")
        
        if hasattr(rag_system, 'warnings') and rag_system.warnings:
            for warning in rag_system.warnings:
                logger.warning(f"⚠️ RAG Warning: {warning}")
        
        logger.info("✅ RAG system initialized successfully")
        return rag_system
        
    except Exception as e:
        logger.exception("❌ RAG system initialization failed")
        rag_system = None
        raise

# Routes with better error handling
@app.route("/")
def index():
    """Main page with error handling"""
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"❌ Index render error: {e}")
        return f"""
        <html><head><title>SEC RAG Assistant</title></head><body>
        <h1>SEC RAG Assistant</h1>
        <p><strong>Template Error:</strong> {e}</p>
        <p>Please ensure templates/index.html exists.</p>
        <div style="margin-top: 20px;">
            <button 
            onclick="fetch('/api/initialize', {{method: 'POST'}})
                .then(r => r.json())
                .then(d => alert(JSON.stringify(d, null, 2)))">
            Test Initialize API
            </button>

        </div>
        </body></html>
        """

@app.route("/dashboard")
def dashboard():
    try:
        template_path = TEMPLATES_DIR / "dashboard.html"
        if template_path.exists():
            return render_template("dashboard.html")
        else:
            logger.warning("📄 dashboard.html not found, redirecting to index")
            return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"❌ Dashboard render error: {e}")
        return redirect(url_for("index"))

@app.route("/upload")
def upload():
    try:
        template_path = TEMPLATES_DIR / "upload.html"
        if template_path.exists():
            return render_template("upload.html")
        else:
            logger.warning("📄 upload.html not found, redirecting to index")
            return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"❌ Upload render error: {e}")
        return redirect(url_for("index"))

@app.route("/analytics")
def analytics():
    try:
        template_path = TEMPLATES_DIR / "analytics.html"
        if template_path.exists():
            return render_template("analytics.html")
        else:
            logger.warning("📄 analytics.html not found, redirecting to index")
            return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"❌ Analytics render error: {e}")
        return redirect(url_for("index"))

# API Routes with enhanced error handling
@app.route("/api/initialize", methods=["POST"])
def api_initialize():
    """Initialize API with detailed error reporting"""
    try:
        logger.info("🚀 API Initialize called")
        
        system = initialize_rag()
        if system is None:
            error_msg = "Failed to initialize RAG system - check server logs"
            logger.error(f"❌ {error_msg}")
            return jsonify({
                "success": False, 
                "message": error_msg,
                "errors": ["System initialization returned None"]
            }), 500

        # Get status with error handling
        try:
            status = system.get_system_status() if hasattr(system, "get_system_status") else {}
        except Exception as e:
            logger.exception("❌ Failed to get system status")
            status = {"error": str(e)}

        response_data = {
            "success": True,
            "message": "RAG system initialized successfully",
            "companies": status.get("companies", []),
            "system_info": {
                "model": "Gemini 1.5 Flash",
                "vectordb": "FAISS",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "system_ready": status.get("system_ready", False),
                "mode": status.get("mode", "demo"),
                "errors": status.get("errors", []),
                "warnings": status.get("warnings", []),
                "dependencies": status.get("dependencies", {}),
                "total_companies": status.get("total_companies", 0)
            }
        }
        
        logger.info(f"✅ API Initialize successful - Mode: {status.get('mode', 'unknown')}")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"API initialization failed: {str(e)}"
        logger.exception(f"❌ {error_msg}")
        return jsonify({
            "success": False,
            "message": error_msg,
            "errors": [str(e)],
            "traceback": traceback.format_exc() if app.debug else None
        }), 500

@app.route("/api/query", methods=["POST"])
def api_query():
    """Enhanced query API with better error handling"""
    try:
        logger.info("🔍 API Query called")
        
        system = initialize_rag()
        if system is None:
            return jsonify({
                "success": False,
                "message": "RAG system not initialized - call /api/initialize first"
            }), 500

        # Parse request data with validation
        try:
            data = request.get_json(force=True) or {}
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Invalid JSON data: {str(e)}"
            }), 400

        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({
                "success": False,
                "message": "Query cannot be empty"
            }), 400

        try:
            k = int(data.get("num_results", 3))
            k = max(1, min(k, 10))  # Clamp between 1 and 10
        except (ValueError, TypeError):
            k = 3

        logger.info(f"🔍 Processing query: '{query}' (k={k})")

        # Execute query
        result = system.enhanced_query_with_ai(query, k=k)
        
        logger.info(f"✅ Query processed successfully in {result.get('search_time', 0):.3f}s")
        return jsonify({"success": True, "result": result})

    except Exception as e:
        error_msg = f"Query processing failed: {str(e)}"
        logger.exception(f"❌ {error_msg}")
        return jsonify({
            "success": False,
            "message": error_msg,
            "traceback": traceback.format_exc() if app.debug else None
        }), 500

@app.route("/api/companies", methods=["GET"])
def api_companies():
    """Get companies list with error handling"""
    try:
        system = initialize_rag()
        if system:
            companies = getattr(system, "companies", [])
            logger.info(f"📋 Retrieved {len(companies)} companies")
            return jsonify({"success": True, "companies": sorted(companies)})
        else:
            logger.warning("⚠️ System not initialized for companies API")
            return jsonify({"success": True, "companies": []})
            
    except Exception as e:
        logger.exception("❌ Companies API error")
        return jsonify({"success": False, "companies": [], "error": str(e)}), 500

@app.route("/api/system_info", methods=["GET"])
def api_system_info():
    """Get detailed system information"""
    try:
        system = initialize_rag()
        if not system:
            return jsonify({
                "success": False,
                "message": "System not initialized",
                "system_info": {"status": "not_initialized"}
            })

        status = system.get_system_status() if hasattr(system, "get_system_status") else {}
        
        system_info = {
            "status": "ready" if status.get("system_ready") else "demo",
            "model": "Gemini 1.5 Flash",
            "vectordb": "FAISS",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "total_companies": len(getattr(system, "companies", [])),
            **status
        }
        
        return jsonify({
            "success": True,
            "system_info": system_info
        })
        
    except Exception as e:
        logger.exception("❌ System info API error")
        return jsonify({
            "success": False,
            "message": str(e),
            "traceback": traceback.format_exc() if app.debug else None
        }), 500

@app.route("/api/sample_queries", methods=["GET"])
def api_sample_queries():
    """Get sample queries for UI"""
    try:
        sample_queries = [
            {
                "category": "Financial Performance",
                "queries": [
                    "What was Apple's revenue in the latest quarter?",
                    "How did Tesla perform financially this year?",
                    "Which company has the highest profit margins?",
                    "Compare revenue growth across tech companies",
                    "What are Microsoft's key financial metrics?"
                ]
            },
            {
                "category": "Business Strategy",
                "queries": [
                    "What is Netflix's content strategy?",
                    "How does Microsoft compete in cloud computing?",
                    "What are Google's AI investments?",
                    "What is Amazon's expansion strategy?",
                    "How is Apple diversifying its business?"
                ]
            },
            {
                "category": "Risk Analysis",
                "queries": [
                    "What are Apple's key risk factors?",
                    "What risks do tech companies face?",
                    "How are companies managing supply chain issues?",
                    "What regulatory risks affect the industry?",
                    "What are the cybersecurity concerns mentioned?"
                ]
            },
            {
                "category": "Market & Competition",
                "queries": [
                    "How does Tesla view competition in EV market?",
                    "What does Netflix say about streaming competition?",
                    "How is Microsoft positioned against competitors?",
                    "What market opportunities do companies see?",
                    "How are companies adapting to market changes?"
                ]
            }
        ]
        return jsonify({"success": True, "sample_queries": sample_queries})
    except Exception as e:
        logger.exception("❌ Sample queries API error")
        return jsonify({"success": False, "sample_queries": []})

@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint"""
    try:
        health_info = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "environment": {
                "python_version": sys.version,
                "flask_debug": app.debug,
                "project_root": str(PROJECT_ROOT)
            },
            "dependencies": {
                "src_in_path": str(SRC_DIR) in sys.path,
                "templates_dir_exists": TEMPLATES_DIR.exists(),
                "static_dir_exists": STATIC_DIR.exists()
            },
            "rag_system": {
                "initialized": rag_system is not None,
                "type": type(rag_system).__name__ if rag_system else None
            }
        }
        
        return jsonify(health_info)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    try:
        if (TEMPLATES_DIR / "404.html").exists():
            return render_template("404.html"), 404
    except Exception:
        pass
    
    return """
    <html><head><title>404 - Not Found</title></head><body>
    <h1>404 - Page Not Found</h1>
    <p>The requested page could not be found.</p>
    <a href="/">← Back to Home</a>
    </body></html>
    """, 404

@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    logger.exception("❌ 500 Server Error")
    
    try:
        if (TEMPLATES_DIR / "500.html").exists():
            return render_template("500.html"), 500
    except Exception:
        pass
    
    return """
    <html><head><title>500 - Server Error</title></head><body>
    <h1>500 - Server Error</h1>
    <p>An internal server error occurred.</p>
    <a href="/">← Back to Home</a>
    </body></html>
    """, 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Generic exception handler"""
    logger.exception("❌ Unhandled exception")
    
    if app.debug:
        # In debug mode, let the default handler show the traceback
        return None
    
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

def main():
    """Main function to run the app"""
    try:
        # Configuration
        host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
        port = int(os.getenv("FLASK_RUN_PORT", "5000"))
        debug = os.getenv("FLASK_DEBUG", "1").lower() in ("1", "true", "yes", "on")
        
        # Log startup information
        logger.info("🚀 Starting SEC RAG Assistant Server")
        logger.info(f"🌐 Server: http://{host}:{port}")
        logger.info(f"🔧 Debug mode: {debug}")
        logger.info(f"📁 Project root: {PROJECT_ROOT}")
        logger.info(f"📁 Templates: {TEMPLATES_DIR}")
        logger.info(f"📁 Static: {STATIC_DIR}")
        
        # Check critical paths
        if not TEMPLATES_DIR.exists():
            logger.error(f"❌ Templates directory not found: {TEMPLATES_DIR}")
        if not (TEMPLATES_DIR / "index.html").exists():
            logger.error(f"❌ index.html not found in templates directory")
        
        # Pre-initialize system check (optional)
        logger.info("🔍 Checking system readiness...")
        try:
            test_system = initialize_rag()
            if test_system:
                logger.info("✅ RAG system ready for requests")
            else:
                logger.warning("⚠️ RAG system will initialize on first request")
        except Exception as e:
            logger.warning(f"⚠️ RAG system pre-check failed: {e}")
        
        # Start server
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.exception("❌ Failed to start server")
        sys.exit(1)

if __name__ == "__main__":
    main()