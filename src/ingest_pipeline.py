# src/ingest_pipeline.py
from pathlib import Path
import json
import time
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from PyPDF2 import PdfReader

def pdf_to_pages(pdf_path: str) -> List[Dict]:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page": i, "text": text})
    return pages

def build_chunks(pages: List[Dict], chunk_size=1000, chunk_overlap=200) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for p in pages:
        parts = splitter.split_text(p["text"] or "")
        for idx, part in enumerate(parts):
            chunks.append({"page": p["page"], "content": part})
    return chunks

def build_faiss_from_chunks(chunks: List[Dict], company: str, embeddings=None, out_dir="data/processed/vectorstore"):
    embeddings = embeddings or HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    texts = [c["content"] for c in chunks if c["content"]]
    metas = [{"company": company.upper(), "page_number": c["page"]} for c in chunks if c["content"]]
    if not texts:
        raise ValueError("No text chunks to index")
    vs = FAISS.from_texts(texts, embedding=embeddings, metadatas=metas)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    vs.save_local(out_dir)
    return out_dir

def update_company_registry(company: str, registry_file="data/processed/vectordb_info.json"):
    reg = {}
    p = Path(registry_file)
    if p.exists():
        try:
            reg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            reg = {}
    companies = set(reg.get("companies", []))
    companies.add(company.upper())
    reg["companies"] = sorted(companies)
    reg["updated_at"] = time.time()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return reg
