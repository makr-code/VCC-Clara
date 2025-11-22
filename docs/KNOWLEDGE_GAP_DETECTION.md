# Knowledge Gap Detection and Tracking

**Date:** 2025-11-22  
**Version:** 1.0.0  
**Status:** ✅ **PRODUCTION READY**

---

## 📋 Overview

Automatic detection and tracking of knowledge gaps during LoRA adapter training and evaluation. Gaps are identified when adapters fail evaluations, show low confidence, or lack coverage in specific topics.

**Key Features:**
- Automatic gap detection from evaluation failures
- Severity classification (Critical, High, Medium, Low)
- Priority scoring for addressing gaps
- Database storage with full metadata
- Integration with training pipeline
- CLI tools for gap management

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              LoRA Adapter Evaluation                      │
│         (LLM Judge on Golden Dataset)                     │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  Knowledge Gap Detector    │
        │  (Automatic Detection)     │
        └────────────┬───────────────┘
                     │
         ┌───────────┴────────────┐
         ▼                        ▼
┌────────────────┐      ┌─────────────────────┐
│ Knowledge Gap  │      │   Priority Scoring   │
│   Database     │      │   & Classification   │
│  (JSONL file)  │      └──────────┬──────────┘
└────────┬───────┘                 │
         │                         │
         └──────────┬──────────────┘
                    ▼
        ┌────────────────────────┐
        │  Training Data         │
        │  Collection Guidance   │
        │  (Suggested Queries)   │
        └────────────────────────┘
```

---

## 🔍 Gap Detection

### Detection Sources

1. **Evaluation Failures** - Gaps detected when LLM judge scores fall below thresholds
2. **Training Metrics** - High perplexity or low validation accuracy
3. **Topic Coverage** - Underrepresented topics in training data
4. **Production Inference** - Low confidence predictions (future)

### Severity Classification

| Severity | Score Range | Description | Action |
|----------|-------------|-------------|--------|
| **CRITICAL** | <50 | Complete failure | Immediate training data collection |
| **HIGH** | 50-60 | Very low score | Priority training data collection |
| **MEDIUM** | 60-70 | Below acceptable | Scheduled training data collection |
| **LOW** | 70-85 | Borderline | Optional improvement |

### Priority Calculation

```python
priority = base_severity_score
          + (20 if eval_score < 50 else 0)
          + (15 if confidence < 0.3 else 0)

# Capped at 100
```

**Base Scores:**
- Critical: 40
- High: 30
- Medium: 20
- Low: 10

---

## 💾 Database Structure

### Knowledge Gap Model

```python
KnowledgeGap:
    gap_id: str                    # Unique identifier
    domain: str                    # Domain/specialty
    adapter_id: str               # Adapter that failed
    
    # Gap Details
    topic: str                     # Specific topic/area
    severity: GapSeverity         # Critical/High/Medium/Low
    source: GapSource             # Evaluation/Training/Inference
    
    # Context
    prompt: str                    # Input that failed
    expected_output: str           # Expected response
    actual_output: str             # Adapter's response
    confidence_score: float        # 0-1
    evaluation_score: float        # 0-100
    
    # Metadata
    detected_at: datetime
    detected_by: str
    tags: List[str]               # e.g., ["§123", "photovoltaik"]
    
    # Status
    status: str                    # open/in_progress/resolved
    resolved_at: datetime
    resolution_notes: str
    
    # Training Data
    requires_training_data: bool
    suggested_data_query: str      # Query for collecting data
    training_samples_collected: int
```

### Storage Format

**File:** `data/knowledge_gaps/gaps.jsonl`

**Format:** One JSON object per line (JSONL)

```json
{"gap_id": "gap-verwaltungsrecht-lora-v1.0.0-1", "domain": "verwaltungsrecht", "topic": "Photovoltaik Genehmigungsverfahren", "severity": "high", "source": "evaluation", "evaluation_score": 55.2, "suggested_data_query": "verwaltungsrecht Photovoltaik Genehmigungsverfahren", "status": "open", ...}
{"gap_id": "gap-verwaltungsrecht-lora-v1.0.0-2", "domain": "verwaltungsrecht", "topic": "Baurecht Dachanlage", "severity": "medium", "source": "evaluation", "evaluation_score": 65.8, "suggested_data_query": "verwaltungsrecht Baurecht Dachanlage", "status": "open", ...}
```

---

## 🚀 Usage

### Automatic Detection (Integrated)

Knowledge gaps are automatically detected during the lifecycle pipeline:

```bash
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Photovoltaik Baurecht" \
    --golden-dataset verwaltungsrecht-golden-v1
```

**Pipeline Output:**
```
🧑‍⚖️ Step 4/5: Evaluating with LLM judge...
📊 Evaluation Results:
   Overall Score: 78.5/100
   Pass Rate: 85.0%
   Samples: 17/20
   Knowledge Gaps Detected: 3

🔍 Saving 3 knowledge gaps to database...
✅ Knowledge gaps saved to database
   Severity breakdown:
     high: 1
     medium: 2
```

### Manual Gap Management

#### List All Open Gaps

```bash
python scripts/clara_knowledge_gaps.py list
```

**Output:**
```
================================================================================
Knowledge Gaps (3 found)
================================================================================

1. gap-verwaltungsrecht-lora-v1.0.0-1
   Domain: verwaltungsrecht
   Topic: Photovoltaik Genehmigungsverfahren...
   Severity: high | Priority: 65.0/100
   Source: evaluation
   Evaluation Score: 55.2/100
   Suggested Query: verwaltungsrecht Photovoltaik Genehmigungsverfahren
   Tags: §123, photovoltaik, genehmigung
   Status: open
   Detected: 2025-11-22T14:20:00Z
```

#### Show Priority Gaps

```bash
python scripts/clara_knowledge_gaps.py priority --top 10
```

#### Filter by Domain

```bash
python scripts/clara_knowledge_gaps.py list --domain verwaltungsrecht
```

#### Filter by Severity

```bash
python scripts/clara_knowledge_gaps.py list --severity critical
```

#### Show Statistics

```bash
python scripts/clara_knowledge_gaps.py stats
```

**Output:**
```
================================================================================
Knowledge Gap Statistics
================================================================================

Total Gaps: 15
Open: 12
Resolved: 2
In Progress: 1
Average Priority: 52.3/100

By Severity:
  critical: 2
  high: 5
  medium: 6
  low: 2

By Domain:
  verwaltungsrecht: 10
  steuerrecht: 5

By Source:
  evaluation: 13
  training: 2
```

#### Mark Gap as Resolved

```bash
python scripts/clara_knowledge_gaps.py resolve gap-123 \
    --notes "Added 50 training samples on Photovoltaik Genehmigungsverfahren"
```

#### Export Gaps for Data Collection

```bash
python scripts/clara_knowledge_gaps.py export gaps.json \
    --domain verwaltungsrecht
```

**Output File:**
```json
[
  {
    "gap_id": "gap-verwaltungsrecht-lora-v1.0.0-1",
    "domain": "verwaltungsrecht",
    "topic": "Photovoltaik Genehmigungsverfahren",
    "severity": "high",
    "suggested_query": "verwaltungsrecht Photovoltaik Genehmigungsverfahren",
    "priority": 65.0,
    "tags": ["§123", "photovoltaik", "genehmigung"]
  }
]
```

---

## 🔄 Integration with Training Pipeline

### Workflow

1. **Train Adapter** → Evaluate with LLM Judge
2. **Detect Gaps** → Save to database with priority scores
3. **Query Database** → Get high-priority gaps
4. **Collect Data** → Use suggested queries to stream training data
5. **Retrain Adapter** → Include new data targeting gaps
6. **Re-evaluate** → Verify gaps are resolved
7. **Mark Resolved** → Update gap status in database

### Example: Continuous Improvement Loop

```bash
# Step 1: Initial training and gap detection
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Verwaltungsrecht general" \
    --golden-dataset verwaltungsrecht-golden-v1

# Step 2: Check detected gaps
python scripts/clara_knowledge_gaps.py priority --top 5

# Step 3: Collect targeted training data for top gap
python scripts/clara_stream_training_data.py \
    --query "verwaltungsrecht Photovoltaik Genehmigungsverfahren" \
    --output data/gap_training_photovoltaik.jsonl \
    --top-k 500

# Step 4: Retrain adapter with gap-focused data
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Photovoltaik Genehmigungsverfahren" \
    --golden-dataset verwaltungsrecht-golden-v1

# Step 5: Mark gap as resolved
python scripts/clara_knowledge_gaps.py resolve gap-verwaltungsrecht-lora-v1.0.0-1 \
    --notes "Retrained with 500 Photovoltaik samples"
```

---

## 📊 Python API

### Detect Gaps

```python
from shared.adapters import KnowledgeGapDetector, get_knowledge_gap_database

# Initialize detector
detector = KnowledgeGapDetector(
    critical_threshold=50.0,
    high_threshold=60.0,
    medium_threshold=70.0,
    low_threshold=85.0
)

# Detect gaps from evaluation results
gaps = detector.detect_from_evaluation(
    adapter_id="verwaltungsrecht-lora-v1.0.0",
    domain="verwaltungsrecht",
    evaluation_results=results  # List of EvaluationResult
)

# Save to database
gap_db = get_knowledge_gap_database()
gap_db.add_gaps(gaps)
```

### Query Gaps

```python
from shared.adapters import get_knowledge_gap_database, GapSeverity

gap_db = get_knowledge_gap_database()

# Get all open gaps for a domain
gaps = gap_db.get_gaps(
    domain="verwaltungsrecht",
    status="open"
)

# Get critical gaps only
critical_gaps = gap_db.get_gaps(
    severity=GapSeverity.CRITICAL,
    status="open"
)

# Get top priority gaps
priority_gaps = gap_db.get_priority_gaps(top_n=10)

# Get statistics
stats = gap_db.get_statistics()
```

### Update Gap Status

```python
# Mark gap as in progress
gap_db.update_gap_status(
    gap_id="gap-123",
    status="in_progress"
)

# Mark gap as resolved
gap_db.update_gap_status(
    gap_id="gap-123",
    status="resolved",
    resolution_notes="Added 100 training samples"
)
```

---

## 🎯 Best Practices

### 1. Regular Gap Review

- Review priority gaps weekly
- Focus on critical/high severity gaps first
- Export gaps for data collection planning

### 2. Systematic Data Collection

- Use suggested queries from gaps
- Aim for 50-100 samples per gap
- Verify quality before retraining

### 3. Gap Resolution Tracking

- Always add resolution notes
- Document training samples collected
- Link to retrained adapter versions

### 4. Continuous Monitoring

- Monitor gap statistics over time
- Track resolution rate
- Identify recurring gap topics

---

## 📈 Metrics & Analytics

### Gap Metrics

- **Total Gaps:** Count of all detected gaps
- **Open Rate:** Percentage of unresolved gaps
- **Resolution Time:** Average time to resolve gaps
- **Priority Distribution:** Breakdown by severity

### Domain Coverage

- **Gaps per Domain:** Identify domains with most gaps
- **Topic Coverage:** Track underrepresented topics
- **Severity Trends:** Monitor if gaps are getting worse/better

---

## 🐛 Troubleshooting

### Issue: Too many gaps detected

**Cause:** Evaluation threshold too high

**Solution:**
```python
# Adjust detector thresholds
detector = KnowledgeGapDetector(
    critical_threshold=40.0,  # Lower from 50
    high_threshold=50.0,      # Lower from 60
    medium_threshold=60.0,    # Lower from 70
    low_threshold=75.0        # Lower from 85
)
```

### Issue: Gaps not being detected

**Cause:** All evaluations passing

**Solution:**
- Lower auto-approve threshold in pipeline
- Add more challenging samples to golden dataset
- Review evaluation criteria

### Issue: Database file not found

**Cause:** First run, database not created yet

**Solution:**
- Database is created automatically on first gap
- Check `data/knowledge_gaps/gaps.jsonl`

---

## 📚 Related Documentation

- [ADAPTER_LIFECYCLE_AUTOMATION.md](ADAPTER_LIFECYCLE_AUTOMATION.md)
- [STREAMING_JSONL_RETRIEVAL.md](STREAMING_JSONL_RETRIEVAL.md)

---

## 📝 Summary

**Status:** ✅ **PRODUCTION READY**

**Features:**
- ✅ Automatic gap detection from evaluations
- ✅ Severity classification and priority scoring
- ✅ Database storage with full metadata
- ✅ CLI tools for gap management
- ✅ Integration with training pipeline
- ✅ Suggested queries for data collection

**Benefits:**
- Identifies weak areas automatically
- Guides targeted training data collection
- Tracks improvement over time
- Enables continuous adapter improvement

**Ready for:** Production use with full automation support!

---

**Last Updated:** 2025-11-22  
**Maintainer:** Clara Development Team
