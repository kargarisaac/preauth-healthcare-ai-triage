from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime

import tiktoken

from preauth_system.utils import get_config

_CFG = get_config()


def _resolve_kb_dir() -> Path:
    rag_cfg = _CFG.get("rag", {}) if isinstance(_CFG, dict) else {}
    kb_dirs: List[str] = rag_cfg.get("kb_dirs", []) or []
    for d in [Path(p) for p in kb_dirs]:
        if d.exists():
            return d
    return Path("preauth_system/rag/kb")


def _count_tokens(text: str, model: str = "gpt-5") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def build_kb_token_csv() -> Path:
    kb_dir = _resolve_kb_dir()
    out_path = kb_dir / "kb_token_counts.csv"
    rows: List[Tuple[str, int, int, str]] = []

    for md_path in kb_dir.rglob("*.md"):
        try:
            text = md_path.read_text(encoding="utf-8")
            num_tokens = _count_tokens(text)
            num_chars = len(text)
            mtime = datetime.fromtimestamp(md_path.stat().st_mtime).isoformat()
            rows.append((str(md_path), num_tokens, num_chars, mtime))
        except Exception:
            rows.append((str(md_path), 0, 0, datetime.utcnow().isoformat()))

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "num_tokens", "num_chars", "last_modified"])
        writer.writerows(rows)

    return out_path


if __name__ == "__main__":
    path = build_kb_token_csv()
    print(f"KB token counts written to {path}")
