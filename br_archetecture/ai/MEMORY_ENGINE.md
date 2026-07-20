# 🧠 BR JARVIS — Multi-Tier Advanced Memory Engine (`memory/`)

## Overview
BR JARVIS implements a unified multi-tier memory system capable of handling transient active state, long-term semantic knowledge, and high-throughput caching.

---

## 🏗️ Memory Layers

1. **Working Memory (`memory/working.py`)**: Stores active conversation history and current task state (token limit: 100,000).
2. **TTL Cache Layer (`memory/cache.py`)**: High-performance in-memory cache utilizing fast non-cryptographic FNV-1a frame hashing (`native_bridge.py`) and automatic TTL decay.
3. **Memory Archiver (`memory/archiver.py`)**: Consolidates older session interactions and archives stale entries to `workspace/logs/memory_archive.jsonl`.
4. **Vector Store (`memory/vector_store.py`)**: Local ChromaDB embedding store for RAG document retrieval.
5. **Unified Memory Coordinator (`memory/unified_memory.py`)**: Master coordinator providing unified access across all memory tiers.
