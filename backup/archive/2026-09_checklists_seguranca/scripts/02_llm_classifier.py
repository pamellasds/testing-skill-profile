"""Classifica uma amostra do pool checklist_platform_candidates_v3_1592.json
quanto a natureza da revisao de seguranca (nature) e as referencias externas
citadas (tools / firms_platforms / checklists), usando a API do Mistral.
Reproduz o schema e o prompt das Secoes 3-4 do relatorio de metodologia.

Chaves de API: qualquer variavel MISTRAL_* em .env e usada, com rotacao
automatica para a proxima chave quando a atual atinge o limite de taxa.

Uso:
    python 02_llm_classifier.py --sample-size 30
"""
from __future__ import annotations

import argparse
import importlib
import json
import random
import re
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

generate_plots = importlib.import_module("03_generate_plots")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/checklist_platform_filter/checklist_platform_candidates_v3_1592.json"
DEFAULT_PLOTS_OUTDIR = ROOT / "data/checklist_platform_filter/plots"
DEFAULT_OUTPUT = ROOT / "data/checklist_platform_filter/llm_classification_sample.json"
ENV_PATH = ROOT / ".env"

API_URL = "https://api.mistral.ai/v1/chat/completions"
REFERENCE_BLOCKS = ("tools", "firms_platforms", "checklists")

PROMPT_TEMPLATE = """Voce vai classificar uma skill de agente de IA quanto a sua relacao com
revisao de seguranca de smart contracts.

repo: {repo}
path: {path}
name: {name}
description: {description}
content:
\"\"\"
{content}
\"\"\"

Retorne APENAS um JSON (sem markdown, sem comentarios) com os campos:

1. nature - um de: follows_standard | own_standard | audit_support_tool | not_security_review
   - follows_standard: a skill modela sua orientacao de seguranca explicitamente
     sobre um padrao/checklist externo NOMEADO.
   - own_standard: organiza processo/checklist proprio e estruturado, sem se
     apoiar num padrao externo nomeado.
   - audit_support_tool: pertence ao entorno de uma auditoria (formatacao de
     relatorio, consulta a banco de achados historicos etc.) mas nao executa
     analise de vulnerabilidade.
   - not_security_review: nao e de fato conteudo de revisao de seguranca de
     smart contract. Inclui: (a) coincidencia de nome de marca/termo (ex.:
     "least authority" como principio generico de seguranca, nao como a
     firma de auditoria Least Authority); (b) skill de OUTRO dominio de
     seguranca que so compartilha vocabulario com seguranca de smart
     contract (ex.: controle de acesso/autorizacao de agentes de IA,
     seguranca de infraestrutura, seguranca web generica) sem de fato
     tratar de auditoria/vulnerabilidade de smart contract.

2. nature_evidence - citacao VERBATIM do content que sustenta a classificacao
   (deve ser encontravel por busca exata, case-insensitive, dentro do content).

3. nature_rationale - 1-2 frases explicando o porque.

4. Se nature for not_security_review ou audit_support_tool: tools,
   firms_platforms e checklists devem ser objetos vazios ({{}}).

   Caso contrario, para cada ferramenta, firma/plataforma ou checklist de
   SEGURANCA/AUDITORIA DE SMART CONTRACT efetivamente citada no texto,
   adicione uma entrada (chave = nome citado). ESCOPO OBRIGATORIO: só
   entram entidades cujo papel no texto e analise de vulnerabilidade,
   scanner/fuzzer de seguranca, verificacao formal, firma/plataforma de
   auditoria, ou checklist/padrao de seguranca nomeado.

   NAO INCLUA (mesmo se citado no texto), por nao serem de seguranca/auditoria:
   - provedores de infraestrutura/RPC (Alchemy, Infura, Helius, QuickNode...)
   - block explorers e dashboards de analytics (Etherscan, Snowtrace,
     Blockscout, Solscan, Dune...)
   - carteiras, multisig, marketplaces, exchanges (MetaMask, Gnosis Safe,
     OpenSea, Blur...)
   - frameworks genericos de agente de IA sem relacao com smart contracts
     (LangChain, CrewAI, AutoGen, Google ADK, OpenAI, MCP, A2A...)
   - plataformas de hospedagem/colaboracao genericas (GitHub, GitLab...)
   - frameworks/bibliotecas GENERICOS de desenvolvimento ou teste, sem
     funcao de deteccao de vulnerabilidade (Hardhat, Chai, ethers.js,
     hardhat-gas-reporter, hardhat-network-helpers, proptest, Hypothesis,
     fast-check) - so entram se a citacao for especificamente sobre rodar
     fuzzing/invariant testing/coverage de seguranca com eles
   - checklists que sao standard de token (ERC-20, ERC-721...), docs de
     protocolo, paper de pesquisa geral, ou checklist de deploy/lancamento
     SEM foco em vulnerabilidade - so entram se forem checklist/padrao de
     seguranca nomeado (SWC Registry, SCSVS, OWASP, DASP, guidelines de
     auditoria de uma firma, etc.)
   - nomes de usuario, chains, ou qualquer entidade cujo papel no texto
     nao seja especificamente seguranca/auditoria.
   Na duvida se uma entidade e de seguranca/auditoria ou nao, DEIXE DE FORA.

   Para as entradas que passam no escopo, preencha:
   - role: para tools, um de recommended_run | output_consumed |
     embedded_ruleset | mentioned_reference.
     Para firms_platforms, um de methodology_source | data_source |
     library_dependency | named_reference.
     Para checklists, um de primary_structure | partial_reference | named_only.
   - points_externally: embedded | internal_pointer | external_pointer | mixed.
   - evidence: citacao verbatim (mesma regra de verificacao).

5. vulnerabilities - lista simples (sem evidencia, sem papel) com o nome de
   cada categoria de vulnerabilidade de smart contract efetivamente
   mencionada no texto (ex.: "Reentrancy", "Access Control", "Integer
   Overflow", "Oracle Manipulation", "Flash Loan Attack", "Front-Running").
   Use o nome como aparece no texto; lista vazia se nenhuma for mencionada.

Regras gerais:
- Nunca infira nome que nao aparece literalmente no texto.
- Uma lista conjunta de varias firmas ("Code4rena, Sherlock, Trail of
  Bits...") gera uma entrada por firma, nao uma entrada agregada.
- Toda evidence deve ser um TRECHO CONTIGUO copiado exatamente do content,
  pontuacao e simbolos inclusos (barras invertidas, crases, hifens).
  NUNCA use reticencias ("...", "[...]") para encurtar uma citacao longa -
  se o trecho relevante for longo, escolha um pedaco mais curto que exista
  literalmente, em vez de resumir.
  NUNCA junte pedacos de linhas ou colunas de tabela diferentes numa unica
  citacao (ex.: nao misture o cabecalho de uma tabela com uma celula de
  dado, nem reordene colunas) - cite apenas uma linha ou trecho continuo.

Formato de saida (estrutura de exemplo, nao copie os valores):
{{"nature": "own_standard", "nature_evidence": "...", "nature_rationale": "...",
  "tools": {{"Slither": {{"role": "mentioned_reference", "points_externally": "embedded", "evidence": "..."}}}},
  "firms_platforms": {{}}, "checklists": {{}},
  "vulnerabilities": ["Reentrancy", "Access Control"]}}
"""


class KeyRotator:
    """Round-robin sobre chaves MISTRAL_* do .env, avancando ao bater rate limit."""

    def __init__(self, env_path: Path):
        keys = [v for k, v in dotenv_values(env_path).items() if k.startswith("MISTRAL_") and v]
        if not keys:
            raise RuntimeError(f"nenhuma variavel MISTRAL_* encontrada em {env_path}")
        self._keys = keys
        self._index = 0

    @property
    def current(self) -> str:
        return self._keys[self._index]

    def rotate(self) -> None:
        self._index = (self._index + 1) % len(self._keys)

    def __len__(self) -> int:
        return len(self._keys)


def call_mistral(prompt: str, model: str, rotator: KeyRotator, max_attempts: int = 6) -> dict:
    """Chama a API do Mistral com retry e rotacao de chave em rate limit/erro de auth."""
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
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
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
            last_error = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            continue
        if resp.status_code >= 500:
            last_error = RuntimeError(f"HTTP {resp.status_code}")
            time.sleep(min(2 ** attempt, 30))
            continue

        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    raise RuntimeError(f"falha ao chamar Mistral apos {max_attempts} tentativas: {last_error}")


_WHITESPACE_RE = re.compile(r"\s+")
_MARKDOWN_DECORATION_RE = re.compile(r"[`*_#|]")


def _normalize(text: str) -> str:
    """Colapsa espacos/quebras de linha (comuns em YAML com word-wrap) e tira
    decoracao markdown (crases, negrito, pipes de tabela) antes de comparar -
    o LLM costuma citar o texto "visivel", sem a pontuacao de formatacao."""
    text = _MARKDOWN_DECORATION_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def is_verbatim(evidence: str, content: str) -> bool:
    return bool(evidence) and _normalize(evidence) in _normalize(content)


def verify(result: dict, content: str) -> list[str]:
    """Lista de referencias com evidencia nao-verbatim (vazia = tudo ok)."""
    problems = []
    if not is_verbatim(result.get("nature_evidence", ""), content):
        problems.append("nature_evidence")
    for block in REFERENCE_BLOCKS:
        for name, info in result.get(block, {}).items():
            if not is_verbatim(info.get("evidence", ""), content):
                problems.append(f"{block}.{name}")
    return problems


SHORT_CIRCUIT_NATURES = {"not_security_review", "audit_support_tool"}


def enforce_short_circuit(result: dict) -> dict:
    """O modelo as vezes preenche tools/firms_platforms/checklists mesmo
    quando nature manda deixar vazio - a regra e mais confiavel aplicada em
    codigo do que apenas pedida no prompt."""
    if result.get("nature") in SHORT_CIRCUIT_NATURES:
        for block in REFERENCE_BLOCKS:
            result[block] = {}
    return result


# Nomes que o modelo repetidamente inclui mesmo com instrucao explicita no
# prompt para excluir - ministral-14b (menor, free tier) nao segue essa
# regra de forma confiavel so por texto, entao ela e reforcada em codigo.
# Categorias: infra/RPC, block explorers/analytics, carteiras/multisig/
# marketplaces, frameworks de agente de IA genericos, plataformas de
# hospedagem, e frameworks/bibliotecas de desenvolvimento ou teste sem
# funcao especifica de deteccao de vulnerabilidade (compiladores, linters,
# libs de asserção/property-testing genericas).
NON_SECURITY_DENYLIST = {
    # infra / RPC
    "alchemy", "infura", "helius", "quicknode",
    # block explorers / analytics
    "etherscan", "snowtrace", "blockscout", "solscan", "dune", "dune analytics",
    # carteiras / multisig / marketplaces / exchanges
    "metamask", "gnosis", "gnosis safe", "safe", "opensea", "blur",
    # frameworks de agente de IA genericos
    "langchain", "crewai", "autogen", "google adk", "openai", "mcp", "a2a", "claude",
    # hospedagem / colaboracao genericas
    "github", "gitlab", "taskoutput",
    # compiladores / linters / package managers genericos
    "solc", "clippy", "npm", "pip",
    # frameworks/libs de dev ou teste genericos (nao especificos de seguranca)
    "hardhat", "truffle", "brownie", "anchor", "foundry", "forge", "forge test",
    "forge-std", "forge-std/test.sol", "cargo test", "chai", "ethers", "ethers.js",
    "proptest", "hypothesis", "fast-check", "hardhat-gas-reporter",
    "hardhat gas reporter", "@nomicfoundation/hardhat-network-helpers",
    "hardhat network helpers", "@nomiclabs/hardhat-etherscan",
    "@nomicfoundation/hardhat-toolbox", "execution-spec-tests", "soroban-sdk",
    "solana-bankrun", "glob",
    # firmas/orgs genericas (nao sao firma de auditoria de smart contract)
    "paradigm", "chainlink", "deloitte", "bdo italia", "cyberexpress",
    "web3_research", "token_security_audits",
    # libs genericas de parsing/criptografia, nao ferramentas de seguranca
    "py_ecc", "tree-sitter",
}


def looks_like_file_path(name: str) -> bool:
    """O modelo as vezes cita um caminho de arquivo interno do proprio
    repositorio (ex.: 'reference/anchor/', 'solidity-checks.md') como se
    fosse o nome de uma ferramenta/checklist - isso nao e uma entidade
    nomeada, e uma referencia de arquivo."""
    return "/" in name or name.lower().endswith((".md", ".sol", ".py", ".rs"))


def strip_non_security_entries(result: dict) -> dict:
    """Remove de tools/firms_platforms/checklists qualquer nome no denylist
    ou que pareca um path de arquivo, independente do que o modelo decidiu -
    reforco em codigo da regra de escopo do prompt (Secao 4 do relatorio)."""
    for block in REFERENCE_BLOCKS:
        result[block] = {
            name: info for name, info in result.get(block, {}).items()
            if name.strip().lower() not in NON_SECURITY_DENYLIST
            and not looks_like_file_path(name)
        }
    return result


def classify_item(item: dict, model: str, rotator: KeyRotator, max_retries: int) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        repo=item["repo"], path=item["path"], name=item.get("name", ""),
        description=item.get("description", ""), content=item["content"],
    )
    result: dict = {}
    problems = ["not attempted"]
    for _ in range(max_retries + 1):
        result = strip_non_security_entries(enforce_short_circuit(call_mistral(prompt, model, rotator)))
        problems = verify(result, item["content"])
        if not problems:
            break
        prompt += (
            f"\n\nATENCAO: as evidencias a seguir nao foram encontradas literalmente "
            f"no content: {problems}. Corrija usando apenas citacoes verbatim."
        )
    return {**item, **result, "verification_ok": not problems, "verification_issues": problems}


def stratified_sample(pool: list[dict], size: int, seed: int) -> list[dict]:
    """Amostra aleatoria estratificada por faixa de n_terms, para cobrir tanto
    skills com poucos quanto com muitos termos batidos."""
    random.seed(seed)
    buckets: dict[str, list[dict]] = {"low": [], "mid": [], "high": []}
    for item in pool:
        n = item["n_terms"]
        bucket = "low" if n <= 1 else "mid" if n <= 3 else "high"
        buckets[bucket].append(item)

    per_bucket = max(1, size // len(buckets))
    chosen, chosen_keys = [], set()
    for items in buckets.values():
        picked = random.sample(items, min(per_bucket, len(items)))
        chosen.extend(picked)
        chosen_keys.update((i["repo"], i["path"]) for i in picked)

    if len(chosen) < size:
        remaining = [i for i in pool if (i["repo"], i["path"]) not in chosen_keys]
        chosen.extend(random.sample(remaining, min(size - len(chosen), len(remaining))))

    return chosen[:size]


def fixed_sample(pool: list[dict], reference_path: Path) -> list[dict]:
    """Seleciona do pool os itens com o mesmo (repo, path) de um JSON de
    referencia (ex.: a amostra classificada manualmente), para comparar
    a classificacao do LLM contra a classificacao manual nos mesmos casos."""
    reference = json.loads(reference_path.read_text())
    wanted = {(r["repo"], r["path"]) for r in reference}
    selected = [item for item in pool if (item["repo"], item["path"]) in wanted]
    missing = wanted - {(i["repo"], i["path"]) for i in selected}
    if missing:
        print(f"aviso: {len(missing)} itens de {reference_path.name} nao encontrados no pool: {missing}")
    return selected


def checkpoint_path_for(output: Path) -> Path:
    return output.with_suffix(".checkpoint.jsonl")


def load_checkpoint(checkpoint_path: Path) -> dict[tuple[str, str], dict]:
    """Le itens ja processados de uma execucao anterior (uma linha JSON por
    item), para retomar sem reprocessar - cada linha e um checkpoint atomico,
    entao uma interrupcao no meio nunca corrompe o que ja foi salvo."""
    if not checkpoint_path.exists():
        return {}
    done = {}
    for line in checkpoint_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        done[(record["repo"], record["path"])] = record
    return done


def update_plots(done: dict[tuple[str, str], dict], sample: list[dict], pool_path: Path, outdir: Path) -> None:
    """Regera os graficos (script 03) com o que ja foi classificado ate agora
    na amostra - a nuvem de palavras usa o pool inteiro, entao nao muda com
    o progresso e nao precisa ser refeita a cada chamada."""
    processed = [done[(item["repo"], item["path"])] for item in sample if (item["repo"], item["path"]) in done]
    print(f"  atualizando graficos ({len(processed)} itens classificados ate agora)...")
    generate_plots.generate_all(processed, pool_path, outdir, include_wordcloud=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sample-size", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fixed-sample", type=Path, default=None, help="JSON com itens (repo, path) fixos a usar em vez de amostragem aleatoria")
    parser.add_argument("--model", default="ministral-14b-latest", help="mistral-medium/-small ficaram 429 nesta conta; ministral-14b e o maior liberado")
    parser.add_argument("--max-retries", type=int, default=2, help="novas tentativas por item se a evidencia falhar")
    parser.add_argument("--sleep", type=float, default=1.5, help="segundos entre chamadas")
    parser.add_argument("--update-plots-every", type=int, default=25, help="regera os graficos a cada N itens processados (0 desativa)")
    parser.add_argument("--plots-outdir", type=Path, default=DEFAULT_PLOTS_OUTDIR)
    args = parser.parse_args()

    pool = json.loads(args.input.read_text())
    if args.fixed_sample:
        sample = fixed_sample(pool, args.fixed_sample)
    else:
        sample = stratified_sample(pool, args.sample_size, args.seed)
    print(f"amostra: {len(sample)} de {len(pool)} skills")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_path_for(args.output)
    done = load_checkpoint(checkpoint_path)
    pending = [item for item in sample if (item["repo"], item["path"]) not in done]
    if done:
        print(f"retomando checkpoint: {len(done)} ja processados, {len(pending)} restantes -> {checkpoint_path}")

    rotator = KeyRotator(ENV_PATH)
    print(f"{len(rotator)} chave(s) Mistral disponivel(is)")

    with checkpoint_path.open("a") as checkpoint_file:
        for i, item in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] {item['repo']} | {item['path']}")
            try:
                result = classify_item(item, args.model, rotator, args.max_retries)
            except Exception as exc:  # um item com falha nao derruba o lote inteiro
                print(f"  falhou: {exc}")
                result = {**item, "nature": None, "verification_ok": False, "verification_issues": [str(exc)]}
            checkpoint_file.write(json.dumps(result, ensure_ascii=False) + "\n")
            checkpoint_file.flush()
            done[(item["repo"], item["path"])] = result

            if args.update_plots_every and i % args.update_plots_every == 0:
                update_plots(done, sample, args.input, args.plots_outdir)

            time.sleep(args.sleep)

    results = [done[(item["repo"], item["path"])] for item in sample]
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    if args.update_plots_every:
        update_plots(done, sample, args.input, args.plots_outdir)

    ok = sum(r["verification_ok"] for r in results)
    print(f"\nconcluido: {ok}/{len(results)} com evidencia 100% verbatim -> {args.output}")
    print(f"checkpoint mantido em {checkpoint_path} (apague se quiser reprocessar do zero)")


if __name__ == "__main__":
    main()
