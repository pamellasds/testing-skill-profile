---
title: "Plano de Pesquisa — MSR 2027 Mining Challenge"
subtitle: "Orientação de verificação e teste Web3 em agent skills (GitSkills)"
author: "Pamella Soares"
date: "30 de setembro de 2026"
status: "rascunho para o short paper (4 páginas + 1 de referências)"
dataset: "GitSkills (jul/2026) — linhagem agent_skills_mandatory_only"
---

# 1. Problema de pesquisa

Agent skills são artefatos em linguagem natural que **instruem** coding agents sobre como executar tarefas. Diferente de código, não há compilador que garanta que a orientação de teste seja completa, correta ou adequada ao domínio. Em **blockchain / DApps**, falhas de verificação têm custo alto (fundos, exploits, estado on-chain irreversível). A pilha típica de verificação Web3 não se resume à pirâmide clássica unit → integration → e2e: inclui também **fork/mainnet**, **fuzz/invariant**, análise estática e critérios de oráculo (reverts, eventos, propriedades).

O problema que este short paper explora é:

> **Em que medida as agent skills do ecossistema blockchain instruem agentes de forma adequada quanto à verificação e aos testes de smart contracts e aplicações descentralizadas — e quais camadas da pilha Web3 essa orientação cobre ou omite?**

Não se pretende, neste artigo, provar impacto causal em contratos reais nem construir um agente novo. O objetivo é um **estudo empírico piloto** sobre o que as skills *de fato ensinam*, como evidência do estado da instrução a agentes nesse domínio crítico. Resultados e gaps alimentam trabalhos futuros (SLR, rubrica de adequação, tese).

**Encaixe no MSR 2027 Mining Challenge.** O artigo usa o dataset **GitSkills** e alinha-se às direções sugeridas de *taxonomia de propósitos*, *reuso/templates* e *métricas/qualidade de instruções em linguagem natural*, com recorte em **teste e verificação Web3**.

---

# 2. Questões de pesquisa

Para caber em **4 páginas**, limitamos a **duas RQs** (uma quantitativa, uma qualitativa assistida por LLM).

## RQ1 — Cobertura da pilha de teste Web3 *(quantitativa)*

*Em skills relacionadas a blockchain (base `mandatory_only`), com que frequência a orientação de teste menciona cada camada da pilha Web3 — em especial unit, integration/fork e system/e2e, além de fuzz/invariant e sinais correlatos — e como essa distribuição se compara a uma pilha de verificação on-chain saudável?*

**Implicação (discussão, não experimento):** omissões por camada sugerem riscos diferentes para o sistema a desenvolver/testar (ex.: sem fork → falso verde em mocks; sem fuzz/invariant → estados raros e propriedades DeFi não exercitados).

## RQ2 — Testing Skill Profile *(qualitativa com LLM + Practical Test Pyramid)*

*Nas skills do pool de tipos de teste, quais **skills de granularidade de teste** são evidenciadas pela orientação ao agente — Unit, Integration, Contract, UI, End-to-End, Acceptance, Exploratory e Automation — segundo a [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) (Vocke/Fowler)?*

**Escopo declarado:** não é taxonomia completa de testing (ISTQB/ISO); é operacionalização do modelo da pirâmide para minerar *skill evidenced / skill instructed*. Acceptance é **ortogonal** à pirâmide (não forçar como topo). Ausência de evidência ≠ “o autor não conhece X”.

**Protocolo:** LLM responde checklist Q1–Q8 (`YES`/`NO`/`UNCERTAIN` + quote) → regras derivam `skills_evidenced` / **Testing Skill Profile**.

Guideline + piloto: `data/test_pyramid_skills/` (`guideline.md`, `run_pilot.py`).

**Alternativa mais fina (tese / fora do foco de 4p):** checklist CTFL multi-dimensão em `data/test_types_filter/llm_checklist_ctfl_guideline.md`.

## Extensão — cruzamento com Web3BlockSet

**Viável, mas não como eixo pareado do short paper.** Medição (2026-10-02):

| Junção `owner/repo` | N |
|---|---|
| Web3BlockSet (381 repos) ∩ skills `mandatory_only` | **12** |
| ∩ pool de tipos de teste | **6** (9 skills) |
| Issues/PRs WBS com sinal lexical de teste | ~**20,5k** / **293** repos |

Chave: `repositories.html_url` ↔ GitSkills `repo_full_name`.  
Path dos dados: `/home/pamella/Desktop/phd/2026_web3blockset_dashboard/web3blockset/`.

**Uso recomendado:** bridge *não-pareado* — mesmo checklist Pyramid em (a) skills = instrução e (b) issues/PRs WBS = discurso de prática, estratos por `repository_category`; cases pareados (n=6–12) só ilustrativos. Não exige overlap de repos e não afirma causalidade.

Plano metodológico fechado da trilha: `data/test_pyramid_skills/plano_metodologico.md` (esboço irmão consensus: `2026_web3blockset_dashboard/2027_msr/2027_short_paper_bridge/`).

> **Nota:** a Seção 4 descreve o filtro lexical já executado. Amostra e métricas de acordo da RQ2 entram nos próximos passos.

---

# 3. Contribuições esperadas

Ao final do short paper, espera-se:

1. **Caracterização empírica** da orientação de teste/verificação em agent skills do domínio blockchain (GitSkills → `mandatory_only` → filtro de tipos de teste), com distribuição por camada da pilha Web3.
2. **Testing Skill Profile** (RQ2): checklist Pyramid (Unit…Automation) respondido pela LLM → cobertura de skills evidenciadas, com evidência verbatim auditável.
3. **Síntese de gaps na instrução a agentes** (pilha incompleta, labels desalinhados do conteúdo, templates genéricos vs. metodologias ricas), posicionando implicações para verificação de SC/DApps.
4. **Artefatos reproduzíveis** alinhados à open science do challenge: listas de termos por camada, scripts de filtragem, pool candidato, gráficos e (quando aplicável) saídas da classificação LLM amostrada — com referência explícita à versão/snapshot do GitSkills utilizado.

**Fora de escopo deste artigo:** framework completo de adequação para tese; experimento controlado agente×contrato; SLR da interseção AI×Blockchain×Testes (trabalhos seguintes).

---

# 4. Metodologia já executada (até a filtragem por tipos de teste)

## 4.1 Linhagem de dados

| Passo | Ação | Entrada → Saída |
|---|---|---|
| 0 | Coleta GitSkills (jul/2026) | Universo público de `SKILL.md` |
| 1 | Filtro por vocabulário blockchain (`mandatory_terms`, 389 termos) | `agent_skills_mandatory_only.db` — **89.649** skills distintas (`dedup_primary = 1`) |
| 2 | Filtro por **tipos de teste / camadas** (este estudo; vocabulário CTFL+Web3) | Pool `test_types_candidates.json` — **17.847** skills |

A base `agent_skills_blockchain_filtered.db` **não** entra nesta linhagem. Toda a análise de tipos de teste usa apenas **`mandatory_only`**.

Critério do passo 1 (já materializado no `.db`): presença de ≥1 termo de `keywords.json` → `mandatory_terms`, com hits registrados em `keyword_matches.mandatory_hits`. É rede de alto *recall* (aceita ruído de termos ambíguos); o passo 2 restringe ao vocabulário de **teste**.

## 4.2 Vocabulário de tipos de teste (camadas)

Arquivo: `data/test_types_filter/keywords_by_layer.json`.

- Frases compostas (evita o termo isolado `test`).
- Busca **case-insensitive por substring** em `content` + `name` + `description`.
- Uma skill entra no pool com **≥1 termo** em qualquer camada; anota-se o conjunto de camadas e termos batidos.
- Fontes dos termos: pirâmide prática (Cohn/Vocke) + stack Web3 + sinônimos/tipos do **ISTQB CTFL Syllabus v4.0.1** (`Certified Tester.pdf`) — p.ex. *component testing*, *component/system integration testing*, *confirmation testing*, *black-box* / *white-box*, *exploratory testing*, *non-functional testing*.

Camadas definidas (pirâmide + tipos CTFL + extensões Web3):

| ID | Camada |
|---|---|
| `unit` | Unit / component (CTFL) |
| `integration` | Integration (component/system integration) |
| `system_e2e` | System / end-to-end |
| `acceptance` | Acceptance (UAT, alpha/beta, ATDD, …) |
| `confirmation` | Confirmation testing (CTFL) |
| `regression` | Regression / smoke |
| `maintenance` | Maintenance testing (CTFL) |
| `static_analysis` | Static testing / analysis |
| `black_box` | Black-box techniques (CTFL) |
| `white_box` | White-box techniques (CTFL) |
| `exploratory` | Exploratory / experience-based (CTFL) |
| `functional` | Functional testing (CTFL) |
| `non_functional` | Non-functional testing (CTFL) |
| `fork` | Fork / mainnet fork (Web3) |
| `fuzz_property` | Fuzz / property-based / invariant (Web3) |
| `formal_symbolic` | Formal verification / symbolic execution |
| `mutation` | Mutation testing |
| `differential` | Differential testing |
| `gas_performance` | Gas / performance |
| `coverage` | Coverage |

Para as RQs do paper, a **pirâmide central** a reportar com ênfase é **unit → integration (/fork) → system/e2e**, com **fuzz/invariant** (e correlatos) como extensão crítica da pilha Web3. Demais camadas (incl. tipos CTFL) entram como contexto quantitativo.

## 4.3 Procedimento de filtragem (implementado)

Script: `data/test_types_filter/filter_test_types.py`.

1. Carrega skills com `dedup_primary = 1` de `agent_skills_mandatory_only.db`.
2. Para cada skill, calcula `matched_layers` e `matched_terms_by_layer`.
3. Persiste:
   - `data/test_types_filter/test_types_candidates.json` — pool
   - `data/test_types_filter/test_types_summary.json` — contagens

## 4.4 Resultado preliminar do filtro (estado atual)

Sobre **89.649** skills distintas em `mandatory_only` (após inclusão dos termos CTFL):

| Métrica | Valor |
|---|---:|
| Skills com ≥1 tipo de teste | **17.847** |
| Skills multi-camada (≥2) | **7.491** |

Contagens por camada (uma skill pode contar em várias):

| Camada | Skills |
|---|---:|
| unit | 5.348 |
| coverage | 5.344 |
| regression | 4.748 |
| integration | 4.215 |
| system_e2e | 2.552 |
| static_analysis | 2.266 |
| formal_symbolic | 2.025 |
| fuzz_property | 1.772 |
| non_functional | 1.375 |
| gas_performance | 859 |
| fork | 497 |
| acceptance | 496 |
| functional | 284 |
| mutation | 267 |
| confirmation | 217 |
| white_box | 204 |
| black_box | 91 |
| differential | 76 |
| exploratory | 36 |
| maintenance | 2 |

Gráficos gerados em `data/test_types_filter/plots/` (`by_layer`, `tvm_pyramid`, `multi_layer`, `layer_cooccurrence`, `top_terms`, etc.).

Leitura qualitativa exploratória (amostra manual por camada) já indicou padrões a investigar nas RQs: unit frequentemente reduzido a “rode `forge test`”; integration misturado com pentest/ops; e2e frequentemente template Playwright/Web2; metodologias ricas (ex.: Aztec testing, Bulloak/BTT) concentradas e pouco generalizadas; fuzz/fork relativamente raros frente a unit/coverage.

## 4.5 Exemplos por camada da pirâmide

Pasta: `data/test_types_filter/examples_pyramid/` (skills completas + `meta.json` com `mandatory_hits` do `mandatory_only`). Usados para inspeção e discussão; a amostra da RQ2 será definida nos próximos passos.

## 4.6 Classificação LLM pós-filtro *(RQ2 — abordagem do short paper)*

Pasta: `data/test_pyramid_skills/`. Após o filtro lexical, a LLM responde o checklist da **Practical Test Pyramid** (8 skills); regras derivam o Testing Skill Profile.

| Artefato | Papel |
|---|---|
| `test_types_filter/` (keywords + pool) | Pré-seleção lexical (executado) |
| `test_pyramid_skills/guideline.md` | Checklist Q1–Q8 + escopo Vocke/Fowler |
| `test_pyramid_skills/run_pilot.py` | Piloto LLM → `pilot_results.json` |

Abordagem CTFL (mais dimensions) permanece em `test_types_filter/llm_checklist_ctfl_guideline.md` para trabalho futuro/tese.

---

# 5. Próximos passos (a refinar por RQ)

1. **Refinar o recorte Web3 da pilha para o paper** — ênfase unit / integration+fork / e2e / fuzz_property; o que vai a figura principal vs. apêndice; eventual limpeza de ruído do `mandatory_only` se necessário para a narrativa.
2. **RQ1** — estatísticas finais, figuras da pirâmide/pilha, co-ocorrência; discussão de omissões por camada (implicação de risco, sem causalidade).
3. **RQ2 — Testing Skill Profile (Pyramid)** — `data/test_pyramid_skills/`:
   - amostra estratificada do pool;
   - LLM responde Q1–Q8 (Unit…Automation) com YES/NO/UNCERTAIN + quote;
   - agregar cobertura / perfil (presença, não proficiência);
   - validação substring + amostra humana se couber.
4. **Redação do short paper** — referência Vocke/Fowler, método, resultados, ameaças (ambiguidade de nomes de camada, overclassification, UNCERTAIN), open science.

---

# 6. Relação com trabalhos paralelos do projeto

O filtro por **checklists/ferramentas/firmas** (`data/checklist_platform_filter/`, 1.592 skills) e o classificador LLM de natureza/segurança (`scripts/02_llm_classifier.py`) são linhagens **irmãs** (mesmo `mandatory_only`), úteis como contexto ou estudo futuro. **Não** são pré-requisito deste short paper de tipos de teste; podem ser citados se houver espaço para contrastar “orientação de segurança nomeada” vs. “orientação de teste por camada”.

---

# 7. Referências de dataset (para o paper)

- Destefanis et al., *GitSkills: A Dataset of Agent Skills on GitHub*, MSR 2027 Mining Challenge (arXiv:2608.10906).
- Snapshot a citar na submissão: versão GitSkills / Zenodo usada na análise (preencher na redação final).
