"""
LLM-as-Judge Evaluation System

Automated adapter quality evaluation using an LLM as judge.

Features:
- Automated evaluation of adapter outputs
- Comparison with expected outputs
- Multi-criteria scoring
- Quality regression detection
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EvaluationCriteria:
    """Criteria for LLM evaluation"""
    name: str
    description: str
    weight: float = 1.0
    max_score: float = 10.0


@dataclass
class EvaluationResult:
    """Result from LLM judge evaluation"""
    sample_id: str
    adapter_id: str
    
    # Outputs
    prompt: str
    adapter_output: str
    expected_output: str
    
    # Scores
    overall_score: float  # 0-100
    criteria_scores: Dict[str, float]  # Per-criterion scores
    
    # Evaluation Details
    judge_reasoning: str
    passed: bool
    
    # Metadata
    evaluated_at: str
    judge_model: str
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationResult':
        """Create from dict"""
        return cls(**data)


class LLMJudge:
    """
    LLM-as-Judge for Adapter Evaluation
    
    Uses an LLM to evaluate adapter outputs against golden dataset.
    Provides automated quality scoring and comparison.
    """
    
    def __init__(
        self,
        judge_model: str = "gpt-4",
        pass_threshold: float = 70.0
    ):
        """
        Initialize LLM Judge
        
        Args:
            judge_model: Model to use as judge (e.g., gpt-4, claude-3)
            pass_threshold: Minimum score to pass (0-100)
        """
        self.judge_model = judge_model
        self.pass_threshold = pass_threshold
        
        # Default evaluation criteria
        self.criteria = [
            EvaluationCriteria(
                name="accuracy",
                description="Factual correctness and accuracy of information",
                weight=2.0
            ),
            EvaluationCriteria(
                name="relevance",
                description="Relevance to the prompt and context",
                weight=1.5
            ),
            EvaluationCriteria(
                name="style",
                description="Appropriate tone, formality, and language style",
                weight=1.0
            ),
            EvaluationCriteria(
                name="completeness",
                description="Coverage of all required points",
                weight=1.5
            ),
            EvaluationCriteria(
                name="coherence",
                description="Logical flow and coherence",
                weight=1.0
            )
        ]
        
        logger.info(f"🧑‍⚖️ LLM Judge initialized: {judge_model}")
    
    async def evaluate_sample(
        self,
        adapter_id: str,
        sample_id: str,
        prompt: str,
        adapter_output: str,
        expected_output: str,
        criteria: Optional[List[EvaluationCriteria]] = None
    ) -> EvaluationResult:
        """
        Evaluate a single adapter output
        
        Args:
            adapter_id: Adapter being evaluated
            sample_id: Sample ID from golden dataset
            prompt: Input prompt
            adapter_output: Output from adapter
            expected_output: Expected output from golden dataset
            criteria: Optional custom criteria
            
        Returns:
            EvaluationResult with scores and reasoning
        """
        if criteria is None:
            criteria = self.criteria
        
        # Build evaluation prompt
        eval_prompt = self._build_evaluation_prompt(
            prompt, adapter_output, expected_output, criteria
        )
        
        # Call LLM judge
        judge_response = await self._call_judge(eval_prompt)
        
        # Parse response
        scores = self._parse_judge_response(judge_response, criteria)
        
        # Calculate overall score
        total_weight = sum(c.weight for c in criteria)
        overall_score = sum(
            scores.get(c.name, 0) * c.weight 
            for c in criteria
        ) / total_weight * 10  # Scale to 0-100
        
        # Determine pass/fail
        passed = overall_score >= self.pass_threshold
        
        result = EvaluationResult(
            sample_id=sample_id,
            adapter_id=adapter_id,
            prompt=prompt,
            adapter_output=adapter_output,
            expected_output=expected_output,
            overall_score=overall_score,
            criteria_scores=scores,
            judge_reasoning=judge_response,
            passed=passed,
            evaluated_at=datetime.now().isoformat(),
            judge_model=self.judge_model
        )
        
        logger.info(f"📊 Evaluated {sample_id}: {overall_score:.1f}/100 ({'PASS' if passed else 'FAIL'})")
        
        return result
    
    async def evaluate_adapter(
        self,
        adapter_id: str,
        golden_dataset: Any,  # GoldenDataset
        adapter_inference_fn: Any  # Async callable that runs inference
    ) -> Dict[str, Any]:
        """
        Evaluate adapter against golden dataset
        
        Args:
            adapter_id: Adapter to evaluate
            golden_dataset: Golden dataset to test against
            adapter_inference_fn: Async function to get adapter output
                                 signature: async fn(prompt) -> output
            
        Returns:
            Dict with evaluation summary, detailed results, and knowledge gaps
        """
        logger.info(f"🧑‍⚖️ Evaluating adapter {adapter_id} on {golden_dataset.dataset_id}")
        
        results = []
        
        for sample in golden_dataset.samples:
            # Get adapter output
            try:
                adapter_output = await adapter_inference_fn(sample.prompt, sample.context)
            except Exception as e:
                logger.error(f"Inference failed for {sample.sample_id}: {e}")
                continue
            
            # Evaluate output
            result = await self.evaluate_sample(
                adapter_id=adapter_id,
                sample_id=sample.sample_id,
                prompt=sample.prompt,
                adapter_output=adapter_output,
                expected_output=sample.expected_output,
                criteria=self.criteria
            )
            
            results.append(result)
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        summary['adapter_id'] = adapter_id
        summary['golden_dataset_id'] = golden_dataset.dataset_id
        summary['evaluated_at'] = datetime.now().isoformat()
        
        # Detect knowledge gaps from failed evaluations
        from .knowledge_gaps import KnowledgeGapDetector
        gap_detector = KnowledgeGapDetector()
        knowledge_gaps = gap_detector.detect_from_evaluation(
            adapter_id=adapter_id,
            domain=golden_dataset.domain,
            evaluation_results=results
        )
        
        # Add gaps to summary
        summary['knowledge_gaps_detected'] = len(knowledge_gaps)
        
        return {
            "summary": summary,
            "results": [r.to_dict() for r in results],
            "knowledge_gaps": [g.to_dict() for g in knowledge_gaps]
        }
    
    def _build_evaluation_prompt(
        self,
        prompt: str,
        adapter_output: str,
        expected_output: str,
        criteria: List[EvaluationCriteria]
    ) -> str:
        """Build prompt for LLM judge"""
        criteria_text = "\n".join([
            f"{i+1}. {c.name.upper()} ({c.weight}x weight): {c.description}"
            for i, c in enumerate(criteria)
        ])
        
        return f"""You are an expert evaluator of AI-generated text. Evaluate the following adapter output.

INPUT PROMPT:
{prompt}

ADAPTER OUTPUT:
{adapter_output}

EXPECTED OUTPUT (Reference):
{expected_output}

EVALUATION CRITERIA:
{criteria_text}

For each criterion, provide a score from 0-10 and brief reasoning.
Then provide an overall assessment.

Respond in JSON format:
{{
    "scores": {{
        "accuracy": <score>,
        "relevance": <score>,
        "style": <score>,
        "completeness": <score>,
        "coherence": <score>
    }},
    "reasoning": {{
        "accuracy": "<brief explanation>",
        "relevance": "<brief explanation>",
        "style": "<brief explanation>",
        "completeness": "<brief explanation>",
        "coherence": "<brief explanation>"
    }},
    "overall_assessment": "<overall evaluation>"
}}"""
    
    async def _call_judge(self, prompt: str) -> str:
        """
        Call LLM judge (placeholder for actual LLM API call)
        
        In production, this would call OpenAI/Anthropic/etc. API
        """
        # Placeholder: Return mock response
        # In production: Call actual LLM API
        logger.info(f"🔮 Calling {self.judge_model} judge...")
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Mock response (in production, parse actual LLM response)
        mock_response = {
            "scores": {
                "accuracy": 8.5,
                "relevance": 9.0,
                "style": 7.5,
                "completeness": 8.0,
                "coherence": 8.5
            },
            "reasoning": {
                "accuracy": "Information is factually correct",
                "relevance": "Highly relevant to the prompt",
                "style": "Appropriate formal style",
                "completeness": "Covers most required points",
                "coherence": "Logical and well-structured"
            },
            "overall_assessment": "High-quality output with minor style improvements possible"
        }
        
        return json.dumps(mock_response)
    
    def _parse_judge_response(
        self,
        response: str,
        criteria: List[EvaluationCriteria]
    ) -> Dict[str, float]:
        """Parse LLM judge response to extract scores"""
        try:
            data = json.loads(response)
            return data.get("scores", {})
        except Exception as e:
            logger.error(f"Failed to parse judge response: {e}")
            return {c.name: 5.0 for c in criteria}  # Default middle score
    
    def _calculate_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Calculate summary statistics from evaluation results"""
        if not results:
            return {
                "total_samples": 0,
                "pass_rate": 0.0,
                "average_score": 0.0
            }
        
        passed_count = sum(1 for r in results if r.passed)
        
        return {
            "total_samples": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "pass_rate": passed_count / len(results) * 100,
            "average_score": sum(r.overall_score for r in results) / len(results),
            "min_score": min(r.overall_score for r in results),
            "max_score": max(r.overall_score for r in results),
            "criteria_averages": self._average_criteria_scores(results)
        }
    
    def _average_criteria_scores(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """Calculate average scores per criterion"""
        if not results:
            return {}
        
        criteria_sums = {}
        for result in results:
            for criterion, score in result.criteria_scores.items():
                criteria_sums[criterion] = criteria_sums.get(criterion, 0) + score
        
        return {
            criterion: total / len(results)
            for criterion, total in criteria_sums.items()
        }


class AdapterEvaluationManager:
    """
    Manages adapter evaluations and tracks results
    
    Coordinates LLM judge, golden datasets, and result storage.
    """
    
    def __init__(
        self,
        results_dir: str = "data/evaluation_results",
        judge_model: str = "gpt-4"
    ):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.judge = LLMJudge(judge_model=judge_model)
        
        logger.info(f"📊 AdapterEvaluationManager initialized")
    
    async def evaluate_adapter(
        self,
        adapter_id: str,
        golden_dataset_id: str,
        adapter_inference_fn: Any
    ) -> str:
        """
        Evaluate adapter and save results
        
        Args:
            adapter_id: Adapter to evaluate
            golden_dataset_id: Golden dataset to use
            adapter_inference_fn: Function to run inference
            
        Returns:
            Path to evaluation results file
        """
        from .golden_dataset import get_golden_dataset_manager
        
        # Get golden dataset
        dataset_manager = get_golden_dataset_manager()
        golden_dataset = dataset_manager.get_dataset(golden_dataset_id)
        
        if not golden_dataset:
            raise ValueError(f"Golden dataset not found: {golden_dataset_id}")
        
        # Run evaluation
        evaluation = await self.judge.evaluate_adapter(
            adapter_id=adapter_id,
            golden_dataset=golden_dataset,
            adapter_inference_fn=adapter_inference_fn
        )
        
        # Save results
        results_file = self._save_results(adapter_id, evaluation)
        
        logger.info(f"✅ Evaluation complete: {results_file}")
        
        return str(results_file)
    
    def _save_results(self, adapter_id: str, evaluation: Dict) -> Path:
        """Save evaluation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{adapter_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(evaluation, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def get_evaluation_history(self, adapter_id: str) -> List[Dict]:
        """Get evaluation history for an adapter"""
        history = []
        
        pattern = f"{adapter_id}_*.json"
        for results_file in self.results_dir.glob(pattern):
            try:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                history.append(data)
            except Exception as e:
                logger.error(f"Failed to load {results_file}: {e}")
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x['summary']['evaluated_at'], reverse=True)
        
        return history


# Global instance
_eval_manager = None

def get_evaluation_manager() -> AdapterEvaluationManager:
    """Get global evaluation manager instance"""
    global _eval_manager
    if _eval_manager is None:
        _eval_manager = AdapterEvaluationManager()
    return _eval_manager
