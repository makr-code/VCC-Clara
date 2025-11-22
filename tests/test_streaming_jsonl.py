"""
Test Streaming JSONL Retrieval

Tests for the streaming functionality without requiring UDS3 to be installed.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
import json
import tempfile


def test_imports():
    """Test that streaming modules can be imported"""
    from shared.database.dataset_search import (
        DatasetSearchAPI,
        DatasetSearchQuery,
        DatasetDocument,
        UDS3_AVAILABLE
    )
    
    assert DatasetSearchAPI is not None
    assert DatasetSearchQuery is not None
    assert DatasetDocument is not None
    print(f"✅ Imports successful (UDS3 Available: {UDS3_AVAILABLE})")


def test_dataset_search_query_creation():
    """Test DatasetSearchQuery creation"""
    from shared.database.dataset_search import DatasetSearchQuery
    
    query = DatasetSearchQuery(
        query_text="test query",
        top_k=100,
        filters={"domain": "test"},
        min_quality_score=0.5,
        search_types=["vector", "graph"],
        weights={"vector": 0.6, "graph": 0.4}
    )
    
    assert query.query_text == "test query"
    assert query.top_k == 100
    assert query.filters == {"domain": "test"}
    assert query.min_quality_score == 0.5
    print("✅ DatasetSearchQuery creation successful")


def test_dataset_document_format():
    """Test DatasetDocument to_training_format"""
    from shared.database.dataset_search import DatasetDocument
    
    doc = DatasetDocument(
        document_id="test-123",
        content="Test content",
        metadata={"domain": "test", "title": "Test Document"},
        score=0.85,
        quality_score=0.75
    )
    
    training_format = doc.to_training_format()
    
    assert training_format["text"] == "Test content"
    assert training_format["document_id"] == "test-123"
    assert training_format["source"] == "uds3_search"
    assert training_format["quality_score"] == 0.75
    assert training_format["relevance_score"] == 0.85
    assert training_format["metadata"]["domain"] == "test"
    print("✅ DatasetDocument.to_training_format() successful")


def test_api_has_streaming_methods():
    """Test that DatasetSearchAPI has streaming methods"""
    from shared.database.dataset_search import DatasetSearchAPI
    
    api = DatasetSearchAPI()
    
    # Check for streaming methods
    assert hasattr(api, 'stream_datasets'), "stream_datasets method missing"
    assert hasattr(api, 'stream_to_jsonl'), "stream_to_jsonl method missing"
    
    # Check for backward compatibility
    assert hasattr(api, 'search_datasets'), "search_datasets method missing"
    assert hasattr(api, 'export_to_jsonl'), "export_to_jsonl method missing"
    
    print("✅ All streaming methods available:")
    print("   - stream_datasets (NEW)")
    print("   - stream_to_jsonl (NEW)")
    print("   - search_datasets (existing)")
    print("   - export_to_jsonl (existing)")


def test_export_to_jsonl_batch_mode():
    """Test batch export to JSONL (without UDS3)"""
    from shared.database.dataset_search import DatasetSearchAPI, DatasetDocument
    
    api = DatasetSearchAPI()
    
    # Create test documents
    documents = [
        DatasetDocument(
            document_id=f"test-{i}",
            content=f"Test content {i}",
            metadata={"domain": "test", "index": i},
            score=0.8,
            quality_score=0.7
        )
        for i in range(5)
    ]
    
    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = f.name
    
    try:
        success = api.export_to_jsonl(documents, temp_path)
        assert success, "Export failed"
        
        # Verify file content
        with open(temp_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}"
        
        # Verify first line format
        first_doc = json.loads(lines[0])
        assert first_doc["text"] == "Test content 0"
        assert first_doc["document_id"] == "test-0"
        assert first_doc["source"] == "uds3_search"
        
        print(f"✅ Batch export successful: {len(lines)} documents")
    
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def test_config_streaming_options():
    """Test that streaming config options are available"""
    from config import config
    
    assert hasattr(config, 'streaming_enabled'), "streaming_enabled config missing"
    assert hasattr(config, 'streaming_batch_size'), "streaming_batch_size config missing"
    
    # Check default values
    print(f"✅ Streaming config available:")
    print(f"   - streaming_enabled: {config.streaming_enabled}")
    print(f"   - streaming_batch_size: {config.streaming_batch_size}")


def test_cli_script_exists():
    """Test that CLI script exists and is executable"""
    script_path = Path("scripts/clara_stream_training_data.py")
    
    assert script_path.exists(), "CLI script not found"
    assert script_path.stat().st_size > 0, "CLI script is empty"
    
    # Check shebang
    with open(script_path, 'r') as f:
        first_line = f.readline()
    
    assert first_line.startswith("#!/usr/bin/env python"), "Missing Python shebang"
    
    print(f"✅ CLI script exists: {script_path}")
    print(f"   Size: {script_path.stat().st_size} bytes")


def test_documentation_exists():
    """Test that documentation was created"""
    doc_path = Path("docs/STREAMING_JSONL_RETRIEVAL.md")
    
    assert doc_path.exists(), "Documentation not found"
    assert doc_path.stat().st_size > 5000, "Documentation too small"
    
    # Check for key sections
    with open(doc_path, 'r') as f:
        content = f.read()
    
    assert "Streaming JSONL Retrieval" in content
    assert "stream_datasets" in content
    assert "stream_to_jsonl" in content
    assert "API Reference" in content
    
    print(f"✅ Documentation exists: {doc_path}")
    print(f"   Size: {doc_path.stat().st_size} bytes")


if __name__ == "__main__":
    """Run all tests"""
    print("=" * 60)
    print("Testing Streaming JSONL Implementation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_dataset_search_query_creation,
        test_dataset_document_format,
        test_api_has_streaming_methods,
        test_export_to_jsonl_batch_mode,
        test_config_streaming_options,
        test_cli_script_exists,
        test_documentation_exists,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n▶ Running: {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        exit(1)
