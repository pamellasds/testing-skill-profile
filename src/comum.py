"""Utilitários compartilhados pelas fases (caminhos, seed, texto exibido, CSV, RUNLOG)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SEED = 20270402
MAX_CHARS = 8000  # texto exibido: idêntico para LLM e humanos (Fase 3)

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/raw/gitskills_sample/agent_skills_mandatory_only.db"
CONFIG, DERIVED, RESULTS, ANNOT = (ROOT / p for p in ("config", "data/derived", "results", "annotation"))
INSTRUMENT = ROOT / "instrument/instrumento.md"


def compile_terms(terms: list[str]) -> list[tuple[str, re.Pattern]]:
    """Uma regex por termo, aplicada ao texto em minúsculas. A fronteira inicial é checada fora da
    regex (lookbehind desliga a busca por prefixo literal do `re` e deixa tudo ~40x mais lento)."""
    return [(t, re.compile(rf"(?:{t.lower()})(?![a-z0-9])")) for t in terms]


def hits(compiled: list[tuple[str, re.Pattern]], text: str) -> list[str]:
    """Termos presentes no texto (já em minúsculas), com fronteira alfanumérica nas duas pontas."""
    return sorted(t for t, rx in compiled
                  if any(m.start() == 0 or not re.match(r"[a-z0-9]", text[m.start() - 1]) for m in rx.finditer(text)))


def display_text(name: str, description: str, content: str) -> str:
    body = content[:MAX_CHARS] + ("\n[... truncado em 8000 caracteres]" if len(content) > MAX_CHARS else "")
    return f"NAME: {name}\nDESCRIPTION: {description}\n\n{body}"


def blind_id(file_sha: str) -> str:
    """ID opaco e estável por conteúdo (não revela repo/sha)."""
    return "GS-" + hashlib.sha256(f"{SEED}:{file_sha}".encode()).hexdigest()[:8].upper()


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [float("nan")] * 2
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM: abre certo no Excel/LibreOffice
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_run(summary: dict, outputs: list[Path]) -> None:
    """Acrescenta uma entrada ao RUNLOG.md (convenção do protocolo)."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"\n## {now} — `python {' '.join(Path(a).name if i == 0 else a for i, a in enumerate(sys.argv))}`\n",
             f"- seed: {SEED}"]
    lines += [f"- {k}: {v}" for k, v in summary.items()]
    lines += ["- saídas:"] + [f"  - `{p.relative_to(ROOT)}`" for p in outputs]
    with (ROOT / "RUNLOG.md").open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
