# Testing Skill Profile — execução do protocolo (passo a passo e resultados)

Protocolo: [`docs/protocolo/Protocolo_Testing_Skill_Profile_MSR2027.pdf`](protocolo/Protocolo_Testing_Skill_Profile_MSR2027.pdf) (16/out/2026).
Convenções seguidas: um script por fase com cálculo, seed `20270402`, toda execução registrada em
[`RUNLOG.md`](../RUNLOG.md) (automático), todo número abaixo lido de um JSON em [`results/`](../results/).

| Fase | Estado em 22/out/2026 |
|---|---|
| 1 — Seleção | ✅ executada · ⏳ aguardando revisão dos termos e validação humana (100 + 100) |
| 2 — Instrumento | ✅ v0 escrito · ⏳ aguardando calibração (30 skills) para congelar |
| 3 — Amostragem | ✅ executada · planilhas blind prontas (calibração 30, subamostra 60) |
| 4 — Classificação por LLM | 🟡 calibração (30) rodada com `ministral-14b-2512`: 46,5% dos itens descartados; ver §Fase 4 · 384 aguardam instrumento congelado e escolha do modelo |
| 5 — Anotação humana | ⏳ planilhas prontas para R1 e R2 · métricas de concordância a implementar |
| 6 — Análise e paper | 🟡 metodologia escrita em `paper/main.tex`; gráficos descritivos das Fases 1 e 3 (`src/fase6_paper.py`) |

---

## Fase 1 — Seleção das skills

**Script:** `python src/fase1_selecao.py` → [`results/fase1_selecao.json`](../results/fase1_selecao.json)

### 1.1 Base de dados

`data/raw/gitskills_sample/agent_skills_mandatory_only.db`: subconjunto do GitSkills (jul/2026)
que já tinha passado por um filtro amplo de 389 termos blockchain
(`data/raw/provenance/mandatory_terms_keywords.json`). Unidade de análise: um `SKILL.md`
distinto (`dedup_primary = 1`) → **89.649 skills distintas**.

> **Limitação — o GitSkills completo (41 GB) não está nesta máquina.** O recorte desta fase é
> calculado dentro do `mandatory_only.db`, cuja lista de origem **não** inclui `solidity`, `foundry`,
> `hardhat`, `ethereum` nem `web3`. Assim, uma skill que só mencionasse esses termos (e nenhum dos
> 389) ficou fora. O script aceita `--db <GitSkills completo>.db` e roda sem alterações no banco
> completo (o schema é o mesmo); recomenda-se reexecutar antes da submissão.

### 1.2 Recorte de domínio (termos fortes e fracos)

Arquivo: [`config/termos_dominio.json`](../config/termos_dominio.json) — **75 fortes, 17 fracos**.

- Casamento por regex, sem diferenciar maiúsculas, **com fronteira alfanumérica** (evita `dapp` em
  `dapper`, `evm` em `devmode`), aplicado a nome + descrição + conteúdo.
- Regra do protocolo: entra se tiver **≥ 1 forte** ou **≥ 2 fracos distintos**.
- Os termos foram gerados por LLM (proposta) e **ainda precisam da revisão de R1 e R2**, feita em
  [`annotation/fase1_revisao_termos/revisao_termos.csv`](../annotation/fase1_revisao_termos/revisao_termos.csv).
  A planilha mostra, para cada termo, em quantas skills ele aparece e quantas **só entram por causa
  dele** (contribuição exclusiva), o que indica o impacto de remover cada termo.

**Iteração v0 → v0.1 (registrada em `_notas_de_decisao` no JSON).** Na v0, com fracos genéricos,
o recorte teve 50.169 skills, das quais 22.433 entraram só por fracos. Inspecionei 40 delas, sorteadas,
e quase todas eram Web2 (`plan-eng-review`, `dcf-model`, `turborepo`), puxadas por pares como
`tokens` + `layer 1`, termos comuns em skills de LLM. Foram removidos ou qualificados: `tokens`
(aceito só como `token address/balance/transfer…`), `layer 1/2` e `l2` isolados, `validators`, `consensus`,
`cosmos`, `optimism`, `ledger`, `crypto`, `dao`, `pallets`, `rollup`, `rpc`, `private keys`,
`nonce`, `foundry` e `anvil` isolados (Azure AI Foundry, Foundry VTT). As formas inequívocas continuam
fortes (`foundry.toml`, `forge test`, `anchor-lang`, `cosmos-sdk`).

| Resultado (v0.1) | n |
|---|---:|
| Skills distintas escaneadas | 89.649 |
| **Recorte de domínio** | **28.244** |
| ↳ com ≥ 1 forte | 27.736 |
| ↳ só por ≥ 2 fracos | 508 |

Fortes mais frequentes no recorte: `blockchain` (9.017), `on-chain` (8.576), `mainnet` (6.816),
`ethereum` (6.622), `smart contract` (5.375), `solana` (5.251), `defi` (5.094).

**Pontos de atenção para a revisão dos termos:** `reentrancy` também é termo de concorrência
(ex.: atores Orleans/.NET); `blockchain` é forte mesmo como menção única (ex.: uma skill `debug`). Esses casos
são esperados no recorte e devem receber `web2_incidental` na classificação (Fases 4/5). A
validação de 100 skills vai mostrar se derrubam a precisão abaixo de 0,90.

### 1.3 Filtro de teste

Arquivo: [`config/termos_teste.json`](../config/termos_teste.json) — **56 frases compostas**
(nunca `test` isolado), cobrindo as camadas Q1–Q9, runners (`forge test`, `hardhat test`, `pytest`,
`jest`, `playwright`), fuzz/invariant/formal/fork e TDD/BDD. Como no protocolo, o filtro **só seleciona
candidatas**; quem classifica são as Fases 4 e 5. `brownie test` não teve nenhum acerto.

| Resultado | n |
|---|---:|
| **Pool de candidatas** (recorte ∩ teste) | **4.928** |
| Repositórios distintos (do representante) | 2.100 |
| Conteúdos com ≥ 2 cópias | 1.073 |
| Cópias somadas (todas as ocorrências) | 12.314 |
| Máximo de cópias de um conteúdo | 302 |

Frases de teste mais frequentes no pool: `unit test` (1.169), `fuzz` (1.005), `e2e` (958),
`integration test` (911), `test suite` (699), `playwright` (586), `forge test` (548).

> **Desvio em relação ao protocolo:** o protocolo estimava um pool de ≈ 17,8 mil. Esse número vinha do
> filtro anterior (`archive/2026-09_filtro_lexical_tipos_teste/`), que aplicava os testes sobre
> todas as 89.649 skills do `mandatory_only`, sem o recorte forte/fraco. Com o recorte, o pool
> cai para 4.928. Os 384 da amostra continuam viáveis: há 2.100 repositórios e 3.314 grupos de
> quase-duplicatas.

Saídas: `data/derived/fase1_pool.jsonl` (pool com conteúdo, nº de cópias e repos, termos que
casaram) e `data/derived/fase1_recorte_indice.csv` (recorte sem conteúdo).

### 1.4 Validação da seleção (pendente — humano)

Duas amostras aleatórias simples de 100, geradas com a seed:

| Planilha | Pergunta | Base |
|---|---|---|
| `annotation/fase1_validacao/validacao_dominio_100_blind.csv` | "é blockchain/Web3?" (S/N) | recorte (28.244) |
| `annotation/fase1_validacao/validacao_teste_100_blind.csv` | "fala de teste?" (S/N) | pool (4.928) |

As planilhas são blind: mostram só um ID opaco e o texto exibido, sem repositório, caminho ou termos
que casaram (esses ficam em `annotation/_chaves/`). Depois de preenchidas:
`python src/fase1_selecao.py --precisao` → `results/fase1_validacao.json`, com precisão, IC 95%
de Wilson e se a meta ≥ 0,90 foi atingida (pela estimativa pontual e pelo limite inferior do IC).

**Se a precisão do domínio ficar < 0,90**, o caminho é ajustar os termos com base nos falsos
positivos (a chave mostra quais termos os trouxeram), reexecutar as Fases 1 e 3 e anotar uma nova amostra
de validação.

---

## Fase 2 — Instrumento

Arquivo: [`instrument/instrumento.md`](../instrument/instrumento.md), em inglês porque é também o
prompt. Contém:

- a pergunta única ("o texto **instrui** o agente a fazer isto?"; mencionar ou listar não conta);
- a classe de domínio (`onchain`, `offchain_web3`, `misto`, `web2_incidental`, `indeterminado`);
- os contextos, com regra de decisão em 3 passos;
- o checklist **Q1–Q9**, com critério de YES, adaptação on/off-chain e "não conta";
- o codebook **P1–P10**, com boa e má prática e as fontes da polaridade;
- as regras de evidência (citação literal de 5–40 palavras, justificativa de uma frase, contexto,
  uma citação por item);
- o formato de saída: JSON para a LLM, CSV equivalente para humanos.

Estado **v0 (pré-calibração)**. SHA-256 v0: `520415df15746d90cde8c3df78ce68def700fa1d08733b7342405509902a5b36`
(registrado em `results/fase3_amostragem.json` na exportação das planilhas).

**Calibração (pendente):** R1, R2 e a LLM anotam as 30 skills de `annotation/calibracao_30/`
(fora da amostra principal, sem repetir repositório nem grupo). Em seguida, ajustam os exemplos uma vez,
incluindo novas categorias em P10, e congelam a **v1**. Se o texto mudar, reexecutar
`src/fase3_amostragem.py` só atualiza o hash; a amostra não muda, porque depende apenas do pool e da seed.

---

## Fase 3 — Amostragem

**Script:** `python src/fase3_amostragem.py` → [`results/fase3_amostragem.json`](../results/fase3_amostragem.json)

### 3.1 Quase-duplicatas

MinHash com 128 permutações sobre shingles de 5 palavras do conteúdo (minúsculas). LSH com 16 bandas
× 8 linhas (limiar efetivo ≈ 0,71) gera os pares candidatos; um par é confirmado quando o Jaccard
estimado é ≥ 0,8. Os grupos são o fecho transitivo dos pares (union-find).

| Resultado | n |
|---|---:|
| Grupos de quase-duplicatas no pool | 3.314 |
| Skills em grupos com ≥ 2 membros | 2.078 (42,2% do pool) |
| Maior grupo | 151 (skills templated `agentpmt-tool-*`, 4 repositórios) |
| 2º maior | 61 (`e2e-testing`, copiado em 52 repositórios) |

### 3.2 Sorteio

1. O pool é ordenado por `file_sha` e embaralhado com `random.Random(20270402)`.
2. **Amostra principal (384):** percorre a ordem e aceita uma skill se nem seu repositório nem seu
   grupo já foram usados.
3. **Calibração (30):** continua a mesma ordem com as mesmas restrições, de modo que nenhuma
   skill de calibração compartilha repositório ou grupo com a amostra principal.
4. **Subamostra humana (60):** `rng.sample` dentro das 384.

Verificado: as 414 skills (384 + 30) vêm de 414 repositórios distintos e 414 grupos distintos.

**Texto exibido** (idêntico para LLM e humanos): `NAME` + `DESCRIPTION` + conteúdo até 8.000
caracteres, com o marcador `[... truncado em 8000 caracteres]`. **246 das 384 (64%) são truncadas.**
Isso entra como ameaça à validade, porque instruções de teste no fim de skills longas ficam de fora.

### 3.3 Saídas

| Arquivo | Uso |
|---|---|
| `data/derived/fase3_amostra_principal_384.csv` | entrada da Fase 4 (LLM) — inclui repo e `na_subamostra_60` |
| `data/derived/fase3_grupos_minhash.csv` | grupo de quase-duplicata de cada skill do pool |
| `annotation/calibracao_30/{R1,R2}/` | calibração (Fase 2) |
| `annotation/fase5_subamostra_60/{R1,R2}/` | anotação cega (Fase 5) |
| `annotation/_chaves/*_chave.csv` | ID opaco → repo/path/sha (**não abrir durante a anotação**) |

Cada pasta de revisor tem `skills.csv` (classe de domínio, tempo, status e texto), `camadas.csv`
(9 linhas por skill, Q1–Q9) e `praticas.csv` (uma linha por prática encontrada). Os textos também estão em
`textos/<ID>.txt` para leitura confortável. Instruções: [`annotation/LEIA-ME_ANOTACAO.md`](../annotation/LEIA-ME_ANOTACAO.md).

---

## Fase 4 (parcial) — LLM na calibração

**Script:** `python src/fase4_llm.py --conjunto calibracao_30|principal_384|subamostra_60 [--execucoes 3]`
→ `results/fase4_<conjunto>.json`, `data/derived/fase4_llm/` (checkpoint JSONL + planilhas no formato de R1/R2).
O prompt de sistema é o `instrumento.md` sem alteração (hash registrado). Na checagem automática, cada item com
evidência precisa de enum válido e de uma citação de 5–40 palavras, literal e não repetida. Os itens que falham
voltam uma vez ao modelo (prompt de correção também com hash); se falharem de novo, viram UNCERTAIN.

**Modelo:** só a família `ministral` responde nas chaves atuais (medium/small/magistral dão 429; large dá 403).
Usado `ministral-14b-2512` (versão fixa), temperatura 0.

| Calibração, 30 skills (Mistral) | n |
|---|---:|
| Skills que precisaram da 2ª tentativa | 29 / 30 |
| Itens com evidência | 260 |
| Itens UNCERTAIN (descartados) | **121 (46,5%)** |
| Classe de domínio | onchain 8 · offchain_web3 5 · misto 6 · web2_incidental 11 |

**Comparação com Claude (Opus, subagente, mesmo instrumento, às cegas) nas primeiras 6 skills:** o Claude
teve 0 de 19 itens reprovados na checagem, contra 28 de 52 (54%) do Mistral. A classe de domínio coincidiu nas 6,
e a concordância bruta nas camadas foi de 74%. O Mistral superclassifica: na `guardian-protocol` marcou 7
camadas e 9 práticas onde o Claude não marcou nenhuma, porque a skill descreve um produto e não instrui
teste. Saída do Claude: `data/derived/fase4_claude/` (só para comparação; o subagente não tem temperatura
nem versão fixas, então não serve como execução oficial da Fase 4).

**Casos ambíguos levantados para a calibração:** (1) execução simbólica (Mythril) não está nomeada no Q9;
(2) fronteira "descrever capacidades de um produto" × "instruir a testar"; (3) exploração manual de exploit
como Q7 e validação de cadeia de exploit como Q5; (4) candidata a P10: "não reportar como confirmado o que não
foi verificado".

**Decisão pendente:** o `ministral-14b` não parece adequado para a Fase 4 (46,5% de descarte e
superclassificação). Alternativa: Claude via API, com modelo fixo e temperatura 0 (exige `ANTHROPIC_API_KEY`).

## Fase 6 (parcial) — gráficos descritivos

**Script:** `python src/fase6_paper.py`, que gera `paper/numeros.tex` (macros LaTeX: todo número do paper),
`paper/figures/*.pdf` (matplotlib) e [`results/fase6_descritivo.json`](../results/fase6_descritivo.json).

- **`grupos_tamanho.pdf`**: skills do pool por tamanho do grupo de quase-duplicatas. 57,8% são
  únicas; 12,7% pertencem a templates com mais de 20 variantes.
- **`camadas_lexicas.pdf`**: % de skills com ≥ 1 frase de teste mapeada a cada camada Q1–Q9, no pool e
  na amostra de 384 (IC 95% de Wilson). O mapeamento frase → camada está em `LAYER_TERMS`. São
  **casamentos de termos, não a classificação** (ex.: "contract testing" casa com "smart contract
  testing"); servem como linha de base lexical para comparar com a LLM e o consenso depois. O valor do pool
  cai dentro do IC da amostra em 8 das 9 camadas. A exceção é E2E (20,8% no pool contra 15,6% na amostra):
  o template `e2e-testing`, copiado em 52 repositórios, infla o pool e aparece uma única vez na amostra.

A Figura 1 (diagrama da metodologia) é TikZ: `paper/figures/fig_metodologia.tex`.

## Próximos passos

1. **R1 + R2:** revisar os termos (`revisao_termos.csv`). Se algum termo mudar, reexecutar as Fases 1 e 3.
2. **R1:** anotar a validação da seleção (100 + 100) e rodar `--precisao`.
3. **R1 + R2 + LLM:** calibração com as 30 skills, depois congelar o instrumento v1.
4. **Fase 4 (LLM):** escolher modelo e versão, temperatura 0, hash do prompt, checagem automática
   de citação e 3 execuções nas 60 da subamostra.
5. **Fase 5:** R1 e R2 anotam as 60 sem ver a LLM; implementar κ/AC1, F1 e o casamento de citações
   com sobreposição ≥ 50%.
6. Reexecutar a Fase 1 no GitSkills completo, se o banco de 41 GB estiver disponível.

## Ameaças registradas até aqui

- **Base parcial:** o recorte foi feito dentro do `mandatory_only.db`, não do GitSkills completo (§1.1).
- **Termos:** a v0.1 foi ajustada por inspeção informal de 40 skills; a precisão formal depende da
  validação de 100 (§1.4).
- **Truncamento:** 64% da amostra passa de 8.000 caracteres (§3.2).
- **1 por repositório** usa o repositório do representante do conteúdo; cópias do mesmo conteúdo
  em outros repositórios não bloqueiam esses repositórios.
