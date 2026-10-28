"""Piloto RQ2: Prompt A (checklist CTFL multi-label) + derivacao de skills_evidenced.

Reusa o padrao de API/rotacao de chaves de scripts/02_llm_classifier.py.
Roda por padrao nas 3 skills da piramide + 3 do pool (fuzz / fork / regression).

Uso:
    python data/test_types_filter/run_llm_checklist_pilot.py
    python data/test_types_filter/run_llm_checklist_pilot.py --max-skills 3
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
CANDIDATES = Path(__file__).resolve().parent / "test_types_candidates.json"
EXAMPLES_INDEX = Path(__file__).resolve().parent / "examples_pyramid" / "index.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "llm_checklist_pilot_results.json"
API_URL = "https://api.mistral.ai/v1/chat/completions"
MAX_CONTENT_CHARS = 14000

# Labels por dimensao (Prompt B / regras)
LEVEL_LABELS = [
    "component", "component_integration", "system", "system_integration", "acceptance",
]
TYPE_LABELS = ["functional", "non_functional"]
NF_ASPECTS = ["performance", "security", "usability", "reliability", "compatibility"]
TECHNIQUE_LABELS = [
    "black_box", "white_box", "experience_based",
    "equivalence_partitioning", "boundary_value_analysis", "decision_table_testing",
    "state_transition_testing", "statement_testing", "branch_testing",
    "error_guessing", "exploratory_testing", "checklist_based_testing",
]
PURPOSE_LABELS = ["confirmation", "regression"]
STRATEGY_LABELS = ["test_pyramid"]
EXTENSION_LABELS = [
    "smoke_testing", "mutation_testing", "fuzz_testing", "property_invariant_testing",
    "fork_testing", "load_testing", "stress_testing", "contract_testing",
]

PROMPT_A = """Voce e um anotador de mineracao de repositorios. Analise a agent skill abaixo
e RESPONDA O CHECKLIST de evidencias de testing skills. NAO avalie qualidade,
corretude ou proficiencia. Classifique apenas o que o TEXTO instrui/evidencia.

Principio: skill evidenced / skill instructed — nao skill proficiency.
Ausencia de evidencia != "o autor nao conhece X".
Multi-label permitido SOMENTE com evidencia independente por label.
Todo YES exige quote VERBATIM (substring literal do content; sem reticencias "...").

repo: {repo}
path: {path}
name: {name}
description: {description}
content:
\"\"\"
{content}
\"\"\"

Retorne APENAS um JSON (sem markdown) com esta estrutura exata:

{{
  "artifact_type": "test_guidance_skill | not_test_related | uncertain",
  "confidence": "high | medium | low",
  "checklist": {{
    "E0": {{
      "is_test_related": {{"answer": "YES|NO|UNCERTAIN", "evidence": {{"quote": "...", "reason": "..."}} | null}},
      "has_observable_guidance": {{"answer": "YES|NO|UNCERTAIN", "evidence": {{"quote": "...", "reason": "..."}} | null}}
    }},
    "test_level": {{
      "component": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "component_integration": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "system": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "system_integration": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "acceptance": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
    }},
    "test_type": {{
      "functional": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "non_functional": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "non_functional_aspects": {{
        "performance": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
        "security": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
        "usability": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
        "reliability": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
        "compatibility": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
      }}
    }},
    "test_technique": {{
      "black_box": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "white_box": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "experience_based": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "equivalence_partitioning": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "boundary_value_analysis": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "decision_table_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "state_transition_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "statement_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "branch_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "error_guessing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "exploratory_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "checklist_based_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
    }},
    "test_purpose": {{
      "confirmation": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "regression": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
    }},
    "test_strategy": {{
      "test_pyramid": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
    }},
    "extensions": {{
      "smoke_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "mutation_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "fuzz_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "property_invariant_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "fork_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "load_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "stress_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}},
      "contract_testing": {{"answer": "YES|NO|UNCERTAIN", "evidence": null}}
    }}
  }}
}}

Definicoes (ISTQB CTFL v4.0.1 — operacionalizacao para texto de skill):
- component: instrui testes de unidade/componente isolado (mocks/harness ok)
- component_integration: interacao entre componentes/interfaces
- system: sistema integrado / fluxo amplo
- system_integration: integracao entre sistemas
- acceptance: cenarios de negocio/aceitacao/stakeholders
- functional: o que o sistema deve fazer
- non_functional: como se comporta (qualidade); aspects se aplicavel
- techniques: so marque especificas com evidencia clara; exploratory/checklist so com mencao explicita
- confirmation / regression: purpose, NAO level
- test_pyramid: estrategia de distribuicao por granularidade, NAO level
- extensions: fora do CTFL; so com evidencia explicita

Se answer != YES, evidence deve ser null.
Se E0.is_test_related = NO, deixe as demais como NO com evidence null e confidence low.
"""


class KeyRotator:
    def __init__(self, env_path: Path):
        keys = [v for k, v in dotenv_values(env_path).items() if k.startswith("MISTRAL_") and v]
        if not keys:
            raise RuntimeError(f"nenhuma variavel MISTRAL_* em {env_path}")
        self._keys = keys
        self._index = 0

    @property
    def current(self) -> str:
        return self._keys[self._index]

    def rotate(self) -> None:
        self._index = (self._index + 1) % len(self._keys)

    def __len__(self) -> int:
        return len(self._keys)


def parse_json_content(raw: str) -> dict:
    """Parse JSON da LLM com fallbacks leves (cercas markdown / quebras em strings)."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # remove control chars ilegais em JSON (exceto \n \r \t)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # tenta extrair o maior objeto {...}
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        return json.loads(cleaned[start : end + 1])
    raise


def call_mistral(prompt: str, model: str, rotator: KeyRotator, max_attempts: int = 8) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        headers = {"Authorization": f"Bearer {rotator.current}", "Content-Type": "application/json"}
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 30))
            continue
        if resp.status_code == 429:
            rotator.rotate()
            time.sleep(min(2 ** attempt, 30))
            continue
        if resp.status_code in (401, 403):
            rotator.rotate()
            last_error = RuntimeError(f"HTTP {resp.status_code}")
            continue
        if resp.status_code >= 500:
            last_error = RuntimeError(f"HTTP {resp.status_code}")
            time.sleep(min(2 ** attempt, 30))
            continue
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            return parse_json_content(raw)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            last_error = exc
            # pede JSON limpo na proxima tentativa
            prompt = prompt + "\n\nATENCAO: a resposta anterior nao era JSON valido. Retorne SOMENTE JSON valido."
            time.sleep(min(2 ** attempt, 10))
            continue
    raise RuntimeError(f"falha Mistral apos {max_attempts} tentativas: {last_error}")


_WHITESPACE_RE = re.compile(r"\s+")
_MARKDOWN_DECORATION_RE = re.compile(r"[`*_#|]")


def _normalize(text: str) -> str:
    text = _MARKDOWN_DECORATION_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def is_verbatim(quote: str, content: str) -> bool:
    return bool(quote) and _normalize(quote) in _normalize(content)


def iter_checklist_cells(checklist: dict):
    """Yield (path, cell) for every answerable leaf."""
    if not isinstance(checklist, dict):
        return
    for section, body in checklist.items():
        if not isinstance(body, dict):
            continue
        for key, cell in body.items():
            if key == "non_functional_aspects" and isinstance(cell, dict):
                for aspect, acell in cell.items():
                    if isinstance(acell, dict) and "answer" in acell:
                        yield f"{section}.non_functional_aspects.{aspect}", acell
                continue
            if isinstance(cell, dict) and "answer" in cell:
                yield f"{section}.{key}", cell


def verify_yes_quotes(checklist: dict, content: str) -> list[str]:
    problems = []
    for path, cell in iter_checklist_cells(checklist):
        if str(cell.get("answer", "")).upper() != "YES":
            continue
        ev = cell.get("evidence") or {}
        quote = ev.get("quote", "") if isinstance(ev, dict) else ""
        if not is_verbatim(quote, content):
            problems.append(path)
    return problems


def derive_skills(checklist: dict, content: str) -> tuple[dict, list[str]]:
    """Prompt B em codigo: so YES com quote verbatim vira skill evidenciada."""
    skills = {
        "test_level": [],
        "test_type": [],
        "non_functional_aspects": [],
        "test_technique": [],
        "test_purpose": [],
        "test_strategy": [],
        "extensions": [],
    }
    dropped = []
    mapping = [
        ("test_level", LEVEL_LABELS, skills["test_level"]),
        ("test_type", TYPE_LABELS, skills["test_type"]),
        ("test_technique", TECHNIQUE_LABELS, skills["test_technique"]),
        ("test_purpose", PURPOSE_LABELS, skills["test_purpose"]),
        ("test_strategy", STRATEGY_LABELS, skills["test_strategy"]),
        ("extensions", EXTENSION_LABELS, skills["extensions"]),
    ]
    for section, labels, out in mapping:
        block = (checklist or {}).get(section) or {}
        for label in labels:
            cell = block.get(label) or {}
            if str(cell.get("answer", "")).upper() != "YES":
                continue
            ev = cell.get("evidence") or {}
            quote = ev.get("quote", "") if isinstance(ev, dict) else ""
            if is_verbatim(quote, content):
                out.append(label)
            else:
                dropped.append(f"{section}.{label}")

    nf = ((checklist or {}).get("test_type") or {}).get("non_functional_aspects") or {}
    for aspect in NF_ASPECTS:
        cell = nf.get(aspect) or {}
        if str(cell.get("answer", "")).upper() != "YES":
            continue
        ev = cell.get("evidence") or {}
        quote = ev.get("quote", "") if isinstance(ev, dict) else ""
        if is_verbatim(quote, content):
            skills["non_functional_aspects"].append(aspect)
        else:
            dropped.append(f"test_type.non_functional_aspects.{aspect}")
    return skills, dropped


def truncate_content(content: str) -> tuple[str, bool]:
    if len(content) <= MAX_CONTENT_CHARS:
        return content, False
    return content[:MAX_CONTENT_CHARS], True


def load_pyramid_examples() -> list[dict]:
    index = json.loads(EXAMPLES_INDEX.read_text())
    items = []
    base = Path(__file__).resolve().parent
    for entry in index:
        skill_path = base / entry["skill_file"]
        content = skill_path.read_text(encoding="utf-8", errors="replace")
        items.append({
            "source": "examples_pyramid",
            "pilot_layer_hint": entry["layer"],
            "repo": entry["repo"],
            "path": entry["path"],
            "name": entry.get("name", ""),
            "description": "",
            "content": content,
            "matched_layers": [entry["layer"]],
        })
    return items


def load_extra_from_candidates(n_per: int = 1) -> list[dict]:
    """Pega 1 skill por camada alvo do pool (preferindo nomes blockchain-ish)."""
    wanted = ["fuzz_property", "fork", "regression"]
    pool = json.loads(CANDIDATES.read_text())
    picked = []
    for layer in wanted:
        candidates = [i for i in pool if layer in i.get("matched_layers", [])]
        # prefer shorter content for piloto e termos web3 no name/path
        def score(item: dict) -> tuple:
            text = f"{item.get('name','')} {item.get('path','')}".lower()
            web3 = any(t in text for t in ("blockchain", "solidity", "foundry", "forge", "smart", "contract", "ethereum", "dapp"))
            return (0 if web3 else 1, len(item.get("content", "")))
        candidates.sort(key=score)
        for item in candidates[:n_per]:
            picked.append({
                "source": "candidates",
                "pilot_layer_hint": layer,
                "repo": item["repo"],
                "path": item["path"],
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "content": item.get("content", ""),
                "matched_layers": item.get("matched_layers", []),
            })
    return picked


def classify_one(item: dict, model: str, rotator: KeyRotator, max_retries: int) -> dict:
    content, truncated = truncate_content(item["content"])
    prompt = PROMPT_A.format(
        repo=item["repo"],
        path=item["path"],
        name=item.get("name", ""),
        description=item.get("description", ""),
        content=content,
    )
    checklist_resp: dict = {}
    problems = ["not attempted"]
    for _ in range(max_retries + 1):
        checklist_resp = call_mistral(prompt, model, rotator)
        checklist = checklist_resp.get("checklist") or {}
        problems = verify_yes_quotes(checklist, content)
        if not problems:
            break
        prompt += (
            f"\n\nATENCAO: quotes dos seguintes YES nao sao substrings literais do content: "
            f"{problems}. Corrija com citacoes verbatim curtas e contiguas, ou mude answer para NO/UNCERTAIN."
        )

    checklist = checklist_resp.get("checklist") or {}
    skills, dropped = derive_skills(checklist, content)
    return {
        "repo": item["repo"],
        "path": item["path"],
        "name": item.get("name", ""),
        "source": item.get("source"),
        "pilot_layer_hint": item.get("pilot_layer_hint"),
        "matched_layers_keywords": item.get("matched_layers", []),
        "content_truncated": truncated,
        "content_chars_sent": len(content),
        "artifact_type": checklist_resp.get("artifact_type"),
        "confidence": checklist_resp.get("confidence"),
        "checklist": checklist,
        "skills_evidenced": skills,
        "verification_ok": not problems,
        "verification_issues": problems,
        "dropped_non_verbatim": dropped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default="ministral-14b-latest")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--sleep", type=float, default=1.5)
    parser.add_argument("--max-skills", type=int, default=6, help="limite total do piloto")
    parser.add_argument("--pyramid-only", action="store_true")
    args = parser.parse_args()

    items = load_pyramid_examples()
    if not args.pyramid_only:
        items.extend(load_extra_from_candidates(1))
    items = items[: args.max_skills]
    print(f"piloto: {len(items)} skills")

    rotator = KeyRotator(ENV_PATH)
    print(f"{len(rotator)} chave(s) Mistral; model={args.model}")

    results = []
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {item['pilot_layer_hint']} | {item['repo']} | {item.get('name') or item['path']}")
        try:
            result = classify_one(item, args.model, rotator, args.max_retries)
            skills_flat = [s for v in result["skills_evidenced"].values() for s in v]
            print(f"  artifact={result['artifact_type']} conf={result['confidence']} "
                  f"verbatim_ok={result['verification_ok']} skills={skills_flat}")
        except Exception as exc:
            print(f"  falhou: {exc}", file=sys.stderr)
            result = {
                "repo": item["repo"], "path": item["path"], "name": item.get("name", ""),
                "source": item.get("source"), "pilot_layer_hint": item.get("pilot_layer_hint"),
                "error": str(exc), "verification_ok": False,
            }
        results.append(result)
        time.sleep(args.sleep)

    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    ok = sum(1 for r in results if r.get("verification_ok"))
    print(f"\nconcluido: {ok}/{len(results)} com YES verbatim-ok -> {args.output}")


if __name__ == "__main__":
    main()
