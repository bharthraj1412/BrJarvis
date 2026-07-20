# memory/vector_store.py
"""
ChromaDB-backed vector memory for JARVIS MK37.
Uses Gemini API for fast embeddings, with a pure-Python TF-IDF similarity fallback if ChromaDB is missing.
"""
from __future__ import annotations

import os
import json
import re
import math
import uuid
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).resolve().parent.parent / "memory_db"

# ── Optional dependency guard ─────────────────────────────────────────────
_CHROMA_AVAILABLE = False
_BaseClass = object

try:
    import chromadb  # type: ignore
    from chromadb.api.types import EmbeddingFunction
    _BaseClass = EmbeddingFunction
    _CHROMA_AVAILABLE = True
except ImportError:
    pass


class GeminiEmbeddingFunction(_BaseClass):
    """ChromaDB embedding function using Gemini Client."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        self.model = "gemini-embedding-001"

    @staticmethod
    def name() -> str:
        return "gemini"

    def get_config(self) -> dict:
        return {"model": self.model}

    @property
    def client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            try:
                res = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config={"output_dimensionality": 768}
                )
                val = res.embeddings[0].values
                embeddings.append(val)
            except Exception as e:
                print(f"[VectorMemory] Embedding generation warning: {e}")
                embeddings.append([0.0] * 768)
        return embeddings


def _load_api_key() -> str:
    """Load Gemini API key from env or config/api_keys.json."""
    for env in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env, "").strip()
        if val:
            return val

    cfg_path = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            key = data.get("gemini_api_key", "").strip()
            if key:
                return key
        except Exception:
            pass
    return ""


class TextSimilarityMemory:
    """Fallback term-frequency TF-IDF relevance memory for offline/zero-dependency search."""
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.entries = []
        self._load()

    def _load(self):
        if self.filepath.exists():
            try:
                self.entries = json.loads(self.filepath.read_text(encoding="utf-8"))
            except Exception:
                self.entries = []

    def _save(self):
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.filepath.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
        except Exception:
            pass

    def store(self, text: str, metadata: dict = None, doc_id: str = None):
        # Dedup: check if identical text already exists
        if any(e["text"].strip() == text.strip() for e in self.entries):
            return
        self.entries.append({
            "id": doc_id or str(uuid.uuid4()),
            "text": text,
            "metadata": metadata or {}
        })
        self._save()

    def recall(self, query: str, n: int = 5) -> list[str]:
        if not self.entries:
            return []
        
        query_words = set(re.findall(r'\w+', query.lower()))
        if not query_words:
            return [e["text"] for e in self.entries[:n]]

        ranked = []
        for e in self.entries:
            doc_words = re.findall(r'\w+', e["text"].lower())
            doc_word_set = set(doc_words)
            overlap = query_words.intersection(doc_word_set)
            
            score = 0.0
            for w in overlap:
                tf = doc_words.count(w)
                df = sum(1 for doc in self.entries if w in doc["text"].lower())
                idf = math.log((1 + len(self.entries)) / (1 + df)) + 1.0
                score += math.log(1 + tf) * idf
                
            if score > 0:
                ranked.append((score, e["text"]))

        ranked.sort(reverse=True)
        if not ranked:
            # Fallback: return recent items
            return [e["text"] for e in self.entries[:n]]
        return [text for _, text in ranked[:n]]


class VectorMemory:
    """
    Unified vector memory. Uses ChromaDB with Gemini Embeddings when available,
    and falls back gracefully to a pure-Python TF-IDF similarity store otherwise.
    """

    def __init__(self, collection_name: str = "jarvis"):
        self._collection = None
        self._fallback = None
        self._available = False

        api_key = _load_api_key()
        
        if _CHROMA_AVAILABLE and api_key:
            try:
                ef = GeminiEmbeddingFunction(api_key=api_key)
                client = chromadb.PersistentClient(path=str(_DB_PATH))
                self._collection = client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=ef,
                )
                self._available = True
                print("[VectorMemory] ✅ ChromaDB vector store initialized.")
            except Exception as e:
                print(f"[VectorMemory] ⚠️ ChromaDB initialization failed ({e}). Falling back to text similarity.")
        
        if not self._available:
            self._fallback = TextSimilarityMemory(_DB_PATH / "fallback_memory.json")
            self._available = True
            print("[VectorMemory] ✓ Fallback text similarity memory active.")

    # ── Public API ────────────────────────────────────────────────────────

    def store(
        self,
        text: str,
        metadata: Optional[dict] = None,
        doc_id: Optional[str] = None,
    ) -> None:
        if not self._available:
            return

        if self._collection:
            try:
                # Dedup check via query
                existing = self._collection.query(query_texts=[text], n_results=1)
                if existing and existing["documents"] and existing["documents"][0]:
                    if existing["documents"][0][0].strip() == text.strip():
                        return  # Dedup matched
                
                self._collection.add(
                    documents=[text],
                    metadatas=[metadata or {}],
                    ids=[doc_id or str(uuid.uuid4())],
                )
            except Exception as e:
                print(f"[VectorMemory] ⚠️ store() failed: {e}")
        elif self._fallback:
            self._fallback.store(text, metadata, doc_id)

    def recall(self, query: str, n: int = 5) -> list[str]:
        if not self._available:
            return []

        if self._collection:
            try:
                count = self._collection.count()
                if count == 0:
                    return []
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(n, count),
                )
                return results["documents"][0] if results.get("documents") else []
            except Exception as e:
                print(f"[VectorMemory] ⚠️ recall() failed: {e}")
                return []
        elif self._fallback:
            return self._fallback.recall(query, n)
        return []

    @property
    def available(self) -> bool:
        return self._available
