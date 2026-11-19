# RUNLOG — execuções dos scripts (gerado automaticamente por src/comum.py:log_run)


## 2026-10-22 23:51 UTC — `python fase1_selecao.py`

- seed: 20270402
- skills_distintas_escaneadas: 89649
- recorte_dominio: 28244
- pool_candidatas: 4928
- saídas:
  - `data/derived/fase1_pool.jsonl`
  - `data/derived/fase1_recorte_indice.csv`
  - `annotation/fase1_revisao_termos/revisao_termos.csv`
  - `annotation/fase1_validacao/validacao_dominio_100_blind.csv`
  - `annotation/_chaves/validacao_dominio_100_chave.csv`
  - `annotation/fase1_validacao/validacao_teste_100_blind.csv`
  - `annotation/_chaves/validacao_teste_100_chave.csv`
  - `results/fase1_selecao.json`

## 2026-10-22 23:52 UTC — `python fase3_amostragem.py`

- seed: 20270402
- pool: 4928
- grupos_quase_dup: 3314
- amostra_principal: 384
- calibracao: 30
- subamostra_humana: 60
- saídas:
  - `data/derived/fase3_grupos_minhash.csv`
  - `data/derived/fase3_amostra_principal_384.csv`
  - `annotation/calibracao_30`
  - `annotation/_chaves/calibracao_30_chave.csv`
  - `annotation/fase5_subamostra_60`
  - `annotation/_chaves/fase5_subamostra_60_chave.csv`
  - `results/fase3_amostragem.json`

## 2026-10-23 00:09 UTC — `python fase6_paper.py`

- seed: 20270402
- macros: 47
- saídas:
  - `paper/numeros.tex`
  - `paper/figures/dados/camadas_lexicas.dat`
  - `paper/figures/dados/grupos_tamanho.dat`
  - `results/fase6_descritivo.json`

## 2026-10-23 00:15 UTC — `python fase6_paper.py`

- seed: 20270402
- macros: 47
- saídas:
  - `paper/numeros.tex`
  - `paper/figures/camadas_lexicas.pdf`
  - `paper/figures/grupos_tamanho.pdf`
  - `results/fase6_descritivo.json`

## 2026-10-23 00:16 UTC — `python fase6_paper.py`

- seed: 20270402
- macros: 47
- saídas:
  - `paper/numeros.tex`
  - `paper/figures/camadas_lexicas.pdf`
  - `paper/figures/grupos_tamanho.pdf`
  - `results/fase6_descritivo.json`

## 2026-10-23 00:43 UTC — `python fase4_llm.py --conjunto calibracao_30`

- seed: 20270402
- modelo: ministral-14b-2512
- conjunto: calibracao_30
- execucoes: 1
- instrumento_sha256: 520415df1574
- saídas:
  - `data/derived/fase4_llm/calibracao_30_exec1.jsonl`
  - `data/derived/fase4_llm/calibracao_30_exec1`
  - `results/fase4_calibracao_30.json`
