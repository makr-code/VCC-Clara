# Unified PostgreSQL Knowledge Gap Database

**Date:** 2025-11-22  
**Version:** 2.0.0  
**Status:** ✅ **PRODUCTION READY**

---

## 📋 Overview

Centralized PostgreSQL database for knowledge gap detection across **Clara**, **Veritas**, and **Covina** systems. Replaces file-based storage with a unified table that tracks gaps from all three systems.

**Key Features:**
- Single PostgreSQL table for all systems
- Source tracking (Clara/Veritas/Covina)
- SQL query capabilities
- Concurrent access safe
- Backward compatible with file-based storage

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│         Unified Knowledge Gap Database                   │
│         PostgreSQL Table: knowledge_gaps                  │
└────────────────────┬─────────────────────────────────────┘
                     │
         ┌───────────┴────────────┬──────────────┐
         ▼                        ▼              ▼
    ┌─────────┐            ┌──────────┐   ┌──────────┐
    │  Clara  │            │ Veritas  │   │  Covina  │
    │  (LoRA) │            │  (Docs)  │   │  (Admin) │
    └─────────┘            └──────────┘   └──────────┘
         │                        │              │
         └────────────────────────┴──────────────┘
                     All write to same table
                  with system_source identifier
```

---

## 💾 Database Schema

### Table: `public.knowledge_gaps`

| Column | Type | Description |
|--------|------|-------------|
| **gap_id** | VARCHAR(255) | Primary key, unique gap identifier |
| **system_source** | VARCHAR(50) | System origin (clara/veritas/covina) |
| **domain** | VARCHAR(255) | Domain/specialty |
| **adapter_id** | VARCHAR(255) | Related adapter (nullable) |
| **topic** | TEXT | Specific topic/area |
| **severity** | VARCHAR(50) | critical/high/medium/low |
| **source** | VARCHAR(50) | Detection source (evaluation/training/inference) |
| **prompt** | TEXT | Input that failed |
| **expected_output** | TEXT | Expected response |
| **actual_output** | TEXT | Actual response |
| **confidence_score** | FLOAT | Confidence 0-1 |
| **evaluation_score** | FLOAT | Score 0-100 |
| **detected_at** | TIMESTAMP | When detected |
| **detected_by** | VARCHAR(255) | User/system |
| **tags** | JSONB | Array of tags |
| **status** | VARCHAR(50) | open/in_progress/resolved |
| **resolved_at** | TIMESTAMP | When resolved |
| **resolution_notes** | TEXT | Resolution details |
| **requires_training_data** | BOOLEAN | Needs training data |
| **suggested_data_query** | TEXT | Query for data collection |
| **training_samples_collected** | INTEGER | Samples collected |
| **metadata** | JSONB | Additional metadata |
| **created_at** | TIMESTAMP | Row creation time |
| **updated_at** | TIMESTAMP | Last update time |

### Indexes

```sql
-- Single column indexes
idx_knowledge_gaps_system_source (system_source)
idx_knowledge_gaps_domain (domain)
idx_knowledge_gaps_severity (severity)
idx_knowledge_gaps_status (status)
idx_knowledge_gaps_detected_at (detected_at DESC)

-- Composite indexes
idx_knowledge_gaps_system_status (system_source, status)
idx_knowledge_gaps_domain_status (domain, status)
```

---

## 🚀 Usage

### Python API

#### Initialize Database

```python
from shared.adapters import get_knowledge_gap_pg_database, SystemSource

# Get database instance (uses config)
gap_db = get_knowledge_gap_pg_database()

# Or with custom config
gap_db = get_knowledge_gap_pg_database(
    host="192.168.178.94",
    port=5432,
    user="postgres",
    password="postgres",
    database="postgres",
    schema="public"
)
```

#### Add Gaps

```python
from shared.adapters import KnowledgeGap, SystemSource, GapSeverity, GapSource

# Create gap
gap = KnowledgeGap(
    gap_id="gap-clara-001",
    domain="verwaltungsrecht",
    topic="Photovoltaik Genehmigungsverfahren",
    severity=GapSeverity.HIGH,
    source=GapSource.EVALUATION,
    # ... other fields
)

# Add to database with source tracking
gap_db.add_gap(gap, system_source=SystemSource.CLARA)

# Batch add
gaps = [gap1, gap2, gap3]
gap_db.add_gaps(gaps, system_source=SystemSource.VERITAS)
```

#### Query Gaps

```python
# Get all Clara gaps
clara_gaps = gap_db.get_gaps(system_source=SystemSource.CLARA)

# Get high-severity Veritas gaps
veritas_high = gap_db.get_gaps(
    system_source=SystemSource.VERITAS,
    severity=GapSeverity.HIGH,
    status="open"
)

# Get gaps for specific domain
domain_gaps = gap_db.get_gaps(domain="verwaltungsrecht")

# Get all systems for a domain
all_systems = gap_db.get_gaps(domain="steuerrecht")  # No system filter
```

#### Priority Gaps

```python
# Top 10 priority gaps from Clara
clara_priority = gap_db.get_priority_gaps(
    top_n=10,
    system_source=SystemSource.CLARA
)

# Top priority gaps across all systems
all_priority = gap_db.get_priority_gaps(top_n=20)
```

#### Statistics

```python
# Clara statistics
clara_stats = gap_db.get_statistics(system_source=SystemSource.CLARA)

# All systems statistics
all_stats = gap_db.get_statistics()
# Returns breakdown by system in 'by_system' field
```

#### Update Status

```python
# Mark gap as resolved
gap_db.update_gap_status(
    gap_id="gap-clara-001",
    status="resolved",
    resolution_notes="Added 100 training samples"
)
```

### CLI Usage

The CLI tool supports both file-based and PostgreSQL storage.

#### List Gaps

```bash
# File-based (default)
python scripts/clara_knowledge_gaps.py list

# PostgreSQL (all systems)
python scripts/clara_knowledge_gaps.py list --postgres

# PostgreSQL (Clara only)
python scripts/clara_knowledge_gaps.py list --postgres --system clara

# PostgreSQL (Veritas, high severity)
python scripts/clara_knowledge_gaps.py list --postgres --system veritas --severity high

# PostgreSQL (domain filter)
python scripts/clara_knowledge_gaps.py list --postgres --domain verwaltungsrecht
```

#### Priority Gaps

```bash
# Top 10 from Clara
python scripts/clara_knowledge_gaps.py priority --top 10 --postgres --system clara

# Top 20 across all systems
python scripts/clara_knowledge_gaps.py priority --top 20 --postgres
```

#### Statistics

```bash
# All systems breakdown
python scripts/clara_knowledge_gaps.py stats --postgres

# Clara only
python scripts/clara_knowledge_gaps.py stats --postgres --system clara

# Veritas only
python scripts/clara_knowledge_gaps.py stats --postgres --system veritas
```

**Example Output:**
```
================================================================================
Knowledge Gap Statistics
(System: clara)
================================================================================

Total Gaps: 45
Open: 32
Resolved: 10
In Progress: 3
Average Score: 62.3/100

By Severity:
  critical: 5
  high: 15
  medium: 20
  low: 5

By Domain:
  verwaltungsrecht: 25
  steuerrecht: 15
  strafrecht: 5

By Source:
  evaluation: 40
  training: 3
  inference: 2
```

#### Resolve Gaps

```bash
# PostgreSQL
python scripts/clara_knowledge_gaps.py resolve gap-123 \
    --notes "Added 50 training samples" \
    --postgres
```

#### Export Gaps

```bash
# Export Clara gaps for data collection
python scripts/clara_knowledge_gaps.py export gaps.json \
    --postgres --system clara --domain verwaltungsrecht
```

### Automated Pipeline Integration

```bash
# Use PostgreSQL for gap storage
python scripts/clara_adapter_lifecycle.py \
    --domain verwaltungsrecht \
    --query "Photovoltaik Baurecht" \
    --golden-dataset verwaltungsrecht-golden-v1 \
    --use-postgres
```

**Pipeline Output:**
```
🔍 Saving 3 knowledge gaps to database...
✅ Knowledge gaps saved to database
   Database: PostgreSQL (source: clara)
   Severity breakdown:
     high: 1
     medium: 2
```

---

## 🔄 Migration from File-Based

### Gradual Migration

1. **Start Using PostgreSQL** - New gaps go to PostgreSQL
2. **Keep File-Based** - Existing gaps remain in JSONL
3. **Optionally Migrate** - Move historical data if needed

### Migration Script (Optional)

```python
from shared.adapters import (
    get_knowledge_gap_database,  # File-based
    get_knowledge_gap_pg_database,  # PostgreSQL
    SystemSource
)

# Get instances
file_db = get_knowledge_gap_database()
pg_db = get_knowledge_gap_pg_database()

# Migrate gaps
file_gaps = file_db.get_gaps()
pg_db.add_gaps(file_gaps, system_source=SystemSource.CLARA)

print(f"✅ Migrated {len(file_gaps)} gaps to PostgreSQL")
```

---

## 📊 Queries

### SQL Examples

```sql
-- Gaps by system
SELECT system_source, COUNT(*) as count
FROM public.knowledge_gaps
GROUP BY system_source;

-- Critical gaps across all systems
SELECT gap_id, system_source, domain, topic, evaluation_score
FROM public.knowledge_gaps
WHERE severity = 'critical' AND status = 'open'
ORDER BY detected_at DESC;

-- Domain coverage by system
SELECT system_source, domain, COUNT(*) as gaps
FROM public.knowledge_gaps
WHERE status = 'open'
GROUP BY system_source, domain
ORDER BY gaps DESC;

-- Resolution rate by system
SELECT 
    system_source,
    COUNT(*) FILTER (WHERE status = 'resolved') * 100.0 / COUNT(*) as resolution_rate
FROM public.knowledge_gaps
GROUP BY system_source;
```

### Analytics Queries

```sql
-- Average resolution time
SELECT 
    system_source,
    AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at))/3600) as avg_hours_to_resolve
FROM public.knowledge_gaps
WHERE status = 'resolved'
GROUP BY system_source;

-- Gaps detected per day (last 30 days)
SELECT 
    DATE(detected_at) as date,
    system_source,
    COUNT(*) as gaps
FROM public.knowledge_gaps
WHERE detected_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(detected_at), system_source
ORDER BY date DESC;

-- Most problematic topics
SELECT topic, COUNT(*) as occurrences
FROM public.knowledge_gaps
WHERE status = 'open'
GROUP BY topic
ORDER BY occurrences DESC
LIMIT 10;
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# PostgreSQL connection
export POSTGRES_HOST=192.168.178.94
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_DATABASE=postgres
export POSTGRES_SCHEMA=public
```

### Config File (config/base.py)

Already configured with PostgreSQL settings:
```python
postgres_host: str = Field(default="192.168.178.94")
postgres_port: int = Field(default=5432)
postgres_user: str = Field(default="postgres")
postgres_password: str = Field(default="postgres")
postgres_database: str = Field(default="postgres")
postgres_schema: str = Field(default="public")
```

---

## 🔒 Security

### Database Access

- Uses existing PostgreSQL credentials
- No new authentication required
- Same security model as other PostgreSQL tables

### Concurrent Access

- Thread-safe connections
- Transaction support
- Row-level locking for updates

---

## 📈 Performance

### Indexes

Optimized indexes for common queries:
- Fast filtering by system, domain, severity, status
- Efficient date-based queries
- Quick composite lookups

### Scalability

- Handles millions of gaps
- Sub-second queries with indexes
- Batch insert support

---

## 🐛 Troubleshooting

### Connection Failed

```python
# Check PostgreSQL is running
psql -h 192.168.178.94 -U postgres -d postgres -c "SELECT 1;"

# Test connection in Python
from shared.adapters import get_knowledge_gap_pg_database
try:
    gap_db = get_knowledge_gap_pg_database()
    print("✅ Connected")
except Exception as e:
    print(f"❌ Failed: {e}")
```

### Table Not Created

```python
# Manually create table
gap_db = get_knowledge_gap_pg_database()
gap_db._create_table()  # Force table creation
```

### Missing psycopg2

```bash
pip install psycopg2-binary
```

---

## 📚 Related Documentation

- [KNOWLEDGE_GAP_DETECTION.md](KNOWLEDGE_GAP_DETECTION.md) - Gap detection guide
- [ADAPTER_LIFECYCLE_AUTOMATION.md](ADAPTER_LIFECYCLE_AUTOMATION.md) - Pipeline automation

---

## 📝 Summary

**Status:** ✅ **PRODUCTION READY**

**Key Benefits:**
- ✅ Unified database for Clara, Veritas, Covina
- ✅ System source tracking
- ✅ SQL query capabilities
- ✅ Concurrent access safe
- ✅ Backward compatible
- ✅ Production-ready indexes

**Usage:**
- Python API for programmatic access
- CLI tool with `--postgres` flag
- Automated pipeline support
- Migration path from file-based storage

**Ready for:** Immediate production use across all three systems!

---

**Last Updated:** 2025-11-22  
**Maintainer:** Clara Development Team
