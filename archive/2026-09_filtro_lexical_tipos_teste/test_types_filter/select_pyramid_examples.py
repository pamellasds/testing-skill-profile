"""Seleciona 1 skill-exemplo por camada da piramide (unit/integration/e2e)
a partir do pool de test_types, exigindo hits reais de mandatory_terms
registrados no agent_skills_mandatory_only.db (tabela keyword_matches).

Descarta skills cujo unico sinal de blockchain sao termos ambiguos.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
POOL = HERE / "test_types_candidates.json"
DB = ROOT / "gitskills_sample" / "agent_skills_mandatory_only.db"
KEYWORDS = ROOT / "keywords.json"
OUTDIR = HERE / "examples_pyramid"

PYRAMID = ["unit", "integration", "system_e2e"]

# termos que sozinhos nao bastam como evidencia de blockchain
NOISY_ALONE = {
    "integer overflow", "msg.value", "wallet", "transferable",
    "edge case handling", "output validation", "audit report",
    "fungible", "non-fungible", "minting", "burnable", "pallet", "pallets",
    "staking", "layer 0", "layer 1", "layer 2", "layer0", "layer1", "layer2",
    "layer-0", "layer-1", "layer-2", "formal verification", "whitepaper",
    "optimism", "cosmos", "rollup", "nft", "dapp",
}

CORE = {
    "smart contract", "smart-contract", "smart contracts", "smartcontracts",
    "solidity", "ethereum", "blockchain", "web3", "defi", "foundry",
    "hardhat", "echidna", "slither", "evm", "solana", "anchor",
    "erc20", "erc-20", "openzeppelin", "cryptocurrency", "decentralized finance",
}


def parse_hits(raw: str) -> list[str]:
    if not raw:
        return []
    parts = []
    for chunk in raw.replace(";", ",").split(","):
        t = chunk.strip().lower()
        if t:
            parts.append(t)
    return parts


def is_strong(hits: list[str]) -> bool:
    if not hits:
        return False
    if any(h in CORE for h in hits):
        return True
    # algum hit composto contendo core
    if any(any(c in h for c in CORE) for h in hits):
        return True
    non_noisy = [h for h in hits if h not in NOISY_ALONE]
    return bool(non_noisy) and any(len(h) >= 10 for h in non_noisy)


def load_km(db: Path) -> dict[tuple[str, str], list[str]]:
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT repo_full_name, path, mandatory_hits FROM keyword_matches"
        ).fetchall()
    finally:
        con.close()
    return {(r, p): parse_hits(h or "") for r, p, h in rows}


def score(item: dict, layer: str, hits: list[str]) -> tuple:
    layers = set(item.get("matched_layers", []))
    exclusive = layers == {layer}
    name = f"{item.get('name', '')} {item.get('description', '')}".lower()
    testing = any(
        w in name
        for w in (
            "test", "testing", "qa", "pytest", "jest", "e2e",
            "unit", "integration", "foundry", "hardhat", "forge",
        )
    )
    bc_name = any(
        w in name
        for w in (
            "solidity", "smart", "web3", "blockchain", "foundry",
            "hardhat", "defi", "evm", "solana", "contract",
        )
    )
    strong_n = len([h for h in hits if h not in NOISY_ALONE or h in CORE])
    return (
        1 if is_strong(hits) else 0,
        1 if exclusive else 0,
        1 if testing else 0,
        1 if bc_name else 0,
        strong_n,
        -len(layers),
        len(item.get("matched_terms_by_layer", {}).get(layer, [])),
    )


def main() -> None:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    km = load_km(DB)

    # so skills que existem em keyword_matches do mandatory_only
    selected: dict[str, dict] = {}
    report = []

    for layer in PYRAMID:
        cands = []
        for item in pool:
            if layer not in item.get("matched_layers", []):
                continue
            key = (item["repo"], item["path"])
            if key not in km:
                continue
            hits = km[key]
            sc = score(item, layer, hits)
            if sc[0] == 0:
                continue
            cands.append((sc, hits, item))
        cands.sort(key=lambda x: x[0], reverse=True)
        if not cands:
            raise SystemExit(f"nenhum candidato forte para camada {layer}")
        sc, hits, best = cands[0]
        selected[layer] = {"item": best, "mandatory_hits": hits, "score": sc}
        report.append({
            "layer": layer,
            "repo": best["repo"],
            "path": best["path"],
            "name": best.get("name"),
            "matched_layers": best.get("matched_layers"),
            "test_terms": best.get("matched_terms_by_layer", {}).get(layer),
            "mandatory_hits": hits,
            "n_candidates_strong": len(cands),
        })
        print(f"[{layer}] {best['repo']} :: {best.get('name')}")
        print(f"  layers={best.get('matched_layers')}")
        print(f"  mandatory_hits={hits}")
        print(f"  strong_cands={len(cands)}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    folder_map = {
        "unit": "01_unit",
        "integration": "02_integration",
        "system_e2e": "03_system_e2e",
    }
    index = []
    all_parts = [
        "# Exemplos completos — pirâmide de testes (GitSkills / mandatory_only)\n\n"
        "Selecionados a partir de `agent_skills_mandatory_only.db` "
        "(`keyword_matches.mandatory_hits`) + filtro de camadas de teste.\n"
    ]

    for layer in PYRAMID:
        best = selected[layer]["item"]
        hits = selected[layer]["mandatory_hits"]
        folder = folder_map[layer]
        dest_dir = OUTDIR / folder
        dest_dir.mkdir(exist_ok=True)
        skill_path = dest_dir / "SKILL.md"
        meta_path = dest_dir / "meta.json"
        skill_path.write_text(best["content"], encoding="utf-8")
        meta = {
            "layer": layer,
            "source_db": "agent_skills_mandatory_only.db",
            "selection": "keyword_matches.mandatory_hits + test_types layer exclusive/strong",
            "repo": best["repo"],
            "path": best["path"],
            "name": best.get("name"),
            "description": best.get("description"),
            "matched_layers": best.get("matched_layers"),
            "matched_terms_by_layer": best.get("matched_terms_by_layer"),
            "matched_terms": best.get("matched_terms"),
            "mandatory_hits": hits,
            "n_layers": best.get("n_layers"),
            "n_terms": best.get("n_terms"),
        }
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")

        flat = OUTDIR / f"{layer}__{(best.get('name') or 'skill').replace('/', '_')}__SKILL.md"
        flat.write_text(best["content"], encoding="utf-8")

        index.append({
            "layer": layer,
            "dir": folder,
            "repo": best["repo"],
            "path": best["path"],
            "name": best.get("name"),
            "mandatory_hits": hits,
            "skill_file": str(skill_path.relative_to(HERE)),
            "bytes": skill_path.stat().st_size,
            "lines": skill_path.read_text(encoding="utf-8").count("\n") + 1,
        })
        all_parts.append(
            f"\n\n---\n\n# Camada: `{layer}`\n\n"
            f"- **repo:** `{best['repo']}`\n"
            f"- **path:** `{best['path']}`\n"
            f"- **name:** `{best.get('name')}`\n"
            f"- **mandatory_hits:** `{', '.join(hits)}`\n\n"
            f"```markdown\n{best['content']}\n```\n"
        )
        print(f"  wrote {skill_path}")

    (OUTDIR / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUTDIR / "selection_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUTDIR / "ALL_EXAMPLES_COMPLETE.md").write_text(
        "".join(all_parts), encoding="utf-8"
    )
    print(f"\nindex -> {OUTDIR / 'index.json'}")


if __name__ == "__main__":
    main()
