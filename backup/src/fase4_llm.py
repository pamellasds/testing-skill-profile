"""Fase 4 — Classificação por LLM (Mistral).

O prompt de sistema é instrument/instrumento.md, sem alterações (seu SHA-256 é registrado). Para cada skill,
a LLM devolve o JSON do §7 do instrumento. Checagem automática por item (camada com YES e cada prática):
enum válido, citação de 5 a 40 palavras que existe no texto exibido e não se repete entre itens. Os itens
que falham são devolvidos uma vez ao modelo com a lista de erros; se falharem de novo, viram UNCERTAIN.

Conjuntos:
    calibracao_30   as 30 de calibração (Fase 2)
    principal_384   a amostra principal (rodar só com o instrumento congelado)
    subamostra_60   as 60 da subamostra, para medir estabilidade (--execucoes 3)

Uso:
    python src/fase4_llm.py --conjunto calibracao_30
    python src/fase4_llm.py --conjunto subamostra_60 --execucoes 3
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter

from comum import ANNOT, DERIVED, INSTRUMENT, RESULTS, ROOT, log_run, sha256_file, write_csv, write_json

MODEL = "ministral-14b-2512"  # versão fixa; mistral-medium/small/large dão 429/403 nesta conta
API = "https://api.mistral.ai/v1/chat/completions"
LAYERS = [f"Q{i}" for i in range(1, 10)]
CONTEXTS, DOMAINS = {"onchain", "offchain_web3", "web2"}, {"onchain", "offchain_web3", "misto", "web2_incidental",
                                                           "indeterminado"}
CATEGORIES = {f"P{i}" for i in range(1, 11)}
OUT = DERIVED / "fase4_llm"
FIX_PROMPT = ("Some items failed the automatic evidence check. For each item listed below, either (a) replace its "
              "quote with 5-40 words copied character by character from ONE contiguous passage of the skill text "
              "(do not join a heading with the code below it, do not add, drop or reorder words) and give a valid "
              "context, or (b) if no such passage exists, set that layer's answer to NO or remove that practice. "
              "Return the complete JSON object again.\n")
csv.field_size_limit(10**8)


def load_texts(conjunto: str) -> dict[str, str]:
    if conjunto == "calibracao_30":
        return {p.stem: p.read_text(encoding="utf-8") for p in sorted((ANNOT / "calibracao_30/textos").glob("*.txt"))}
    with (DERIVED / "fase3_amostra_principal_384.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r["skill_id"]: r["texto_exibido"] for r in rows if conjunto == "principal_384" or r["na_subamostra_60"] == "1"}


class Mistral:
    """Rotaciona as chaves MISTRAL_* do .env em 429/401/403."""

    def __init__(self) -> None:
        self.keys = [l.split("=", 1)[1].strip() for l in (ROOT / ".env").read_text().splitlines()
                     if re.match(r"MISTRAL_\d+=", l)]
        self.i = 0

    def chat(self, messages: list[dict]) -> str:
        body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 6000,
                           "response_format": {"type": "json_object"}}).encode()
        for attempt in range(12):
            req = urllib.request.Request(API, body, {"Authorization": f"Bearer {self.keys[self.i]}",
                                                     "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return json.load(r)["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                if e.code not in (429, 401, 403, 500, 502, 503):
                    raise
                self.i = (self.i + 1) % len(self.keys)
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(min(60, 2 ** attempt))
        raise RuntimeError("API indisponível após 12 tentativas")


def norm(s: str) -> str:
    s = re.sub(r"[*`_]", "", s.replace("’", "'").replace("“", '"').replace("”", '"'))
    return re.sub(r"\s+", " ", s).strip().lower()


def items(res: dict) -> dict[str, dict]:
    """Itens que exigem evidência: camadas com YES e cada prática."""
    out = {q: v for q, v in (res.get("layers") or {}).items() if isinstance(v, dict) and v.get("answer") == "YES"}
    out.update({f"practice[{i}]": p for i, p in enumerate(res.get("practices") or []) if isinstance(p, dict)})
    return out


def check(res: dict, text: str) -> dict[str, str]:
    """Erro por item (vazio = item válido)."""
    errors, seen, ntext = {}, Counter(), norm(text)
    its = items(res)
    for it in its.values():
        seen[norm(it.get("quote") or "")] += 1
    for key, it in its.items():
        q = norm(it.get("quote") or "")
        problems = []
        if not 5 <= len(q.split()) <= 40:
            problems.append("quote must have 5-40 words")
        if q and q not in ntext:
            problems.append("quote is not a literal, contiguous excerpt of the text")
        if seen[q] > 1:
            problems.append("the same quote justifies another item")
        if it.get("context") not in CONTEXTS:
            problems.append("context must be onchain, offchain_web3 or web2")
        if key.startswith("practice") and (it.get("category") not in CATEGORIES or it.get("polarity") not in ("good", "bad")):
            problems.append("category must be P1-P10 and polarity good or bad")
        if problems:
            errors[key] = "; ".join(problems)
    return errors


def classify(api: Mistral, system: str, text: str) -> dict:
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": f"Skill text:\n<<<\n{text}\n>>>\nReturn only the JSON object."}]
    raw1 = api.chat(messages)
    res = json.loads(raw1)
    errors = check(res, text)
    log = {"tentativas": 1, "erros_tentativa_1": errors}
    if errors:  # segunda tentativa só para os itens com erro
        fix = FIX_PROMPT + "\n".join(f"- {k}: {v}" for k, v in errors.items())
        res2 = json.loads(api.chat(messages + [{"role": "assistant", "content": raw1}, {"role": "user", "content": fix}]))
        log["tentativas"] = 2
        # camadas: substitui só as que falharam; práticas: usa a lista nova (índices mudam entre tentativas)
        for q in (k for k in errors if k in LAYERS):
            res.setdefault("layers", {})[q] = (res2.get("layers") or {}).get(q, res["layers"].get(q))
        if any(k.startswith("practice") for k in errors):
            res["practices"] = res2.get("practices") or []
        errors = check(res, text)
        for key in errors:
            target = res["layers"][key] if key in LAYERS else res["practices"][int(key[9:-1])]
            target["status"] = "UNCERTAIN"
        log["erros_finais"] = errors
    res["_checagem"] = log
    return res


def to_sheets(conjunto: str, run: int, results: dict[str, dict]) -> list:
    """Exporta no mesmo formato das planilhas de R1/R2, para comparar na calibração / Fase 5."""
    base = OUT / f"{conjunto}_exec{run}"
    skills, layers, practices = [], [], []
    for sid, res in sorted(results.items()):
        skills.append({"skill_id": sid, "classe_dominio": res.get("domain_class", ""),
                       "n_uncertain": sum(1 for it in items(res).values() if it.get("status") == "UNCERTAIN")})
        for q in LAYERS:
            v = (res.get("layers") or {}).get(q) or {}
            layers.append({"skill_id": sid, "item": q, "resposta": v.get("status") or v.get("answer", ""),
                           "citacao": v.get("quote") or "", "justificativa": v.get("justification") or "",
                           "contexto": v.get("context") or ""})
        for p in res.get("practices") or []:
            practices.append({"skill_id": sid, "categoria": p.get("category", ""), "polaridade": p.get("polarity", ""),
                              "status": p.get("status", "OK"), "citacao": p.get("quote", ""),
                              "contexto": p.get("context", ""), "justificativa": p.get("justification", "")})
    write_csv(base / "skills.csv", skills)
    write_csv(base / "camadas.csv", layers)
    write_csv(base / "praticas.csv", practices, ["skill_id", "categoria", "polaridade", "status", "citacao",
                                                 "contexto", "justificativa"])
    return [base]


def summarize(results: dict[str, dict]) -> dict:
    layer_yes = Counter(q for r in results.values() for q, v in (r.get("layers") or {}).items()
                        if isinstance(v, dict) and v.get("answer") == "YES" and v.get("status") != "UNCERTAIN")
    its = [it for r in results.values() for it in items(r).values()]
    return {"skills": len(results),
            "classe_dominio": Counter(r.get("domain_class") for r in results.values()),
            "yes_por_camada": {q: layer_yes[q] for q in LAYERS},
            "praticas": Counter(f"{p.get('category')}_{p.get('polarity')}" for r in results.values()
                                for p in r.get("practices") or [] if p.get("status") != "UNCERTAIN"),
            "itens_com_evidencia": len(its), "itens_uncertain": sum(it.get("status") == "UNCERTAIN" for it in its),
            "skills_com_2a_tentativa": sum(r["_checagem"]["tentativas"] == 2 for r in results.values())}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conjunto", choices=["calibracao_30", "principal_384", "subamostra_60"], required=True)
    ap.add_argument("--execucoes", type=int, default=1)
    a = ap.parse_args()

    system, texts, api = INSTRUMENT.read_text(encoding="utf-8"), load_texts(a.conjunto), Mistral()
    OUT.mkdir(parents=True, exist_ok=True)
    res_all, outs = {}, []
    for run in range(1, a.execucoes + 1):
        ckpt = OUT / f"{a.conjunto}_exec{run}.jsonl"  # checkpoint: retoma de onde parou
        done = {json.loads(l)["skill_id"]: json.loads(l)["resultado"] for l in ckpt.open()} if ckpt.exists() else {}
        with ckpt.open("a", encoding="utf-8") as f:
            for n, (sid, text) in enumerate(texts.items(), 1):
                if sid in done:
                    continue
                try:
                    done[sid] = classify(api, system, text)
                except (json.JSONDecodeError, RuntimeError) as e:
                    print(f"  {sid}: falhou ({e}); será refeita na próxima execução do script")
                    continue
                f.write(json.dumps({"skill_id": sid, "resultado": done[sid]}, ensure_ascii=False) + "\n")
                f.flush()
                print(f"exec {run} [{n}/{len(texts)}] {sid} tentativas={done[sid]['_checagem']['tentativas']}")
        res_all[f"exec{run}"] = summarize(done)
        outs += [ckpt] + to_sheets(a.conjunto, run, done)

    res = {"modelo": MODEL, "temperatura": 0, "instrumento_sha256": sha256_file(INSTRUMENT),
           "prompt_correcao_sha256": hashlib.sha256(FIX_PROMPT.encode()).hexdigest(),
           "conjunto": a.conjunto, "execucoes": res_all}
    write_json(RESULTS / f"fase4_{a.conjunto}.json", res)
    log_run({"modelo": MODEL, "conjunto": a.conjunto, "execucoes": a.execucoes,
             "instrumento_sha256": res["instrumento_sha256"][:12]}, outs + [RESULTS / f"fase4_{a.conjunto}.json"])
    print(json.dumps(res, indent=1, ensure_ascii=False, default=dict))


if __name__ == "__main__":
    main()
