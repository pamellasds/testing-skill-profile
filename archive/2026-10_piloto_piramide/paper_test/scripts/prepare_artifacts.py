"""Prepara artefatos do short paper MSR 2027 Mining Challenge (trilha Pyramid).

- regenera plots em PT (termo: nivel de teste)
- amostra estratificada blind por nivel (unit/integration/e2e/acceptance)
- tabelas-resumo para o paper

Uso (na raiz gitskills):
    python 2027_short_paper_challenge/scripts/prepare_artifacts.py
"""
from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CH = Path(__file__).resolve().parents[1]
POOL = ROOT / "data/test_types_filter/test_types_candidates.json"
PILOT = ROOT / "data/test_pyramid_skills/pilot_results.json"
OUT_PLOTS = CH / "data/plots"
OUT_RES = CH / "data/results"
OUT_MAN = CH / "data/manual_review"
PAPER_FIG = CH / "paper/figures"

CORE = ["unit", "integration", "system_e2e", "acceptance"]
CORE_PT = {
    "unit": "Unitário",
    "integration": "Integração",
    "system_e2e": "Ponta a ponta (E2E)",
    "acceptance": "Aceitação",
}
SKILL_PT = {
    "unit": "Unitário",
    "integration": "Integração",
    "contract": "Contrato",
    "ui": "UI",
    "end_to_end": "E2E",
    "acceptance": "Aceitação",
    "exploratory": "Exploratório",
    "automation": "Automação",
}
SAMPLE_PER = 8
SEED = 20270402


def load_pool() -> list[dict]:
    return json.loads(POOL.read_text())


def exclusive_stratum(pool: list[dict]) -> dict[str, list[dict]]:
    buckets = {k: [] for k in CORE}
    for item in pool:
        core = [L for L in item.get("matched_layers", []) if L in CORE]
        if len(core) == 1:
            buckets[core[0]].append(item)
    return buckets


def make_blind_sample(pool: list[dict]) -> None:
    random.seed(SEED)
    buckets = exclusive_stratum(pool)
    rows_blind, rows_key = [], []
    sid = 1
    for level in CORE:
        items = buckets[level]
        # prefer shorter content for reviewability
        items = sorted(items, key=lambda x: len(x.get("content") or ""))
        # take from mid-length band to avoid empty stubs
        mid = [i for i in items if 800 <= len(i.get("content") or "") <= 12000]
        pool_pick = mid if len(mid) >= SAMPLE_PER else items
        picked = random.sample(pool_pick, min(SAMPLE_PER, len(pool_pick)))
        for it in picked:
            content = it.get("content") or ""
            # truncate for reviewers
            excerpt = content if len(content) <= 6000 else content[:6000] + "\n\n[... truncado ...]"
            blind = {
                "sample_id": f"S{sid:03d}",
                "repo": it["repo"],
                "path": it["path"],
                "name": it.get("name") or "",
                "description": it.get("description") or "",
                "content_excerpt": excerpt,
            }
            key = {
                **blind,
                "stratum_nivel": level,
                "stratum_nivel_pt": CORE_PT[level],
                "matched_layers": it.get("matched_layers", []),
                "matched_terms": it.get("matched_terms", []),
                "n_terms": it.get("n_terms"),
            }
            rows_blind.append(blind)
            rows_key.append(key)
            sid += 1

    OUT_MAN.mkdir(parents=True, exist_ok=True)
    (OUT_MAN / "sample_blind.json").write_text(
        json.dumps(rows_blind, indent=2, ensure_ascii=False)
    )
    (OUT_MAN / "sample_key.json").write_text(
        json.dumps(rows_key, indent=2, ensure_ascii=False)
    )
    # CSV for spreadsheet annotation
    with (OUT_MAN / "annotation_sheet.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "sample_id", "repo", "path", "name",
                "unit", "integration", "contract", "ui", "end_to_end",
                "acceptance", "exploratory", "automation",
                "notes",
            ],
        )
        w.writeheader()
        for r in rows_blind:
            w.writerow({
                "sample_id": r["sample_id"], "repo": r["repo"], "path": r["path"],
                "name": r["name"],
                "unit": "", "integration": "", "contract": "", "ui": "",
                "end_to_end": "", "acceptance": "", "exploratory": "", "automation": "",
                "notes": "",
            })
    print(f"amostra blind: {len(rows_blind)} ({SAMPLE_PER}/nível × {len(CORE)})")


def write_stats(pool: list[dict]) -> dict:
    anyc, excl = Counter(), Counter()
    for item in pool:
        core = [L for L in item.get("matched_layers", []) if L in CORE]
        for c in core:
            anyc[c] += 1
        if len(core) == 1:
            excl[core[0]] += 1
    multi = sum(1 for i in pool if len([L for L in i.get("matched_layers", []) if L in CORE]) >= 2)
    extra = {
        k: sum(1 for i in pool if k in i.get("matched_layers", []))
        for k in ["fork", "fuzz_property", "coverage", "regression", "contract_testing"
                  if False else "mutation"]
    }
    # fix extras
    extra = {
        k: sum(1 for i in pool if k in i.get("matched_layers", []))
        for k in ["fork", "fuzz_property", "coverage", "regression", "mutation", "gas_performance"]
    }
    pilot = json.loads(PILOT.read_text()) if PILOT.exists() else []
    guidance = [r for r in pilot if r.get("artifact_type") == "test_guidance_skill"]
    skill_cov = {}
    for s in SKILL_PT:
        skill_cov[s] = sum(1 for r in guidance if s in (r.get("skills_evidenced") or []))

    stats = {
        "n_pool": len(pool),
        "n_mandatory_only": 89649,
        "prevalence_any_core": dict(anyc),
        "prevalence_exclusive_core": dict(excl),
        "multi_core": multi,
        "extras": extra,
        "llm_pilot_n": len(pilot),
        "llm_guidance_n": len(guidance),
        "llm_skill_coverage": skill_cov,
        "manual_sample_per_nivel": SAMPLE_PER,
        "manual_sample_total": SAMPLE_PER * len(CORE),
        "seed": SEED,
    }
    OUT_RES.mkdir(parents=True, exist_ok=True)
    (OUT_RES / "paper_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    return stats


def plot_nivel_prevalence(stats: dict) -> None:
    OUT_PLOTS.mkdir(parents=True, exist_ok=True)
    PAPER_FIG.mkdir(parents=True, exist_ok=True)
    n = stats["n_pool"]
    levels = CORE
    vals = [100 * stats["prevalence_any_core"].get(L, 0) / n for L in levels]
    counts = [stats["prevalence_any_core"].get(L, 0) for L in levels]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    colors = ["#1d3557", "#457b9d", "#a8dadc", "#e9c46a"]
    bars = ax.barh([CORE_PT[L] for L in levels][::-1], vals[::-1], color=colors[::-1], height=0.62)
    ax.set_xlim(0, max(vals) * 1.25)
    ax.set_xlabel("% das skills do pool de orientação a teste (n=17.847)")
    ax.set_title("Prevalência lexical por nível de teste (pirâmide prática)")
    for i, (c, v) in enumerate(zip(counts[::-1], vals[::-1])):
        ax.text(v + 0.4, i, f"{v:.1f}% ({c})", va="center", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for dest in (OUT_PLOTS / "fig_nivel_prevalence.png", PAPER_FIG / "fig_nivel_prevalence.png"):
        fig.savefig(dest, dpi=200)
    plt.close()

    # pyramid visual
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    order = ["unit", "integration", "system_e2e"]  # clássico unit→int→e2e
    ys = [0.5, 1.5, 2.5]
    cols = ["#1d3557", "#457b9d", "#a8dadc"]
    for y, L, c in zip(ys, order, cols):
        w = 100 * stats["prevalence_any_core"].get(L, 0) / n
        ax.barh(y, w, height=0.85, left=(100 - w) / 2, color=c)
        ax.text(50, y, f"{CORE_PT[L]}\n{w:.1f}%", ha="center", va="center",
                color="white" if w > 18 else "#1d3557", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 3.2)
    ax.set_yticks([])
    ax.set_xlabel("% com menção lexical no pool")
    ax.set_title("Pirâmide prática — prevalência por nível")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    for dest in (OUT_PLOTS / "fig_pyramid_niveis.png", PAPER_FIG / "fig_pyramid_niveis.png"):
        fig.savefig(dest, dpi=200)
    plt.close()


def plot_llm_profile() -> None:
    pilot = json.loads(PILOT.read_text())
    skills = list(SKILL_PT.keys())
    guidance = [r for r in pilot if r.get("artifact_type") == "test_guidance_skill"]
    n = max(1, len(guidance))
    counts = [sum(1 for r in guidance if s in (r.get("skills_evidenced") or [])) for s in skills]
    pcts = [100 * c / n for c in counts]

    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.barh([SKILL_PT[s] for s in skills][::-1], pcts[::-1],
            color=["#2a6f97" if p else "#adb5bd" for p in pcts][::-1], height=0.62)
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"% das skills com orientação a teste no piloto LLM (n={n})")
    ax.set_title("Testing Skill Profile — evidência via checklist Pyramid (piloto)")
    for i, (c, p) in enumerate(zip(counts[::-1], pcts[::-1])):
        ax.text(min(p + 1.5, 92), i, f"{p:.0f}% ({c}/{n})", va="center", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for dest in (OUT_PLOTS / "fig_skill_profile_piloto.png", PAPER_FIG / "fig_skill_profile_piloto.png"):
        fig.savefig(dest, dpi=200)
    plt.close()

    # matrix
    names = [(r.get("name") or Path(r["path"]).name)[:26] for r in pilot]
    mat = []
    for r in pilot:
        row = []
        for s in skills:
            st = (r.get("skill_profile") or {}).get(s, "no")
            row.append({"yes": 2, "uncertain": 1, "dropped_quote": 1, "no": 0}.get(st, 0))
        mat.append(row)
    fig, ax = plt.subplots(figsize=(8.2, 3.4))
    ax.imshow(np.array(mat), aspect="auto",
              cmap=matplotlib.colors.ListedColormap(["#e9ecef", "#ffd166", "#2a9d8f"]),
              vmin=0, vmax=2)
    ax.set_xticks(range(len(skills)))
    ax.set_xticklabels([SKILL_PT[s] for s in skills], rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_title("Perfil por skill (piloto LLM)")
    fig.tight_layout()
    for dest in (OUT_PLOTS / "fig_skill_matrix_piloto.png", PAPER_FIG / "fig_skill_matrix_piloto.png"):
        fig.savefig(dest, dpi=200)
    plt.close()


def main() -> None:
    print("carregando pool...")
    pool = load_pool()
    stats = write_stats(pool)
    print("stats:", json.dumps({k: stats[k] for k in ("n_pool", "multi_core", "llm_guidance_n")}, ensure_ascii=False))
    make_blind_sample(pool)
    plot_nivel_prevalence(stats)
    plot_llm_profile()
    print("ok →", CH)


if __name__ == "__main__":
    main()
