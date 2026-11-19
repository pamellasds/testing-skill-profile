"""Fase 1 — Seleção das skills.

1. Recorte de domínio (termos fortes/fracos) sobre as skills com dedup_primary = 1.
2. Filtro de teste (frases compostas) sobre o recorte -> pool de candidatas.
3. Nº de cópias e de repositórios por conteúdo (file_sha).
4. Planilhas para revisão dos termos e para validação da seleção (100 + 100, blind).

Uso:
    python src/fase1_selecao.py              # executa a seleção e gera as planilhas
    python src/fase1_selecao.py --precisao   # após a anotação: precisão com IC 95%
    python src/fase1_selecao.py --db <GitSkills completo>.db   # mesma execução no dataset completo
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

from comum import (ANNOT, CONFIG, DB, DERIVED, RESULTS, SEED, blind_id, compile_terms, display_text, hits,
                   log_run, read_csv, sha256_file, wilson, write_csv, write_json)

DOM = json.loads((CONFIG / "termos_dominio.json").read_text())
TST = json.loads((CONFIG / "termos_teste.json").read_text())["termos"]
RX_STRONG, RX_WEAK, RX_TEST = compile_terms(DOM["fortes"]), compile_terms(DOM["fracos"]), compile_terms(TST)
VAL = ANNOT / "fase1_validacao"
KEYS = ANNOT / "_chaves"


def in_domain(strong: list, weak: list) -> bool:
    return bool(strong) or len(weak) >= 2


def match(row: tuple) -> dict | None:
    repo, path, sha, name, desc, content = row
    text = f"{name or ''}\n{desc or ''}\n{content or ''}".lower()
    strong, weak = hits(RX_STRONG, text), hits(RX_WEAK, text)
    if not in_domain(strong, weak):
        return None
    return {"file_sha": sha, "repo": repo, "path": path, "name": name or "", "description": desc or "",
            "content": content or "", "strong": strong, "weak": weak, "test": hits(RX_TEST, text)}


def term_review(all_hits: Counter, exclusive: Counter, terms: list[str], lista: str) -> list[dict]:
    return [{"lista": lista, "termo_regex": t, "skills_com_termo": all_hits[t],
             "skills_que_so_entram_por_ele": exclusive[t], "R1_decisao (manter/remover/mover)": "",
             "R2_decisao (manter/remover/mover)": "", "comentario": ""} for t in terms]


def run(db: Path) -> None:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, check_same_thread=False)  # cursor lido pela thread do Pool
    copies = {sha: (n, r) for sha, n, r in con.execute(
        "SELECT file_sha, COUNT(*), COUNT(DISTINCT repo_full_name) FROM artifacts GROUP BY file_sha")}
    n_scanned = con.execute("SELECT COUNT(*) FROM artifacts WHERE dedup_primary = 1").fetchone()[0]
    rows = con.execute("SELECT repo_full_name, path, file_sha, name, description, content "
                       "FROM artifacts WHERE dedup_primary = 1 ORDER BY file_sha")
    with Pool() as p:
        recorte = [r for r in p.imap(match, rows, chunksize=200) if r]
    con.close()

    pool = [r for r in recorte if r["test"]]
    for r in recorte:
        r["n_copies"], r["n_repos"] = copies[r["file_sha"]]

    # contagens por termo e contribuição exclusiva (a skill sairia sem aquele termo)
    c = {k: Counter() for k in ("strong", "weak", "test", "x_strong", "x_weak", "x_test")}
    for r in recorte:
        c["strong"].update(r["strong"]); c["weak"].update(r["weak"])
        c["x_strong"].update(t for t in r["strong"] if not in_domain([s for s in r["strong"] if s != t], r["weak"]))
        c["x_weak"].update(t for t in r["weak"] if not in_domain(r["strong"], [w for w in r["weak"] if w != t]))
    for r in pool:
        c["test"].update(r["test"])
        if len(r["test"]) == 1:
            c["x_test"][r["test"][0]] += 1

    DERIVED.mkdir(parents=True, exist_ok=True)
    pool_path = DERIVED / "fase1_pool.jsonl"
    with pool_path.open("w", encoding="utf-8") as f:
        for r in pool:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    idx_fields = ["file_sha", "repo", "path", "name", "n_copies", "n_repos", "strong", "weak", "test"]
    write_csv(DERIVED / "fase1_recorte_indice.csv",
              [{k: ("; ".join(r[k]) if isinstance(r[k], list) else r[k]) for k in idx_fields} for r in recorte])

    rev = (term_review(c["strong"], c["x_strong"], DOM["fortes"], "dominio_forte (contado no recorte)")
           + term_review(c["weak"], c["x_weak"], DOM["fracos"], "dominio_fraco (contado no recorte)")
           + term_review(c["test"], c["x_test"], TST, "teste (contado no pool)"))
    write_csv(ANNOT / "fase1_revisao_termos/revisao_termos.csv", rev)

    # validação da seleção: 100 do recorte ("é blockchain/Web3?") e 100 do pool ("fala de teste?")
    rng = random.Random(SEED)
    outs = [pool_path, DERIVED / "fase1_recorte_indice.csv", ANNOT / "fase1_revisao_termos/revisao_termos.csv"]
    for nome, base, pergunta in (("dominio", recorte, "e_blockchain_web3 (S/N)"),
                                 ("teste", pool, "fala_de_teste (S/N)")):
        amostra = sorted(rng.sample(base, 100), key=lambda r: blind_id(r["file_sha"]))
        write_csv(VAL / f"validacao_{nome}_100_blind.csv",
                  [{"skill_id": blind_id(r["file_sha"]), pergunta: "", "observacao": "",
                    "texto_exibido": display_text(r["name"], r["description"], r["content"])} for r in amostra])
        write_csv(KEYS / f"validacao_{nome}_100_chave.csv",
                  [{"skill_id": blind_id(r["file_sha"]), "file_sha": r["file_sha"], "repo": r["repo"],
                    "path": r["path"], "strong": "; ".join(r["strong"]), "weak": "; ".join(r["weak"]),
                    "test": "; ".join(r["test"])} for r in amostra])
        outs += [VAL / f"validacao_{nome}_100_blind.csv", KEYS / f"validacao_{nome}_100_chave.csv"]

    res = {
        "db": db.name, "db_bytes": db.stat().st_size,
        "config_sha256": {p.name: sha256_file(p) for p in (CONFIG / "termos_dominio.json", CONFIG / "termos_teste.json")},
        "n_termos": {"fortes": len(DOM["fortes"]), "fracos": len(DOM["fracos"]), "teste": len(TST)},
        "skills_distintas_escaneadas": n_scanned,
        "recorte_dominio": len(recorte),
        "recorte_por_regra": {"com_forte": sum(bool(r["strong"]) for r in recorte),
                              "so_fracos_ge2": sum(not r["strong"] for r in recorte)},
        "pool_candidatas": len(pool),
        "pool_copias_total": sum(r["n_copies"] for r in pool),
        "pool_repos_distintos_representante": len({r["repo"] for r in pool}),
        "pool_conteudos_com_copias": sum(r["n_copies"] > 1 for r in pool),
        "pool_max_copias": max(r["n_copies"] for r in pool),
        "top_termos_teste_no_pool": c["test"].most_common(15),
        "top_fortes_no_recorte": c["strong"].most_common(15),
    }
    write_json(RESULTS / "fase1_selecao.json", res)
    log_run({k: res[k] for k in ("skills_distintas_escaneadas", "recorte_dominio", "pool_candidatas")},
            outs + [RESULTS / "fase1_selecao.json"])
    print(json.dumps(res, indent=2, ensure_ascii=False))


def precisao() -> None:
    res = {}
    for nome, col in (("dominio", "e_blockchain_web3 (S/N)"), ("teste", "fala_de_teste (S/N)")):
        ans = [r[col].strip().upper()[:1] for r in read_csv(VAL / f"validacao_{nome}_100_blind.csv")]
        k, n = ans.count("S"), ans.count("S") + ans.count("N")
        res[nome] = {"anotadas": n, "positivas": k, "precisao": round(k / n, 4) if n else None,
                     "ic95_wilson": wilson(k, n),
                     "meta_0_90": {"estimativa_pontual": bool(n) and k / n >= 0.90,
                                   "limite_inferior_ic": bool(n) and wilson(k, n)[0] >= 0.90}}
    write_json(RESULTS / "fase1_validacao.json", res)
    log_run({k: v["precisao"] for k, v in res.items()}, [RESULTS / "fase1_validacao.json"])
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--precisao", action="store_true")
    a = ap.parse_args()
    precisao() if a.precisao else run(a.db)
