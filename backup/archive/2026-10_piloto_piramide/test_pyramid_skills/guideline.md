---
title: "Testing Skill Profile — Practical Test Pyramid"
reference: "Ham Vocke / Martin Fowler — The Practical Test Pyramid"
url: "https://martinfowler.com/articles/practical-test-pyramid.html"
object: "SKILL.md — testing skills evidenciadas na orientação ao agente"
version: "1.0"
---

# Escopo (declarar no paper)

Esta abordagem **não** propõe uma taxonomia completa de software testing (ISTQB/ISO/SWEBOK).

Usa o modelo da [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) como referência operacional para identificar **skills relacionadas à granularidade dos testes** instruídas/evidenciadas em agent skills.

- Cohn (pirâmide clássica citada no artigo): Unit → Service → UI  
- Vocke (visão prática): Unit, Integration, Contract, UI, End-to-End, Acceptance (+ Exploratory; Automation como preocupação transversal do artigo)

Fowler/Vocke alertam que **nomes de camadas não são universais**. Adotamos explicitamente o vocabulário do artigo como glossário operacional.

Pergunta à LLM: *há evidência dessa skill no texto?* — **não** *o teste é bom?* / *o autor é competente?*

Fluxo: **Referência → Checklist → LLM → Evidências → Testing Skill Profile**

---

# Definições (Vocke / Practical Test Pyramid)

Fonte: Ham Vocke, *The Practical Test Pyramid* (Fowler, 2018).  
Cohn (citado no artigo): Unit → Service → UI. Vocke usa nomes práticos e alerta que **os nomes das camadas não são universais**.

Essência da pirâmide: testes com **granularidades diferentes**; quanto mais alto, **menos** testes.

| # | Nível | Definição no artigo (para o anotador) |
|---|---|---|
| Q1 | **Unitário** | Base da suíte. Uma *unidade* (função, método ou classe) funciona como o esperado. Escopo mais estreito; deve ser o tipo mais numeroso. Colaboradores externos → *test doubles* (mocks/stubs). Pode ser *solitary* ou *sociable*. |
| Q2 | **Integração** | Testa a integração com partes **fora** da unidade (banco, filesystem, outro serviço). Em geral exige o colaborador real ou, na leitura *narrow* de Vocke, **um ponto de integração por vez** na fronteira do serviço. |
| Q3 | **Contrato** | Interface entre **provedor** e **consumidor** (REST, RPC, filas). O contrato é a especificação dessa interface. O teste verifica se as partes (e fakes usados em integração) respeitam o acordo (incl. CDC). |
| Q4 | **UI** | Interface com o usuário. REST API ou CLI **também** são UI, não só GUI. Verifica entrada, ações, dados apresentados e mudança de estado. **Não** é o mesmo que E2E (dá para testar UI em nível baixo). |
| Q5 | **End-to-End** | *Broad stack tests*: sistema **inteiro, completamente integrado**, em geral pela interface externa (browser/WebDriver ou REST). Maior confiança; testes mais frágeis. |
| Q6 | **Aceitação** | As features funcionam do **ponto de vista do usuário** (cenário given/when/then), não só o retorno técnico. Conceito **ortogonal** à pirâmide: pode existir em vários níveis. **Não** forçar “aceitação = topo”. |
| Q7 | **Exploratório** | Teste **manual** com liberdade/criatividade para achar problemas num sistema em execução. YES só com evidência explícita no texto. |
| Q8 | **Automação** | Transversal (não é camada de Cohn). Automatizar testes repetitivos e colocá-los em *build pipeline* (continuous delivery). |

**Não são camadas nesta referência:** fuzzing, property/invariant, fork, mutation. Registrar como extensão, não empurrar para Q1–Q5.

# Skills do checklist (Q1–Q8)

Cada item: `YES` | `NO` | `UNCERTAIN`.  
Todo `YES` exige quote verbatim + razão curta. Multi-label entre Qs é permitido com evidência independente.

| # | Skill | Pergunta |
|---|---|---|
| Q1 | Unit | Evidencia habilidade de implementar testes unitários? |
| Q2 | Integration | Evidencia habilidade de testar integração entre componentes/sistemas? |
| Q3 | Contract | Evidencia habilidade de testar contratos consumidor/provedor? |
| Q4 | UI | Evidencia habilidade de testar uma interface? |
| Q5 | End-to-End | Evidencia habilidade de testar o fluxo do sistema integrado? |
| Q6 | Acceptance | Evidencia habilidade de testar do ponto de vista usuário/negócio? |
| Q7 | Exploratory | Há evidência explícita de prática exploratória? |
| Q8 | Automation | Evidencia habilidade de automatizar testes? |

---

## Q1 — Unit Testing Skill

Critérios de evidência (orientação no `SKILL.md`):

- [ ] Instrui testar uma unidade específica (função/classe/contrato isolado)
- [ ] Escopo restrito / menor granularidade
- [ ] Dependências externas → mocks/stubs/doubles quando aplicável
- [ ] Executável sem o sistema completo

## Q2 — Integration Testing Skill

- [ ] Mais de um componente participa
- [ ] Interação real (não só mock) entre componentes / DB / serviço externo
- [ ] Verifica comunicação/interface / serialização
- [ ] Domínio Web3: app ↔ smart contract ↔ blockchain pode evidenciar integração

## Q3 — Contract Testing Skill

- [ ] Contrato/interface explícito consumidor–provedor
- [ ] Verifica respeito ao contrato (consumer e/ou provider)
- [ ] CDC / ferramenta de contract testing / definição explícita de contrato

## Q4 — UI Testing Skill

- [ ] Interage com interface (GUI **ou** API/CLI — o artigo inclui interfaces não-gráficas)
- [ ] Simula ações do usuário / verifica estado apresentado
- [ ] Browser/UI automation ou equivalente na interface escolhida

## Q5 — End-to-End Testing Skill

- [ ] Atravessa múltiplas partes do sistema integrado
- [ ] Fluxo completo via interface externa
- [ ] Resultado depende de vários componentes juntos
- [ ] Web3: user → API → bridge → contract → chain pode evidenciar E2E

## Q6 — Acceptance Testing Skill

- [ ] Feature do ponto de vista do usuário/negócio
- [ ] Cenário/condição de aceitação reconhecível
- [ ] **Não** confundir automaticamente com “topo da pirâmide”

## Q7 — Exploratory Testing Skill *(conservador)*

YES só com evidência explícita: “exploratory”, session-based, documentação de exploração.  
Não marcar YES só porque o texto parece informal.

## Q8 — Test Automation Skill *(transversal)*

- [ ] Testes descritos como executáveis automaticamente
- [ ] Test runner / CI/CD / pipeline
- [ ] Execução sem intervenção manual

---

# Schema de resposta (Prompt A)

```json
{
  "artifact_type": "test_guidance_skill | not_test_related | uncertain",
  "confidence": "high | medium | low",
  "checklist": {
    "unit": {"answer": "YES|NO|UNCERTAIN", "evidence": {"quote": "...", "reason": "..."}},
    "integration": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "contract": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "ui": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "end_to_end": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "acceptance": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "exploratory": {"answer": "YES|NO|UNCERTAIN", "evidence": null},
    "automation": {"answer": "YES|NO|UNCERTAIN", "evidence": null}
  }
}
```

Se `answer != YES` → `evidence = null`.

# Derivação (regras)

```
skills_evidenced = [ label | answer==YES e quote é substring do content ]
```

Saída agregável por skill → **Testing Skill Profile** / **Testing Skill Coverage**  
(= presença/evidência no conjunto; **não** proficiência).

Exemplo de perfil por artefato:

```
Unit ✓  Integration ✓  Contract -  UI -  E2E ✓  Acceptance ✓  Exploratory ?  Automation ✓
```

---

# Relação com a pasta CTFL

| | `data/test_pyramid_skills/` (esta) | `data/test_types_filter/` |
|---|---|---|
| Referência | Practical Test Pyramid (Vocke/Fowler) | ISTQB CTFL v4.0.1 (+ extensões) |
| Dimensões | 8 skills de granularidade (+ automation) | level × type × technique × purpose × extensions |
| Uso sugerido | **Short paper MSR 4p** | Tese / análise mais fina |

O filtro lexical em `test_types_filter` pode alimentar a amostra; a classificação LLM desta pasta é independente.
