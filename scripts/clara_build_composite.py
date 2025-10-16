"""Erstellt (optionale) Composite-Adapter durch Kombination mehrerer LoRA/DoRA Adapter.

Phase: Skeleton

Strategien (geplant):
- additive: Elementweise Summierung der Delta-Gewichte
- weighted: Gewichtete Mischung (Argument --weights)
- sequential: Anwendung in definierter Reihenfolge (experimentell)

Aktueller Stand: Nur Argument-Parsing + Struktur. Die eigentliche Merge-Logik
muss implementiert werden, sobald Adapter-Verzeichnis-Layout konsolidiert ist.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import shutil
from pathlib import Path
from typing import List, Optional

# TODO: tatsächliche PEFT / safetensors Verarbeitung importieren
# from peft import PeftModel  # Beispiel


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Composite Adapter Builder (Skeleton)")
    p.add_argument("--adapters", nargs="+", required=True, help="Liste von Adapter IDs oder Pfaden")
    p.add_argument("--strategy", choices=["additive", "weighted", "sequential"], default="additive")
    p.add_argument("--weights", nargs="*", type=float, help="Gewichte für 'weighted' Strategie")
    p.add_argument("--out", required=True, help="Zielverzeichnis für Composite")
    p.add_argument("--dry-run", action="store_true", help="Nur Validierung, kein Schreiben")
    return p.parse_args()


def validate(adapters: List[str], strategy: str, weights: Optional[List[float]]):
    if strategy == "weighted":
        if not weights or len(weights) != len(adapters):
            raise ValueError("Für 'weighted' müssen Gewichte in gleicher Anzahl wie Adapter angegeben werden.")
        s = sum(weights)
        if abs(s - 1.0) > 1e-6:
            raise ValueError("Gewichte müssen sich zu 1.0 summieren.")


def compute_composite_id(adapters: List[str], strategy: str) -> str:
    raw = "|".join(adapters) + f"::{strategy}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def main() -> None:
    args = parse_args()
    validate(args.adapters, args.strategy, args.weights)
    composite_id = compute_composite_id(args.adapters, args.strategy)
    out_dir = Path(args.out) / composite_id

    if out_dir.exists():
        print(f"[INFO] Composite Verzeichnis existiert bereits: {out_dir}")
    else:
        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "id": composite_id,
        "adapters": args.adapters,
        "strategy": args.strategy,
        "weights": args.weights,
        "status": "PENDING_IMPLEMENTATION",
    }

    meta_path = out_dir / "composite.json"
    if not args.dry_run:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"[OK] Composite Metadaten geschrieben: {meta_path}")
    else:
        print("[DRY-RUN] Würde Composite anlegen:")
        print(json.dumps(meta, indent=2, ensure_ascii=False))

    # TODO: Merge-Logik implementieren (safetensors laden, Layer mappen, kombinieren, speichern)
    print("[TODO] Merge-Implementierung ausstehend.")

if __name__ == "__main__":
    main()
