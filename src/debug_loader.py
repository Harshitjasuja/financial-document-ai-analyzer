from pathlib import Path

def debug_filenames():
    """Debug what's happening with filenames"""
    pdf_directory = Path("data/raw")
    pdf_files = list(pdf_directory.glob("*.pdf"))
    
    print("🔍 Debugging filename extraction...")
    print(f"Found {len(pdf_files)} PDF files:")
    
    for pdf_path in pdf_files:
        print(f"\nFile: {pdf_path}")
        print(f"  pdf_path: {pdf_path}")
        print(f"  pdf_path.name: {pdf_path.name}")
        print(f"  pdf_path.stem: {pdf_path.stem}")
        print(f"  type of stem: {type(pdf_path.stem)}")
        
        # Try the extraction
        try:
            stem_str = str(pdf_path.stem)
            if '_' in stem_str:
                company = stem_str.split('_').upper()
            else:
                company = stem_str.upper()
            print(f"  extracted company: {company}")
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    debug_filenames()
