# Instruções para os revisores (R1, R2)

**Regra de ouro (blind):** trabalhe só na sua pasta (`R1/` ou `R2/`). Não abra a pasta do outro
revisor, `annotation/_chaves/`, `data/derived/` nem qualquer saída de LLM até terminar.

Leia antes o instrumento: [`../instrument/instrumento.md`](../instrument/instrumento.md).

## 1. Revisão dos termos (Fase 1) — R1 e R2

`fase1_revisao_termos/revisao_termos.csv`: para cada termo, preencha a sua coluna
`R?_decisao` com `manter`, `remover` ou `mover` (forte ↔ fraco) e use `comentario` se precisar.
`skills_que_so_entram_por_ele` mostra quantas skills sairiam se o termo fosse removido.

## 2. Validação da seleção (Fase 1) — um revisor

- `fase1_validacao/validacao_dominio_100_blind.csv` → coluna `e_blockchain_web3 (S/N)`
- `fase1_validacao/validacao_teste_100_blind.csv` → coluna `fala_de_teste (S/N)`

Responda `S` ou `N`. Na dúvida, use `N` e explique em `observacao`. Depois rode
`python src/fase1_selecao.py --precisao`.

## 3. Calibração (30) e subamostra (60) — R1 e R2, independentes

Pastas `calibracao_30/` e `fase5_subamostra_60/`. Cada skill tem um ID opaco (`GS-XXXXXXXX`) e
o texto em `textos/<ID>.txt` (o mesmo de `texto_exibido`). Tempo esperado: ≈ 10 min por skill.

| Planilha | O que preencher |
|---|---|
| `skills.csv` | `classe_dominio` (`onchain`, `offchain_web3`, `misto`, `web2_incidental`, `indeterminado`), `justificativa_classe`, `tempo_min`, `status` → `concluida` |
| `camadas.csv` | 9 linhas por skill (Q1–Q9): `resposta` YES/NO; se YES, `citacao` (literal, 5–40 palavras), `justificativa` (1 frase) e `contexto` (`onchain`, `offchain_web3`, `web2`) |
| `praticas.csv` | **uma linha por prática instruída**: `skill_id`, `categoria` (P1–P10), `polaridade` (`good`/`bad`, conforme o codebook), `citacao`, `contexto`, `justificativa`. Skill sem práticas não ganha linha; marque `concluida` em `skills.csv` mesmo assim |

Regras de evidência: copie a citação **literalmente** (sem "…" e sem reconstruir tabelas); a mesma
citação não pode justificar dois itens; só conta o que é **instruído**.

Os CSVs estão em UTF-8 com BOM e abrem direto no LibreOffice ou no Excel. Salve mantendo o formato CSV e
o separador vírgula.
