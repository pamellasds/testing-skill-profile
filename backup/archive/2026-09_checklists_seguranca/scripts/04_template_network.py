"""Duas analises sobre repeticao no pool: (1) concentracao de skills por
owner/repo; (2) rede de proliferacao de template - skills quase-identicas
publicadas por owners diferentes, que passam pelo dedup de conteudo exato
mas nao deveriam contar como amostras independentes.

Deteccao de quase-duplicata via MinHash/LSH (shingles de palavras) sobre o
content ja limpo de HTML/URLs/badges (mesma limpeza do script 03) -
escala bem para o pool inteiro e pega copia quase-literal de template, que
e o padrao observado (~95% de similaridade entre repos diferentes).

Uso:
    python 05_template_network.py --similarity-threshold 0.8
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from datasketch import MinHash, MinHashLSH

from text_cleaning import clean_content

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/checklist_platform_filter/checklist_platform_candidates_v3_1592.json"
DEFAULT_OUTDIR = ROOT / "data/checklist_platform_filter/network"

SHINGLE_SIZE = 8  # palavras por shingle; maior = exige trecho mais longo em comum
NUM_PERM = 128    # permutacoes do MinHash; mais = estimativa mais precisa, mais lento


def shingles(text: str, k: int) -> set[str]:
    words = text.split()
    if len(words) < k:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def minhash_for(text: str, num_perm: int) -> MinHash:
    mh = MinHash(num_perm=num_perm)
    for shingle in shingles(text.lower(), SHINGLE_SIZE):
        mh.update(shingle.encode("utf-8"))
    return mh


def build_similarity_graph(pool: list[dict], threshold: float, num_perm: int) -> nx.Graph:
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    minhashes = {}

    for i, item in enumerate(pool):
        key = str(i)
        mh = minhash_for(clean_content(item["content"]), num_perm)
        minhashes[key] = mh
        lsh.insert(key, mh)

    graph = nx.Graph()
    graph.add_nodes_from(str(i) for i in range(len(pool)))
    for i, item in enumerate(pool):
        key = str(i)
        for match in lsh.query(minhashes[key]):
            if match != key:
                graph.add_edge(key, match)
    return graph


def owner_of(repo: str) -> str:
    return repo.split("/")[0]


def analyze_owner_concentration(pool: list[dict], outdir: Path, top_n: int) -> None:
    repo_counts = Counter(item["repo"] for item in pool)
    owner_counts = Counter(owner_of(item["repo"]) for item in pool)

    print(f"repos distintos: {len(repo_counts)} | owners distintos: {len(owner_counts)}")

    top_owners = owner_counts.most_common(top_n)
    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(top_owners))))
    labels, values = zip(*top_owners)
    ax.barh(labels, values, color="#4C72B0")
    ax.invert_yaxis()
    ax.set_xlabel("skills no pool")
    ax.set_title(f"Top {top_n} owners por numero de skills")
    fig.tight_layout()
    fig.savefig(outdir / "owner_concentration.png", dpi=150)
    plt.close(fig)
    print(f"salvo {outdir / 'owner_concentration.png'}")

    (outdir / "owner_counts.json").write_text(
        json.dumps([{"owner": o, "skills": n} for o, n in owner_counts.most_common()], indent=2, ensure_ascii=False)
    )


def plot_network_graph(graph: nx.Graph, components: list[set[str]], outfile: Path) -> None:
    """Desenha o grafo de similaridade: cada cluster de template vira um
    'blob' de nos proximos e coloridos, conectados por arestas; nos sem
    par (singletons) ficam de fora para nao virar uma nuvem ilegivel."""
    nodes_in_clusters = {n for c in components for n in c}
    subgraph = graph.subgraph(nodes_in_clusters)
    if subgraph.number_of_nodes() == 0:
        print("nenhum cluster para desenhar como rede, pulando")
        return

    component_of = {n: i for i, c in enumerate(components) for n in c}
    cluster_size = {n: len(components[component_of[n]]) for n in subgraph.nodes()}
    node_color = [cluster_size[n] for n in subgraph.nodes()]
    node_size = [15 + 3 * cluster_size[n] for n in subgraph.nodes()]

    pos = nx.spring_layout(subgraph, k=0.3, seed=42)

    fig, ax = plt.subplots(figsize=(12, 12))
    nx.draw_networkx_edges(subgraph, pos, ax=ax, alpha=0.15, width=0.5)
    nodes = nx.draw_networkx_nodes(
        subgraph, pos, ax=ax, node_size=node_size, node_color=node_color,
        cmap="viridis", alpha=0.85,
    )
    fig.colorbar(nodes, ax=ax, shrink=0.6, label="tamanho do cluster (skills quase-identicas)")
    ax.set_title(f"Rede de quase-duplicatas: {len(components)} clusters, {subgraph.number_of_nodes()} skills")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    plt.close(fig)
    print(f"salvo {outfile}")


def analyze_template_clusters(pool: list[dict], graph: nx.Graph, outdir: Path, top_n: int) -> None:
    components = [c for c in nx.connected_components(graph) if len(c) > 1]
    components.sort(key=len, reverse=True)

    n_in_clusters = sum(len(c) for c in components)
    print(f"clusters de template (tamanho > 1): {len(components)}")
    print(f"skills envolvidas em algum cluster: {n_in_clusters}/{len(pool)} ({n_in_clusters / len(pool):.1%})")

    cluster_records = []
    for cluster_id, members in enumerate(components):
        items = [pool[int(idx)] for idx in members]
        owners = {owner_of(item["repo"]) for item in items}
        cluster_records.append({
            "cluster_id": cluster_id,
            "size": len(items),
            "distinct_owners": len(owners),
            "example_path": items[0]["path"],
            "skills": [{"repo": item["repo"], "path": item["path"]} for item in items],
        })
    (outdir / "template_clusters.json").write_text(json.dumps(cluster_records, indent=2, ensure_ascii=False))
    print(f"salvo {outdir / 'template_clusters.json'}")

    plot_network_graph(graph, components, outdir / "template_network.png")

    top_clusters = cluster_records[:top_n]
    if top_clusters:
        labels = [f"{c['example_path'].split('/')[-2] if '/' in c['example_path'] else c['example_path']} (#{c['cluster_id']})" for c in top_clusters]
        sizes = [c["size"] for c in top_clusters]
        fig, ax = plt.subplots(figsize=(9, max(3, 0.45 * len(top_clusters))))
        ax.barh(labels, sizes, color="#DD8452")
        ax.invert_yaxis()
        ax.set_xlabel("copias quase-identicas (skills)")
        ax.set_title(f"Top {len(top_clusters)} clusters de template proliferado")
        fig.tight_layout()
        fig.savefig(outdir / "template_clusters.png", dpi=150)
        plt.close(fig)
        print(f"salvo {outdir / 'template_clusters.png'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--similarity-threshold", type=float, default=0.8, help="Jaccard estimado minimo para considerar quase-duplicata")
    parser.add_argument("--num-perm", type=int, default=NUM_PERM)
    parser.add_argument("--top-n", type=int, default=15)
    args = parser.parse_args()

    pool = json.loads(args.input.read_text())
    print(f"{len(pool)} skills carregadas de {args.input}")
    args.outdir.mkdir(parents=True, exist_ok=True)

    analyze_owner_concentration(pool, args.outdir, args.top_n)

    print(f"\nconstruindo grafo de similaridade (threshold={args.similarity_threshold})...")
    graph = build_similarity_graph(pool, args.similarity_threshold, args.num_perm)
    analyze_template_clusters(pool, graph, args.outdir, args.top_n)


if __name__ == "__main__":
    main()
