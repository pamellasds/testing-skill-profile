"""Piloto: checklist Practical Test Pyramid (Vocke/Fowler) → Testing Skill Profile.

Um unico script. Carrega as 3 skills de examples_pyramid (+ extras opcionais do
pool test_types) e classifica via Mistral. Ver guideline.md.

Uso:
    python data/test_pyramid_skills/run_pilot.py
    python data/test_pyramid_skills/run_pilot.py --pyramid-only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
EXAMPLES_INDEX = ROOT / "data/test_types_filter/examples_pyramid/index.json"
CANDIDATES = ROOT / "data/test_types_filter/test_types_candidates.json"
OUT = HERE / "pilot_results.json"
API_URL = "https://api.mistral.ai/v1/chat/completions"
MAX_CONTENT = 14000

SKILLS = [
    "unit", "integration", "contract", "ui",
    "end_to_end", "acceptance", "exploratory", "automation",
]

PROMPT = """Voce anota agent skills quanto a TESTING SKILLS evidenciadas no texto.
Referencia: Practical Test Pyramid (Ham Vocke / Martin Fowler).
NAO avalie qualidade nem proficiencia. Pergunta: ha evidencia dessa skill?
Respostas: YES | NO | UNCERTAIN. Todo YES exige quote VERBATIM (substring do content, sem "...").

repo: {repo}
path: {path}
name: {name}
content:
\"\"\"
{content}
\"\"\"

Retorne APENAS JSON:
{{
  "artifact_type": "test_guidance_skill | not_test_related | uncertain",
  "confidence": "high | medium | low",
  "checklist": {{
    "unit": {{"answer": "YES|NO|UNCERTAIN", "evidence": {{"quote": "...", "reason": "..."}} | null}},
    "integration": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "contract": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "ui": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "end_to_end": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "acceptance": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "exploratory": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
    "automation": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
  }}
}}

Criterios (orientacao no texto):
- unit: unidade isolada; escopo restrito; mocks/doubles; sem sistema completo
- integration: multiplos componentes; interacao real; DB/servico; app↔contract↔chain
- contract: contrato consumidor/provedor; CDC; ferramenta/definicao de contrato
- ui: interface GUI OU API/CLI; acoes de usuario; automation de UI quando cabivel
- end_to_end: fluxo sistema integrado via interface externa; multiplos componentes
- acceptance: feature usuario/negocio; cenario de aceitacao (ORTOGONAL a piramide — nao forcar como topo)
- exploratory: SO com evidencia explicita (exploratory/session-based); nao inferir de texto informal
- automation: test runner / CI/CD / executavel sem intervencao manual

Se answer != YES, evidence=null. Se nao for skill de teste, artifact_type=not_test_related e checklist NO.
"""


class KeyRotator:
    def __init__(self, env_path: Path):
        keys = [v for k, v in dotenv_values(env_path).items() if k.startswith("MISTRAL_") and v]
        if not keys:
            raise RuntimeError(f"sem MISTRAL_* em {env_path}")
        self._keys, self._i = keys, 0

    @property
    def current(self) -> str:
        return self._keys[self._i]

    def rotate(self) -> None:
        self._i = (self._i + 1) % len(self._keys)

    def __len__(self) -> int:
        return len(self._keys)


def parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            a, b = cleaned.find("{"), cleaned.rfind("}")
            return json.loads(cleaned[a : b + 1])


def call_mistral(prompt: str, model: str, rotator: KeyRotator) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    err = None
    for attempt in range(8):
        headers = {"Authorization": f"Bearer {rotator.current}", "Content-Type": "application/json"}
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            err = exc
            time.sleep(min(2 ** attempt, 30))
            continue
        if resp.status_code == 429:
            rotator.rotate()
            time.sleep(min(2 ** attempt, 30))
            continue
        if resp.status_code in (401, 403):
            rotator.rotate()
            err = RuntimeError(f"HTTP {resp.status_code}")
            continue
        if resp.status_code >= 500:
            err = RuntimeError(f"HTTP {resp.status_code}")
            time.sleep(min(2 ** attempt, 30))
            continue
        resp.raise_for_status()
        try:
            return parse_json(resp.json()["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            err = exc
            prompt += "\n\nATENCAO: retorne SOMENTE JSON valido."
            time.sleep(2)
    raise RuntimeError(f"falha Mistral: {err}")


_WS = re.compile(r"\s+")
_MD = re.compile(r"[`*_#|]")


def norm(t: str) -> str:
    return _WS.sub(" ", _MD.sub("", t)).strip().lower()


def verbatim(quote: str, content: str) -> bool:
    return bool(quote) and norm(quote) in norm(content)


def derive(checklist: dict, content: str) -> tuple[list[str], list[str], dict]:
    evidenced, dropped, profile = [], [], {}
    for skill in SKILLS:
        cell = (checklist or {}).get(skill) or {}
        ans = str(cell.get("answer", "NO")).upper()
        if ans != "YES":
            profile[skill] = "uncertain" if ans == "UNCERTAIN" else "no"
            continue
        quote = ((cell.get("evidence") or {}) if isinstance(cell.get("evidence"), dict) else {}).get("quote", "")
        if verbatim(quote, content):
            evidenced.append(skill)
            profile[skill] = "yes"
        else:
            dropped.append(skill)
            profile[skill] = "dropped_quote"
    return evidenced, dropped, profile


def load_items(pyramid_only: bool, max_skills: int) -> list[dict]:
    items = []
    for e in json.loads(EXAMPLES_INDEX.read_text()):
        content = (ROOT / "data/test_types_filter" / e["skill_file"]).read_text(encoding="utf-8", errors="replace")
        items.append({
            "source": "examples_pyramid", "hint": e["layer"],
            "repo": e["repo"], "path": e["path"], "name": e.get("name", ""),
            "content": content,
        })
    if not pyramid_only and CANDIDATES.exists():
        pool = json.loads(CANDIDATES.read_text())
        for layer in ("fuzz_property", "fork", "regression"):
            cands = sorted(
                [i for i in pool if layer in i.get("matched_layers", [])],
                key=lambda i: (
                    0 if any(t in f"{i.get('name','')} {i.get('path','')}".lower()
                             for t in ("blockchain", "solidity", "foundry", "forge", "smart", "contract"))
                    else 1,
                    len(i.get("content", "")),
                ),
            )
            if cands:
                i = cands[0]
                items.append({
                    "source": "candidates", "hint": layer,
                    "repo": i["repo"], "path": i["path"], "name": i.get("name", ""),
                    "content": i.get("content", ""),
                })
    return items[:max_skills]


def classify(item: dict, model: str, rotator: KeyRotator, retries: int) -> dict:
    content = item["content"][:MAX_CONTENT]
    prompt = PROMPT.format(
        repo=item["repo"], path=item["path"], name=item.get("name", ""), content=content,
    )
    resp, issues = {}, ["not attempted"]
    for _ in range(retries + 1):
        resp = call_mistral(prompt, model, rotator)
        cl = resp.get("checklist") or {}
        issues = [
            s for s in SKILLS
            if str((cl.get(s) or {}).get("answer", "")).upper() == "YES"
            and not verbatim(((cl.get(s) or {}).get("evidence") or {}).get("quote", "")
                             if isinstance((cl.get(s) or {}).get("evidence"), dict) else "", content)
        ]
        if not issues:
            break
        prompt += f"\n\nATENCAO: quotes invalidas em {issues}. Use substring literal ou mude para NO/UNCERTAIN."
    evidenced, dropped, profile = derive(resp.get("checklist") or {}, content)
    return {
        "repo": item["repo"], "path": item["path"], "name": item.get("name", ""),
        "source": item["source"], "hint": item["hint"],
        "artifact_type": resp.get("artifact_type"), "confidence": resp.get("confidence"),
        "checklist": resp.get("checklist"),
        "skills_evidenced": evidenced,
        "skill_profile": profile,
        "verification_ok": not issues,
        "verification_issues": issues,
        "dropped_non_verbatim": dropped,
        "content_truncated": len(item["content"]) > MAX_CONTENT,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="ministral-14b-latest")
    ap.add_argument("--max-skills", type=int, default=6)
    ap.add_argument("--pyramid-only", action="store_true")
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()

    items = load_items(args.pyramid_only, args.max_skills)
    rotator = KeyRotator(ENV_PATH)
    print(f"piloto pyramid: {len(items)} skills | {len(rotator)} chave(s)")

    results = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {item['hint']} | {item.get('name') or item['path']}")
        try:
            r = classify(item, args.model, rotator, args.max_retries)
            print(f"  {r['artifact_type']} | profile={r['skill_profile']} | skills={r['skills_evidenced']}")
        except Exception as exc:
            print(f"  falhou: {exc}", file=sys.stderr)
            r = {**{k: item[k] for k in ("repo", "path", "name", "source", "hint")}, "error": str(exc)}
        results.append(r)
        time.sleep(args.sleep)

    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    # coverage no lote
    cov = {s: sum(1 for r in results if s in (r.get("skills_evidenced") or [])) for s in SKILLS}
    n = max(1, sum(1 for r in results if r.get("artifact_type") == "test_guidance_skill"))
    print("\nTesting Skill Coverage (sobre test_guidance_skill):")
    for s in SKILLS:
        pct = 100 * cov[s] / n
        bar = "█" * int(pct // 10) + "░" * (10 - int(pct // 10))
        print(f"  {s:12} {bar} {pct:5.1f}% ({cov[s]}/{n})")
    plot_dir = write_plots(results)
    print(f"\n→ {args.output}")
    print(f"→ plots: {plot_dir}")


def write_plots(results: list[dict]) -> Path:
    """Gera PNGs de cobertura/perfil a partir dos resultados do piloto."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    import numpy as np

    labels = {
        "unit": "Unit", "integration": "Integration", "contract": "Contract", "ui": "UI",
        "end_to_end": "End-to-End", "acceptance": "Acceptance", "exploratory": "Exploratory",
        "automation": "Automation",
    }
    out = HERE / "plots"
    out.mkdir(exist_ok=True)
    guidance = [r for r in results if r.get("artifact_type") == "test_guidance_skill"]
    n = max(1, len(guidance))
    counts = {s: sum(1 for r in guidance if s in (r.get("skills_evidenced") or [])) for s in SKILLS}
    pcts = [100 * counts[s] / n for s in SKILLS]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = ["#2a6f97" if p > 0 else "#adb5bd" for p in pcts]
    ax.barh([labels[s] for s in SKILLS][::-1], pcts[::-1], color=colors[::-1], height=0.65)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% das skills de orientação a teste")
    ax.set_title(f"Testing Skill Coverage — Practical Test Pyramid (n={n})")
    for i, (s, p) in enumerate(zip(SKILLS[::-1], pcts[::-1])):
        ax.text(min(p + 1.5, 96), i, f"{p:.0f}% ({counts[s]}/{n})", va="center", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "skill_coverage.png", dpi=160)
    plt.close()

    names = [r.get("name") or Path(r["path"]).name for r in results]
    mat = []
    for r in results:
        row = []
        for s in SKILLS:
            st = (r.get("skill_profile") or {}).get(s, "no")
            row.append({"yes": 2, "uncertain": 1, "dropped_quote": 1, "no": 0}.get(st, 0))
        mat.append(row)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.imshow(np.array(mat), aspect="auto", cmap=ListedColormap(["#e9ecef", "#ffd166", "#2a9d8f"]), vmin=0, vmax=2)
    ax.set_xticks(range(len(SKILLS)))
    ax.set_xticklabels([labels[s] for s in SKILLS], rotation=35, ha="right")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([n if len(n) < 28 else n[:25] + "…" for n in names])
    ax.set_title("Testing Skill Profile por skill")
    ax.legend(handles=[
        Patch(facecolor="#2a9d8f", label="YES"),
        Patch(facecolor="#ffd166", label="UNCERTAIN / quote drop"),
        Patch(facecolor="#e9ecef", label="NO"),
    ], loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    fig.tight_layout()
    fig.savefig(out / "skill_profile_matrix.png", dpi=160, bbox_inches="tight")
    plt.close()

    order = ["unit", "integration", "end_to_end"]
    fig, ax = plt.subplots(figsize=(6, 5))
    for y, s, c in zip([0.5, 1.5, 2.5], order, ["#1d3557", "#457b9d", "#a8dadc"]):
        w = counts[s] / n * 100
        ax.barh(y, w, height=0.8, left=(100 - w) / 2, color=c)
        ax.text(50, y, f"{labels[s]}  {w:.0f}%", ha="center", va="center",
                color="white" if w > 25 else "#1d3557", fontsize=11, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 3.2)
    ax.set_yticks([])
    ax.set_xlabel("% com evidência")
    ax.set_title("Pirâmide prática — prevalência")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "pyramid_prevalence.png", dpi=160)
    plt.close()
    return out


if __name__ == "__main__":
    main()
