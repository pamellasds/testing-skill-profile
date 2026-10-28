"""Gera graficos da busca por tipos de teste (todas as camadas).

Uso:
    python generate_plots.py \\
      --summary test_types_summary.json \\
      --pool test_types_candidates.json \\
      --keywords keywords_by_layer.json \\
      --outdir plots
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent

# Ordem visual da piramide classica + camadas web3/extras
LAYER_ORDER = [
    # pirâmide / níveis CTFL
    "unit",
    "integration",
    "system_e2e",
    "acceptance",
    # tipos CTFL
    "confirmation",
    "regression",
    "maintenance",
    "static_analysis",
    "black_box",
    "white_box",
    "exploratory",
    "functional",
    "non_functional",
    # web3 / extras
    "fork",
    "fuzz_property",
    "formal_symbolic",
    "mutation",
    "differential",
    "gas_performance",
    "coverage",
]

# Camadas da piramide classica (base -> topo) para o grafico TVM/piramide
PYRAMID_LAYERS = ["unit", "integration", "system_e2e"]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def layer_labels(keywords: dict) -> dict[str, str]:
    return {
        lid: meta.get("label", lid)
        for lid, meta in keywords.get("layers", {}).items()
    }


def plot_by_layer(summary: dict, labels: dict[str, str], outfile: Path) -> None:
    by_layer = summary["by_layer"]
    ordered = [lid for lid in LAYER_ORDER if lid in by_layer]
    names = [labels.get(lid, lid) for lid in ordered]
    values = [by_layer[lid] for lid in ordered]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, values, color="#4C72B0")
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills")
    ax.set_title(
        f"Skills por camada de teste (n={summary['n_skills']})"
    )
    for bar, v in zip(bars, values):
        ax.text(v + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_top_terms(summary: dict, outfile: Path, top_n: int = 25) -> None:
    top = summary.get("top_terms", [])[:top_n]
    if not top:
        print(f"sem termos para {outfile}, pulando")
        return
    terms, values = zip(*top)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.4 * len(terms))))
    bars = ax.barh(list(terms), list(values), color="#55A868")
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills")
    ax.set_title(f"Top {len(terms)} termos de tipo de teste")
    for bar, v in zip(bars, values):
        ax.text(v + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_n_layers_hist(pool: list[dict], outfile: Path) -> None:
    counts = Counter(item.get("n_layers", 0) for item in pool)
    xs = sorted(counts)
    ys = [counts[x] for x in xs]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([str(x) for x in xs], ys, color="#C44E52")
    ax.set_xlabel("numero de camadas distintas por skill")
    ax.set_ylabel("quantidade de skills")
    ax.set_title("Distribuicao de multi-camada")
    for i, v in enumerate(ys):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_pyramid(summary: dict, labels: dict[str, str], outfile: Path) -> None:
    """Barras horizontais das 3 camadas classicas (unit / integration / e2e)."""
    by_layer = summary["by_layer"]
    values = [by_layer.get(lid, 0) for lid in PYRAMID_LAYERS]
    names = [labels.get(lid, lid) for lid in PYRAMID_LAYERS]
    colors = ["#4C72B0", "#55A868", "#C44E52"]

    fig, ax = plt.subplots(figsize=(8, 4))
    # unit na base visual (embaixo)
    y = [0, 1, 2]
    ax.barh(y, values, color=colors, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("quantidade de skills")
    ax.set_title(
        "Camadas classicas da piramide de testes (TVM)\n"
        f"skills no pool (n={summary['n_skills']})"
    )
    for yi, v in zip(y, values):
        ax.text(v, yi, f" {v}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_pyramid_trapazoids(summary: dict, labels: dict[str, str], outfile: Path) -> None:
    """Piramide com trapezoides (visual TVM classico), base larga = mais skills."""
    by_layer = summary["by_layer"]
    # De cima para baixo na figura: e2e, integration, unit
    order_top_to_bottom = ["system_e2e", "integration", "unit"]
    values = [by_layer.get(lid, 0) for lid in order_top_to_bottom]
    names = [labels.get(lid, lid) for lid in order_top_to_bottom]
    max_v = max(values) if any(values) else 1

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#C44E52", "#55A868", "#4C72B0"]
    n = len(values)
    # Larguras normalizadas; topo mais estreito se tiver menos skills
    widths = [0.25 + 0.7 * (v / max_v) for v in values]

    for i, (name, val, w, color) in enumerate(zip(names, values, widths, colors)):
        y0 = 1 - (i + 1) / n
        y1 = 1 - i / n
        # Trapezóide: topo usa largura da faixa de cima, base a desta faixa
        w_top = widths[i - 1] if i > 0 else w * 0.85
        # Para visual de piramide limpa, cada faixa usa sua propria largura
        # (retangulo arredondado via polygon centrado)
        xs = [0.5 - w / 2, 0.5 + w / 2, 0.5 + w / 2, 0.5 - w / 2]
        ys = [y0, y0, y1, y1]
        ax.fill(xs, ys, color=color, edgecolor="white", linewidth=2)
        ax.text(0.5, (y0 + y1) / 2, f"{name}\n{val} skills",
                ha="center", va="center", color="white",
                fontsize=12, fontweight="bold")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        "TVM — piramide de testes (unit / integration / e2e)\n"
        "contagem de skills que mencionam cada camada",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_cooccurrence(pool: list[dict], labels: dict[str, str], outfile: Path) -> None:
    """Heatmap de co-ocorrencia entre camadas."""
    layers = [lid for lid in LAYER_ORDER]
    idx = {lid: i for i, lid in enumerate(layers)}
    mat = np.zeros((len(layers), len(layers)), dtype=int)
    for item in pool:
        ls = [lid for lid in item.get("matched_layers", []) if lid in idx]
        for a in ls:
            for b in ls:
                mat[idx[a], idx[b]] += 1

    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(mat, cmap="YlOrRd")
    short = [labels.get(lid, lid).split(" / ")[0] for lid in layers]
    ax.set_xticks(range(len(layers)))
    ax.set_yticks(range(len(layers)))
    ax.set_xticklabels(short, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(short, fontsize=8)
    ax.set_title("Co-ocorrencia de camadas de teste nas skills")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="skills")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path,
                        default=HERE / "test_types_summary.json")
    parser.add_argument("--pool", type=Path,
                        default=HERE / "test_types_candidates.json")
    parser.add_argument("--keywords", type=Path,
                        default=HERE / "keywords_by_layer.json")
    parser.add_argument("--outdir", type=Path, default=HERE / "plots")
    parser.add_argument("--top-n", type=int, default=25)
    args = parser.parse_args()

    summary = load_json(args.summary)
    keywords = load_json(args.keywords)
    labels = layer_labels(keywords)
    # Pool pode ser grande; so carrega campos leves se necessario
    pool = load_json(args.pool)

    args.outdir.mkdir(parents=True, exist_ok=True)
    plot_by_layer(summary, labels, args.outdir / "by_layer.png")
    plot_top_terms(summary, args.outdir / "top_terms.png", args.top_n)
    plot_n_layers_hist(pool, args.outdir / "multi_layer.png")
    plot_pyramid_trapazoids(summary, labels, args.outdir / "tvm_pyramid.png")
    plot_pyramid(summary, labels, args.outdir / "tvm_pyramid_bars.png")
    plot_cooccurrence(pool, labels, args.outdir / "layer_cooccurrence.png")

    print(f"\n{summary['n_skills']} skills no pool; graficos em {args.outdir}")


if __name__ == "__main__":
    main()
