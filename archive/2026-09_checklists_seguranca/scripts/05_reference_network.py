"""Rede de referencias EXPLICITAS entre skills - diferente do script 04
(que mede similaridade de texto/clonagem de template), aqui a aresta e uma
skill citando outra de proposito: campo related_skills do frontmatter, ou
link markdown para outro SKILL.md. Normalmente e composicao dentro do mesmo
repo (uma skill de metodologia apontando para severity/checklists/etc.).

Uso:
    python 05_reference_network.py
"""
from __future__ import annotations

import argparse
import json
import posixpath
import re
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/checklist_platform_filter/checklist_platform_candidates_v3_1592.json"
DEFAULT_OUTDIR = ROOT / "data/checklist_platform_filter/network"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
MD_LINK_TO_SKILL_RE = re.compile(r"\[[^\]]*\]\(([^)]*SKILL\.md[^)]*)\)", re.IGNORECASE)


def extract_frontmatter(content: str) -> dict:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def referenced_paths(item: dict) -> set[str]:
    """Referencias cruas (ainda relativas, com possivel #fragmento) citadas
    no frontmatter (related_skills) e no corpo (links markdown para outro
    SKILL.md)."""
    refs = set()

    frontmatter = extract_frontmatter(item["content"])
    for ref in frontmatter.get("related_skills") or []:
        if isinstance(ref, str):
            refs.add(ref)

    for ref in MD_LINK_TO_SKILL_RE.findall(item["content"]):
        refs.add(ref)

    return refs


def resolve_reference(source_path: str, raw_ref: str) -> str:
    """Resolve um link relativo (visto de dentro do arquivo fonte) para um
    path absoluto dentro do repo, descartando fragmento (#...) e query."""
    ref = raw_ref.split("#", 1)[0].split("?", 1)[0].strip()
    base_dir = posixpath.dirname(source_path)
    return posixpath.normpath(posixpath.join(base_dir, ref))


def build_reference_graph(pool: list[dict]) -> tuple[nx.DiGraph, int]:
    index = {(item["repo"], item["path"]): i for i, item in enumerate(pool)}
    graph = nx.DiGraph()
    graph.add_nodes_from(range(len(pool)))

    dangling = 0
    for i, item in enumerate(pool):
        for raw_ref in referenced_paths(item):
            resolved = resolve_reference(item["path"], raw_ref)
            target = index.get((item["repo"], resolved))
            if target is not None and target != i:
                graph.add_edge(i, target)
            else:
                dangling += 1
    return graph, dangling


def save_edges(pool: list[dict], graph: nx.DiGraph, outfile: Path) -> None:
    edges = [
        {"source_repo": pool[u]["repo"], "source_path": pool[u]["path"],
         "target_repo": pool[v]["repo"], "target_path": pool[v]["path"]}
        for u, v in graph.edges()
    ]
    outfile.write_text(json.dumps(edges, indent=2, ensure_ascii=False))
    print(f"salvo {outfile}")


def plot_most_referenced(pool: list[dict], graph: nx.DiGraph, outfile: Path, top_n: int) -> None:
    in_degrees = sorted(graph.in_degree(), key=lambda x: x[1], reverse=True)
    in_degrees = [(node, deg) for node, deg in in_degrees if deg > 0][:top_n]
    if not in_degrees:
        print("nenhuma skill referenciada por outra, pulando grafico de top-referenciadas")
        return

    labels = [f"{pool[n]['repo']}/{pool[n]['path'].split('/')[-2] if '/' in pool[n]['path'] else pool[n]['path']}" for n, _ in in_degrees]
    values = [deg for _, deg in in_degrees]
    fig, ax = plt.subplots(figsize=(9, max(3, 0.45 * len(in_degrees))))
    ax.barh(labels, values, color="#55A868")
    ax.invert_yaxis()
    ax.set_xlabel("quantidade de skills que referenciam esta")
    ax.set_title(f"Top {len(in_degrees)} skills mais referenciadas (hubs)")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def plot_reference_network(pool: list[dict], graph: nx.DiGraph, outfile: Path) -> None:
    connected = {n for n in graph.nodes() if graph.degree(n) > 0}
    subgraph = graph.subgraph(connected)
    if subgraph.number_of_nodes() == 0:
        print("nenhuma referencia entre skills do pool, pulando rede")
        return

    owner_of = {n: pool[n]["repo"].split("/")[0] for n in subgraph.nodes()}
    distinct_owners = sorted(set(owner_of.values()))
    owner_color = {o: i for i, o in enumerate(distinct_owners)}
    colors = [owner_color[owner_of[n]] for n in subgraph.nodes()]
    in_deg = dict(subgraph.in_degree())
    sizes = [40 + 25 * in_deg.get(n, 0) for n in subgraph.nodes()]

    pos = nx.spring_layout(subgraph, k=0.5, seed=42)

    fig, ax = plt.subplots(figsize=(12, 12))
    nx.draw_networkx_edges(subgraph, pos, ax=ax, alpha=0.3, width=0.8, arrows=True, arrowsize=8, connectionstyle="arc3,rad=0.05")
    nx.draw_networkx_nodes(subgraph, pos, ax=ax, node_size=sizes, node_color=colors, cmap="tab20", alpha=0.9)
    ax.set_title(f"Rede de referencias explicitas entre skills: {subgraph.number_of_nodes()} skills, {subgraph.number_of_edges()} links")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--top-n", type=int, default=15)
    args = parser.parse_args()

    pool = json.loads(args.input.read_text())
    print(f"{len(pool)} skills carregadas de {args.input}")
    args.outdir.mkdir(parents=True, exist_ok=True)

    graph, dangling = build_reference_graph(pool)
    n_edges = graph.number_of_edges()
    n_connected = sum(1 for n in graph.nodes() if graph.degree(n) > 0)
    print(f"referencias resolvidas dentro do pool: {n_edges}")
    print(f"referencias para fora do pool (skill irma nao capturada pelo filtro): {dangling}")
    print(f"skills envolvidas em pelo menos uma referencia: {n_connected}/{len(pool)}")

    save_edges(pool, graph, args.outdir / "reference_edges.json")
    plot_reference_network(pool, graph, args.outdir / "reference_network.png")
    plot_most_referenced(pool, graph, args.outdir / "reference_hubs.png", args.top_n)


if __name__ == "__main__":
    main()
