---
title: "Guideline de classificação LLM — Testing skills evidenciadas em agent skills"
subtitle: "Checklist multi-label baseado no ISTQB CTFL v4.0.1"
version: "1.0"
date: "30 de setembro de 2026"
taxonomy_base: "ISTQB Certified Tester Foundation Level Syllabus v4.0.1"
object: "SKILL.md (GitSkills / mandatory_only) — orientação de teste instruída ao agente"
---

# Princípio central

O objeto **não** é avaliar se o teste é bom, correto, adequado ou se o desenvolvedor é competente.

Pergunta à LLM:

> **Que conhecimento/prática de teste é evidenciado pelo texto desta agent skill (orientação prescritiva ao agente)?**

Classificamos **skill evidenced / skill instructed**, não *skill proficiency* nem *test quality*.

- **Evidência** = trecho observável no `SKILL.md` (e front matter).
- **Ausência de evidência ≠ ausência de conhecimento** do autor — só: *não identificado neste artefato*.
- **Multi-label** permitido em cada dimensão, **somente** com evidência independente por label.
- Respostas por item: `YES` | `NO` | `UNCERTAIN` | `NOT_APPLICABLE`.
- Todo `YES` exige `evidence` (citação verbatim + razão curta).

Referência normativa da taxonomia: **ISTQB CTFL v4.0.1** (`Certified Tester.pdf`).  
Extensões fora do CTFL (smoke, mutation, fuzz, fork, load/stress) ficam em dimensão `extensions` e **não** devem ser atribuídas ao ISTQB.

---

# Fluxo (duas etapas)

```
SKILL.md
    ↓
Prompt A — Evidence extraction (responde o CHECKLIST)
    ↓
respostas YES/NO/UNCERTAIN + evidence
    ↓
Prompt B / regras — Skill classification
    ↓
skills_evidenced[]  (somente labels com YES + evidência)
```

A LLM **não** deve pular direto para `"skill": "unit_testing"`.  
Primeiro responde o checklist; depois derivam-se as skills.

---

# Etapa 0 — Evidência mínima

| # | Pergunta | Resposta |
|---|---|---|
| E0.1 | O artefato trata de teste/verificação de software? | YES / NO / UNCERTAIN |
| E0.2 | Há orientação observável (procedimento, comando, critério, exemplo de teste)? | YES / NO / UNCERTAIN |
| E0.3 | A classificação pode ser justificada por trecho literal do texto? | YES / NO / UNCERTAIN |
| E0.4 | A classificação baseia-se no que o texto *instrui*, não em intenção inferida do autor? | YES / NO / UNCERTAIN |

Se E0.1 = NO → `artifact_type = not_test_related`, encerrar.  
Se E0.2–E0.4 insuficientes → `skills = []`, `confidence = low`, não forçar classificação.

---

# Etapa 1 — Test Level (CTFL §2.2.1, p. 28–29)

Pergunta: *Que nível de teste a skill instrui o agente a implementar/praticar?*

Multi-label. Para cada label: YES / NO / UNCERTAIN + evidence se YES.

### 1.1 Component / Unit — `component`
- Instrui testar um componente/unidade individual?
- Instrui isolamento (mocks/stubs/harness/framework de unit)?
- O objeto descrito é função, método, classe, contrato ou componente isolado?

### 1.2 Component Integration — `component_integration`
- Instrui verificar interação entre componentes?
- Foco em interfaces/interações entre componentes (não sistema inteiro)?

### 1.3 System — `system`
- Instrui avaliar comportamento/capacidade do sistema como um todo?
- Envolve sistema integrado / fluxo que atravessa múltiplos componentes?

### 1.4 System Integration — `system_integration`
- Instrui verificar interação entre o sistema sob teste e outro sistema/serviço externo?
- Foco em interfaces entre sistemas?

### 1.5 Acceptance — `acceptance`
- Instrui avaliar atendimento a necessidades/requisitos de stakeholders?
- Relacionado a aceitação do produto (UAT, negócio, uso real)?

**Importante:** Regression / Confirmation **não** são test levels (ver Etapa 4).

---

# Etapa 2 — Test Type (CTFL §2.2.2, p. 29–30)

Pergunta: *Que tipo de preocupação de testing a skill instrui?*

### 2.1 Functional — `functional`
- Verifica *o que* o sistema/componente deve fazer?
- Função/comportamento esperado e resultado relacionado à funcionalidade?

### 2.2 Non-functional — `non_functional`
- Avalia *como* o sistema se comporta (qualidade), não só o quê?
- Se YES, sub-labels opcionais (multi-label, cada um com evidência):
  - `performance` | `security` | `usability` | `reliability` | `compatibility`

---

# Etapa 3 — Test Technique (CTFL §4, p. 38–46)

Pergunta: *Que técnica de projeto/execução a skill instrui?*

### 3.1 Categoria
- `black_box` — projetável sem estrutura interna; derivado de especificação/requisitos  
- `white_box` — considera estrutura interna do código  
- `experience_based` — baseado em experiência / exploração / checklist  

### 3.2 Específicas (só se categoria YES e houver evidência)

**Black-box:**  
`equivalence_partitioning` | `boundary_value_analysis` | `decision_table_testing` | `state_transition_testing`

**White-box:**  
`statement_testing` | `branch_testing`

**Experience-based:**  
`error_guessing` | `exploratory_testing` | `checklist_based_testing`

**Cuidado:** não marcar `exploratory_testing` ou `checklist_based_testing` sem evidência explícita no texto (nome, procedimento session-based, checklist citada). Não inferir só porque o texto é “informal”.

---

# Etapa 4 — Test Purpose (CTFL §2.2.3, p. 30) — *não é level*

### 4.1 Confirmation — `confirmation`
- A skill instrui reexecutar teste após correção de defeito conhecido?
- Objetivo: confirmar que o defeito foi corrigido?

### 4.2 Regression — `regression`
- A skill instrui verificar se mudanças não causaram efeitos adversos?
- Suíte/prática de regressão explicitamente descrita (não basta “rodar CI” genérico sem evidência)?

---

# Etapa 5 — Test Strategy (CTFL p. 50) — *não substitui level*

### 5.1 Test Pyramid — `test_pyramid`
- A skill organiza/recomenda testes por granularidade (muitos baixo nível, poucos alto nível)?
- Menciona pirâmide / distribuição por camadas como estratégia?

`test_pyramid` é **estratégia**, não um `test_level`.

---

# Etapa 6 — Extensões (fora do CTFL — marcar `taxonomy: extension`)

Só com evidência explícita no texto:

| Label | Evidência típica na skill |
|---|---|
| `smoke_testing` | suíte/estratégia nomeada smoke |
| `mutation_testing` | mutation / mutant testing |
| `fuzz_testing` | fuzz / fuzzer / fuzzing |
| `property_invariant_testing` | property-based / invariant testing |
| `fork_testing` | mainnet fork / createSelectFork |
| `load_testing` | load testing |
| `stress_testing` | stress testing |
| `contract_testing` | contract tests (consumer/provider) — Vocke; não CTFL |

Não atribuir essas labels ao ISTQB no texto do paper.

---

# Schema JSON — resposta do checklist (Prompt A)

```json
{
  "repo": "owner/repo",
  "path": "path/to/SKILL.md",
  "artifact_type": "test_guidance_skill | not_test_related | uncertain",
  "checklist": {
    "E0": {
      "is_test_related": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
      "has_observable_guidance": {"answer": "YES|NO|UNCERTAIN", "evidence": null}
    },
    "test_level": {
      "component": {"answer": "YES|NO|UNCERTAIN", "evidence": {"quote": "...", "reason": "..."}},
      "component_integration": {"answer": "NO", "evidence": null},
      "system": {"answer": "NO", "evidence": null},
      "system_integration": {"answer": "NO", "evidence": null},
      "acceptance": {"answer": "NO", "evidence": null}
    },
    "test_type": {
      "functional": {"answer": "YES|NO|UNCERTAIN", "evidence": {...}},
      "non_functional": {"answer": "NO", "evidence": null},
      "non_functional_aspects": {
        "performance": {"answer": "NO", "evidence": null},
        "security": {"answer": "NO", "evidence": null},
        "usability": {"answer": "NO", "evidence": null},
        "reliability": {"answer": "NO", "evidence": null},
        "compatibility": {"answer": "NO", "evidence": null}
      }
    },
    "test_technique": {
      "black_box": {"answer": "YES|NO|UNCERTAIN", "evidence": {...}},
      "white_box": {"answer": "NO", "evidence": null},
      "experience_based": {"answer": "NO", "evidence": null},
      "equivalence_partitioning": {"answer": "NO", "evidence": null},
      "boundary_value_analysis": {"answer": "NO", "evidence": null},
      "decision_table_testing": {"answer": "NO", "evidence": null},
      "state_transition_testing": {"answer": "NO", "evidence": null},
      "statement_testing": {"answer": "NO", "evidence": null},
      "branch_testing": {"answer": "NO", "evidence": null},
      "error_guessing": {"answer": "NO", "evidence": null},
      "exploratory_testing": {"answer": "NO", "evidence": null},
      "checklist_based_testing": {"answer": "NO", "evidence": null}
    },
    "test_purpose": {
      "confirmation": {"answer": "NO", "evidence": null},
      "regression": {"answer": "NO", "evidence": null}
    },
    "test_strategy": {
      "test_pyramid": {"answer": "NO", "evidence": null}
    },
    "extensions": {
      "smoke_testing": {"answer": "NO", "evidence": null},
      "mutation_testing": {"answer": "NO", "evidence": null},
      "fuzz_testing": {"answer": "NO", "evidence": null},
      "property_invariant_testing": {"answer": "NO", "evidence": null},
      "fork_testing": {"answer": "NO", "evidence": null},
      "load_testing": {"answer": "NO", "evidence": null},
      "stress_testing": {"answer": "NO", "evidence": null},
      "contract_testing": {"answer": "NO", "evidence": null}
    }
  },
  "confidence": "high|medium|low"
}
```

Regras de `evidence`:
- `quote` deve ser **substring literal** do `content` da skill (normalização de espaço ok).
- Se `answer != YES`, `evidence` = null.
- Proibido reticências inventadas (`...`) no meio da quote para “resumir”.

---

# Derivação — skills evidenciadas (Prompt B / código)

```text
para cada dimensão, para cada label:
  se answer == YES e evidence.quote é substring do content:
    incluir label em skills_evidenced
  senão:
    não incluir
```

Saída agregada:

```json
{
  "repo": "...",
  "path": "...",
  "skills_evidenced": {
    "test_level": ["component"],
    "test_type": ["functional"],
    "test_technique": ["black_box"],
    "test_purpose": [],
    "test_strategy": [],
    "extensions": ["fuzz_testing"]
  },
  "checklist_ref": "...",
  "confidence": "high"
}
```

---

# Regras anti-overclassification

1. Compatibilidade entre labels **não** justifica multi-label — só evidência independente.  
2. Menção isolada a uma palavra (ex.: “security”) sem instrução de *como* testar → preferir `UNCERTAIN` ou `NO`.  
3. Não promover `exploratory` / `checklist_based` / `regression` sem evidência explícita de prática.  
4. Não concluir proficiência (“advanced unit testing skill”).  
5. `test_pyramid` nunca substitui um `test_level`.  
6. Extensões Web3 nunca entram como se fossem CTFL.

---

# Páginas-base CTFL v4.0.1

| Categoria | Páginas (syllabus) |
|---|---|
| Fundamentos / o que é teste | p. 8–9 |
| Test Levels | p. 28–29 |
| Test Types | p. 29–30 |
| Confirmation / Regression | p. 30 |
| Black-box techniques | p. 39–42 |
| White-box techniques | p. 42–43 |
| Experience-based | p. 43–44 |
| Acceptance / ATDD | p. 45–46 |
| Test Pyramid | p. 50 |

---

# Validação recomendada (paper / tese)

- Amostra com acordo LLM × humano (Cohen’s κ ou Krippendorff’s α)  
- Auditoria de quotes (substring check automático, como em `02_llm_classifier.py`)  
- Relatar taxa de `UNCERTAIN` e casos de overclassification  

---

# Relação com o filtro por keywords

O filtro lexical (`keywords_by_layer.json`) é **recall alto / pré-seleção**.  
Este checklist LLM é a **classificação estruturada** na amostra (RQ2): multi-dimensão CTFL + extensões, com evidência — não substitui o filtro e não avalia qualidade.
