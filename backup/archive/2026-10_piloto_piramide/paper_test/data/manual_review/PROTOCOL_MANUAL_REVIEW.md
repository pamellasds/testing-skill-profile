# Protocolo de revisão manual (anotação cega)

**Objetivo.** Validar o construto *testing skill evidenciada* em agent skills, alinhado à Practical Test Pyramid (Vocke/Fowler), e medir acordo humano×humano e humano×LLM.  
**Não-objetivo.** Não avaliar se o teste é “bom”, se o autor é competente, nem se a skill “deveria” existir.

**Arquivos**

| Arquivo | Quem vê | Conteúdo |
|---|---|---|
| `sample_blind.json` | Revisores | 32 skills sem rótulo de nível lexical |
| `annotation_sheet.csv` | Revisores | planilha YES/NO/UNCERTAIN por skill Pyramid |
| `sample_key.json` | Coordenação (não enviar aos revisores) | estrato lexical + termos batidos |
| `PROTOCOL_MANUAL_REVIEW.md` | Revisores + coordenação | este documento |

**Desenho da amostra**

- Estratificação por **nível de teste** lexical *exclusivo* no pool: Unitário · Integração · E2E · Aceitação.
- **8** itens por estrato → **n = 32** (seed `20270402`).
- Itens escolhidos preferencialmente com conteúdo entre 800–12.000 caracteres (revisáveis).
- Amostra **cega**: o revisor **não** recebe `matched_layers` nem o estrato.

---

## Passo a passo do revisor

### 1. Preparação
1. Ler a referência: [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) (seções Unit, Integration, Contract, UI, E2E, Acceptance, Exploratory).
2. Abrir `sample_blind.json` + `annotation_sheet.csv`.
3. **Não** abrir `sample_key.json`.
4. Trabalhar sozinho (sem discutir rótulos com o outro revisor até o fim).

### 2. Unidade de análise
Para cada `sample_id`, ler `name`, `description` e `content_excerpt` do `SKILL.md`.  
Pergunta-guia:

> *Há evidência observável de que esta skill **instrui** o agente a praticar a skill de teste X?*

Respostas por coluna (Q1–Q8): `YES` | `NO` | `UNCERTAIN`.

| Coluna | Skill | Marque YES se… |
|---|---|---|
| `unit` | Unitário | Instrui testes de unidade/componente isolado; mocks/doubles; escopo restrito |
| `integration` | Integração | Instrui interação real entre componentes / DB / serviços / app↔contrato↔chain |
| `contract` | Contrato | Contrato consumidor–provedor / CDC / definição explícita de contrato |
| `ui` | UI | Interface (GUI **ou** API/CLI) e ações/estado do usuário |
| `end_to_end` | E2E | Fluxo do sistema integrado via interface externa |
| `acceptance` | Aceitação | Feature/negócio/usuário; condição de aceitação (**ortogonal** à pirâmide — não forçar como “topo”) |
| `exploratory` | Exploratório | Evidência **explícita** (exploratory / session-based). Não inferir de texto informal |
| `automation` | Automação | Test runner / CI/CD / execução sem intervenção manual |

### 3. Regras anti-fraqueza
1. **Multi-label permitido** só com evidência independente por coluna.  
2. Menção isolada à palavra (“security”, “test”) **sem** instrução → `NO` ou `UNCERTAIN`.  
3. Ausência de evidência ≠ “o autor não conhece”; só “não evidenciado neste trecho”.  
4. Em dúvida entre dois níveis → `UNCERTAIN` no(s) disputado(s); anote em `notes`.  
5. Se o artefato **não** for orientação a teste → preencha tudo `NO` e note `not_test_related` em `notes`.  
6. Não use o nome do repositório como prova (pode enviesar); use o texto.

### 4. Preenchimento
1. Preencha `annotation_sheet.csv` (uma linha por `sample_id`).  
2. Campos `unit`…`automation`: exatamente `YES`, `NO` ou `UNCERTAIN` (maiúsculas).  
3. `notes`: livre (opcional, obrigatório se UNCERTAIN).  
4. Salve como `annotation_R1.csv` / `annotation_R2.csv` (identificador do revisor).

### 5. Entrega
Enviar apenas o CSV preenchido à coordenação. Tempo sugerido: ~2–3 min/item → ~1,5–2 h no total.

---

## Passo a passo da coordenação (após anotações)

1. Calcular acordo **R1×R2** por coluna (Cohen’s κ ou Krippendorff’s α).  
2. Divergências: discussão + consenso documentado (ou terceiro revisor).  
3. Comparar consenso humano × `llm_pilot` / classificação LLM futura (precisão/recall por skill; κ).  
4. **Só então** consultar `sample_key.json` para checar se o estrato lexical coincide com o julgamento humano (validação do filtro, não do gold da Pyramid).  
5. Registrar ameaças: cegueira quebrada, fadiga, truncamento do excerpt, overclassification.

### O que reportar no paper
- n=32, 8/nível, seed.  
- κ médio (e por skill).  
- Discordâncias típicas (ex.: integração vs E2E; UI vs API).  
- Em WIP: pode reportar o **desenho** agora e κ após anotação.

---

## Checklist rápido (imprimir)

- [ ] Li o artigo da pirâmide  
- [ ] Não vi `sample_key.json`  
- [ ] Só YES/NO/UNCERTAIN  
- [ ] Exploratório só com evidência explícita  
- [ ] Acceptance não forçado como topo  
- [ ] CSV salvo com meu ID de revisor  
