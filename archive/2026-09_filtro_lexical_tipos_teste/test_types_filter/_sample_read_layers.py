"""Amostra 2 skills extras por camada da piramide com sinal blockchain forte."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = json.loads((HERE / "test_types_candidates.json").read_text())
DB = HERE.parents[1] / "gitskills_sample" / "agent_skills_mandatory_only.db"
OUT = HERE / "_layer_samples.json"

CORE = (
    "smart contract", "smart-contract", "solidity", "ethereum", "blockchain",
    "foundry", "hardhat", "web3", "defi", "echidna", "forge",
)

con = sqlite3.connect(DB)
km = {
    (r, p): (h or "")
    for r, p, h in con.execute(
        "SELECT repo_full_name, path, mandatory_hits FROM keyword_matches"
    )
}
con.close()

# already used examples
used = {
    ("youugiuhiuh/web3-demos", ".agents/skills/smart-contract-dev/SKILL.md"),
    ("abelrguezr/hacktricks-skills", "skills/pentesting-web/dapps-DecentralizedApplications/SKILL.MD"),
    ("flare-foundation/flare-ai-skills", "skills/flare-fcc-skill/SKILL.md"),
}

samples = {}
for layer in ("unit", "integration", "system_e2e"):
    cands = []
    for item in POOL:
        if layer not in item.get("matched_layers", []):
            continue
        key = (item["repo"], item["path"])
        if key in used or key not in km:
            continue
        hits = km[key].lower()
        if not any(c in hits for c in CORE):
            continue
        exclusive = set(item.get("matched_layers", [])) == {layer}
        name = f"{item.get('name','')} {item.get('description','')}".lower()
        testing = any(w in name for w in ("test", "testing", "foundry", "hardhat", "forge", "e2e", "fuzz"))
        cands.append((1 if exclusive else 0, 1 if testing else 0, len(hits), item, hits))
    cands.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    picked = []
    for _, _, _, item, hits in cands[:3]:
        content = item["content"]
        picked.append({
            "repo": item["repo"],
            "path": item["path"],
            "name": item.get("name"),
            "description": (item.get("description") or "")[:300],
            "matched_layers": item.get("matched_layers"),
            "mandatory_hits": hits,
            "excerpt": content[:2500],
            "len": len(content),
        })
    samples[layer] = picked

OUT.write_text(json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")
for layer, items in samples.items():
    print("==", layer, len(items))
    for i in items:
        print("-", i["name"], "|", i["repo"])
        print("  layers", i["matched_layers"])
        print("  hits", i["mandatory_hits"][:120])
