"""Gera graficos quantitativos a partir da saida do 02_llm_classifier.py:
distribuicao da categoria principal (nature), das subcategorias (role e
points_externally de tools/firms_platforms/checklists), dos nomes mais
citados em cada bloco, e das vulnerabilidades mais mencionadas.

Estilo unico: barras horizontais, rotulos em portugues, top-N, valores
nas barras, grade leve.

Uso:
    python 03_generate_plots.py \\
      --input data/checklist_platform_filter/llm_classification_full.checkpoint.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from wordcloud import STOPWORDS, WordCloud

from text_cleaning import EXTRA_STOPWORDS, clean_content

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/checklist_platform_filter/llm_classification_full.checkpoint.jsonl"
DEFAULT_POOL = ROOT / "data/checklist_platform_filter/checklist_platform_candidates_v3_1592.json"
DEFAULT_OUTDIR = ROOT / "data/checklist_platform_filter/plots"

REFERENCE_BLOCKS = ("tools", "firms_platforms", "checklists")

BLOCK_TITLES = {
    "tools": "Ferramentas / scanners",
    "firms_platforms": "Firmas / plataformas",
    "checklists": "Checklists / padroes",
}

NATURE_LABELS = {
    "follows_standard": "Segue padrao externo",
    "own_standard": "Padrao proprio",
    "audit_support_tool": "Apoio a auditoria",
    "not_security_review": "Nao e revisao de seguranca",
    "falhou (erro na API)": "Falhou (erro na API)",
}

NATURE_ORDER = [
    "follows_standard",
    "own_standard",
    "audit_support_tool",
    "not_security_review",
    "falhou (erro na API)",
]

NATURE_COLORS = {
    "follows_standard": "#2CA02C",
    "own_standard": "#4C72B0",
    "audit_support_tool": "#DD8452",
    "not_security_review": "#8C8C8C",
    "falhou (erro na API)": "#C44E52",
}

POINTS_LABELS = {
    "embedded": "Embutido no texto",
    "internal_pointer": "Ponteiro interno",
    "external_pointer": "Ponteiro externo",
    "mixed": "Misto",
}

POINTS_ORDER = ["embedded", "internal_pointer", "external_pointer", "mixed"]

ROLE_LABELS = {
    "recommended_run": "Recomendado executar",
    "output_consumed": "Saida consumida",
    "embedded_ruleset": "Ruleset embutido",
    "mentioned_reference": "Mencao / referencia",
    "methodology_source": "Fonte de metodologia",
    "data_source": "Fonte de dados",
    "library_dependency": "Dependencia de biblioteca",
    "named_reference": "Referencia nomeada",
    "primary_structure": "Estrutura principal",
    "partial_reference": "Referencia parcial",
    "named_only": "So nomeado",
}

ROLE_COLORS = {
    "recommended_run": "#4C72B0",
    "output_consumed": "#55A868",
    "embedded_ruleset": "#C44E52",
    "mentioned_reference": "#8172B3",
    "methodology_source": "#CCB974",
    "data_source": "#64B5CD",
    "library_dependency": "#8C8C8C",
    "named_reference": "#937860",
    "primary_structure": "#DA8BC3",
    "partial_reference": "#8C8C8C",
    "named_only": "#B8B8B8",
}

ACCENT = "#4C72B0"
PALETTE = [
    "#4C72B0", "#55A868", "#C44E52", "#8172B3", "#CCB974",
    "#64B5CD", "#DA8BC3", "#937860", "#8C8C8C", "#DD8452",
]


def _apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#CCCCCC",
        "axes.grid": True,
        "grid.color": "#E6E6E6",
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    })


def _label(mapping: dict[str, str], key) -> str:
    if key is None:
        return mapping.get("falhou (erro na API)", "Falhou (erro na API)")
    return mapping.get(str(key), str(key).replace("_", " "))


def _save(fig: plt.Figure, outfile: Path) -> None:
    fig.tight_layout()
    fig.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"salvo {outfile}")


def _annotate_bars(ax, values: list[int], horizontal: bool = True) -> None:
    pad = max(values) * 0.015 if values and max(values) else 0.1
    for i, v in enumerate(values):
        if horizontal:
            ax.text(v + pad, i, str(v), va="center", ha="left", fontsize=9, color="#333333")
        else:
            ax.text(i, v + pad, str(v), va="bottom", ha="center", fontsize=9, color="#333333")


def load_items(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def count_nature(items: list[dict]) -> Counter:
    return Counter(item.get("nature") for item in items)


def count_points_externally(items: list[dict]) -> Counter:
    counter: Counter = Counter()
    for item in items:
        for block in REFERENCE_BLOCKS:
            for info in item.get(block, {}).values():
                counter[info.get("points_externally")] += 1
    return counter


def count_named_by_role(items: list[dict], block: str) -> dict[str, Counter]:
    """Para cada nome citado no bloco (ex.: 'Slither'), quantas vezes aparece
    com cada papel (ex.: recommended_run x3, mentioned_reference x1)."""
    by_name: dict[str, Counter] = {}
    for item in items:
        for name, info in item.get(block, {}).items():
            by_name.setdefault(name, Counter())[info.get("role")] += 1
    return by_name


def count_vulnerabilities(items: list[dict], top_n: int) -> Counter:
    # o LLM nao e consistente na capitalizacao ("Reentrancy" vs "reentrancy") -
    # normaliza por chave em minusculas e exibe em Title Case
    counter: Counter = Counter()
    for item in items:
        counter.update(
            name.strip().title()
            for name in item.get("vulnerabilities", [])
            if name and name.strip()
        )
    return Counter(dict(counter.most_common(top_n)))


def plot_wordcloud(pool_path: Path, outfile: Path) -> None:
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    text = " ".join(clean_content(item.get("content", "")) for item in pool)
    if not text.strip():
        print("sem conteudo para a nuvem de palavras, pulando")
        return

    wc = WordCloud(
        width=1600, height=900, background_color="white", min_word_length=3,
        stopwords=STOPWORDS | EXTRA_STOPWORDS, max_words=150,
        collocations=True, collocation_threshold=15,
    ).generate(text)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(f"Termos mais frequentes no conteudo das {len(pool)} skills do pool")
    _save(fig, outfile)


def plot_nature(counter: Counter, outfile: Path, n_skills: int) -> None:
    if not counter:
        print(f"sem dados para nature, pulando")
        return
    normalized = Counter({
        ("falhou (erro na API)" if k is None else str(k)): v
        for k, v in counter.items()
    })
    # frequencia decrescente; empate segue NATURE_ORDER
    rank = {k: i for i, k in enumerate(NATURE_ORDER)}
    keys = sorted(
        normalized,
        key=lambda k: (-normalized[k], rank.get(k, 99)),
    )
    labels = [_label(NATURE_LABELS, k) for k in keys]
    values = [normalized[k] for k in keys]
    colors = [NATURE_COLORS.get(k, ACCENT) for k in keys]

    fig, ax = plt.subplots(figsize=(9, max(3.2, 0.55 * len(keys))))
    ax.barh(labels, values, color=colors, height=0.65)
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills")
    ax.set_title(f"Natureza da skill — categoria principal (n={n_skills})")
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    _annotate_bars(ax, values)
    _save(fig, outfile)


def plot_points_externally(counter: Counter, outfile: Path) -> None:
    if not counter:
        print("sem dados para points_externally, pulando")
        return
    rank = {k: i for i, k in enumerate(POINTS_ORDER)}
    keys = sorted(
        (k for k in counter if k is not None),
        key=lambda k: (-counter[k], rank.get(k, 99)),
    )
    labels = [_label(POINTS_LABELS, k) for k in keys]
    values = [counter[k] for k in keys]

    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.55 * len(keys))))
    ax.barh(labels, values, color=ACCENT, height=0.65)
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de citacoes")
    ax.set_title("Nivel de entrega da referencia externa")
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    _annotate_bars(ax, values)
    _save(fig, outfile)


def plot_named_by_role(
    by_name: dict[str, Counter],
    title: str,
    outfile: Path,
    top_n: int | None = 15,
) -> None:
    """Barra horizontal empilhada: um nome por linha, segmentado por papel."""
    if not by_name:
        print(f"sem dados para '{title}', pulando")
        return

    names = sorted(by_name, key=lambda n: sum(by_name[n].values()), reverse=True)
    if top_n:
        names = names[:top_n]
    roles = sorted({role for n in names for role in by_name[n] if role is not None})

    fig, ax = plt.subplots(figsize=(10, max(3.5, 0.48 * len(names) + 1.2)))
    left = [0] * len(names)
    for i, role in enumerate(roles):
        values = [by_name[n].get(role, 0) for n in names]
        color = ROLE_COLORS.get(str(role), PALETTE[i % len(PALETTE)])
        ax.barh(
            names, values, left=left,
            label=_label(ROLE_LABELS, role),
            color=color, height=0.7,
        )
        left = [l + v for l, v in zip(left, values)]

    totals = [sum(by_name[n].values()) for n in names]
    _annotate_bars(ax, totals)
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills")
    ax.set_title(title)
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    ax.legend(
        title="papel", loc="lower right", fontsize=8,
        framealpha=0.95, edgecolor="#DDDDDD",
    )
    # margem a direita para os numeros
    xmax = max(totals) if totals else 1
    ax.set_xlim(0, xmax * 1.12)
    _save(fig, outfile)


def plot_vulnerabilities(counter: Counter, outfile: Path, top_n: int) -> None:
    if not counter:
        print("sem dados para vulnerabilidades, pulando")
        return
    items = counter.most_common()
    labels = [name for name, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(9, max(3.5, 0.5 * len(labels))))
    ax.barh(labels, values, color="#C44E52", height=0.65)
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills")
    ax.set_title(f"Top {top_n} vulnerabilidades mencionadas")
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    _annotate_bars(ax, values)
    _save(fig, outfile)


def generate_all(
    items: list[dict],
    pool_path: Path,
    outdir: Path,
    top_n: int = 10,
    include_wordcloud: bool = True,
    named_top_n: int = 15,
) -> None:
    """Gera todos os graficos a partir de uma lista de itens ja classificados
    (em memoria ou lida de disco) - usada tanto pelo CLI deste script quanto
    por 02_llm_classifier.py para atualizar os graficos durante uma run longa."""
    _apply_style()
    outdir.mkdir(parents=True, exist_ok=True)
    n_skills = len(items)

    if include_wordcloud and pool_path.exists():
        plot_wordcloud(pool_path, outdir / "wordcloud_pool.png")

    plot_nature(count_nature(items), outdir / "nature.png", n_skills)

    for block in REFERENCE_BLOCKS:
        plot_named_by_role(
            count_named_by_role(items, block),
            f"{BLOCK_TITLES[block]} mais citadas, por papel (top {named_top_n})",
            outdir / f"{block}_named.png",
            top_n=named_top_n,
        )

    plot_points_externally(count_points_externally(items), outdir / "points_externally.png")
    plot_vulnerabilities(
        count_vulnerabilities(items, top_n),
        outdir / "vulnerabilities.png",
        top_n,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--pool", type=Path, default=DEFAULT_POOL,
        help="JSON com o pool completo (para a nuvem de palavras)",
    )
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--top-n", type=int, default=10,
                        help="Top N vulnerabilidades")
    parser.add_argument("--named-top-n", type=int, default=15,
                        help="Top N nomes em tools/firmas/checklists")
    parser.add_argument("--no-wordcloud", action="store_true")
    args = parser.parse_args()

    items = load_items(args.input)
    generate_all(
        items, args.pool, args.outdir, args.top_n,
        include_wordcloud=not args.no_wordcloud,
        named_top_n=args.named_top_n,
    )
    print(f"\n{len(items)} skills classificadas processadas")


if __name__ == "__main__":
    main()
