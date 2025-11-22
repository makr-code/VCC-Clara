#!/usr/bin/env python3
"""
Stream Training Data from UDS3/Themis for LoRA Training

This script demonstrates automatic streaming retrieval of JSONL data
from UDS3/Themis database for LoRA adapter training.

Features:
- Memory-efficient streaming (no full dataset in memory)
- Automatic quality filtering
- Progressive data loading during training
- Configurable batch sizes

Usage:
    # Stream to file
    python scripts/clara_stream_training_data.py --query "Verwaltungsrecht" --output data/training.jsonl
    
    # Stream with custom filters
    python scripts/clara_stream_training_data.py \\
        --query "Photovoltaik" \\
        --domain verwaltungsrecht \\
        --min-quality 0.7 \\
        --top-k 5000 \\
        --output data/pv_training.jsonl
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

from shared.database import DatasetSearchAPI, DatasetSearchQuery, UDS3_AVAILABLE
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def stream_training_data(
    query_text: str,
    output_path: str,
    top_k: int = 1000,
    domain: Optional[str] = None,
    min_quality: float = 0.5,
    batch_size: int = 100
):
    """
    Stream training data from UDS3/Themis to JSONL file
    
    Args:
        query_text: Search query
        output_path: Output JSONL file path
        top_k: Maximum number of documents
        domain: Optional domain filter
        min_quality: Minimum quality score (0.0-1.0)
        batch_size: Streaming batch size
    """
    
    if not UDS3_AVAILABLE:
        logger.error("❌ UDS3 not available. Cannot stream data from Themis.")
        logger.info("   Install UDS3: pip install -e ../uds3")
        return False
    
    logger.info("=" * 60)
    logger.info("🌊 Streaming Training Data from UDS3/Themis")
    logger.info("=" * 60)
    logger.info(f"Query: {query_text}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Top-K: {top_k}")
    logger.info(f"Domain: {domain or 'all'}")
    logger.info(f"Min Quality: {min_quality}")
    logger.info(f"Batch Size: {batch_size}")
    logger.info("=" * 60)
    
    try:
        # Initialize API
        api = DatasetSearchAPI()
        
        if not api.search_api:
            logger.error("❌ Failed to initialize UDS3 Search API")
            return False
        
        # Create search query
        filters = {"domain": domain} if domain else None
        
        query = DatasetSearchQuery(
            query_text=query_text,
            top_k=top_k,
            filters=filters,
            min_quality_score=min_quality,
            search_types=["vector", "graph"],
            weights={"vector": 0.6, "graph": 0.4}
        )
        
        # Stream to JSONL (memory-efficient)
        logger.info("🚀 Starting streaming...")
        count = await api.stream_to_jsonl(
            query=query,
            output_path=output_path,
            batch_size=batch_size
        )
        
        logger.info("=" * 60)
        logger.info(f"✅ SUCCESS: Streamed {count} documents to {output_path}")
        logger.info("=" * 60)
        logger.info(f"📊 File size: {Path(output_path).stat().st_size / 1024 / 1024:.2f} MB")
        logger.info(f"🔧 Ready for LoRA training with: --dataset {output_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Streaming failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Stream training data from UDS3/Themis for LoRA training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic streaming
  python scripts/clara_stream_training_data.py \\
      --query "Verwaltungsrecht Photovoltaik" \\
      --output data/training.jsonl
  
  # Advanced streaming with filters
  python scripts/clara_stream_training_data.py \\
      --query "Baurecht Dachanlage" \\
      --domain verwaltungsrecht \\
      --min-quality 0.7 \\
      --top-k 5000 \\
      --batch-size 200 \\
      --output data/baurecht_training.jsonl
  
  # Large dataset streaming
  python scripts/clara_stream_training_data.py \\
      --query "Verwaltungsverfahren" \\
      --top-k 10000 \\
      --output data/large_training.jsonl
"""
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query text"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSONL file path"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=1000,
        help="Maximum number of documents (default: 1000)"
    )
    
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Domain filter (e.g., verwaltungsrecht)"
    )
    
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.5,
        help="Minimum quality score 0.0-1.0 (default: 0.5)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"Streaming batch size (default: {config.streaming_batch_size})"
    )
    
    args = parser.parse_args()
    
    # Use config default if not specified
    batch_size = args.batch_size if args.batch_size is not None else config.streaming_batch_size
    
    # Run streaming
    success = asyncio.run(stream_training_data(
        query_text=args.query,
        output_path=args.output,
        top_k=args.top_k,
        domain=args.domain,
        min_quality=args.min_quality,
        batch_size=batch_size
    ))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
