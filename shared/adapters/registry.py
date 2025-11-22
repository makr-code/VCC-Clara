"""
LoRA Adapter Registry with Versioning

Centralized registry for tracking, versioning, and managing LoRA adapters.

Features:
- Semantic versioning (v1.0.0, v1.1.0, etc.)
- Adapter metadata tracking
- Version comparison and diff
- Quality metrics history
- Review status tracking
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class AdapterStatus(str, Enum):
    """Adapter Review Status"""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class AdapterMethod(str, Enum):
    """Adapter Training Method"""
    LORA = "lora"
    QLORA = "qlora"
    DORA = "dora"


@dataclass
class AdapterVersion:
    """
    LoRA Adapter Version Metadata
    
    Tracks all metadata for a specific version of an adapter,
    including quality metrics, review status, and deployment info.
    """
    # Identification
    adapter_id: str  # e.g., "verwaltungsrecht-lora-v1.0.0"
    version: str  # Semantic version: "1.0.0"
    domain: str  # Domain/specialty (e.g., "verwaltungsrecht")
    method: AdapterMethod  # LoRA, QLoRA, DoRA
    
    # Training Configuration
    rank: int  # LoRA rank (e.g., 16, 32)
    base_model: str  # Base model name/path
    base_model_hash: str  # SHA256 of base model
    
    # Files & Paths
    adapter_path: str  # Path to adapter weights
    adapter_checksum: str  # SHA256 of adapter files
    config_path: Optional[str] = None  # Training config
    dataset_path: Optional[str] = None  # Training dataset
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Quality Metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    # Example metrics:
    # - perplexity: 7.1
    # - domain_score: 0.83
    # - llm_judge_score: 85.5
    # - golden_dataset_accuracy: 0.92
    
    # Review & Approval
    status: AdapterStatus = AdapterStatus.PENDING_REVIEW
    review_notes: List[str] = field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    # Deployment
    deployed: bool = False
    deployment_count: int = 0
    last_used: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['method'] = self.method.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdapterVersion':
        """Create from dict"""
        data['method'] = AdapterMethod(data['method'])
        data['status'] = AdapterStatus(data['status'])
        return cls(**data)
    
    def get_semantic_version(self) -> tuple:
        """Get version as tuple (major, minor, patch)"""
        parts = self.version.split('.')
        return tuple(int(p) for p in parts)
    
    def increment_version(self, level: str = 'patch') -> str:
        """
        Increment version number
        
        Args:
            level: 'major', 'minor', or 'patch'
            
        Returns:
            New version string
        """
        major, minor, patch = self.get_semantic_version()
        
        if level == 'major':
            return f"{major + 1}.0.0"
        elif level == 'minor':
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"


@dataclass
class AdapterFamily:
    """
    Group of related adapter versions (same domain/method)
    
    Tracks all versions of a specific adapter type,
    maintains version history, and provides comparison.
    """
    family_id: str  # e.g., "verwaltungsrecht-lora"
    domain: str
    method: AdapterMethod
    versions: List[AdapterVersion] = field(default_factory=list)
    
    def add_version(self, version: AdapterVersion):
        """Add new version to family"""
        self.versions.append(version)
        self.versions.sort(key=lambda v: v.get_semantic_version(), reverse=True)
    
    def get_latest_version(self) -> Optional[AdapterVersion]:
        """Get most recent version"""
        return self.versions[0] if self.versions else None
    
    def get_latest_approved(self) -> Optional[AdapterVersion]:
        """Get most recent approved version"""
        approved = [v for v in self.versions if v.status == AdapterStatus.APPROVED]
        return approved[0] if approved else None
    
    def get_version(self, version: str) -> Optional[AdapterVersion]:
        """Get specific version"""
        for v in self.versions:
            if v.version == version:
                return v
        return None
    
    def compare_versions(self, v1: str, v2: str) -> Dict[str, Any]:
        """
        Compare two versions
        
        Returns dict with differences in metrics, status, etc.
        """
        version1 = self.get_version(v1)
        version2 = self.get_version(v2)
        
        if not version1 or not version2:
            return {"error": "Version not found"}
        
        comparison = {
            "version1": v1,
            "version2": v2,
            "metrics_diff": {},
            "status_changed": version1.status != version2.status,
            "rank_changed": version1.rank != version2.rank
        }
        
        # Compare metrics
        all_metrics = set(version1.metrics.keys()) | set(version2.metrics.keys())
        for metric in all_metrics:
            val1 = version1.metrics.get(metric, 0)
            val2 = version2.metrics.get(metric, 0)
            if val1 != val2:
                comparison["metrics_diff"][metric] = {
                    "old": val1,
                    "new": val2,
                    "delta": val2 - val1,
                    "delta_percent": ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                }
        
        return comparison


class AdapterRegistry:
    """
    Central Registry for LoRA Adapters
    
    Manages all adapters, versions, and metadata.
    Provides versioning, tracking, and lifecycle management.
    """
    
    def __init__(self, registry_path: str = "metadata/adapter_registry.json"):
        self.registry_path = Path(registry_path)
        self.families: Dict[str, AdapterFamily] = {}
        
        # Create directory if needed
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        self.load()
        
        logger.info(f"📚 AdapterRegistry loaded: {len(self.families)} families")
    
    def load(self):
        """Load registry from disk"""
        if not self.registry_path.exists():
            logger.info("Creating new adapter registry")
            self.save()
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            for family_data in data.get('families', []):
                family = AdapterFamily(
                    family_id=family_data['family_id'],
                    domain=family_data['domain'],
                    method=AdapterMethod(family_data['method']),
                    versions=[
                        AdapterVersion.from_dict(v) 
                        for v in family_data['versions']
                    ]
                )
                self.families[family.family_id] = family
            
            logger.info(f"✅ Loaded {len(self.families)} adapter families")
        
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            self.families = {}
    
    def save(self):
        """Save registry to disk"""
        try:
            data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "families": [
                    {
                        "family_id": family.family_id,
                        "domain": family.domain,
                        "method": family.method.value,
                        "versions": [v.to_dict() for v in family.versions]
                    }
                    for family in self.families.values()
                ]
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Registry saved: {self.registry_path}")
        
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def register_adapter(
        self,
        domain: str,
        method: AdapterMethod,
        adapter_path: str,
        base_model: str,
        rank: int,
        version: Optional[str] = None,
        **kwargs
    ) -> AdapterVersion:
        """
        Register new adapter or new version of existing adapter
        
        Args:
            domain: Domain/specialty
            method: LoRA/QLoRA/DoRA
            adapter_path: Path to adapter weights
            base_model: Base model name
            rank: LoRA rank
            version: Optional version string (auto-incremented if None)
            **kwargs: Additional metadata
            
        Returns:
            Created AdapterVersion
        """
        family_id = f"{domain}-{method.value}"
        
        # Get or create family
        if family_id not in self.families:
            self.families[family_id] = AdapterFamily(
                family_id=family_id,
                domain=domain,
                method=method
            )
        
        family = self.families[family_id]
        
        # Determine version
        if version is None:
            latest = family.get_latest_version()
            if latest:
                version = latest.increment_version('patch')
            else:
                version = "1.0.0"
        
        # Calculate checksums
        adapter_checksum = self._calculate_checksum(adapter_path)
        base_model_hash = self._calculate_model_hash(base_model)
        
        # Create adapter ID
        adapter_id = f"{domain}-{method.value}-v{version}"
        
        # Create new version
        new_version = AdapterVersion(
            adapter_id=adapter_id,
            version=version,
            domain=domain,
            method=method,
            rank=rank,
            base_model=base_model,
            base_model_hash=base_model_hash,
            adapter_path=adapter_path,
            adapter_checksum=adapter_checksum,
            **kwargs
        )
        
        # Add to family
        family.add_version(new_version)
        
        # Save registry
        self.save()
        
        logger.info(f"✅ Registered adapter: {adapter_id}")
        
        return new_version
    
    def get_adapter(self, adapter_id: str) -> Optional[AdapterVersion]:
        """Get adapter by ID"""
        for family in self.families.values():
            for version in family.versions:
                if version.adapter_id == adapter_id:
                    return version
        return None
    
    def list_adapters(
        self,
        domain: Optional[str] = None,
        method: Optional[AdapterMethod] = None,
        status: Optional[AdapterStatus] = None
    ) -> List[AdapterVersion]:
        """
        List adapters with optional filters
        
        Args:
            domain: Filter by domain
            method: Filter by method
            status: Filter by review status
            
        Returns:
            List of matching adapters
        """
        adapters = []
        
        for family in self.families.values():
            # Filter by domain/method
            if domain and family.domain != domain:
                continue
            if method and family.method != method:
                continue
            
            # Get versions
            for version in family.versions:
                if status and version.status != status:
                    continue
                adapters.append(version)
        
        return adapters
    
    def update_metrics(self, adapter_id: str, metrics: Dict[str, float]):
        """Update adapter metrics"""
        adapter = self.get_adapter(adapter_id)
        if adapter:
            adapter.metrics.update(metrics)
            self.save()
            logger.info(f"✅ Updated metrics for {adapter_id}")
        else:
            logger.warning(f"Adapter not found: {adapter_id}")
    
    def approve_adapter(self, adapter_id: str, approved_by: str, notes: Optional[str] = None):
        """Approve adapter for deployment"""
        adapter = self.get_adapter(adapter_id)
        if adapter:
            adapter.status = AdapterStatus.APPROVED
            adapter.approved_by = approved_by
            adapter.approved_at = datetime.now().isoformat()
            if notes:
                adapter.review_notes.append(notes)
            self.save()
            logger.info(f"✅ Approved adapter: {adapter_id} by {approved_by}")
        else:
            logger.warning(f"Adapter not found: {adapter_id}")
    
    def reject_adapter(self, adapter_id: str, reason: str):
        """Reject adapter"""
        adapter = self.get_adapter(adapter_id)
        if adapter:
            adapter.status = AdapterStatus.REJECTED
            adapter.review_notes.append(f"REJECTED: {reason}")
            self.save()
            logger.info(f"❌ Rejected adapter: {adapter_id}")
        else:
            logger.warning(f"Adapter not found: {adapter_id}")
    
    def _calculate_checksum(self, path: str) -> str:
        """Calculate SHA256 checksum of file/directory"""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return "unknown"
        
        hasher = hashlib.sha256()
        
        if path_obj.is_file():
            with open(path_obj, 'rb') as f:
                hasher.update(f.read())
        else:
            # Directory - hash all files
            for file_path in sorted(path_obj.rglob('*')):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        hasher.update(f.read())
        
        return hasher.hexdigest()[:16]
    
    def _calculate_model_hash(self, model_name: str) -> str:
        """Calculate hash for base model (placeholder)"""
        # In production, this would hash the actual model files
        return hashlib.sha256(model_name.encode()).hexdigest()[:16]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_adapters = sum(len(f.versions) for f in self.families.values())
        approved = sum(
            1 for f in self.families.values() 
            for v in f.versions 
            if v.status == AdapterStatus.APPROVED
        )
        pending = sum(
            1 for f in self.families.values()
            for v in f.versions
            if v.status == AdapterStatus.PENDING_REVIEW
        )
        
        return {
            "total_families": len(self.families),
            "total_adapters": total_adapters,
            "approved": approved,
            "pending_review": pending,
            "domains": list(set(f.domain for f in self.families.values())),
            "methods": list(set(f.method.value for f in self.families.values()))
        }


# Global registry instance
_registry = None

def get_adapter_registry() -> AdapterRegistry:
    """Get global adapter registry instance"""
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
    return _registry
