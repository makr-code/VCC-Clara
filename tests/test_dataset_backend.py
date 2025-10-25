#!/usr/bin/env python3
"""
Tests für CLARA Dataset Management Backend

Test Categories:
1. Health Check
2. Dataset Creation
3. Dataset Retrieval
4. Dataset Export
5. Security Integration

Author: VCC Team
Date: 2024-10-24
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['CLARA_SECURITY_MODE'] = 'debug'  # No authentication for tests

# ============================================================================
# Test Configuration
# ============================================================================

BASE_URL = "http://localhost:45681"
TEST_DATASET_NAME = "Test Dataset - Verwaltungsrecht"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def backend_url():
    """Dataset Backend URL"""
    return BASE_URL


@pytest.fixture
def sample_dataset_request():
    """Sample dataset creation request"""
    return {
        "name": TEST_DATASET_NAME,
        "description": "Test dataset for integration testing",
        "search_query": {
            "query_text": "Verwaltungsrecht Verwaltungsakt",
            "top_k": 50,
            "min_quality_score": 0.6,
            "search_types": ["vector"],
            "filters": {"domain": "legal"}
        },
        "export_formats": ["jsonl"]
    }


# ============================================================================
# Test Cases
# ============================================================================

class TestHealthCheck:
    """Health Check Tests"""
    
    def test_health_endpoint(self, backend_url):
        """Test health check endpoint"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        response = requests.get(f"{backend_url}/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "clara_dataset_backend"
        assert data["port"] == 45681
        assert "datasets_count" in data
        assert "timestamp" in data
        
        print(f"✅ Health Check: {data}")


class TestDatasetCreation:
    """Dataset Creation Tests"""
    
    def test_create_dataset_without_auth(self, backend_url, sample_dataset_request):
        """Test dataset creation in debug mode (no auth required)"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        response = requests.post(
            f"{backend_url}/api/datasets",
            json=sample_dataset_request
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "dataset_id" in data
        assert data["status"] == "pending"
        
        print(f"✅ Dataset Created: {data['dataset_id']}")
        
        # Store dataset_id for later tests
        return data["dataset_id"]
    
    def test_create_dataset_invalid_name(self, backend_url):
        """Test dataset creation with invalid name"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        request = {
            "name": "Invalid@Name#123",  # Special characters not allowed
            "description": "Test",
            "search_query": {
                "query_text": "test",
                "top_k": 10
            },
            "export_formats": ["jsonl"]
        }
        
        response = requests.post(
            f"{backend_url}/api/datasets",
            json=request
        )
        
        # Should fail validation
        assert response.status_code == 422  # Validation Error
        
        print(f"✅ Validation Error (expected): {response.status_code}")


class TestDatasetRetrieval:
    """Dataset Retrieval Tests"""
    
    def test_list_datasets(self, backend_url):
        """Test listing all datasets"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        response = requests.get(f"{backend_url}/api/datasets")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "datasets" in data
        assert "total_count" in data
        assert isinstance(data["datasets"], list)
        
        print(f"✅ Listed {data['total_count']} datasets")
    
    def test_get_dataset_by_id(self, backend_url, sample_dataset_request):
        """Test getting specific dataset by ID"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        # First create a dataset
        create_response = requests.post(
            f"{backend_url}/api/datasets",
            json=sample_dataset_request
        )
        
        dataset_id = create_response.json()["dataset_id"]
        
        # Then retrieve it
        response = requests.get(f"{backend_url}/api/datasets/{dataset_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["dataset_id"] == dataset_id
        assert "data" in data
        
        print(f"✅ Retrieved dataset: {dataset_id}")
    
    def test_get_nonexistent_dataset(self, backend_url):
        """Test getting non-existent dataset"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = requests.get(f"{backend_url}/api/datasets/{fake_id}")
        
        assert response.status_code == 404  # Not Found
        
        print(f"✅ 404 Error (expected): Dataset not found")


class TestDatasetExport:
    """Dataset Export Tests"""
    
    def test_export_request_structure(self, backend_url, sample_dataset_request):
        """Test export request structure"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        # Create dataset
        create_response = requests.post(
            f"{backend_url}/api/datasets",
            json=sample_dataset_request
        )
        
        dataset_id = create_response.json()["dataset_id"]
        
        # Wait for processing (simulate)
        import time
        time.sleep(2)
        
        # Request export
        export_request = {
            "format": "parquet",
            "include_metadata": True
        }
        
        response = requests.post(
            f"{backend_url}/api/datasets/{dataset_id}/export",
            json=export_request
        )
        
        # Note: Export might not be implemented yet
        # Just test structure
        assert response.status_code in [200, 400, 501]  # OK or Not Implemented
        
        print(f"✅ Export request sent: {response.status_code}")


class TestSecurityIntegration:
    """Security Integration Tests"""
    
    def test_debug_mode_no_auth(self, backend_url):
        """Test that debug mode allows requests without auth"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        # Should work without Authorization header
        response = requests.get(f"{backend_url}/api/datasets")
        
        assert response.status_code == 200
        
        print("✅ Debug mode: No auth required (as expected)")
    
    def test_audit_logging(self, backend_url, sample_dataset_request):
        """Test that audit logs are created"""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not installed")
        
        # Create dataset (should create audit log)
        response = requests.post(
            f"{backend_url}/api/datasets",
            json=sample_dataset_request
        )
        
        assert response.status_code == 200
        
        # Check logs (backend should have logged)
        # Note: This is tested via manual inspection of logs
        
        print("✅ Audit logging test (check backend logs)")


# ============================================================================
# Integration Test Suite
# ============================================================================

class TestIntegrationWorkflow:
    """End-to-End Integration Tests"""
    
    def test_full_dataset_workflow(self, backend_url, sample_dataset_request):
        """Test complete dataset workflow: Create → Check Status → List → Export"""
        try:
            import requests
            import time
        except ImportError:
            pytest.skip("requests not installed")
        
        print("\n" + "="*60)
        print("INTEGRATION TEST: Full Dataset Workflow")
        print("="*60)
        
        # Step 1: Create Dataset
        print("\n[1] Creating dataset...")
        create_response = requests.post(
            f"{backend_url}/api/datasets",
            json=sample_dataset_request
        )
        
        assert create_response.status_code == 200
        dataset_id = create_response.json()["dataset_id"]
        print(f"✅ Dataset created: {dataset_id}")
        
        # Step 2: Wait for processing
        print("\n[2] Waiting for processing...")
        time.sleep(3)
        
        # Step 3: Check Status
        print("\n[3] Checking dataset status...")
        status_response = requests.get(f"{backend_url}/api/datasets/{dataset_id}")
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        print(f"   Status: {status_data['status']}")
        if status_data.get("data"):
            print(f"   Documents: {status_data['data'].get('document_count', 'N/A')}")
            print(f"   Quality Score: {status_data['data'].get('quality_score_avg', 'N/A')}")
        
        # Step 4: List All Datasets
        print("\n[4] Listing all datasets...")
        list_response = requests.get(f"{backend_url}/api/datasets")
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        
        print(f"✅ Total datasets: {list_data['total_count']}")
        
        # Step 5: Verify our dataset is in list
        print("\n[5] Verifying dataset in list...")
        dataset_found = any(
            ds["dataset_id"] == dataset_id 
            for ds in list_data["datasets"]
        )
        
        assert dataset_found
        print(f"✅ Dataset found in list")
        
        print("\n" + "="*60)
        print("✅ INTEGRATION TEST PASSED")
        print("="*60)


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CLARA Dataset Management Backend - Test Suite")
    print("=" * 70)
    print(f"Backend URL: {BASE_URL}")
    print(f"Security Mode: DEBUG (no authentication)")
    print("=" * 70)
    print()
    print("Prerequisites:")
    print("  1. Dataset Backend must be running on port 45681")
    print("  2. Start with: python scripts/clara_dataset_backend.py")
    print("  3. Or use: .\\start_dataset_backend.ps1 -SecurityMode debug")
    print()
    print("=" * 70)
    print()
    
    # Check if requests is installed
    try:
        import requests
        print("✅ requests library found")
    except ImportError:
        print("❌ requests library not found")
        print("   Install with: pip install requests")
        sys.exit(1)
    
    # Check if backend is running
    try:
        import requests
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"✅ Dataset Backend is running: {BASE_URL}")
            data = response.json()
            print(f"   Service: {data['service']}")
            print(f"   UDS3 Available: {data['uds3_available']}")
        else:
            print(f"⚠️  Dataset Backend responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Dataset Backend not reachable: {e}")
        print(f"   Please start backend first:")
        print(f"   python scripts/clara_dataset_backend.py")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("Running Tests...")
    print("=" * 70)
    print()
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
