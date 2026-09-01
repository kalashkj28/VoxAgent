"""Retrieval Augmented Generation (RAG) using FAISS and SentenceTransformers."""

import os
import numpy as np
from pathlib import Path

class KnowledgeBase:
    """PDF knowledge base with FAISS vector search."""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        self.kb_dir = kb_dir
        self.chunks = []
        self.index = None
        self.embedder = None
        self.is_ready = False
        
    def load_documents(self):
        """Load PDFs, create chunks, generate embeddings, and build FAISS index."""
        print("📚 Loading knowledge base...")
        
        all_text = self._extract_pdfs()
        
        if not all_text:
            print("⚠️ No PDFs found in knowledge_base/ folder!")
            print(f"   Put PDF files in: {os.path.abspath(self.kb_dir)}")
            return
        
        self.chunks = self._create_chunks(all_text, chunk_size=500, overlap=100)
        print(f"📄 Created {len(self.chunks)} chunks from documents")
        
        from sentence_transformers import SentenceTransformer
        print("🔄 Loading embedding model (first time download ~80MB)...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded!")
        
        print("🔄 Generating embeddings...")
        chunk_texts = [c["text"] for c in self.chunks]
        embeddings = self.embedder.encode(chunk_texts, show_progress_bar=True)
        
        import faiss
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings, dtype="float32"))
        
        self.is_ready = True
        print(f"✅ Knowledge base ready! {len(self.chunks)} chunks indexed.")
    
    def search(self, query: str, top_k: int = 3) -> list:
        """Find relevant chunks for a query."""
        if not self.is_ready:
            return [{"text": "Knowledge base not loaded. Put PDFs in knowledge_base/ folder.", 
                     "source": "system", "score": 0}]
        
        query_embedding = self.embedder.encode([query])
        
        import faiss
        distances, indices = self.index.search(
            np.array(query_embedding, dtype="float32"), top_k
        )
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "score": round(float(distances[0][i]), 2)
                })
        
        return results
    
    def _extract_pdfs(self) -> list:
        """Extract text from all PDFs in kb_dir."""
        from pypdf import PdfReader
        
        documents = []
        kb_path = Path(self.kb_dir)
        
        if not kb_path.exists():
            os.makedirs(kb_path, exist_ok=True)
            return []
        
        for pdf_file in kb_path.glob("*.pdf"):
            try:
                reader = PdfReader(str(pdf_file))
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if text.strip():
                    documents.append({
                        "text": text,
                        "source": pdf_file.name
                    })
                    print(f"   📄 Loaded: {pdf_file.name} ({len(text)} chars)")
            except Exception as e:
                print(f"   ❌ Error loading {pdf_file.name}: {e}")
        
        return documents
    
    def _create_chunks(self, documents: list, chunk_size: int = 500, overlap: int = 100) -> list:
        """Split documents into smaller overlapping chunks."""
        chunks = []
        
        for doc in documents:
            text = doc["text"]
            source = doc["source"]
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i + chunk_size].strip()
                if len(chunk_text) > 50:
                    chunks.append({
                        "text": chunk_text,
                        "source": source
                    })
        
        return chunks

kb = KnowledgeBase()
