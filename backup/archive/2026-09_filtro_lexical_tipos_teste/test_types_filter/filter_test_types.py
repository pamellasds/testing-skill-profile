"""Filtra agent_skills_mandatory_only.db por tipos de teste em todas as
camadas (unit, integration, e2e, fork, fuzz/invariant, formal, static,
mutation, differential, gas, coverage, regression/smoke).

Entrada de termos: keywords_by_layer.json (mesmo diretorio).
Qualquer termo em qualquer camada conta; a skill e anotada com as
camadas e termos que bateram.

Uso:
    python filter_test_types.py \\
      --db ../../gitskills_sample/agent_skills_mandatory_only.db \\
      --output test_types_candidates.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_KEYWORDS = HERE / "keywords_by_layer.json"


def load_keywords(path: Path) -> dict[str, list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    layers: dict[str, list[str]] = {}
    for layer_id, meta in raw["layers"].items():
        layers[layer_id] = [t.lower() for t in meta["terms"]]
    return layers


def load_rows(db_path: Path) -> list[tuple]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            "SELECT repo_full_name, path, content, name, description "
            "FROM artifacts WHERE dedup_primary = 1"
        )
        return cur.fetchall()
    finally:
        con.close()


def match_layers(text: str, layers: dict[str, list[str]]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for layer_id, terms in layers.items():
        matched = sorted({t for t in terms if t in text})
        if matched:
            hits[layer_id] = matched
    return hits


def build_pool(rows: list[tuple], layers: dict[str, list[str]]) -> list[dict]:
    pool = []
    for repo, path, content, name, description in rows:
        text = f"{content or ''} {name or ''} {description or ''}".lower()
        layer_hits = match_layers(text, layers)
        if not layer_hits:
            continue
        all_terms = sorted({t for ts in layer_hits.values() for t in ts})
        pool.append({
            "repo": repo,
            "path": path,
            "matched_layers": sorted(layer_hits.keys()),
            "n_layers": len(layer_hits),
            "matched_terms_by_layer": layer_hits,
            "matched_terms": all_terms,
            "n_terms": len(all_terms),
            "name": name or "",
            "description": description or "",
            "content": content or "",
        })
    return pool


def summarize(pool: list[dict], layers: dict[str, list[str]]) -> dict:
    layer_counts = Counter()
    term_counts = Counter()
    for item in pool:
        for layer_id in item["matched_layers"]:
            layer_counts[layer_id] += 1
        for term in item["matched_terms"]:
            term_counts[term] += 1
    return {
        "n_skills": len(pool),
        "by_layer": {lid: layer_counts.get(lid, 0) for lid in layers},
        "top_terms": term_counts.most_common(40),
        "multi_layer": sum(1 for i in pool if i["n_layers"] >= 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True,
                        help="agent_skills_mandatory_only.db")
    parser.add_argument("--keywords", type=Path, default=DEFAULT_KEYWORDS,
                        help="JSON de termos por camada")
    parser.add_argument("--output", type=Path, required=True,
                        help="JSON de saida com o pool filtrado")
    parser.add_argument("--summary", type=Path, default=None,
                        help="JSON opcional com contagens por camada/termo")
    args = parser.parse_args()

    layers = load_keywords(args.keywords)
    rows = load_rows(args.db)
    pool = build_pool(rows, layers)
    stats = summarize(pool, layers)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pool, indent=2, ensure_ascii=False),
                           encoding="utf-8")

    summary_path = args.summary or args.output.with_name(
        args.output.stem + "_summary.json"
    )
    summary_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False),
                            encoding="utf-8")

    print(f"skills escaneadas: {len(rows)}")
    print(f"skills com >=1 tipo de teste: {len(pool)}")
    print(f"skills multi-camada (>=2): {stats['multi_layer']}")
    print("por camada:")
    for lid, n in stats["by_layer"].items():
        print(f"  {lid:20s} {n:6d}")
    print(f"pool salvo em {args.output}")
    print(f"resumo salvo em {summary_path}")


if __name__ == "__main__":
    main()
