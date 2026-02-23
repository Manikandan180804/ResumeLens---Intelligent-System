#!/usr/bin/env python
"""
Startup script for the Resume Intelligence System.
Initializes the database and seed data.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import create_tables
from backend.config import settings

def initialize():
    print("=" * 60)
    print("  Resume Intelligence System - Initializer")
    print("=" * 60)

    print(f"[1] Creating database at: {settings.DATABASE_URL}")
    create_tables()
    print("    ✅ Database tables created")

    # Create FAISS index directory
    import os
    faiss_dir = os.path.dirname(settings.FAISS_INDEX_PATH)
    if faiss_dir:
        os.makedirs(faiss_dir, exist_ok=True)
    print(f"[2] FAISS index directory: {settings.FAISS_INDEX_PATH}")
    print("    ✅ Ready")

    print("[3] Pre-loading embedding model...")
    try:
        from backend.vector_store import get_embedding_generator
        gen = get_embedding_generator()
        test_emb = gen.generate("test embedding initialization")
        print(f"    ✅ Embedding model loaded (dim={len(test_emb)})")
    except Exception as e:
        print(f"    ⚠️  Embedding model will load on first use: {e}")

    print("[4] Pre-loading OCR models...")
    try:
        import easyocr
        # Initialize reader just once to trigger downloads
        reader = easyocr.Reader(['en'], gpu=False)
        print("    ✅ EasyOCR models ready")
    except Exception as e:
        print(f"    ⚠️  OCR models will download on first image upload: {e}")

    print()
    print("=" * 60)
    print("  Setup complete! Start the services:")
    print()
    print("  Terminal 1 (Backend): python -m uvicorn backend.main:app --reload --port 8000")
    print("  Terminal 2 (Frontend): cd frontend; python -m http.server 8501")
    print()
    print("  Note: If you use CMD (Standard), use 'cd frontend && python -m http.server 8501'")
    print("  Note: If you use PowerShell, use 'cd frontend; python -m http.server 8501'")
    print()
    print("  Frontend Access: http://localhost:8501")
    print("  Backend API:      http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    initialize()
