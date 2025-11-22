# LoRA Adapter Lifecycle Automation

**Date:** 2025-11-22  
**Version:** 1.0.0  
**Status:** ✅ **PRODUCTION READY**

---

## 📋 Overview

Complete automation system for LoRA adapter lifecycle management, integrating:

1. **Adapter Versioning** - Semantic versioning with metadata tracking
2. **Golden Datasets** - Benchmark datasets for quality assurance
3. **LLM-as-Judge** - Automated evaluation using LLM
4. **Review Workflow** - Automated approval based on quality scores
5. **Integration** - Seamless integration with streaming data retrieval

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Automated Lifecycle Pipeline                   │
└──────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
   ┌─────────────────┐  ┌─────────────┐  ┌──────────────┐
   │  Stream Data    │  │ Train Adapter│  │  Evaluate    │
   │  (UDS3/Themis)  │  │  (LoRA/QLoRA)│  │ (LLM Judge)  │
   └─────────────────┘  └─────────────┘  └──────────────┘
                ▼              ▼              ▼
   ┌─────────────────────────────────────────────────────┐
   │           Adapter Registry (Versioning)              │
   ├──────────────────────────────────────────────────────┤
   │  • Semantic Versioning (v1.0.0, v1.1.0, v1.2.0)     │
   │  • Metadata Tracking (metrics, status, checksums)    │
   │  • Version Comparison & Diff                         │
   │  • Approval Workflow (pending → approved/rejected)   │
   └─────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
   ┌─────────────────┐  ┌─────────────┐  ┌──────────────┐
   │ Golden Datasets │  │ LLM Judge   │  │  Auto-Approve│
   │  (Benchmarks)   │  │ (Evaluation)│  │  (if >= 85)  │
   └─────────────────┘  └─────────────┘  └──────────────┘
```

---

## 📦 Components

### 1. Adapter Registry (`shared/adapters/registry.py`)

**Features:**
- Semantic versioning (major.minor.patch)
- Adapter metadata tracking
- Version comparison and diff
- Approval workflow management
- Checksum validation

**Data Model:**
```python
AdapterVersion:
  - adapter_id: "verwaltungsrecht-lora-v1.0.0"
  - version: "1.0.0"
  - domain: "verwaltungsrecht"
  - method: LoRA/QLoRA/DoRA
  - rank: 16
  - base_model_hash: "abc123..."
  - adapter_checksum: "def456..."
  - metrics: {
      "llm_judge_score": 87.5,
      "pass_rate": 92.3,
      "golden_dataset_accuracy": 0.89
    }
  - status: pending_review/approved/rejected
```

**Usage:**
```python
from shared.adapters import get_adapter_registry, AdapterMethod

registry = get_adapter_registry()

# Register new adapter
adapter = registry.register_adapter(
    domain="verwaltungsrecht",
    method=AdapterMethod.LORA,
    adapter_path="models/adapters/verwaltungsrecht/lora-r16-v1",
    base_model="leo-base",
    rank=16
)

# Auto-versioning: v1.0.0 → v1.0.1 → v1.1.0
# Update metrics
registry.update_metrics(adapter.adapter_id, {
    "llm_judge_score": 87.5,
    "pass_rate": 92.3
})

# Approve/reject
registry.approve_adapter(adapter.adapter_id, approved_by="reviewer@company.com")
```

### 2. Golden Dataset Manager (`shared/adapters/golden_dataset.py`)

**Features:**
- Golden sample collection
- Expected output tracking
- Difficulty classification
- Version control for benchmarks

**Data Model:**
```python
GoldenSample:
  - sample_id: "verwalt-001"
  - prompt: "Wie beantrage ich...?"
  - expected_output: "Gemäß §123..."
  - expected_score: 0.95
  - difficulty: "medium"
  - criteria: {"accuracy": "Must cite §123"}

GoldenDataset:
  - dataset_id: "verwaltungsrecht-golden-v1"
  - domain: "verwaltungsrecht"
  - samples: [GoldenSample, ...]
  - total_samples: 50
```

**Usage:**
```python
from shared.adapters import get_golden_dataset_manager

manager = get_golden_dataset_manager()

# Create golden dataset
dataset = manager.create_dataset(
    dataset_id="verwaltungsrecht-golden-v1",
    domain="verwaltungsrecht",
    description="Golden dataset for Verwaltungsrecht",
    version="1.0.0"
)

# Add samples
manager.add_sample(
    dataset_id="verwaltungsrecht-golden-v1",
    prompt="Wie beantrage ich eine Baugenehmigung?",
    expected_output="Gemäß §123 BauO...",
    domain="verwaltungsrecht",
    difficulty="medium",
    criteria={"accuracy": "Must cite §123 BauO"}
)

# Export for evaluation
manager.export_for_evaluation(
    dataset_id="verwaltungsrecht-golden-v1",
    output_path="data/golden_datasets/verwaltungsrecht_v1.jsonl",
    format="jsonl"
)
```

### 3. LLM-as-Judge (`shared/adapters/llm_judge.py`)

**Features:**
- Automated quality evaluation
- Multi-criteria scoring
- Comparison with expected outputs
- Performance regression detection

**Evaluation Criteria:**
- **Accuracy** (2.0x weight): Factual correctness
- **Relevance** (1.5x weight): Relevance to prompt
- **Style** (1.0x weight): Tone and formality
- **Completeness** (1.5x weight): Coverage of required points
- **Coherence** (1.0x weight): Logical flow

**Usage:**
```python
from shared.adapters import get_evaluation_manager

eval_mgr = get_evaluation_manager()

# Evaluate adapter
async def adapter_inference(prompt, context=None):
    # Your inference code here
    return model.generate(prompt)

results_path = await eval_mgr.evaluate_adapter(
    adapter_id="verwaltungsrecht-lora-v1.0.0",
    golden_dataset_id="verwaltungsrecht-golden-v1",
    adapter_inference_fn=adapter_inference
)

# Results include:
# - Overall score (0-100)
# - Pass rate
# - Per-criterion scores
# - Detailed reasoning
```

### 4. Automated Pipeline (`scripts/clara_adapter_lifecycle.py`)

**Complete automation pipeline:**

1. ✅ **Stream training data** from UDS3/Themis
2. ✅ **Train LoRA adapter** with custom configuration
3. ✅ **Register version** in adapter registry
4. ✅ **Evaluate with LLM judge** on golden dataset
5. ✅ **Auto-approve** if score >= threshold (default: 85)

**Usage:**
```bash
# Basic pipeline
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Photovoltaik Baurecht" \
    --golden-dataset verwaltungsrecht-golden-v1

# Advanced configuration
python scripts/clara_adapter_lifecycle.py \
    --domain steuerrecht \
    --query "Einkommensteuer" \
    --golden-dataset steuerrecht-golden-v1 \
    --method qlora \
    --rank 32 \
    --auto-approve-threshold 90
```

---

## 🚀 Quick Start

### 1. Create Golden Dataset

```python
from shared.adapters import get_golden_dataset_manager

manager = get_golden_dataset_manager()

# Create dataset
dataset = manager.create_dataset(
    dataset_id="my-domain-golden-v1",
    domain="my-domain",
    description="Golden dataset for my domain",
    version="1.0.0"
)

# Add 10-50 high-quality samples
for i in range(10):
    manager.add_sample(
        dataset_id="my-domain-golden-v1",
        prompt=f"Example prompt {i}",
        expected_output=f"Expected output {i}",
        domain="my-domain"
    )
```

### 2. Run Automated Pipeline

```bash
python scripts/clara_adapter_lifecycle.py \
    --domain my-domain \
    --query "training data query" \
    --golden-dataset my-domain-golden-v1
```

### 3. Check Results

```python
from shared.adapters import get_adapter_registry

registry = get_adapter_registry()

# List all adapters
adapters = registry.list_adapters(domain="my-domain")

for adapter in adapters:
    print(f"ID: {adapter.adapter_id}")
    print(f"Version: {adapter.version}")
    print(f"Status: {adapter.status.value}")
    print(f"Score: {adapter.metrics.get('llm_judge_score', 'N/A')}")
    print(f"Approved: {adapter.status == AdapterStatus.APPROVED}")
    print()
```

---

## 📊 Example Workflow

### Scenario: Create and evaluate Verwaltungsrecht adapter

**Step 1: Create Golden Dataset**
```bash
# Create dataset with 20 high-quality samples
python -c "
from shared.adapters import get_golden_dataset_manager
manager = get_golden_dataset_manager()
dataset = manager.create_dataset(
    dataset_id='verwaltungsrecht-golden-v1',
    domain='verwaltungsrecht',
    description='Golden dataset for Verwaltungsrecht evaluation',
    version='1.0.0'
)
print(f'Created: {dataset.dataset_id}')
"
```

**Step 2: Add Samples (example)**
```python
manager.add_sample(
    dataset_id="verwaltungsrecht-golden-v1",
    prompt="Wie beantrage ich eine Baugenehmigung für eine Photovoltaikanlage?",
    expected_output="Gemäß §§ 123-125 BauO müssen Sie...",
    domain="verwaltungsrecht",
    difficulty="medium",
    criteria={
        "accuracy": "Must cite relevant BauO paragraphs",
        "completeness": "Must mention all required documents"
    }
)
```

**Step 3: Run Automated Pipeline**
```bash
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Verwaltungsrecht Photovoltaik Baurecht" \
    --golden-dataset verwaltungsrecht-golden-v1 \
    --method lora \
    --rank 16 \
    --auto-approve-threshold 85
```

**Pipeline Output:**
```
======================================================================
🚀 Starting LoRA Adapter Lifecycle Pipeline
======================================================================
Domain: verwaltungsrecht
Method: lora
Query: Verwaltungsrecht Photovoltaik Baurecht
Golden Dataset: verwaltungsrecht-golden-v1
======================================================================

📥 Step 1/5: Streaming training data from UDS3/Themis...
✅ Streamed 1247 documents to data/training_datasets/verwaltungsrecht_auto_Verwaltungsrecht_Photovoltaik_Baurecht.jsonl

🔧 Step 2/5: Training lora adapter...
✅ Training complete: models/adapters/verwaltungsrecht/lora-r16-auto

📝 Step 3/5: Registering adapter version...
✅ Registered: verwaltungsrecht-lora-v1.0.0

🧑‍⚖️ Step 4/5: Evaluating with LLM judge...
📊 Evaluation Results:
   Overall Score: 87.5/100
   Pass Rate: 92.3%
   Samples: 18/20

✅ Step 5/5: Review and approval...
✅ AUTO-APPROVED: verwaltungsrecht-lora-v1.0.0
   Score: 87.5/100 (threshold: 85)

======================================================================
🎉 Pipeline Complete!
======================================================================
Adapter ID: verwaltungsrecht-lora-v1.0.0
Version: 1.0.0
Status: approved
Score: 87.5/100
Path: models/adapters/verwaltungsrecht/lora-r16-auto
Evaluation: data/evaluation_results/verwaltungsrecht-lora-v1.0.0_20251122_140530.json
======================================================================
```

---

## 📈 Versioning Strategy

### Semantic Versioning (SemVer)

**Format:** `major.minor.patch`

- **Major** (1.0.0 → 2.0.0): Breaking changes, new base model
- **Minor** (1.0.0 → 1.1.0): New features, significant improvements
- **Patch** (1.0.0 → 1.0.1): Bug fixes, small improvements

**Auto-Increment:**
```python
# Latest version: verwaltungsrecht-lora-v1.0.5

# Register new version (auto-increments to v1.0.6)
adapter = registry.register_adapter(
    domain="verwaltungsrecht",
    method=AdapterMethod.LORA,
    adapter_path="...",
    # version is auto-calculated
)
```

**Manual Version:**
```python
# Force specific version
adapter = registry.register_adapter(
    domain="verwaltungsrecht",
    method=AdapterMethod.LORA,
    adapter_path="...",
    version="2.0.0"  # Major version bump
)
```

---

## 🎯 Evaluation Criteria

### Default LLM-as-Judge Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Accuracy** | 2.0x | Factual correctness, citations |
| **Relevance** | 1.5x | Relevance to prompt/context |
| **Style** | 1.0x | Tone, formality, language |
| **Completeness** | 1.5x | Coverage of required points |
| **Coherence** | 1.0x | Logical flow, structure |

**Scoring Formula:**
```
overall_score = (
    accuracy * 2.0 +
    relevance * 1.5 +
    style * 1.0 +
    completeness * 1.5 +
    coherence * 1.0
) / 7.0 * 10  // Scale to 0-100
```

**Pass Threshold:** 70/100 (configurable)

---

## 📝 Registry Structure

### File Locations

```
metadata/
  adapter_registry.json       # Central registry

data/
  golden_datasets/
    verwaltungsrecht-golden-v1.json
    steuerrecht-golden-v1.json
  evaluation_results/
    verwaltungsrecht-lora-v1.0.0_20251122_140530.json
    verwaltungsrecht-lora-v1.0.1_20251123_091205.json

models/
  adapters/
    verwaltungsrecht/
      lora-r16-v1.0.0/
      lora-r16-v1.0.1/
    steuerrecht/
      qlora-r32-v1.0.0/
```

### Registry Format

```json
{
  "version": "1.0.0",
  "last_updated": "2025-11-22T14:05:30Z",
  "families": [
    {
      "family_id": "verwaltungsrecht-lora",
      "domain": "verwaltungsrecht",
      "method": "lora",
      "versions": [
        {
          "adapter_id": "verwaltungsrecht-lora-v1.0.1",
          "version": "1.0.1",
          "rank": 16,
          "base_model": "leo-base",
          "base_model_hash": "abc123...",
          "adapter_checksum": "def456...",
          "metrics": {
            "llm_judge_score": 87.5,
            "pass_rate": 92.3,
            "golden_dataset_accuracy": 0.89
          },
          "status": "approved",
          "approved_by": "automated-pipeline",
          "approved_at": "2025-11-22T14:10:00Z"
        }
      ]
    }
  ]
}
```

---

## 🔄 Integration with Streaming

### Complete Data Flow

```
UDS3/Themis Database
        ↓
  Stream JSONL (clara_stream_training_data.py)
        ↓
  Training Dataset (data/training_datasets/*.jsonl)
        ↓
  Train Adapter (clara_train_adapter.py / Training Backend)
        ↓
  LoRA Adapter (models/adapters/*/lora-r*/)
        ↓
  Register Version (AdapterRegistry)
        ↓
  Evaluate with LLM Judge (on Golden Dataset)
        ↓
  Auto-Approve (if score >= 85)
        ↓
  Production Deployment
```

**Fully Automated:**
```bash
# Single command for complete lifecycle
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Photovoltaik Baurecht" \
    --golden-dataset verwaltungsrecht-golden-v1
```

---

## 🎓 Best Practices

### 1. Golden Dataset Quality

- **Size:** 20-100 high-quality samples per domain
- **Diversity:** Cover common use cases and edge cases
- **Difficulty:** Mix of easy/medium/hard samples
- **Updates:** Version golden datasets when requirements change

### 2. Evaluation Thresholds

- **Production:** 85-90 for auto-approval
- **Testing:** 70-80 for experimental adapters
- **Critical:** 95+ for safety-critical domains

### 3. Version Management

- **Patch:** Bug fixes, minor improvements
- **Minor:** Feature additions, quality improvements
- **Major:** New base model, breaking changes

### 4. Review Workflow

- **Auto-approve:** Score >= 85
- **Manual review:** 70-84
- **Reject:** < 70

---

## 📚 API Reference

### AdapterRegistry

```python
registry = get_adapter_registry()

# Register adapter
adapter = registry.register_adapter(domain, method, adapter_path, ...)

# Get adapter
adapter = registry.get_adapter(adapter_id)

# List adapters
adapters = registry.list_adapters(domain="verwaltungsrecht", status=AdapterStatus.APPROVED)

# Update metrics
registry.update_metrics(adapter_id, {"score": 87.5})

# Approve/reject
registry.approve_adapter(adapter_id, approved_by="reviewer")
registry.reject_adapter(adapter_id, reason="Low quality")

# Statistics
stats = registry.get_statistics()
```

### GoldenDatasetManager

```python
manager = get_golden_dataset_manager()

# Create dataset
dataset = manager.create_dataset(dataset_id, domain, description, version)

# Add sample
sample = manager.add_sample(dataset_id, prompt, expected_output, ...)

# Get dataset
dataset = manager.get_dataset(dataset_id)

# List datasets
datasets = manager.list_datasets(domain="verwaltungsrecht")

# Export
manager.export_for_evaluation(dataset_id, output_path, format="jsonl")
```

### AdapterEvaluationManager

```python
eval_mgr = get_evaluation_manager()

# Evaluate adapter
results_path = await eval_mgr.evaluate_adapter(
    adapter_id, golden_dataset_id, adapter_inference_fn
)

# Get history
history = eval_mgr.get_evaluation_history(adapter_id)
```

---

## 🐛 Troubleshooting

### Issue: Adapter not auto-approved

**Cause:** Score below threshold (default: 85)

**Solution:**
```bash
# Check score
python -c "
from shared.adapters import get_adapter_registry
registry = get_adapter_registry()
adapter = registry.get_adapter('verwaltungsrecht-lora-v1.0.0')
print(f'Score: {adapter.metrics.get(\"llm_judge_score\", \"N/A\")}')
"

# Lower threshold if appropriate
python scripts/clara_adapter_lifecycle.py \
    --auto-approve-threshold 80  # Lower threshold
```

### Issue: Golden dataset not found

**Cause:** Dataset ID doesn't exist

**Solution:**
```bash
# List available datasets
python -c "
from shared.adapters import get_golden_dataset_manager
manager = get_golden_dataset_manager()
datasets = manager.list_datasets()
for d in datasets:
    print(f'ID: {d.dataset_id}, Domain: {d.domain}')
"
```

---

## 📋 Summary

**Status:** ✅ **PRODUCTION READY**

**Components Implemented:**
- ✅ Adapter versioning system (semantic versioning)
- ✅ Golden dataset management
- ✅ LLM-as-judge evaluation
- ✅ Automated approval workflow
- ✅ Complete lifecycle pipeline

**Key Features:**
- **Automatic versioning** with SemVer
- **Quality assurance** via LLM judge
- **Benchmark datasets** for validation
- **Auto-approval** based on scores
- **Full integration** with streaming retrieval

**Ready for:** Production deployment with full automation support!

---

**Last Updated:** 2025-11-22  
**Maintainer:** Clara Development Team
