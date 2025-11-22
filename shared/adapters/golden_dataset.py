"""
Golden Dataset Management

Manages reference datasets for adapter evaluation and quality benchmarking.

Features:
- Golden sample collection from high-quality data
- Expected output tracking
- Benchmark test suites
- Version control for golden datasets
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class GoldenSample:
    """
    Single golden dataset sample with expected output
    
    Used for evaluating adapter quality and regression testing.
    """
    sample_id: str
    domain: str
    
    # Input
    prompt: str
    context: Optional[str] = None
    
    # Expected Output
    expected_output: str
    expected_score: float = 1.0  # Quality score 0-1
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual"
    
    # Evaluation Criteria
    criteria: Dict[str, str] = field(default_factory=dict)
    # Example: {"accuracy": "Must include §123 reference", "style": "Formal legal language"}
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GoldenSample':
        """Create from dict"""
        return cls(**data)


@dataclass
class GoldenDataset:
    """
    Collection of golden samples for a specific domain
    
    Used as benchmark for adapter evaluation.
    """
    dataset_id: str
    domain: str
    version: str
    description: str
    samples: List[GoldenSample] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    
    # Statistics
    total_samples: int = 0
    difficulty_distribution: Dict[str, int] = field(default_factory=dict)
    
    def add_sample(self, sample: GoldenSample):
        """Add sample to dataset"""
        self.samples.append(sample)
        self.total_samples = len(self.samples)
        self._update_statistics()
    
    def _update_statistics(self):
        """Update dataset statistics"""
        self.difficulty_distribution = {}
        for sample in self.samples:
            difficulty = sample.difficulty
            self.difficulty_distribution[difficulty] = \
                self.difficulty_distribution.get(difficulty, 0) + 1
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['samples'] = [s.to_dict() for s in self.samples]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GoldenDataset':
        """Create from dict"""
        samples = [GoldenSample.from_dict(s) for s in data.pop('samples', [])]
        dataset = cls(**data)
        dataset.samples = samples
        return dataset


class GoldenDatasetManager:
    """
    Manages golden datasets for adapter evaluation
    
    Provides creation, versioning, and access to benchmark datasets.
    """
    
    def __init__(self, datasets_dir: str = "data/golden_datasets"):
        self.datasets_dir = Path(datasets_dir)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        self.datasets: Dict[str, GoldenDataset] = {}
        self.load_all()
        
        logger.info(f"📚 GoldenDatasetManager loaded: {len(self.datasets)} datasets")
    
    def load_all(self):
        """Load all golden datasets"""
        for json_file in self.datasets_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                dataset = GoldenDataset.from_dict(data)
                self.datasets[dataset.dataset_id] = dataset
                logger.info(f"✅ Loaded golden dataset: {dataset.dataset_id}")
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
    
    def create_dataset(
        self,
        dataset_id: str,
        domain: str,
        description: str,
        version: str = "1.0.0",
        **kwargs
    ) -> GoldenDataset:
        """
        Create new golden dataset
        
        Args:
            dataset_id: Unique dataset ID
            domain: Domain/specialty
            description: Dataset description
            version: Version string
            
        Returns:
            Created GoldenDataset
        """
        dataset = GoldenDataset(
            dataset_id=dataset_id,
            domain=domain,
            version=version,
            description=description,
            **kwargs
        )
        
        self.datasets[dataset_id] = dataset
        self.save_dataset(dataset_id)
        
        logger.info(f"✅ Created golden dataset: {dataset_id}")
        
        return dataset
    
    def add_sample(
        self,
        dataset_id: str,
        prompt: str,
        expected_output: str,
        domain: str,
        sample_id: Optional[str] = None,
        **kwargs
    ) -> GoldenSample:
        """
        Add sample to golden dataset
        
        Args:
            dataset_id: Target dataset ID
            prompt: Input prompt
            expected_output: Expected model output
            domain: Domain/specialty
            sample_id: Optional sample ID (auto-generated if None)
            **kwargs: Additional sample metadata
            
        Returns:
            Created GoldenSample
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        if sample_id is None:
            sample_id = f"{dataset_id}-{len(dataset.samples) + 1}"
        
        sample = GoldenSample(
            sample_id=sample_id,
            domain=domain,
            prompt=prompt,
            expected_output=expected_output,
            **kwargs
        )
        
        dataset.add_sample(sample)
        self.save_dataset(dataset_id)
        
        logger.info(f"✅ Added sample to {dataset_id}: {sample_id}")
        
        return sample
    
    def get_dataset(self, dataset_id: str) -> Optional[GoldenDataset]:
        """Get golden dataset by ID"""
        return self.datasets.get(dataset_id)
    
    def list_datasets(self, domain: Optional[str] = None) -> List[GoldenDataset]:
        """
        List golden datasets with optional domain filter
        
        Args:
            domain: Optional domain filter
            
        Returns:
            List of matching datasets
        """
        datasets = list(self.datasets.values())
        
        if domain:
            datasets = [d for d in datasets if d.domain == domain]
        
        return datasets
    
    def save_dataset(self, dataset_id: str):
        """Save dataset to disk"""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            logger.warning(f"Dataset not found: {dataset_id}")
            return
        
        file_path = self.datasets_dir / f"{dataset_id}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(dataset.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved golden dataset: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save dataset: {e}")
    
    def export_for_evaluation(
        self,
        dataset_id: str,
        output_path: str,
        format: str = "jsonl"
    ):
        """
        Export golden dataset for evaluation
        
        Args:
            dataset_id: Dataset to export
            output_path: Output file path
            format: Export format (jsonl, json, csv)
        """
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            with open(output_file, 'w') as f:
                for sample in dataset.samples:
                    f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + '\n')
        
        elif format == "json":
            with open(output_file, 'w') as f:
                json.dump([s.to_dict() for s in dataset.samples], f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            with open(output_file, 'w', newline='') as f:
                fieldnames = ['sample_id', 'prompt', 'expected_output', 'domain', 'difficulty']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for sample in dataset.samples:
                    writer.writerow({k: getattr(sample, k) for k in fieldnames})
        
        logger.info(f"✅ Exported {len(dataset.samples)} samples to {output_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics across all golden datasets"""
        total_samples = sum(d.total_samples for d in self.datasets.values())
        
        domains = {}
        for dataset in self.datasets.values():
            domains[dataset.domain] = domains.get(dataset.domain, 0) + dataset.total_samples
        
        return {
            "total_datasets": len(self.datasets),
            "total_samples": total_samples,
            "domains": domains,
            "average_samples_per_dataset": total_samples / len(self.datasets) if self.datasets else 0
        }


# Global instance
_manager = None

def get_golden_dataset_manager() -> GoldenDatasetManager:
    """Get global golden dataset manager instance"""
    global _manager
    if _manager is None:
        _manager = GoldenDatasetManager()
    return _manager
