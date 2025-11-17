# Clara AI - API Reference

**Version:** 2.0.0  
**Date:** 2025-11-17  
**Status:** ✅ **PRODUCTION READY**

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Training Backend API](#training-backend-api)
4. [Dataset Backend API](#dataset-backend-api)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

Clara AI provides two RESTful backend services:

| Service | Port | Base URL | Purpose |
|---------|------|----------|---------|
| **Training Backend** | 45680 | `http://localhost:45680` | Training job management |
| **Dataset Backend** | 45681 | `http://localhost:45681` | Dataset creation and export |

Both services:
- Use **FastAPI** framework
- Support **JSON** request/response format
- Provide **OpenAPI/Swagger** documentation at `/docs` endpoint
- Support **optional JWT authentication** (configurable)
- Return **standardized error responses**

### Service Status

**Health Check Endpoints:**
```bash
# Training Backend
curl http://localhost:45680/health

# Dataset Backend
curl http://localhost:45681/health
```

**OpenAPI Documentation:**
- Training: `http://localhost:45680/docs`
- Dataset: `http://localhost:45681/docs`

---

## Authentication

### Overview

Clara AI supports **4 security modes** (configurable via `config.security_mode`):

| Mode | Value | Authentication | Use Case |
|------|-------|----------------|----------|
| **Development** | `development` | None | Local development, testing |
| **JWT Optional** | `jwt_optional` | Optional | Flexible authentication |
| **JWT Required** | `jwt_required` | Required (401 if missing) | Production with auth |
| **Production** | `production` | Required + RBAC | Full security |

### JWT Token Format

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "email": "user@example.com",
  "roles": ["admin", "trainer"],
  "exp": 1700000000
}
```

### Using JWT Tokens

**Include in request header:**
```bash
curl -H "Authorization: Bearer <JWT_TOKEN>" \
     http://localhost:45680/api/training/jobs
```

### Role-Based Access Control (RBAC)

**Available Roles:**
- `admin` - Full access to all endpoints
- `trainer` - Training job management
- `analyst` - Dataset read access
- `viewer` - Read-only access

**Endpoint Permissions:**

| Endpoint | Admin | Trainer | Analyst | Viewer |
|----------|-------|---------|---------|--------|
| POST /training/jobs | ✅ | ✅ | ❌ | ❌ |
| GET /training/jobs | ✅ | ✅ | ✅ | ✅ |
| DELETE /training/jobs/{id} | ✅ | ✅ | ❌ | ❌ |
| POST /datasets | ✅ | ✅ | ✅ | ❌ |
| GET /datasets | ✅ | ✅ | ✅ | ✅ |
| POST /datasets/{id}/export | ✅ | ✅ | ✅ | ❌ |

---

## Training Backend API

**Base URL:** `http://localhost:45680/api/training`

### 1. Create Training Job

**POST** `/jobs`

Creates a new training job and submits it to the queue.

**🔐 Security:** JWT Optional, Roles: `admin` OR `trainer`

**Request Body:**
```json
{
  "trainer_type": "lora",
  "config_path": "/path/to/config.yaml",
  "dataset_path": "/path/to/dataset.jsonl",
  "output_dir": "/path/to/output",
  "priority": 1,
  "tags": ["experiment", "baseline"]
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trainer_type` | string | ✅ | Trainer type: `lora`, `qlora`, or `continuous` |
| `config_path` | string | ✅ | Path to training config YAML file |
| `dataset_path` | string | ❌ | Path to training dataset (JSONL format) |
| `output_dir` | string | ❌ | Output directory for model adapters |
| `priority` | integer | ❌ | Job priority (1-10, default: 1) |
| `tags` | array[string] | ❌ | Tags for job categorization |

**Response (201 Created):**
```json
{
  "success": true,
  "job_id": "job_20251117_123456_abc123",
  "status": "pending",
  "message": "Training job created successfully",
  "created_by": "user@example.com",
  "created_at": "2025-11-17T12:34:56.789Z"
}
```

**Response Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Operation success flag |
| `job_id` | string | Unique job identifier |
| `status` | string | Job status: `pending`, `queued`, `running`, `completed`, `failed`, `cancelled` |
| `message` | string | Success/error message |
| `created_by` | string | User email who created the job |
| `created_at` | string | ISO 8601 timestamp |

**cURL Example:**
```bash
curl -X POST http://localhost:45680/api/training/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "trainer_type": "lora",
    "config_path": "/data/configs/lora_config.yaml",
    "dataset_path": "/data/datasets/training_data.jsonl",
    "output_dir": "/data/models/lora_adapter",
    "priority": 5,
    "tags": ["production", "v1.0"]
  }'
```

**Python Example:**
```python
import requests

url = "http://localhost:45680/api/training/jobs"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {jwt_token}"
}
payload = {
    "trainer_type": "lora",
    "config_path": "/data/configs/lora_config.yaml",
    "dataset_path": "/data/datasets/training_data.jsonl",
    "priority": 5
}

response = requests.post(url, json=payload, headers=headers)
job = response.json()
print(f"Job created: {job['job_id']}")
```

---

### 2. Get Training Job Status

**GET** `/jobs/{job_id}`

Retrieve detailed information about a specific training job.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`, `viewer`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Unique job identifier |

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": "job_20251117_123456_abc123",
  "trainer_type": "lora",
  "status": "running",
  "config_path": "/data/configs/lora_config.yaml",
  "dataset_path": "/data/datasets/training_data.jsonl",
  "output_dir": "/data/models/lora_adapter",
  "created_at": "2025-11-17T12:34:56.789Z",
  "started_at": "2025-11-17T12:35:10.123Z",
  "completed_at": null,
  "current_epoch": 2,
  "total_epochs": 5,
  "progress_percent": 40.0,
  "adapter_path": null,
  "metrics": {
    "loss": 0.234,
    "learning_rate": 0.0001
  },
  "error_message": null,
  "priority": 5,
  "tags": ["production", "v1.0"],
  "created_by": "user@example.com"
}
```

**cURL Example:**
```bash
curl http://localhost:45680/api/training/jobs/job_20251117_123456_abc123 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Python Example:**
```python
response = requests.get(
    f"http://localhost:45680/api/training/jobs/{job_id}",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
job_status = response.json()
print(f"Job {job_status['job_id']} is {job_status['status']} ({job_status['progress_percent']}%)")
```

---

### 3. List All Training Jobs

**GET** `/jobs/list`

Retrieve all training jobs with optional filtering.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`, `viewer`

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by job status | `?status=running` |
| `limit` | integer | Maximum jobs to return (default: 100) | `?limit=50` |
| `offset` | integer | Pagination offset (default: 0) | `?offset=10` |

**Response (200 OK):**
```json
{
  "success": true,
  "total": 15,
  "jobs": [
    {
      "job_id": "job_20251117_123456_abc123",
      "trainer_type": "lora",
      "status": "running",
      "progress_percent": 40.0,
      "created_at": "2025-11-17T12:34:56.789Z",
      "created_by": "user@example.com"
    },
    {
      "job_id": "job_20251117_103020_xyz789",
      "trainer_type": "qlora",
      "status": "completed",
      "progress_percent": 100.0,
      "created_at": "2025-11-17T10:30:20.456Z",
      "created_by": "admin@example.com"
    }
  ]
}
```

**cURL Example:**
```bash
# Get all running jobs
curl "http://localhost:45680/api/training/jobs/list?status=running" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get first 10 jobs
curl "http://localhost:45680/api/training/jobs/list?limit=10" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Python Example:**
```python
# Get all completed jobs
response = requests.get(
    "http://localhost:45680/api/training/jobs/list",
    params={"status": "completed"},
    headers={"Authorization": f"Bearer {jwt_token}"}
)
jobs = response.json()
print(f"Found {jobs['total']} completed jobs")
```

---

### 4. Cancel Training Job

**DELETE** `/jobs/{job_id}`

Cancel a running or queued training job.

**🔐 Security:** JWT Optional, Roles: `admin` OR `trainer`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | Unique job identifier |

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": "job_20251117_123456_abc123",
  "status": "cancelled",
  "message": "Training job cancelled successfully"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Cannot cancel job with status: completed"
}
```

**cURL Example:**
```bash
curl -X DELETE http://localhost:45680/api/training/jobs/job_20251117_123456_abc123 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Python Example:**
```python
response = requests.delete(
    f"http://localhost:45680/api/training/jobs/{job_id}",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
result = response.json()
if result['success']:
    print(f"Job {job_id} cancelled successfully")
```

---

## Dataset Backend API

**Base URL:** `http://localhost:45681/api/datasets`

### 1. Create Dataset

**POST** `/`

Create a new dataset from a search query and export it to specified formats.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`

**Request Body:**
```json
{
  "name": "Legal Training Dataset",
  "description": "Legal documents for compliance training",
  "search_query": "compliance AND regulation",
  "export_formats": ["jsonl", "parquet"]
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Dataset name (max 100 chars) |
| `description` | string | ❌ | Dataset description (max 500 chars) |
| `search_query` | string | ✅ | Search query for document selection |
| `export_formats` | array[string] | ❌ | Export formats: `jsonl`, `parquet`, `csv`, `json` (default: `["jsonl"]`) |

**Response (201 Created):**
```json
{
  "success": true,
  "dataset_id": "ds_20251117_123456_abc123",
  "name": "Legal Training Dataset",
  "status": "pending",
  "created_at": "2025-11-17T12:34:56.789Z",
  "created_by": "user@example.com",
  "message": "Dataset creation started"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:45681/api/datasets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "name": "Legal Training Dataset",
    "description": "Legal documents for compliance training",
    "search_query": "compliance AND regulation",
    "export_formats": ["jsonl", "parquet", "csv"]
  }'
```

**Python Example:**
```python
url = "http://localhost:45681/api/datasets"
payload = {
    "name": "Legal Training Dataset",
    "description": "Legal documents for compliance training",
    "search_query": "compliance AND regulation",
    "export_formats": ["jsonl", "parquet"]
}

response = requests.post(url, json=payload, headers=headers)
dataset = response.json()
print(f"Dataset created: {dataset['dataset_id']}")
```

---

### 2. Get Dataset Status

**GET** `/{dataset_id}`

Retrieve detailed information about a specific dataset.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`, `viewer`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `dataset_id` | string | Unique dataset identifier |

**Response (200 OK):**
```json
{
  "success": true,
  "dataset_id": "ds_20251117_123456_abc123",
  "name": "Legal Training Dataset",
  "description": "Legal documents for compliance training",
  "status": "completed",
  "created_at": "2025-11-17T12:34:56.789Z",
  "created_by": "user@example.com",
  "query_text": "compliance AND regulation",
  "document_count": 1250,
  "total_tokens": 4567890,
  "quality_score_avg": 0.87,
  "export_paths": {
    "jsonl": "/data/exports/ds_20251117_123456_abc123.jsonl",
    "parquet": "/data/exports/ds_20251117_123456_abc123.parquet",
    "csv": "/data/exports/ds_20251117_123456_abc123.csv"
  },
  "metadata": {
    "processing_time_seconds": 45.2,
    "avg_document_length": 3654
  }
}
```

**cURL Example:**
```bash
curl http://localhost:45681/api/datasets/ds_20251117_123456_abc123 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Python Example:**
```python
response = requests.get(
    f"http://localhost:45681/api/datasets/{dataset_id}",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
dataset = response.json()
print(f"Dataset {dataset['name']}: {dataset['document_count']} documents, status: {dataset['status']}")
```

---

### 3. List All Datasets

**GET** `/`

Retrieve all datasets with optional filtering.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`, `viewer`

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by dataset status | `?status=completed` |
| `limit` | integer | Maximum datasets to return (default: 100) | `?limit=20` |
| `offset` | integer | Pagination offset (default: 0) | `?offset=10` |

**Response (200 OK):**
```json
{
  "success": true,
  "total": 8,
  "datasets": [
    {
      "dataset_id": "ds_20251117_123456_abc123",
      "name": "Legal Training Dataset",
      "status": "completed",
      "document_count": 1250,
      "created_at": "2025-11-17T12:34:56.789Z",
      "created_by": "user@example.com"
    },
    {
      "dataset_id": "ds_20251117_103020_xyz789",
      "name": "Financial Reports Dataset",
      "status": "processing",
      "document_count": 0,
      "created_at": "2025-11-17T10:30:20.456Z",
      "created_by": "admin@example.com"
    }
  ]
}
```

**cURL Example:**
```bash
# Get all completed datasets
curl "http://localhost:45681/api/datasets?status=completed" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get first 10 datasets
curl "http://localhost:45681/api/datasets?limit=10" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Python Example:**
```python
# Get all datasets
response = requests.get(
    "http://localhost:45681/api/datasets",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
datasets = response.json()
print(f"Total datasets: {datasets['total']}")
for ds in datasets['datasets']:
    print(f"  - {ds['name']}: {ds['status']} ({ds['document_count']} docs)")
```

---

### 4. Export Dataset

**POST** `/{dataset_id}/export`

Export an existing dataset to additional formats.

**🔐 Security:** JWT Optional, Roles: `admin`, `trainer`, `analyst`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `dataset_id` | string | Unique dataset identifier |

**Request Body:**
```json
{
  "formats": ["parquet", "csv"]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "dataset_id": "ds_20251117_123456_abc123",
  "message": "Export started",
  "formats": ["parquet", "csv"]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:45681/api/datasets/ds_20251117_123456_abc123/export \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "formats": ["parquet", "csv"]
  }'
```

**Python Example:**
```python
response = requests.post(
    f"http://localhost:45681/api/datasets/{dataset_id}/export",
    json={"formats": ["parquet", "csv"]},
    headers={"Authorization": f"Bearer {jwt_token}"}
)
result = response.json()
print(f"Export started for formats: {result['formats']}")
```

---

## Data Models

### Training Job

**Statuses:**
- `pending` - Job created, not yet queued
- `queued` - Job in queue, waiting for worker
- `running` - Job currently executing
- `completed` - Job finished successfully
- `failed` - Job failed with error
- `cancelled` - Job cancelled by user

**Trainer Types:**
- `lora` - LoRA (Low-Rank Adaptation) training
- `qlora` - QLoRA (Quantized LoRA) training
- `continuous` - Continuous learning mode

### Dataset

**Statuses:**
- `pending` - Dataset created, not yet processed
- `processing` - Dataset being processed
- `completed` - Dataset ready, exports available
- `failed` - Dataset processing failed

**Export Formats:**
- `jsonl` - JSON Lines (newline-delimited JSON)
- `parquet` - Apache Parquet (columnar format)
- `csv` - Comma-Separated Values
- `json` - Standard JSON array

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions (RBAC) |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service not initialized |

### Error Response Format

**Standard Error Response:**
```json
{
  "success": false,
  "message": "Job not found: job_20251117_999999_invalid",
  "error_code": "JOB_NOT_FOUND",
  "details": {
    "job_id": "job_20251117_999999_invalid"
  }
}
```

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "trainer_type"],
      "msg": "value is not a valid enumeration member; permitted: 'lora', 'qlora', 'continuous'",
      "type": "type_error.enum"
    }
  ]
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_TOKEN` | JWT token invalid or expired | Refresh token, re-authenticate |
| `INSUFFICIENT_PERMISSIONS` | User lacks required role | Contact admin for role assignment |
| `JOB_NOT_FOUND` | Training job doesn't exist | Verify job_id is correct |
| `DATASET_NOT_FOUND` | Dataset doesn't exist | Verify dataset_id is correct |
| `INVALID_STATUS` | Cannot perform action in current state | Check job/dataset status first |
| `VALIDATION_ERROR` | Request parameters invalid | Check request schema |
| `SERVICE_UNAVAILABLE` | Manager not initialized | Wait for service startup |

---

## Rate Limiting

**Current Status:** ✅ No rate limiting implemented

**Future Plans:**
- 100 requests/minute per user
- 1000 requests/hour per IP
- Burst allowance: 20 requests
- Rate limit headers in response

**Recommended Client Behavior:**
- Implement exponential backoff for retries
- Cache responses when possible
- Use WebSocket for real-time updates (if available)

---

## Examples

### Complete Workflow: Training Job

**1. Create Training Job:**
```python
import requests
import time

# Configuration
base_url = "http://localhost:45680/api/training"
headers = {"Authorization": f"Bearer {jwt_token}"}

# Create job
response = requests.post(
    f"{base_url}/jobs",
    json={
        "trainer_type": "lora",
        "config_path": "/data/configs/lora_config.yaml",
        "dataset_path": "/data/datasets/training_data.jsonl",
        "priority": 5
    },
    headers=headers
)
job = response.json()
job_id = job['job_id']
print(f"✅ Job created: {job_id}")
```

**2. Monitor Job Progress:**
```python
# Poll until complete
while True:
    response = requests.get(f"{base_url}/jobs/{job_id}", headers=headers)
    job = response.json()
    
    status = job['status']
    progress = job['progress_percent']
    
    print(f"📊 Status: {status}, Progress: {progress}%")
    
    if status in ['completed', 'failed', 'cancelled']:
        break
    
    time.sleep(5)  # Poll every 5 seconds

# Check final result
if job['status'] == 'completed':
    print(f"✅ Training completed!")
    print(f"📁 Adapter: {job['adapter_path']}")
    print(f"📈 Metrics: {job['metrics']}")
else:
    print(f"❌ Training failed: {job['error_message']}")
```

**3. Cancel Job (if needed):**
```python
response = requests.delete(f"{base_url}/jobs/{job_id}", headers=headers)
if response.json()['success']:
    print(f"🛑 Job cancelled: {job_id}")
```

---

### Complete Workflow: Dataset Creation

**1. Create Dataset:**
```python
import requests
import time

# Configuration
base_url = "http://localhost:45681/api/datasets"
headers = {"Authorization": f"Bearer {jwt_token}"}

# Create dataset
response = requests.post(
    base_url,
    json={
        "name": "Legal Documents",
        "description": "Compliance and regulatory documents",
        "search_query": "compliance AND regulation",
        "export_formats": ["jsonl", "parquet", "csv"]
    },
    headers=headers
)
dataset = response.json()
dataset_id = dataset['dataset_id']
print(f"✅ Dataset created: {dataset_id}")
```

**2. Monitor Dataset Processing:**
```python
# Poll until complete
while True:
    response = requests.get(f"{base_url}/{dataset_id}", headers=headers)
    dataset = response.json()
    
    status = dataset['status']
    print(f"📊 Status: {status}")
    
    if status in ['completed', 'failed']:
        break
    
    time.sleep(5)

# Check final result
if dataset['status'] == 'completed':
    print(f"✅ Dataset ready!")
    print(f"📄 Documents: {dataset['document_count']}")
    print(f"🔤 Tokens: {dataset['total_tokens']:,}")
    print(f"⭐ Quality: {dataset['quality_score_avg']:.2f}")
    print(f"📁 Exports:")
    for fmt, path in dataset['export_paths'].items():
        print(f"  - {fmt}: {path}")
else:
    print(f"❌ Dataset failed")
```

**3. Export to Additional Format:**
```python
# Export to additional format
response = requests.post(
    f"{base_url}/{dataset_id}/export",
    json={"formats": ["json"]},
    headers=headers
)
print(f"📤 Additional export started")
```

---

### Batch Operations

**Create Multiple Training Jobs:**
```python
configs = [
    {"trainer_type": "lora", "config_path": "/data/configs/lora1.yaml"},
    {"trainer_type": "qlora", "config_path": "/data/configs/qlora1.yaml"},
    {"trainer_type": "continuous", "config_path": "/data/configs/cont1.yaml"}
]

job_ids = []
for config in configs:
    response = requests.post(f"{base_url}/jobs", json=config, headers=headers)
    job_id = response.json()['job_id']
    job_ids.append(job_id)
    print(f"✅ Created: {job_id}")

print(f"📋 Total jobs created: {len(job_ids)}")
```

**List All Running Jobs:**
```python
response = requests.get(
    f"{base_url}/jobs/list",
    params={"status": "running"},
    headers=headers
)
jobs = response.json()
print(f"🏃 Running jobs: {jobs['total']}")
for job in jobs['jobs']:
    print(f"  - {job['job_id']}: {job['progress_percent']}%")
```

---

## Additional Resources

**Related Documentation:**
- [CONFIGURATION_REFERENCE.md](./CONFIGURATION_REFERENCE.md) - Configuration options
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [SECURITY_FRAMEWORK.md](./SECURITY_FRAMEWORK.md) - Security details
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions

**External Links:**
- FastAPI Documentation: https://fastapi.tiangolo.com
- OpenAPI Specification: https://spec.openapis.org/oas/latest.html
- JWT.io: https://jwt.io

---

**Last Updated:** 2025-11-17  
**Maintained By:** Clara AI Documentation Team  
**Feedback:** Please report issues or suggest improvements via GitHub Issues
