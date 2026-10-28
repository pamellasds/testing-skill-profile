---
title: "Plano metodológico fechado — Testing Skill Profile (GitSkills × Practical Test Pyramid)"
status: "fechado para short paper MSR 2027 (+ extensão Web3BlockSet)"
date: "2 de outubro de 2026"
---

# 1. Objeto e pergunta

**Objeto:** `SKILL.md` (GitSkills) que *instruem* coding agents sobre teste/verificação no domínio blockchain.  
**Não-objeto:** qualidade do teste, proficiência do autor, impacto causal em contratos.

**Pergunta operacional:**

> Quais *testing skills* (granularidade) são **evidenciadas** na orientação ao agente, segundo a Practical Test Pyramid (Vocke/Fowler)?

Referência única do short paper:  
[The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html).  
CTFL fica fora do paper de 4p (tese/trabalho fino).

---

# 2. Linhagem de dados (trilha principal)

```
GitSkills (jul/2026)
    → agent_skills_mandatory_only.db   (89.649 skills; vocabulário blockchain)
    → filtro lexical tipos de teste    (17.847 skills; keywords_by_layer.json)
    → amostra estratificada
    → LLM responde checklist Q1–Q8     (YES/NO/UNCERTAIN + quote verbatim)
    → regras → skills_evidenced / Testing Skill Profile
```

| Passo | Artefato |
|---|---|
| Filtro lexical | `data/test_types_filter/` |
| Checklist + piloto | `data/test_pyramid_skills/guideline.md`, `run_pilot.py` |
| Saídas | `pilot_results.json`, `plots/` |

**Princípios:** skill evidenced ≠ proficiency; multi-label com evidência independente; Acceptance ortogonal à pirâmide; Exploratory só com menção explícita.

**Checklist (Q1–Q8):** Unit · Integration · Contract · UI · End-to-End · Acceptance · Exploratory · Automation.

---

# 3. RQs do short paper (4p)

| RQ | Tipo | Medida |
|---|---|---|
| **RQ1** | Quantitativa | Prevalência lexical por camada/tipo no pool (pirâmide + sinais Web3: fork, fuzz/invariant) |
| **RQ2** | Qualitativa + LLM | Testing Skill Profile na amostra (checklist Pyramid) |

Discussão: omissões por camada → riscos plausíveis (sem causalidade).

**Fora de escopo do short paper:** experimento agente×contrato; taxonomia ISTQB completa; SLR AI×BC×Testes.

---

# 4. Cruzamento com Web3BlockSet — viabilidade

## 4.1 O que é o Web3BlockSet (local)

Path: `/home/pamella/Desktop/phd/2026_web3blockset_dashboard/web3blockset/`

| Arquivo | Conteúdo (ordem de grandeza) |
|---|---|
| `repositories.csv` | **381** repositórios Web3 (metadados + `repository_category`) |
| `issues_prs.csv` | ~**425k** issues/PRs nesses repos (dataset completo muito maior em linhas brutas; ~379 repos com rows) |

Chave de junção natural: `owner/repo`  
(`repositories.html_url` ↔ GitSkills `artifacts.repo_full_name`).

## 4.2 Overlap empírico (medido em 2026-10-02)

| Junção | N |
|---|---|
| WBS ∩ repos com skills (`mandatory_only`, dedup) | **12** |
| WBS ∩ repos do pool de tipos de teste | **6** |
| Skills do pool nesses 6 repos | **9** |
| Issues/PRs WBS com sinal lexical de teste* | **~20,5k** rows / **293** repos |
| Repos do overlap pool com issues “testish” | **6 / 6** |

\*termos piloto: unit/integration/e2e/fuzz/invariant/forge test/hardhat test/contract test/pytest/jest.

Exemplos de overlap com skills: `openzeppelin/openzeppelin-contracts`, `smartcontractkit/chainlink`, `vyperlang/vyper`, `aztecprotocol/aztec-packages`, `metamask/metamask-mobile`, …

**Conclusão:** cruzamento **pareado por repositório** é possível, mas **N demasiado pequeno** para RQ estatística no short paper (n≈6–12).

## 4.3 Como cruzar de forma válida

### A) Bridge *não-pareado* (recomendado como extensão / discussão / paper irmão)

Comparar **duas populações** com o **mesmo vocabulário Pyramid**:

| Lado | Corpus | Interpretação |
|---|---|---|
| Instrução | GitSkills (skills) | O que agentes são *ensinados* a fazer |
| Prática discursiva | Web3BlockSet (issues/PRs) | O que comunidades *discutem* sobre teste |

Protocolo espelhado:

1. Lexicalizar Q1–Q8 (+ fuzz/fork se útil) em `issues_prs.clean_text`.  
2. Agregar prevalência por `repository_category` (WBS).  
3. Contrastar perfil “instrução (GitSkills)” × “discurso (WBS)” — **gap de cobertura**, sem afirmar causalidade.

Isso **não** exige overlap de repos. Encaixa na provocação já esboçada em `2027_msr/2027_short_paper_bridge/` (lá: consensus; aqui: testing pyramid).

### B) Case study pareado (opcional, n pequeno)

Nos **12** (ou **6**) repos em comum:

1. Extrair skills de teste + Profile LLM.  
2. Amostrar issues/PRs “testish” do mesmo `owner/repo`.  
3. Análise qualitativa: a orientação da skill alinha-se ao que o projeto discute?

Útil como **ilustração** no paper ou apêndice — não como RQ quantitativa principal.

### C) O que *não* fazer

- Não exigir join 1:1 repo→skill como pré-requisito do short paper GitSkills.  
- Não interpretar overlap baixo como “Web3 não usa skills” (skills vivem em muitos repos satélite/templates).  
- Não misturar CTFL + Pyramid + WBS no mesmo 4p.

---

# 5. Desenho metodológico fechado (o que entra onde)

```
                    ┌─────────────────────────────┐
                    │  SHORT PAPER (Mining Challenge) │
                    │  GitSkills + Pyramid Q1–Q8      │
                    │  RQ1 lexical · RQ2 LLM profile  │
                    └──────────────┬──────────────┘
                                   │
              (opcional discussão / WIP irmão)
                                   ▼
                    ┌─────────────────────────────┐
                    │  BRIDGE Web3BlockSet            │
                    │  A) prevalência Pyramid em      │
                    │     issues/PRs (não-pareado)    │
                    │  B) 6–12 cases pareados         │
                    └─────────────────────────────┘
```

| Camada | Dataset | Papel |
|---|---|---|
| Core 4p | GitSkills `mandatory_only` → pool teste | Instrução a agentes |
| Extensão | Web3BlockSet issues/PRs | Prática discursiva / gap |
| Metadado | WBS `repository_category` | Estratos (DeFi, SC library, wallet…) |
| Instrumento | Pyramid checklist (mesmo) | Comparabilidade |

---

# 6. Ameaças (já antecipadas)

1. **Recall do filtro lexical** (ruído Web2 / templates).  
2. **Overclassification LLM** (mitigar: quote verbatim + amostra humana).  
3. **Ambiguidade de nomes de camada** (declarar glossário Vocke/Fowler).  
4. **Selection bias WBS** (repos >300 stars / orgs Awesome Web3 — não é amostra aleatória de DApps).  
5. **Discurso ≠ prática de código** (issues falam de teste; não medimos suíte real).  
6. **Overlap pareado pequeno** (não overclaim estatístico).

---

# 7. Entregáveis e próximos passos

**Já feito:** filtro lexical, guideline Pyramid, piloto LLM (6 skills), plots de coverage/profile, overlap WBS medido.

**Para fechar o short paper:**

1. Congelar amostra estratificada RQ2 (tamanho alvo: dezenas, não milhares).  
2. Rodar `run_pilot.py` na amostra + κ humano×LLM em subamostra.  
3. Figuras RQ1 (pool) + RQ2 (profile/coverage).  
4. Redação 4p citando Vocke/Fowler + GitSkills; Web3BlockSet só se couber como *future work* ou 1 parágrafo de bridge.

**Para o bridge WBS (WIP / 2º paper):**

1. Script único: prevalência Q1–Q8 em `issues_prs` por categoria (reusar termos do guideline).  
2. Tabela/figura “Instruction vs Discourse”.  
3. Opcional: 6 case studies do overlap.

---

# 8. Veredito

| Pergunta | Resposta |
|---|---|
| Dá para cruzar com Web3BlockSet? | **Sim.** |
| Join por repo é o eixo do 4p? | **Não** — N=6–12 demais frágil. |
| Cruzamento útil? | **Sim, não-pareado:** mesmo checklist Pyramid em skills (instrução) vs issues/PRs (discurso), com categorias WBS como estratos; cases pareados só ilustrativos. |
| Plano da trilha Pyramid/GitSkills está fechado? | **Sim** (Seções 1–3 + 5–7). WBS é extensão metodológica explícita, não bloqueador. |
