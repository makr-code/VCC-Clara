Project: VCC-Clara (AI System)
Language: Python (PyTorch, Transformers)

Purpose:
- Training and inference for ML models; support for QLoRA, multi-GPU fine-tuning and continuous learning pipelines.

What Copilot should help with:
- Scaffold training scripts, data loaders, and distributed training utilities.
- Propose reproducible experiment configs, WandB integration, and checkpointing strategies.

Coding style and constraints:
- Keep reproducibility: seed RNGs, log hyperparameters, and store minimal artifacts in `artifacts/` (not in git).
- Provide clear data processing steps; large datasets must be referenced in `docs/DATA_FILES_README.md` with download instructions.

Documentation duties (./docs):
- Add/maintain `docs/experiments.md` describing experiment structure, expected outputs, and evaluation metrics.
- Document model card information for each model produced (purpose, license, data sources).

Todo.md continuation:
- Add tasks like: "[ ] Add evaluation pipeline for model X — @ml-team" with exact commands to run.

Examples for Copilot prompts:
- "Create a PyTorch Lightning training script using Hugging Face Transformers for fine-tuning and WandB logging."
- "Add a script to convert raw dataset to tokenized dataset with caching and dataset splits."

Testing & CI:
- Include small-scale unit tests and reproducibility checks in CI; do not run full training in CI.

Ethics & licensing:
- Note dataset licenses and ensure `docs/datasets.md` covers permitted uses and privacy concerns.
