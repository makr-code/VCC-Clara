"""
Knowledge Gap Detection and Tracking

Identifies potential knowledge gaps during LoRA adapter training and evaluation.
Tracks gaps in database for continuous improvement.

Features:
- Gap detection from evaluation failures
- Low-confidence prediction tracking
- Topic coverage analysis
- Database storage with metadata
- Integration with training pipeline
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class GapSeverity(str, Enum):
    """Knowledge gap severity level"""
    CRITICAL = "critical"  # Complete failure
    HIGH = "high"          # Low confidence (<50%)
    MEDIUM = "medium"      # Medium confidence (50-70%)
    LOW = "low"            # Borderline (70-85%)


class GapSource(str, Enum):
    """Source of gap detection"""
    EVALUATION = "evaluation"      # From LLM judge evaluation
    TRAINING = "training"          # From training metrics
    INFERENCE = "inference"        # From production inference
    USER_FEEDBACK = "user_feedback"  # From user reports


@dataclass
class KnowledgeGap:
    """
    Represents a detected knowledge gap
    
    Tracks areas where the adapter performs poorly or lacks knowledge.
    Used to guide future training data collection.
    
    Note:
        gap_id is a full UUID (e.g., "d4b8c1a2-5f3e-4a7b-9c2d-8e6f1a4b3c5d")
        for complete traceability and uniqueness across all systems.
    """
    gap_id: str  # Full UUID for traceability
    domain: str
    adapter_id: Optional[str] = None
    
    # Gap Details
    topic: str  # e.g., "Photovoltaik Genehmigungsverfahren"
    severity: GapSeverity = GapSeverity.MEDIUM
    source: GapSource = GapSource.EVALUATION
    
    # Context
    prompt: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    confidence_score: Optional[float] = None  # 0-1
    evaluation_score: Optional[float] = None  # 0-100
    
    # Metadata
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    detected_by: str = "system"
    tags: List[str] = field(default_factory=list)
    
    # Status
    status: str = "open"  # open, in_progress, resolved
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    # Training Data
    requires_training_data: bool = True
    suggested_data_query: Optional[str] = None
    training_samples_collected: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['source'] = self.source.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeGap':
        """Create from dict"""
        data['severity'] = GapSeverity(data['severity'])
        data['source'] = GapSource(data['source'])
        return cls(**data)
    
    def calculate_priority(self) -> float:
        """
        Calculate priority score for addressing this gap
        
        Returns:
            Priority score 0-100 (higher = more urgent)
        """
        severity_scores = {
            GapSeverity.CRITICAL: 40,
            GapSeverity.HIGH: 30,
            GapSeverity.MEDIUM: 20,
            GapSeverity.LOW: 10
        }
        
        score = severity_scores.get(self.severity, 10)
        
        # Boost priority if evaluation score is very low
        if self.evaluation_score is not None and self.evaluation_score < 50:
            score += 20
        
        # Boost priority if confidence is very low
        if self.confidence_score is not None and self.confidence_score < 0.3:
            score += 15
        
        # Cap at 100
        return min(score, 100)


class KnowledgeGapDetector:
    """
    Detects knowledge gaps from various sources
    
    Analyzes evaluation results, training metrics, and inference patterns
    to identify areas where the adapter lacks knowledge.
    """
    
    def __init__(
        self,
        critical_threshold: float = 50.0,  # Score below this = critical
        high_threshold: float = 60.0,      # Score below this = high severity
        medium_threshold: float = 70.0,    # Score below this = medium severity
        low_threshold: float = 85.0        # Score below this = low severity
    ):
        self.critical_threshold = critical_threshold
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold
        
        logger.info("📊 KnowledgeGapDetector initialized")
    
    def detect_from_evaluation(
        self,
        adapter_id: str,
        domain: str,
        evaluation_results: List[Any]  # List of EvaluationResult
    ) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps from evaluation results
        
        Args:
            adapter_id: Adapter being evaluated
            domain: Domain/specialty
            evaluation_results: List of evaluation results
            
        Returns:
            List of detected knowledge gaps
        """
        gaps = []
        
        for result in evaluation_results:
            # Skip if passed
            if result.passed:
                continue
            
            # Determine severity based on score
            severity = self._determine_severity(result.overall_score)
            
            # Extract topic from prompt or metadata
            topic = self._extract_topic(result.prompt)
            
            # Create gap with full UUID for traceability
            gap = KnowledgeGap(
                gap_id=str(uuid.uuid4()),
                domain=domain,
                adapter_id=adapter_id,
                topic=topic,
                severity=severity,
                source=GapSource.EVALUATION,
                prompt=result.prompt,
                expected_output=result.expected_output,
                actual_output=result.adapter_output,
                evaluation_score=result.overall_score,
                detected_by="llm-judge",
                tags=self._extract_tags(result.prompt, result.expected_output)
            )
            
            # Generate suggested query for training data
            gap.suggested_data_query = self._generate_data_query(topic, domain)
            
            gaps.append(gap)
        
        logger.info(f"🔍 Detected {len(gaps)} knowledge gaps from evaluation")
        
        return gaps
    
    def detect_from_training_metrics(
        self,
        adapter_id: str,
        domain: str,
        training_metrics: Dict[str, Any]
    ) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps from training metrics
        
        Analyzes loss curves, perplexity, and other metrics to identify
        topics where the model struggles during training.
        
        Args:
            adapter_id: Adapter being trained
            domain: Domain/specialty
            training_metrics: Training metrics dict
            
        Returns:
            List of detected knowledge gaps
        """
        gaps = []
        
        # Example: High final perplexity indicates knowledge gaps
        perplexity = training_metrics.get('final_perplexity', 0)
        if perplexity > 10:  # Threshold
            gap = KnowledgeGap(
                gap_id=str(uuid.uuid4()),
                domain=domain,
                adapter_id=adapter_id,
                topic=f"{domain} general knowledge",
                severity=GapSeverity.MEDIUM,
                source=GapSource.TRAINING,
                detected_by="training-metrics",
                tags=["high-perplexity", "general"]
            )
            gap.suggested_data_query = f"{domain} comprehensive overview"
            gaps.append(gap)
        
        # Example: Low accuracy on validation set
        val_accuracy = training_metrics.get('val_accuracy', 1.0)
        if val_accuracy < 0.7:
            gap = KnowledgeGap(
                gap_id=str(uuid.uuid4()),
                domain=domain,
                adapter_id=adapter_id,
                topic=f"{domain} validation topics",
                severity=GapSeverity.HIGH,
                source=GapSource.TRAINING,
                detected_by="training-metrics",
                tags=["low-accuracy", "validation"]
            )
            gaps.append(gap)
        
        if gaps:
            logger.info(f"🔍 Detected {len(gaps)} knowledge gaps from training metrics")
        
        return gaps
    
    def analyze_topic_coverage(
        self,
        domain: str,
        training_data: List[Dict],
        required_topics: List[str]
    ) -> List[KnowledgeGap]:
        """
        Analyze topic coverage in training data
        
        Identifies topics that are underrepresented in training data.
        
        Args:
            domain: Domain/specialty
            training_data: List of training samples
            required_topics: List of topics that should be covered
            
        Returns:
            List of knowledge gaps for missing topics
        """
        gaps = []
        
        # Count samples per topic (simplified - in production, use NLP)
        topic_counts = {}
        for sample in training_data:
            text = sample.get('text', '')
            for topic in required_topics:
                if topic.lower() in text.lower():
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Identify underrepresented topics
        min_samples = 10  # Minimum samples per topic
        for topic in required_topics:
            count = topic_counts.get(topic, 0)
            if count < min_samples:
                severity = GapSeverity.CRITICAL if count == 0 else GapSeverity.HIGH
                
                gap = KnowledgeGap(
                    gap_id=str(uuid.uuid4()),
                    domain=domain,
                    topic=topic,
                    severity=severity,
                    source=GapSource.TRAINING,
                    detected_by="coverage-analysis",
                    tags=["coverage", "underrepresented"],
                    suggested_data_query=f"{domain} {topic}"
                )
                gap.training_samples_collected = count
                gaps.append(gap)
        
        if gaps:
            logger.info(f"🔍 Detected {len(gaps)} topic coverage gaps")
        
        return gaps
    
    def _determine_severity(self, score: float) -> GapSeverity:
        """Determine gap severity from evaluation score"""
        if score < self.critical_threshold:
            return GapSeverity.CRITICAL
        elif score < self.high_threshold:
            return GapSeverity.HIGH
        elif score < self.medium_threshold:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _extract_topic(self, prompt: str) -> str:
        """Extract topic from prompt (simplified)"""
        # In production, use NLP to extract key topics
        # For now, take first few words
        words = prompt.split()[:5]
        return ' '.join(words) + '...'
    
    def _extract_tags(self, prompt: str, expected_output: str) -> List[str]:
        """Extract relevant tags from text"""
        tags = []
        
        # Extract legal references (e.g., §123)
        import re
        legal_refs = re.findall(r'§\s*\d+', prompt + ' ' + expected_output)
        tags.extend([ref.replace(' ', '') for ref in legal_refs[:3]])
        
        # Add domain-specific keywords
        keywords = ['Genehmigung', 'Antrag', 'Verfahren', 'Photovoltaik', 'Baurecht']
        for keyword in keywords:
            if keyword.lower() in (prompt + ' ' + expected_output).lower():
                tags.append(keyword.lower())
        
        return tags[:5]  # Limit to 5 tags
    
    def _generate_data_query(self, topic: str, domain: str) -> str:
        """Generate search query for collecting training data"""
        return f"{domain} {topic}"


class KnowledgeGapDatabase:
    """
    Database for storing and managing knowledge gaps
    
    Persists gaps to disk and provides query capabilities.
    """
    
    def __init__(self, db_path: str = "data/knowledge_gaps/gaps.jsonl"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📚 KnowledgeGapDatabase initialized: {self.db_path}")
    
    def add_gap(self, gap: KnowledgeGap):
        """Add knowledge gap to database"""
        try:
            with open(self.db_path, 'a') as f:
                f.write(json.dumps(gap.to_dict(), ensure_ascii=False) + '\n')
            
            logger.info(f"✅ Added gap to database: {gap.gap_id}")
        
        except Exception as e:
            logger.error(f"❌ Failed to add gap: {e}")
    
    def add_gaps(self, gaps: List[KnowledgeGap]):
        """Add multiple knowledge gaps"""
        for gap in gaps:
            self.add_gap(gap)
        
        logger.info(f"✅ Added {len(gaps)} gaps to database")
    
    def get_gaps(
        self,
        domain: Optional[str] = None,
        adapter_id: Optional[str] = None,
        severity: Optional[GapSeverity] = None,
        status: str = "open"
    ) -> List[KnowledgeGap]:
        """
        Get knowledge gaps with filters
        
        Args:
            domain: Filter by domain
            adapter_id: Filter by adapter
            severity: Filter by severity
            status: Filter by status (default: open)
            
        Returns:
            List of matching gaps
        """
        if not self.db_path.exists():
            return []
        
        gaps = []
        
        try:
            with open(self.db_path, 'r') as f:
                for line in f:
                    gap_data = json.loads(line)
                    gap = KnowledgeGap.from_dict(gap_data)
                    
                    # Apply filters
                    if domain and gap.domain != domain:
                        continue
                    if adapter_id and gap.adapter_id != adapter_id:
                        continue
                    if severity and gap.severity != severity:
                        continue
                    if status and gap.status != status:
                        continue
                    
                    gaps.append(gap)
        
        except Exception as e:
            logger.error(f"Failed to read gaps: {e}")
        
        return gaps
    
    def get_priority_gaps(self, top_n: int = 10) -> List[KnowledgeGap]:
        """
        Get highest priority gaps for addressing
        
        Args:
            top_n: Number of top gaps to return
            
        Returns:
            List of gaps sorted by priority
        """
        gaps = self.get_gaps(status="open")
        
        # Sort by priority
        gaps.sort(key=lambda g: g.calculate_priority(), reverse=True)
        
        return gaps[:top_n]
    
    def update_gap_status(
        self,
        gap_id: str,
        status: str,
        resolution_notes: Optional[str] = None
    ):
        """Update gap status"""
        # Read all gaps
        gaps = self.get_gaps(status=None)  # Get all statuses
        
        # Update matching gap
        updated = False
        for gap in gaps:
            if gap.gap_id == gap_id:
                gap.status = status
                if status == "resolved":
                    gap.resolved_at = datetime.now().isoformat()
                if resolution_notes:
                    gap.resolution_notes = resolution_notes
                updated = True
                break
        
        if updated:
            # Rewrite database
            self._rewrite_database(gaps)
            logger.info(f"✅ Updated gap status: {gap_id} -> {status}")
        else:
            logger.warning(f"Gap not found: {gap_id}")
    
    def _rewrite_database(self, gaps: List[KnowledgeGap]):
        """Rewrite entire database (for updates)"""
        with open(self.db_path, 'w') as f:
            for gap in gaps:
                f.write(json.dumps(gap.to_dict(), ensure_ascii=False) + '\n')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge gap statistics"""
        gaps = self.get_gaps(status=None)  # All statuses
        
        if not gaps:
            return {
                "total_gaps": 0,
                "open_gaps": 0,
                "resolved_gaps": 0
            }
        
        stats = {
            "total_gaps": len(gaps),
            "open_gaps": sum(1 for g in gaps if g.status == "open"),
            "resolved_gaps": sum(1 for g in gaps if g.status == "resolved"),
            "in_progress": sum(1 for g in gaps if g.status == "in_progress"),
            "by_severity": {},
            "by_domain": {},
            "by_source": {},
            "average_priority": sum(g.calculate_priority() for g in gaps) / len(gaps)
        }
        
        # Severity distribution
        for gap in gaps:
            severity = gap.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
        
        # Domain distribution
        for gap in gaps:
            domain = gap.domain
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        
        # Source distribution
        for gap in gaps:
            source = gap.source.value
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        return stats


# Global instance
_gap_db = None

def get_knowledge_gap_database() -> KnowledgeGapDatabase:
    """Get global knowledge gap database instance"""
    global _gap_db
    if _gap_db is None:
        _gap_db = KnowledgeGapDatabase()
    return _gap_db
