"""
Base Trainer Abstract Class

All trainers (LoRA, QLoRA, Continuous Learning) inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class BaseTrainer(ABC):
    """
    Base class for all trainers
    
    Implements Template Method pattern for training pipeline:
    1. validate() - Validate configuration
    2. train() - Execute training
    3. save() - Save trained model/adapter
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize trainer with configuration
        
        Args:
            config: Training configuration dictionary
        """
        self.config = config
        self.output_dir = Path(config.get("training", {}).get("output_dir", "models/outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate training setup before starting
        
        Returns:
            True if validation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def train(self) -> Dict[str, Any]:
        """
        Train model and return results
        
        Returns:
            Dictionary with:
            - adapter_path: str - Path to trained adapter
            - metrics: Dict[str, float] - Training metrics
        """
        pass
    
    def get_required_config_keys(self) -> list:
        """
        Get list of required config keys
        
        Override in subclasses for specific requirements
        
        Returns:
            List of required config keys
        """
        return ["model_name", "dataset_path", "num_epochs"]
