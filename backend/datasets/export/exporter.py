"""
Dataset Export Handlers

Multi-format export (JSONL, Parquet, CSV, JSON)
"""

import json
import logging
from pathlib import Path
from typing import List, Any

from ..models import Dataset, ExportFormat

logger = logging.getLogger(__name__)


class DatasetExporter:
    """
    Dataset Exporter for multiple formats
    
    Supports: JSONL, Parquet, CSV, JSON
    """
    
    @staticmethod
    def export(
        documents: List[Any],  # DatasetDocument from UDS3
        dataset: Dataset,
        format: ExportFormat,
        base_dir: Path
    ) -> Path:
        """
        Export dataset to specified format
        
        Args:
            documents: List of DatasetDocument objects
            dataset: Dataset metadata
            format: Export format
            base_dir: Base directory for exports
            
        Returns:
            Path to exported file
        """
        logger.info(f"📤 Exporting dataset to {format.value}: {dataset.dataset_id}")
        
        # Safe filename
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in dataset.name)
        
        if format == ExportFormat.JSONL:
            return DatasetExporter._export_jsonl(documents, dataset, safe_name, base_dir)
        elif format == ExportFormat.PARQUET:
            return DatasetExporter._export_parquet(documents, dataset, safe_name, base_dir)
        elif format == ExportFormat.CSV:
            return DatasetExporter._export_csv(documents, dataset, safe_name, base_dir)
        elif format == ExportFormat.JSON:
            return DatasetExporter._export_json(documents, dataset, safe_name, base_dir)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def _export_jsonl(documents: List[Any], dataset: Dataset, safe_name: str, base_dir: Path) -> Path:
        """Export to JSONL format (one JSON object per line)"""
        output_file = base_dir / f"{safe_name}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for doc in documents:
                training_entry = doc.to_training_format()
                f.write(json.dumps(training_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"✅ Exported {len(documents)} documents to JSONL")
        return output_file
    
    @staticmethod
    def _export_parquet(documents: List[Any], dataset: Dataset, safe_name: str, base_dir: Path) -> Path:
        """Export to Parquet format (columnar storage)"""
        output_file = base_dir / f"{safe_name}.parquet"
        
        try:
            import pandas as pd
            import pyarrow as pa
            import pyarrow.parquet as pq
            
            # Convert to DataFrame
            data = [doc.to_training_format() for doc in documents]
            df = pd.DataFrame(data)
            
            # Write Parquet
            table = pa.Table.from_pandas(df)
            pq.write_table(table, output_file)
            
            logger.info(f"✅ Exported {len(documents)} documents to Parquet")
        
        except ImportError:
            logger.warning("⚠️ pandas/pyarrow not installed - falling back to JSONL")
            output_file = base_dir / f"{safe_name}.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for doc in documents:
                    f.write(json.dumps(doc.to_training_format(), ensure_ascii=False) + '\n')
        
        return output_file
    
    @staticmethod
    def _export_csv(documents: List[Any], dataset: Dataset, safe_name: str, base_dir: Path) -> Path:
        """Export to CSV format"""
        output_file = base_dir / f"{safe_name}.csv"
        
        try:
            import csv
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if documents:
                    fieldnames = ['document_id', 'text', 'source', 'quality_score', 'relevance_score']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for doc in documents:
                        entry = doc.to_training_format()
                        writer.writerow({
                            'document_id': entry['document_id'],
                            'text': entry['text'],
                            'source': entry['source'],
                            'quality_score': entry['quality_score'],
                            'relevance_score': entry['relevance_score']
                        })
            
            logger.info(f"✅ Exported {len(documents)} documents to CSV")
        
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
        
        return output_file
    
    @staticmethod
    def _export_json(documents: List[Any], dataset: Dataset, safe_name: str, base_dir: Path) -> Path:
        """Export to JSON format (single array)"""
        output_file = base_dir / f"{safe_name}.json"
        
        data = {
            "dataset_id": dataset.dataset_id,
            "name": dataset.name,
            "description": dataset.description,
            "created_at": dataset.created_at.isoformat(),
            "created_by": dataset.created_by,
            "document_count": len(documents),
            "documents": [doc.to_training_format() for doc in documents]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Exported {len(documents)} documents to JSON")
        
        return output_file
