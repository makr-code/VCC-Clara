#!/usr/bin/env python3
"""
Automated LoRA Adapter Lifecycle Pipeline

Complete automation pipeline integrating:
- Streaming data retrieval from UDS3/Themis
- LoRA adapter training
- LLM-as-judge evaluation
- Version management
- Review workflow

Usage:
    python scripts/clara_adapter_lifecycle.py \\
        --domain verwaltungsrecht \\
        --query "Photovoltaik Baurecht" \\
        --golden-dataset verwaltungsrecht-golden-v1

Features:
- Automatic versioning
- Quality assurance via LLM judge
- Golden dataset validation
- Automated approval workflow
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.adapters import (
    get_adapter_registry,
    get_golden_dataset_manager,
    get_evaluation_manager,
    get_knowledge_gap_database,
    AdapterMethod,
    AdapterStatus
)
from shared.database.dataset_search import DatasetSearchAPI, DatasetSearchQuery
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_lifecycle_pipeline(
    domain: str,
    query_text: str,
    golden_dataset_id: str,
    method: AdapterMethod = AdapterMethod.LORA,
    rank: int = 16,
    auto_approve_threshold: float = 85.0
):
    """
    Run complete adapter lifecycle pipeline
    
    Pipeline steps:
    1. Stream training data from UDS3/Themis
    2. Train LoRA adapter
    3. Evaluate with LLM judge on golden dataset
    4. Register version in adapter registry
    5. Auto-approve if meets threshold
    
    Args:
        domain: Domain/specialty (e.g., "verwaltungsrecht")
        query_text: Search query for training data
        golden_dataset_id: Golden dataset for evaluation
        method: LoRA/QLoRA/DoRA
        rank: LoRA rank
        auto_approve_threshold: Auto-approve if score >= this (0-100)
    """
    logger.info("=" * 70)
    logger.info("🚀 Starting LoRA Adapter Lifecycle Pipeline")
    logger.info("=" * 70)
    logger.info(f"Domain: {domain}")
    logger.info(f"Method: {method.value}")
    logger.info(f"Query: {query_text}")
    logger.info(f"Golden Dataset: {golden_dataset_id}")
    logger.info("=" * 70)
    
    # Initialize managers
    registry = get_adapter_registry()
    dataset_mgr = get_golden_dataset_manager()
    eval_mgr = get_evaluation_manager()
    gap_db = get_knowledge_gap_database()
    
    # Step 1: Stream training data
    logger.info("\n📥 Step 1/5: Streaming training data from UDS3/Themis...")
    training_data_path = await stream_training_data(domain, query_text)
    
    if not training_data_path:
        logger.error("❌ Failed to stream training data")
        return False
    
    # Step 2: Train adapter
    logger.info(f"\n🔧 Step 2/5: Training {method.value} adapter...")
    adapter_path = await train_adapter(
        domain=domain,
        method=method,
        rank=rank,
        training_data=training_data_path
    )
    
    if not adapter_path:
        logger.error("❌ Adapter training failed")
        return False
    
    # Step 3: Register adapter version
    logger.info("\n📝 Step 3/5: Registering adapter version...")
    adapter_version = registry.register_adapter(
        domain=domain,
        method=method,
        adapter_path=adapter_path,
        base_model="leo-base-model",  # TODO: Get from config
        rank=rank,
        dataset_path=training_data_path,
        created_by="automated-pipeline",
        description=f"Auto-trained on query: {query_text[:50]}..."
    )
    
    logger.info(f"✅ Registered: {adapter_version.adapter_id}")
    
    # Step 4: Evaluate with LLM judge
    logger.info("\n🧑‍⚖️ Step 4/5: Evaluating with LLM judge...")
    
    # Get golden dataset
    golden_dataset = dataset_mgr.get_dataset(golden_dataset_id)
    if not golden_dataset:
        logger.error(f"❌ Golden dataset not found: {golden_dataset_id}")
        return False
    
    # Create inference function (placeholder)
    async def adapter_inference(prompt: str, context: Optional[str] = None) -> str:
        # TODO: Implement actual adapter inference
        # In production, this would load the adapter and run inference
        logger.info(f"Running inference on: {prompt[:50]}...")
        await asyncio.sleep(0.1)  # Simulate inference
        return f"Mock output for: {prompt[:30]}..."
    
    # Run evaluation
    results_path = await eval_mgr.evaluate_adapter(
        adapter_id=adapter_version.adapter_id,
        golden_dataset_id=golden_dataset_id,
        adapter_inference_fn=adapter_inference
    )
    
    # Load evaluation results
    import json
    with open(results_path, 'r') as f:
        evaluation = json.load(f)
    
    summary = evaluation['summary']
    overall_score = summary['average_score']
    pass_rate = summary['pass_rate']
    knowledge_gaps = evaluation.get('knowledge_gaps', [])
    
    logger.info(f"📊 Evaluation Results:")
    logger.info(f"   Overall Score: {overall_score:.1f}/100")
    logger.info(f"   Pass Rate: {pass_rate:.1f}%")
    logger.info(f"   Samples: {summary['passed']}/{summary['total_samples']}")
    logger.info(f"   Knowledge Gaps Detected: {len(knowledge_gaps)}")
    
    # Save knowledge gaps to database
    if knowledge_gaps:
        logger.info(f"\n🔍 Saving {len(knowledge_gaps)} knowledge gaps to database...")
        from shared.adapters.knowledge_gaps import KnowledgeGap
        
        for gap_data in knowledge_gaps:
            gap = KnowledgeGap.from_dict(gap_data)
            gap_db.add_gap(gap)
        
        logger.info(f"✅ Knowledge gaps saved to database")
        logger.info(f"   Severity breakdown:")
        severity_counts = {}
        for gap_data in knowledge_gaps:
            sev = gap_data['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        for sev, count in severity_counts.items():
            logger.info(f"     {sev}: {count}")
    
    # Update adapter metrics
    registry.update_metrics(adapter_version.adapter_id, {
        "llm_judge_score": overall_score,
        "pass_rate": pass_rate,
        "golden_dataset_accuracy": summary['passed'] / summary['total_samples'],
        "knowledge_gaps_detected": len(knowledge_gaps)
    })
    
    # Step 5: Auto-approve if meets threshold
    logger.info(f"\n✅ Step 5/5: Review and approval...")
    
    if overall_score >= auto_approve_threshold:
        registry.approve_adapter(
            adapter_id=adapter_version.adapter_id,
            approved_by="automated-pipeline",
            notes=f"Auto-approved: Score {overall_score:.1f} >= threshold {auto_approve_threshold}"
        )
        logger.info(f"✅ AUTO-APPROVED: {adapter_version.adapter_id}")
        logger.info(f"   Score: {overall_score:.1f}/100 (threshold: {auto_approve_threshold})")
    else:
        logger.info(f"⏸️  PENDING MANUAL REVIEW: {adapter_version.adapter_id}")
        logger.info(f"   Score: {overall_score:.1f}/100 (threshold: {auto_approve_threshold})")
        logger.info(f"   Status: {adapter_version.status.value}")
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("🎉 Pipeline Complete!")
    logger.info("=" * 70)
    logger.info(f"Adapter ID: {adapter_version.adapter_id}")
    logger.info(f"Version: {adapter_version.version}")
    logger.info(f"Status: {adapter_version.status.value}")
    logger.info(f"Score: {overall_score:.1f}/100")
    logger.info(f"Path: {adapter_path}")
    logger.info(f"Evaluation: {results_path}")
    logger.info("=" * 70)
    
    return True


async def stream_training_data(domain: str, query_text: str) -> Optional[str]:
    """
    Stream training data from UDS3/Themis
    
    Returns:
        Path to streamed JSONL file, or None if failed
    """
    try:
        api = DatasetSearchAPI()
        
        query = DatasetSearchQuery(
            query_text=query_text,
            top_k=1000,  # Configurable
            filters={"domain": domain},
            min_quality_score=0.6,
            search_types=["vector", "graph"]
        )
        
        output_path = f"data/training_datasets/{domain}_auto_{query_text[:20]}.jsonl"
        output_path = output_path.replace(" ", "_")
        
        count = await api.stream_to_jsonl(
            query=query,
            output_path=output_path,
            batch_size=config.streaming_batch_size
        )
        
        logger.info(f"✅ Streamed {count} documents to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"❌ Streaming failed: {e}", exc_info=True)
        return None


async def train_adapter(
    domain: str,
    method: AdapterMethod,
    rank: int,
    training_data: str
) -> Optional[str]:
    """
    Train LoRA adapter
    
    Returns:
        Path to trained adapter, or None if failed
    """
    try:
        # TODO: Implement actual training
        # In production, this would call clara_train_adapter.py or training backend API
        
        logger.info(f"Training {method.value} adapter...")
        logger.info(f"  Domain: {domain}")
        logger.info(f"  Rank: {rank}")
        logger.info(f"  Dataset: {training_data}")
        
        # Simulate training
        await asyncio.sleep(1.0)
        
        # Mock adapter path
        adapter_path = f"models/adapters/{domain}/{method.value}-r{rank}-auto"
        
        logger.info(f"✅ Training complete: {adapter_path}")
        
        return adapter_path
    
    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        return None


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Automated LoRA Adapter Lifecycle Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic pipeline
  python scripts/clara_adapter_lifecycle.py \\
      --domain verwaltungsrecht \\
      --query "Photovoltaik Baurecht" \\
      --golden-dataset verwaltungsrecht-golden-v1

  # With custom settings
  python scripts/clara_adapter_lifecycle.py \\
      --domain steuerrecht \\
      --query "Einkommensteuer" \\
      --golden-dataset steuerrecht-golden-v1 \\
      --method qlora \\
      --rank 32 \\
      --auto-approve-threshold 90
"""
    )
    
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="Domain/specialty (e.g., verwaltungsrecht)"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query for training data"
    )
    
    parser.add_argument(
        "--golden-dataset",
        type=str,
        required=True,
        help="Golden dataset ID for evaluation"
    )
    
    parser.add_argument(
        "--method",
        type=str,
        default="lora",
        choices=["lora", "qlora", "dora"],
        help="Adapter method (default: lora)"
    )
    
    parser.add_argument(
        "--rank",
        type=int,
        default=16,
        help="LoRA rank (default: 16)"
    )
    
    parser.add_argument(
        "--auto-approve-threshold",
        type=float,
        default=85.0,
        help="Auto-approve threshold (default: 85.0)"
    )
    
    args = parser.parse_args()
    
    # Convert method to enum
    method_map = {
        "lora": AdapterMethod.LORA,
        "qlora": AdapterMethod.QLORA,
        "dora": AdapterMethod.DORA
    }
    method = method_map[args.method]
    
    # Run pipeline
    success = asyncio.run(run_lifecycle_pipeline(
        domain=args.domain,
        query_text=args.query,
        golden_dataset_id=args.golden_dataset,
        method=method,
        rank=args.rank,
        auto_approve_threshold=args.auto_approve_threshold
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
