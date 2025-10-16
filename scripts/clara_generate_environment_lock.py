#!/usr/bin/env python3
"""CLARA Environment Lock Generator

Erzeugt reproduzierbare Snapshot-Dateien:
  - environment/lock_meta.json : Meta-Informationen (Zeit, Python Version, GPU, CUDA, Commit falls git)
  - environment/pip_freeze.txt : Paketliste
  - environment/code_hashes.json : SHA256 Hashes ausgewählter Verzeichnisse/Dateien

Verwendung:
  python scripts/clara_generate_environment_lock.py \
      --paths src scripts metadata/adapter_registry.json requirements.txt

Optionen:
  --paths <pfade...>    Pfade/Dateien deren Hash aufgenommen wird
  --git                 Git Commit Hash (falls Repository) erfassen
  --no-gpu              GPU Abfrage unterdrücken
  --extra <key=value>   Zusätzliche Meta-Einträge

"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_path(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if path.is_file():
        result[str(path)] = sha256_file(path)
    else:
        for p in sorted(path.rglob('*')):
            if p.is_file():
                try:
                    result[str(p)] = sha256_file(p)
                except Exception:
                    continue
    return result


def collect_gpu_info() -> Dict[str, str]:
    info: Dict[str, str] = {}
    try:
        import torch  # type: ignore
        info['cuda_available'] = str(torch.cuda.is_available())
        if torch.cuda.is_available():
            info['cuda_device_count'] = str(torch.cuda.device_count())
            names = []
            for i in range(torch.cuda.device_count()):
                try:
                    names.append(torch.cuda.get_device_name(i))
                except Exception:
                    names.append(f"<unresolved:{i}>")
            info['cuda_devices'] = names
            info['cuda_version'] = getattr(torch.version, 'cuda', 'unknown')
    except Exception:
        info['cuda_available'] = 'import_error'
    return info


def git_commit() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "<no-git>"


def pip_freeze() -> str:
    try:
        return subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], stderr=subprocess.DEVNULL).decode()
    except Exception as e:
        return f"<pip-freeze-error:{e}>"


def parse_extra(pairs: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for pair in pairs:
        if '=' in pair:
            k, v = pair.split('=', 1)
            out[k.strip()] = v.strip()
    return out


def main():
    parser = argparse.ArgumentParser(description="Generate reproducible environment lock snapshots")
    parser.add_argument('--paths', nargs='*', default=['src', 'scripts', 'requirements.txt'], help='Pfade/Dateien für Code Hashes')
    parser.add_argument('--output-dir', default='environment', help='Zielverzeichnis')
    parser.add_argument('--git', action='store_true', help='Git Commit Hash erfassen')
    parser.add_argument('--no-gpu', action='store_true', help='GPU Info nicht erfassen')
    parser.add_argument('--extra', nargs='*', default=[], help='Zusätzliche key=value Metadaten')
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    meta: Dict[str, object] = {
        'created': datetime.utcnow().isoformat() + 'Z',
        'python_version': sys.version.replace('\n', ' '),
        'platform': platform.platform(),
        'executable': sys.executable,
    }
    if args.git:
        meta['git_commit'] = git_commit()

    if not args.no_gpu:
        meta['gpu'] = collect_gpu_info()

    extra = parse_extra(args.extra)
    if extra:
        meta['extra'] = extra

    # Code Hashes
    combined_hashes: Dict[str, str] = {}
    for p in args.paths:
        path_obj = Path(p)
        if path_obj.exists():
            combined_hashes.update(sha256_path(path_obj))
        else:
            combined_hashes[p] = '<missing>'

    # Aggregierter Root Hash
    root_h = hashlib.sha256()
    for k in sorted(combined_hashes.keys()):
        root_h.update(k.encode())
        root_h.update(combined_hashes[k].encode())
    meta['code_root_hash'] = root_h.hexdigest()

    # Schreiben
    (out_dir / 'lock_meta.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    (out_dir / 'code_hashes.json').write_text(json.dumps(combined_hashes, indent=2, ensure_ascii=False), encoding='utf-8')
    (out_dir / 'pip_freeze.txt').write_text(pip_freeze(), encoding='utf-8')

    print(f"✅ Environment Lock erzeugt in {out_dir}")


if __name__ == '__main__':  # pragma: no cover
    main()
