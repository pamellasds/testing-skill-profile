# Testing Skill Profile — GitSkills × Practical Test Pyramid (MSR 2027 Mining Challenge)

Quais práticas de teste as agent skills do domínio blockchain instruem o agente a seguir?
Protocolo: [`docs/protocolo/`](docs/protocolo/Protocolo_Testing_Skill_Profile_MSR2027.pdf).
**Passo a passo e resultados: [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md).** Execuções: [`RUNLOG.md`](RUNLOG.md).

## Estrutura

```
config/          termos da Fase 1 (domínio forte/fraco, frases de teste)
instrument/      instrumento.md — guideline humano = prompt da LLM (Q1–Q9, P1–P10)
src/             comum.py · fase1_selecao.py · fase3_amostragem.py · fase4_llm.py · fase6_paper.py
data/raw/        bancos GitSkills (mandatory_only.db, ...) e proveniência dos termos
data/derived/    saídas intermediárias (pool, grupos MinHash, amostra 384)
results/         JSONs com todo número reportado
annotation/      planilhas blind para revisão manual (+ _chaves/ separadas)
paper/           main.tex (IEEEtran), figures/ (gráficos .pdf gerados em Python), numeros.tex
docs/            protocolo, referências, METODOLOGIA.md
archive/         abordagens anteriores (ver archive/README.md)
```

## Reproduzir

Requer Python 3.10, `numpy` e `matplotlib` (`pip install -r requirements.txt`).

```bash
python src/fase1_selecao.py              # ~3 min (8 núcleos): recorte, pool, planilhas de validação
python src/fase3_amostragem.py           # ~30 s: MinHash, amostras 384/30/60, planilhas blind
python src/fase1_selecao.py --precisao   # após a anotação da validação (100 + 100)
python src/fase6_paper.py                # macros paper/numeros.tex + gráficos paper/figures/*.pdf
cd paper && latexmk -pdf main.tex
```

Seed `20270402`. Os mesmos dados de entrada e configurações produzem as mesmas amostras.
