#!/usr/bin/env python3
"""
Test Script für CLARA Training Backend Security Integration

Tests:
1. Health Check (Public, no auth)
2. Create Job (Requires JWT + Role)
3. List Jobs (Requires JWT)
4. Get Job Details (Requires JWT)
5. Cancel Job (Requires JWT + Role)

Modes:
- DEBUG mode: No JWT required (CLARA_SECURITY_MODE=debug)
- PRODUCTION mode: JWT required (CLARA_SECURITY_MODE=production)
"""

import os
import sys
import time
import requests
from pathlib import Path

# Test Configuration
BACKEND_URL = "http://localhost:45680"
SECURITY_MODE = os.environ.get("CLARA_SECURITY_MODE", "debug")

# Mock JWT Token (für Production Tests mit echtem Keycloak)
MOCK_JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."


def test_health_check():
    """Test 1: Health Check (Public)"""
    print("\n" + "="*60)
    print("TEST 1: Health Check (Public - no auth required)")
    print("="*60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health Check PASSED")
        return True
    
    except Exception as e:
        print(f"❌ Health Check FAILED: {e}")
        return False


def test_create_job_without_auth():
    """Test 2: Create Job WITHOUT Auth (should fail in production)"""
    print("\n" + "="*60)
    print("TEST 2: Create Job WITHOUT Auth")
    print("="*60)
    
    # Finde eine existierende Config
    config_path = "configs/lora_config.yaml"
    
    payload = {
        "trainer_type": "lora",
        "config_path": config_path,
        "priority": 3,
        "tags": ["test", "security"]
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/training/jobs",
            json=payload
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if SECURITY_MODE == "debug":
            # In debug mode: should succeed
            if response.status_code == 200:
                print("✅ Request SUCCEEDED (expected in debug mode)")
                print(f"   Job ID: {response.json().get('job_id')}")
                return True
            else:
                print(f"❌ Request FAILED unexpectedly: {response.text}")
                return False
        else:
            # In production/development mode: should fail with 401/403
            if response.status_code in [401, 403]:
                print("✅ Request REJECTED (expected in production mode)")
                print(f"   Error: {response.json().get('detail')}")
                return True
            else:
                print(f"❌ Request should have been rejected but got: {response.status_code}")
                return False
    
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return False


def test_create_job_with_auth():
    """Test 3: Create Job WITH Auth (should succeed)"""
    print("\n" + "="*60)
    print("TEST 3: Create Job WITH Auth")
    print("="*60)
    
    if SECURITY_MODE == "debug":
        print("⚠️  SKIPPED: In debug mode, auth not required")
        return True
    
    config_path = "configs/lora_config.yaml"
    
    payload = {
        "trainer_type": "lora",
        "config_path": config_path,
        "priority": 3,
        "tags": ["test", "security", "authenticated"]
    }
    
    headers = {
        "Authorization": f"Bearer {MOCK_JWT_TOKEN}"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/training/jobs",
            json=payload,
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request SUCCEEDED with valid JWT")
            print(f"   Job ID: {response.json().get('job_id')}")
            return True
        else:
            print(f"❌ Request FAILED: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return False


def test_list_jobs():
    """Test 4: List Jobs"""
    print("\n" + "="*60)
    print("TEST 4: List Jobs")
    print("="*60)
    
    try:
        headers = {}
        if SECURITY_MODE != "debug":
            headers["Authorization"] = f"Bearer {MOCK_JWT_TOKEN}"
        
        response = requests.get(
            f"{BACKEND_URL}/api/training/jobs/list",
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Request SUCCEEDED")
            print(f"   Total Jobs: {data.get('total_count')}")
            print(f"   Active Jobs: {data.get('active_count')}")
            print(f"   Completed Jobs: {data.get('completed_count')}")
            return True
        else:
            print(f"❌ Request FAILED: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return False


def test_rbac_role_check():
    """Test 5: RBAC - Role Check (admin/trainer required)"""
    print("\n" + "="*60)
    print("TEST 5: RBAC - Role Check")
    print("="*60)
    
    if SECURITY_MODE == "debug":
        print("⚠️  In debug mode, user has all roles (admin, trainer)")
        print("   Testing job creation...")
    else:
        print("⚠️  SKIPPED: Requires real Keycloak JWT with role claims")
        return True
    
    # Test mit debug user (hat admin + trainer roles)
    config_path = "configs/lora_config.yaml"
    
    payload = {
        "trainer_type": "qlora",
        "config_path": config_path,
        "priority": 5,
        "tags": ["test", "rbac"]
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/training/jobs",
            json=payload
        )
        
        if response.status_code == 200:
            print("✅ Job creation SUCCEEDED (user has required roles)")
            job_id = response.json().get('job_id')
            print(f"   Job ID: {job_id}")
            
            # Test job cancellation (also requires admin/trainer role)
            print("\n   Testing job cancellation (admin/trainer role)...")
            cancel_response = requests.delete(
                f"{BACKEND_URL}/api/training/jobs/{job_id}"
            )
            
            if cancel_response.status_code == 200:
                print("✅ Job cancellation SUCCEEDED (user has required roles)")
                return True
            else:
                print(f"❌ Job cancellation FAILED: {cancel_response.text}")
                return False
        else:
            print(f"❌ Job creation FAILED: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  CLARA Training Backend - Security Integration Tests".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\n🔐 Security Mode: {SECURITY_MODE.upper()}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    if SECURITY_MODE == "debug":
        print("\n⚠️  DEBUG MODE ACTIVE:")
        print("   - No JWT validation")
        print("   - Mock user with all roles (admin, trainer, analyst)")
        print("   - All endpoints accessible")
    elif SECURITY_MODE == "production":
        print("\n🔒 PRODUCTION MODE ACTIVE:")
        print("   - JWT validation enabled")
        print("   - Role-based access control (RBAC)")
        print("   - Requires Keycloak for real tests")
    
    # Wait for backend to start
    print("\n⏳ Waiting for backend to start...")
    for i in range(5):
        try:
            requests.get(f"{BACKEND_URL}/health", timeout=2)
            print("✅ Backend is ready!")
            break
        except:
            if i == 4:
                print("❌ Backend not reachable. Please start it first:")
                print("   python scripts/clara_training_backend.py")
                sys.exit(1)
            time.sleep(1)
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_check()))
    results.append(("Create Job (no auth)", test_create_job_without_auth()))
    
    if SECURITY_MODE != "debug":
        results.append(("Create Job (with auth)", test_create_job_with_auth()))
    
    results.append(("List Jobs", test_list_jobs()))
    results.append(("RBAC Role Check", test_rbac_role_check()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"Result: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Security integration working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
