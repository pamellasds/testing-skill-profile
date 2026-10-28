"""Amostra e exporta excerpts maiores por camada (unit/integration/e2e)
com sinal blockchain em keyword_matches do mandatory_only."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = json.loads((HERE / "test_types_candidates.json").read_text(encoding="utf-8"))
DB = HERE.parents[1] / "gitskills_sample" / "agent_skills_mandatory_only.db"
OUT = HERE / "_layer_read_more.json"

CORE = (
    "smart contract", "smart-contract", "solidity", "ethereum", "blockchain",
    "foundry", "hardhat", "web3", "defi", "echidna", "forge", "solana",
    "anchor", "starknet", "cairo", "vyper",
)

TEST_HINT = (
    "test", "testing", "fuzz", "invariant", "fork", "foundry", "hardhat",
    "forge", "echidna", "medusa", "coverage", "e2e", "playwright", "clarinet",
    "litesvm", "anvil", "cheatcode",
)

USED = {
    ("youugiuhiuh/web3-demos", ".agents/skills/smart-contract-dev/SKILL.md"),
    ("abelrguezr/hacktricks-skills", "skills/pentesting-web/dapps-DecentralizedApplications/SKILL.MD"),
    ("flare-foundation/flare-ai-skills", "skills/flare-fcc-skill/SKILL.md"),
}

con = sqlite3.connect(DB)
km = {
    (r, p): (h or "")
    for r, p, h in con.execute(
        "SELECT repo_full_name, path, mandatory_hits FROM keyword_matches"
    )
}
con.close()


def excerpts(text: str, n: int = 12) -> list[str]:
    lines = text.replace("\r\n", "\n").split("\n")
    hits = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(w in low for w in TEST_HINT):
            ctx = " ".join(x.strip() for x in lines[max(0, i - 1) : i + 2] if x.strip())
            if ctx and ctx not in hits:
                hits.append(ctx[:220])
        if len(hits) >= n:
            break
    return hits


samples: dict[str, list] = {}
for layer in ("unit", "integration", "system_e2e"):
    cands = []
    for item in POOL:
        if layer not in item.get("matched_layers", []):
            continue
        key = (item["repo"], item["path"])
        if key in USED or key not in km:
            continue
        hits = km[key].lower()
        if not any(c in hits for c in CORE):
            continue
        name = f"{item.get('name', '')} {item.get('description', '')}".lower()
        testing = sum(1 for w in TEST_HINT if w in name)
        exclusive = 1 if set(item.get("matched_layers", [])) == {layer} else 0
        # prefer richer content
        cands.append((exclusive, testing, len(item.get("content") or ""), item, hits))
    cands.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

    picked = []
    seen_names = set()
    for excl, testing, _, item, hits in cands:
        nm = (item.get("name") or "").lower()
        # skip near-duplicate names
        if nm in seen_names:
            continue
        # skip pure orchestrators for e2e if we already have enough test-ish
        seen_names.add(nm)
        content = item.get("content") or ""
        picked.append({
            "repo": item["repo"],
            "path": item["path"],
            "name": item.get("name"),
            "description": (item.get("description") or "")[:350],
            "matched_layers": item.get("matched_layers"),
            "mandatory_hits": hits,
            "exclusive": bool(excl),
            "test_lines": excerpts(content, 15),
            "head": content[:1800],
            "chars": len(content),
        })
        if len(picked) >= 6:
            break
    samples[layer] = picked

OUT.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")
for layer, items in samples.items():
    print("==", layer, len(items))
    for it in items:
        print(f"- {it['name']} | excl={it['exclusive']} | layers={it['matched_layers']}")
        print(f"  {it['repo']}")
        print(f"  test_lines={len(it['test_lines'])} chars={it['chars']}")
