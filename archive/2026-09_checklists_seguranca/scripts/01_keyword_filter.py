"""Filtra agent_skills_mandatory_only.db pela presenca de nomes proprios de
checklists, ferramentas e firmas/plataformas de auditoria de smart
contracts. Reproduz o pool de 1.592 skills descrito no relatorio de
metodologia (Secao 2): termos fortes contam sozinhos, termos fracos so
contam combinados com pelo menos um termo forte.

Uso:
    python 01_keyword_filter.py --db <agent_skills_mandatory_only.db> --output <pool.json>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

STRONG_TERMS = [
    # checklists / padroes
    "scsvs", "swc registry", "swc-1", "owasp smart contract", "dasp",
    "consensys", "consensys diligence", "ethereum smart contract best practices",
    "building-secure-contracts", "building secure contracts",
    "not-so-smart-contracts", "secure development workflow",
    "veridise security checklist",
    # ferramentas / scanners
    "slither", "mythril", "echidna", "medusa", "manticore", "oyente",
    "rattle", "securify", "solidity-coverage", "eth-security-toolbox",
    # firmas / plataformas
    "trail of bits", "certik", "halborn", "peckshield", "slowmist",
    "zellic", "quantstamp", "hacken", "cyfrin", "solodit", "sherlock",
    "code4rena", "immunefi", "spearbit", "sigma prime", "ackee blockchain",
    "least authority", "dedaub",
]

WEAK_TERMS = ["owasp", "owasp top 10", "openzeppelin", "cwe-", "stride"]


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


def matched_terms_for(text: str) -> list[str]:
    """Termos fracos so contam se houver pelo menos um termo forte no texto."""
    strong_hits = [t for t in STRONG_TERMS if t in text]
    if not strong_hits:
        return []
    weak_hits = [t for t in WEAK_TERMS if t in text]
    return strong_hits + weak_hits


def build_pool(rows: list[tuple]) -> list[dict]:
    pool = []
    for repo, path, content, name, description in rows:
        text = f"{content or ''} {name or ''} {description or ''}".lower()
        terms = matched_terms_for(text)
        if not terms:
            continue
        pool.append({
            "repo": repo,
            "path": path,
            "matched_terms": sorted(terms),
            "n_terms": len(terms),
            "name": name or "",
            "description": description or "",
            "content": content or "",
        })
    return pool


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="agent_skills_mandatory_only.db")
    parser.add_argument("--output", type=Path, required=True, help="JSON de saida com o pool filtrado")
    args = parser.parse_args()

    rows = load_rows(args.db)
    pool = build_pool(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pool, indent=2, ensure_ascii=False))

    print(f"skills escaneadas: {len(rows)}")
    print(f"skills no pool (>=1 termo forte): {len(pool)}")
    print(f"salvo em {args.output}")


if __name__ == "__main__":
    main()
