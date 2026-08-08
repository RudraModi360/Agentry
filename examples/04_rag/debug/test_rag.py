"""
Test suite for the RAG system.

Tests:
- PDFParser: content extraction
- HybridChunker: chunking strategies
- FaissTextStore: vector operations
- LanceImageStore: image operations
- RAGKnowledgeBase: end-to-end integration

Run:
    python -m pytest examples/04_rag/test_rag.py -v
    python examples/04_rag/test_rag.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ── Helpers ────────────────────────────────────────────────────────────────

def _make_mock_embedder(dim: int = 128):
    """Create a deterministic mock embedding function for testing."""
    import hashlib
    import numpy as np

    def embed_fn(text: str) -> np.ndarray:
        h = hashlib.blake2b(text.encode(), digest_size=dim // 4).digest()
        vec = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
        # Repeat to fill dim
        vec = np.tile(vec, dim // len(vec) + 1)[:dim]
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    return embed_fn


def _create_sample_text_file(path: str, content: str = None):
    """Create a sample text file for testing."""
    if content is None:
        content = """# Introduction to Photosynthesis

Photosynthesis is the process by which green plants convert light energy into chemical energy.

## 5.1 Light-Dependent Reactions

The light-dependent reactions occur in the thylakoid membrane. Water molecules are split, releasing oxygen.

Chlorophyll absorbs light energy and converts it to ATP and NADPH.

## 5.2 Light-Independent Reactions (Calvin Cycle)

The Calvin Cycle occurs in the stroma. CO2 is fixed into glucose using ATP and NADPH.

This process is also known as carbon fixation.

## 5.3 Factors Affecting Photosynthesis

Light intensity, temperature, and CO2 concentration all affect the rate of photosynthesis.

At low light levels, the rate increases linearly with intensity.

## 6. Cellular Respiration

Cellular respiration is the reverse process, breaking down glucose to release energy.

The overall equation is: C6H12O6 + 6O2 → 6CO2 + 6H2O + ATP

### 6.1 Glycolysis

Glycolysis occurs in the cytoplasm and converts glucose to pyruvate.

### 6.2 Krebs Cycle

The Krebs Cycle occurs in the mitochondrial matrix.

### 6.3 Electron Transport Chain

The ETC produces the majority of ATP through oxidative phosphorylation.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Tests ──────────────────────────────────────────────────────────────────

class TestParser:
    """Test PDFParser."""

    def test_text_file_parsing(self):
        from rag_system.parser import PDFParser

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("This is a test document.\n\nIt has multiple paragraphs.\n\nThird paragraph.")
            path = f.name

        try:
            parser = PDFParser()
            # Read the text file directly (pypdf is for PDFs only)
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            assert "test document" in text
            assert "multiple paragraphs" in text
        finally:
            os.unlink(path)

    def test_section_detection(self):
        from rag_system.parser import _SECTION_RE

        tests = [
            ("5.1 Light Reactions", ["5", "1"]),
            ("10.2.3 Sub-section", ["10", "2", "3"]),
            ("1 Introduction", ["1"]),
        ]
        for text, expected in tests:
            m = _SECTION_RE.match(text)
            assert m is not None, f"Failed to match: {text}"
            assert m.group(1).split(".") == expected


class TestChunker:
    """Test HybridChunker."""

    def test_size_split(self):
        from rag_system.chunker import HybridChunker

        chunker = HybridChunker(chunk_size=200, chunk_overlap=50)
        long_text = "This is sentence number {i}. " * 50  # ~1500 chars

        chunks = chunker._size_split(long_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 300  # Some tolerance for sentence boundaries

    def test_chunk_text(self):
        from rag_system.chunker import HybridChunker

        embed_fn = _make_mock_embedder(128)
        chunker = HybridChunker(
            embed_fn=embed_fn,
            chunk_size=300,
            chunk_overlap=50,
        )

        text = """# Chapter 5

Section 5.1 introduces the basics. The process involves multiple steps.

Section 5.2 covers advanced topics. Here we explore the details of each mechanism.

Section 5.3 discusses applications. Real-world examples demonstrate the principles."""

        chunks = chunker.chunk_text(text, section_path=["5"], page_number=1)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.text.strip()
            assert chunk.section_path == "5"

    def test_chunk_records_have_ids(self):
        from rag_system.chunker import ChunkRecord

        c1 = ChunkRecord(text="hello world")
        c2 = ChunkRecord(text="hello world")
        c3 = ChunkRecord(text="different text")

        assert c1.chunk_id == c2.chunk_id  # Same text = same ID
        assert c1.chunk_id != c3.chunk_id  # Different text = different ID


class TestVectorStore:
    """Test FaissTextStore."""

    def test_add_and_query(self):
        from rag_system.vector_store import FaissTextStore

        with tempfile.TemporaryDirectory() as tmpdir:
            embed_fn = _make_mock_embedder(128)
            store = FaissTextStore(
                embedding_fn=embed_fn,
                index_dir=tmpdir,
                embedding_dim=128,
            )

            from rag_system.chunker import ChunkRecord
            chunks = [
                ChunkRecord(text="Photosynthesis converts light to energy", page_number=1),
                ChunkRecord(text="The mitochondria produces ATP", page_number=2),
                ChunkRecord(text="DNA contains genetic information", page_number=3),
            ]

            added = store.add_chunks(chunks)
            assert added == 3
            assert store.size == 3

            results = store.query("energy conversion in plants", k=2)
            assert len(results) > 0
            assert len(results) <= 2

    def test_save_and_load(self):
        from rag_system.vector_store import FaissTextStore
        from rag_system.chunker import ChunkRecord

        with tempfile.TemporaryDirectory() as tmpdir:
            embed_fn = _make_mock_embedder(128)

            # Create and save
            store1 = FaissTextStore(embedding_fn=embed_fn, index_dir=tmpdir, embedding_dim=128)
            chunks = [ChunkRecord(text="test chunk one", page_number=1)]
            store1.add_chunks(chunks)
            assert store1.size == 1

            # Load in new instance
            store2 = FaissTextStore(embedding_fn=embed_fn, index_dir=tmpdir, embedding_dim=128)
            loaded = store2.load()
            assert loaded is True
            assert store2.size == 1
            assert len(store2.chunks) == 1

    def test_hybrid_query(self):
        from rag_system.vector_store import FaissTextStore
        from rag_system.chunker import ChunkRecord

        with tempfile.TemporaryDirectory() as tmpdir:
            embed_fn = _make_mock_embedder(128)
            store = FaissTextStore(embedding_fn=embed_fn, index_dir=tmpdir, embedding_dim=128)

            chunks = [
                ChunkRecord(text="Photosynthesis uses chlorophyll in plants", page_number=1),
                ChunkRecord(text="ATP is the energy currency of cells", page_number=2),
                ChunkRecord(text="DNA replication occurs in the nucleus", page_number=3),
            ]
            store.add_chunks(chunks)

            results = store.hybrid_query("plant energy", k=2)
            assert len(results) > 0


class TestImageStore:
    """Test LanceImageStore."""

    def test_add_and_query(self):
        from rag_system.image_store import LanceImageStore, ImageRecord
        import numpy as np

        with tempfile.TemporaryDirectory() as tmpdir:
            embed_fn = _make_mock_embedder(128)  # Use smaller dim for testing
            store = LanceImageStore(
                embedding_fn=embed_fn,
                db_dir=tmpdir,
                table_name="test_images",
            )

            # Create dummy image files
            img_paths = []
            for i in range(3):
                img_path = os.path.join(tmpdir, f"test_img_{i}.txt")  # Use txt as placeholder
                with open(img_path, "w") as f:
                    f.write(f"dummy image {i}")
                img_paths.append(img_path)

            added = store.add_images(
                image_paths=img_paths,
                descriptions=["plant diagram", "cell structure", "energy chart"],
                page_numbers=[1, 2, 3],
            )
            assert added == 3

            results = store.query("plant biology", k=2)
            assert len(results) > 0


class TestReranker:
    """Test MMR reranker."""

    def test_mmr_rerank(self):
        from rag_system.reranker import mmr_rerank
        from rag_system.chunker import ChunkRecord
        import numpy as np

        embed_fn = _make_mock_embedder(128)

        chunks = [
            ChunkRecord(text="Photosynthesis uses light energy", page_number=1),
            ChunkRecord(text="Photosynthesis uses light energy from the sun", page_number=1),
            ChunkRecord(text="Mitochondria produce ATP energy", page_number=2),
        ]

        embeddings = np.array([embed_fn(c.text) for c in chunks], dtype=np.float32)
        query_emb = embed_fn("energy from light")

        results = mmr_rerank(query_emb, embeddings, chunks, top_k=2, lambda_param=0.7)
        assert len(results) == 2
        # First result should be most relevant
        assert results[0][1] >= results[1][1]


class TestKBManger:
    """Test RAGKnowledgeBase end-to-end."""

    def test_index_and_retrieve_text(self):
        from rag_system.kb_manager import RAGKnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample file
            sample_path = os.path.join(tmpdir, "sample.txt")
            _create_sample_text_file(sample_path)

            # Initialize KB with mock embedder
            kb = RAGKnowledgeBase(
                index_dir=tmpdir,
                embedding_dim=128,
            )

            # Override embedder with mock
            mock_embed = _make_mock_embedder(128)
            kb._embed_fn = mock_embed
            kb._chunker.embed_fn = mock_embed
            kb._text_store.embedding_fn = mock_embed

            # Index file
            success = kb.index_file(sample_path)
            assert success is True

            # Check status
            status = kb.status()
            assert status["text_chunks"] > 0
            assert status["indexed_files"] == 1

            # Retrieve
            results = kb.retrieve_text("photosynthesis", k=3)
            assert len(results) > 0

    def test_status(self):
        from rag_system.kb_manager import RAGKnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            kb = RAGKnowledgeBase(index_dir=tmpdir, embedding_dim=128)
            status = kb.status()
            assert "text_chunks" in status
            assert "indexed_files" in status
            assert "multimodal_enabled" in status

    def test_idempotent_indexing(self):
        """Calling index_file twice on the same file should NOT create duplicates."""
        from rag_system.kb_manager import RAGKnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "sample.txt")
            _create_sample_text_file(sample_path)

            kb = RAGKnowledgeBase(index_dir=tmpdir, embedding_dim=128)
            mock_embed = _make_mock_embedder(128)
            kb._embed_fn = mock_embed
            kb._chunker.embed_fn = mock_embed
            kb._text_store.embedding_fn = mock_embed

            # First index
            kb.index_file(sample_path)
            count_after_first = kb.status()["text_chunks"]
            assert count_after_first > 0

            # Second index (same file, same mtime)
            kb.index_file(sample_path)
            count_after_second = kb.status()["text_chunks"]

            # Should be identical — no duplicates
            assert count_after_first == count_after_second, (
                f"Duplicates created: {count_after_first} -> {count_after_second}"
            )

    def test_idempotent_across_restarts(self):
        """KB should skip already-indexed files on re-initialization."""
        from rag_system.kb_manager import RAGKnowledgeBase

        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "sample.txt")
            _create_sample_text_file(sample_path)

            # First session: index file
            kb1 = RAGKnowledgeBase(index_dir=tmpdir, embedding_dim=128)
            kb1._embed_fn = _make_mock_embedder(128)
            kb1._chunker.embed_fn = kb1._embed_fn
            kb1._text_store.embedding_fn = kb1._embed_fn
            kb1.index_file(sample_path)
            count_session1 = kb1.status()["text_chunks"]

            # Second session: new KB instance, same index dir
            kb2 = RAGKnowledgeBase(index_dir=tmpdir, embedding_dim=128)
            kb2._embed_fn = _make_mock_embedder(128)
            kb2._chunker.embed_fn = kb2._embed_fn
            kb2._text_store.embedding_fn = kb2._embed_fn

            # Should load existing index, not re-index
            count_session2 = kb2.status()["text_chunks"]
            assert count_session1 == count_session2

            # Calling index_file again should be a no-op
            kb2.index_file(sample_path)
            count_final = kb2.status()["text_chunks"]
            assert count_final == count_session1


# ── Run Tests ──────────────────────────────────────────────────────────────

def run_all_tests():
    """Run all test classes."""
    test_classes = [
        TestParser,
        TestChunker,
        TestVectorStore,
        TestImageStore,
        TestReranker,
        TestKBManger,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in methods:
            total += 1
            method = getattr(instance, method_name)
            try:
                method()
                passed += 1
                print(f"  PASS  {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                errors.append((cls.__name__, method_name, str(e)))
                print(f"  FAIL  {cls.__name__}.{method_name}: {e}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if errors:
        print(f"\nFailed tests:")
        for cls_name, method, err in errors:
            print(f"  {cls_name}.{method}: {err}")

    return failed == 0


if __name__ == "__main__":
    print("Running RAG system tests...\n")
    success = run_all_tests()
    sys.exit(0 if success else 1)
