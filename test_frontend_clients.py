#!/usr/bin/env python3
"""Test Frontend API Clients"""

from frontend.shared.api.training_client import TrainingAPIClient
from frontend.shared.api.dataset_client import DatasetAPIClient

print("\n=== Testing Frontend API Clients ===\n")

# Initialize clients
training = TrainingAPIClient()
dataset = DatasetAPIClient()

print(f"Training Client: {training.base_url}")
print(f"Dataset Client: {dataset.base_url}")

# Test connections
print("\nTesting connections...\n")

try:
    t_health = training.health_check()
    print(f"✅ Training Backend: {t_health['status']}")
    print(f"   Port: {t_health['port']}")
    print(f"   Jobs: {t_health['active_jobs']}")
except Exception as e:
    print(f"❌ Training Backend Error: {e}")

try:
    d_health = dataset.health_check()
    print(f"\n✅ Dataset Backend: {d_health['status']}")
    print(f"   Port: {d_health['port']}")
    print(f"   UDS3: {d_health.get('uds3_available', False)}")
    print(f"   Datasets: {d_health['datasets_count']}")
except Exception as e:
    print(f"❌ Dataset Backend Error: {e}")

print("\n✅ Frontend API clients ready!\n")
