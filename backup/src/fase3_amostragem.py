"""Fase 3 — Amostragem.

1. Grupos de quase-duplicatas no pool (MinHash 128 permutações, LSH 16x8, Jaccard estimado >= 0,8,
   fecho transitivo via union-find), sobre shingles de 5 palavras do conteúdo.
2. Amostra principal: 384 skills sorteadas (ordem aleatória com a seed), no máximo 1 por repositório
   e 1 por grupo de quase-duplicatas.
3. Calibração: as 30 seguintes da mesma ordem, sem repetir repositório nem grupo da principal.
4. Subamostra humana: 60 sorteadas dentro das 384.
5. Planilhas blind por revisor (R1, R2) e chaves separadas.

Uso:
    python src/fase3_amostragem.py
"""
from __future__ import annotations

import json
import random
import re
import zlib
from collections import Counter, defaultdict

import numpy as np

from comum import (ANNOT, DERIVED, INSTRUMENT, RESULTS, SEED, blind_id, display_text, log_run, sha256_file,
                   write_csv, write_json)

N_MAIN, N_CAL, N_SUB = 384, 30, 60
NPERM, BANDS, SHINGLE, JACCARD = 128, 16, 5, 0.8
MERSENNE = (1 << 61) - 1
LAYERS = [("Q1", "Unit"), ("Q2", "Integration"), ("Q3", "Contract"), ("Q4", "UI"), ("Q5", "E2E"),
          ("Q6", "Acceptance"), ("Q7", "Exploratory"), ("Q8", "Automation"), ("Q9", "Web3-specific")]


def minhash(text: str, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w = re.findall(r"\w+", text.lower())
    sh = {" ".join(w[i:i + SHINGLE]) for i in range(max(1, len(w) - SHINGLE + 1))}
    x = np.fromiter((zlib.crc32(s.encode()) for s in sh), dtype=np.uint64)
    return ((np.outer(x, a) + b) % MERSENNE).min(axis=0)  # a < 2^31, x < 2^32: sem overflow


def near_dup_groups(pool: list[dict]) -> list[int]:
    rs = np.random.RandomState(SEED)
    a = rs.randint(1, 1 << 31, NPERM).astype(np.uint64)
    b = rs.randint(0, 1 << 31, NPERM).astype(np.uint64)
    sig = np.stack([minhash(r["content"], a, b) for r in pool])
    parent = list(range(len(pool)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    rows = NPERM // BANDS
    for band in range(BANDS):
        buckets = defaultdict(list)
        for i, s in enumerate(sig[:, band * rows:(band + 1) * rows]):
            buckets[s.tobytes()].append(i)
        for m in (m for m in buckets.values() if len(m) > 1):
            sim = (sig[m][:, None, :] == sig[m][None, :, :]).mean(axis=2)
            for i, j in zip(*np.nonzero(np.triu(sim >= JACCARD, 1))):
                parent[find(m[i])] = find(m[j])
    roots = [find(i) for i in range(len(pool))]
    ids = {r: k for k, r in enumerate(dict.fromkeys(roots))}
    return [ids[r] for r in roots]


def draw(order: list[int], pool: list[dict], n: int, used_repo: set, used_grp: set) -> list[int]:
    out = []
    for i in order:
        if len(out) == n:
            break
        if pool[i]["repo"] not in used_repo and pool[i]["grupo"] not in used_grp:
            out.append(i)
            used_repo.add(pool[i]["repo"]); used_grp.add(pool[i]["grupo"])
    return out


def export_annotation(name: str, items: list[dict]) -> list:
    """Uma pasta por revisor com as 3 planilhas + textos compartilhados. Ordem por ID opaco."""
    base = ANNOT / name
    items = sorted(items, key=lambda r: r["skill_id"])
    (base / "textos").mkdir(parents=True, exist_ok=True)
    for r in items:
        (base / "textos" / f"{r['skill_id']}.txt").write_text(r["texto"], encoding="utf-8")
    for rv in ("R1", "R2"):
        write_csv(base / rv / "skills.csv", [{
            "skill_id": r["skill_id"], "classe_dominio": "", "justificativa_classe": "", "tempo_min": "",
            "status (pendente/concluida)": "pendente", "observacoes": "", "texto_exibido": r["texto"]} for r in items])
        write_csv(base / rv / "camadas.csv", [{
            "skill_id": r["skill_id"], "item": q, "item_nome": lbl, "resposta (YES/NO)": "", "citacao": "",
            "justificativa": "", "contexto (onchain/offchain_web3/web2)": ""} for r in items for q, lbl in LAYERS])
        write_csv(base / rv / "praticas.csv", [], ["skill_id", "categoria (P1-P10)", "polaridade (good/bad)",
                                                   "citacao", "contexto (onchain/offchain_web3/web2)", "justificativa"])
    write_csv(ANNOT / "_chaves" / f"{name}_chave.csv", [
        {k: r[k] for k in ("skill_id", "file_sha", "repo", "path", "grupo", "n_copies", "n_repos")} for r in items])
    return [base, ANNOT / "_chaves" / f"{name}_chave.csv"]


def main() -> None:
    with (DERIVED / "fase1_pool.jsonl").open(encoding="utf-8") as f:
        pool = sorted((json.loads(l) for l in f), key=lambda r: r["file_sha"])
    for r, g in zip(pool, near_dup_groups(pool)):
        r["grupo"] = g
    sizes = Counter(r["grupo"] for r in pool)
    for r in pool:
        r["tamanho_grupo"], r["skill_id"] = sizes[r["grupo"]], blind_id(r["file_sha"])
        r["texto"] = display_text(r["name"], r["description"], r["content"])

    rng = random.Random(SEED)
    order = list(range(len(pool)))
    rng.shuffle(order)
    used_repo, used_grp = set(), set()
    main_idx = draw(order, pool, N_MAIN, used_repo, used_grp)
    cal_idx = draw(order, pool, N_CAL, used_repo, used_grp)
    sub_ids = {pool[i]["skill_id"] for i in rng.sample(main_idx, N_SUB)}

    write_csv(DERIVED / "fase3_grupos_minhash.csv", [
        {k: r[k] for k in ("file_sha", "repo", "path", "grupo", "tamanho_grupo")} for r in pool])
    sample = sorted((pool[i] for i in main_idx), key=lambda r: r["skill_id"])
    write_csv(DERIVED / "fase3_amostra_principal_384.csv", [
        {**{k: r[k] for k in ("skill_id", "file_sha", "repo", "path", "grupo", "n_copies", "n_repos")},
         "na_subamostra_60": int(r["skill_id"] in sub_ids), "texto_exibido": r["texto"]} for r in sample])
    outs = [DERIVED / "fase3_grupos_minhash.csv", DERIVED / "fase3_amostra_principal_384.csv"]
    outs += export_annotation("calibracao_30", [pool[i] for i in cal_idx])
    outs += export_annotation("fase5_subamostra_60", [r for r in sample if r["skill_id"] in sub_ids])

    eligible = len({r["grupo"] for r in pool})  # teto teórico de skills com 1 por grupo
    res = {
        "pool": len(pool), "grupos_quase_dup": len(sizes),
        "skills_em_grupos_com_2_ou_mais": sum(r["tamanho_grupo"] > 1 for r in pool),
        "maior_grupo": max(sizes.values()), "repos_distintos_pool": len({r["repo"] for r in pool}),
        "teto_1_por_grupo": eligible,
        "minhash": {"permutacoes": NPERM, "bandas": BANDS, "shingle_palavras": SHINGLE, "jaccard_min": JACCARD},
        "amostra_principal": len(main_idx), "calibracao": len(cal_idx), "subamostra_humana": len(sub_ids),
        "texto_exibido": "nome + descrição + conteúdo até 8.000 caracteres",
        "skills_truncadas_na_amostra": sum(len(r["content"]) > 8000 for r in sample),
        "instrumento": {"arquivo": str(INSTRUMENT.relative_to(INSTRUMENT.parents[1])), "sha256": sha256_file(INSTRUMENT)},
    }
    write_json(RESULTS / "fase3_amostragem.json", res)
    log_run({k: res[k] for k in ("pool", "grupos_quase_dup", "amostra_principal", "calibracao", "subamostra_humana")},
            outs + [RESULTS / "fase3_amostragem.json"])
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
