"""
LoRA Adapter Lifecycle Management

Comprehensive adapter management with versioning, evaluation, and automation.

Modules:
- registry: Adapter versioning and registry
- golden_dataset: Golden dataset management for benchmarking
- llm_judge: LLM-as-judge evaluation system
- knowledge_gaps: Knowledge gap detection and tracking
"""

from .registry import (
    AdapterRegistry,
    AdapterVersion,
    AdapterFamily,
    AdapterStatus,
    AdapterMethod,
    get_adapter_registry
)

from .golden_dataset import (
    GoldenDataset,
    GoldenSample,
    GoldenDatasetManager,
    get_golden_dataset_manager
)

from .llm_judge import (
    LLMJudge,
    EvaluationResult,
    EvaluationCriteria,
    AdapterEvaluationManager,
    get_evaluation_manager
)

from .knowledge_gaps import (
    KnowledgeGap,
    KnowledgeGapDetector,
    KnowledgeGapDatabase,
    GapSeverity,
    GapSource,
    get_knowledge_gap_database
)

__all__ = [
    # Registry
    'AdapterRegistry',
    'AdapterVersion',
    'AdapterFamily',
    'AdapterStatus',
    'AdapterMethod',
    'get_adapter_registry',
    
    # Golden Dataset
    'GoldenDataset',
    'GoldenSample',
    'GoldenDatasetManager',
    'get_golden_dataset_manager',
    
    # LLM Judge
    'LLMJudge',
    'EvaluationResult',
    'EvaluationCriteria',
    'AdapterEvaluationManager',
    'get_evaluation_manager',
    
    # Knowledge Gaps
    'KnowledgeGap',
    'KnowledgeGapDetector',
    'KnowledgeGapDatabase',
    'GapSeverity',
    'GapSource',
    'get_knowledge_gap_database',
]
