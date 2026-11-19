# MSR 2027 Mining Challenge — Short Paper (GitSkills × Practical Test Pyramid)

Track: <https://2027.msrconf.org/track/msr-2027-mining-challenge>

**Título (rascunho):** *Que Skills de Teste as Agent Skills Ensinam? Um Perfil Preliminar via Practical Test Pyramid no GitSkills*

**Autora (rascunho interno):** Pamella Soares (UECE).  
> Para submissão HotCRP: gerar PDF **anônimo** (remover `\author`) — o challenge exige double-anonymous.

## Estrutura

```
2027_short_paper_challenge/
├── README.md
├── data/
│   ├── results/          # stats, piloto LLM, guideline
│   ├── plots/            # todos os PNGs
│   └── manual_review/    # amostra blind + protocolo revisores
├── paper/
│   ├── main.tex          # IEEE 10pt conference (PT)
│   ├── references.bib
│   ├── figures/          # figuras usadas no PDF
│   └── main.pdf
└── scripts/
    └── prepare_artifacts.py
```

## Resultados principais (já no paper)

| Nível de teste (lexical, pool n=17.847) | Skills | % |
|---|---:|---:|
| Unitário | 5.348 | 30,0 |
| Integração | 4.215 | 23,6 |
| E2E | 2.552 | 14,3 |
| Aceitação | 496 | 2,8 |

Extras: coverage 29,9%; regression 26,6%; fuzz/property 9,9%; fork 2,8%.

## Revisão manual

1. Revisores: ler `data/manual_review/PROTOCOL_MANUAL_REVIEW.md`
2. Anotar `sample_blind.json` → `annotation_sheet.csv` (não abrir `sample_key.json`)
3. n=32, 8 por nível exclusivo, seed 20270402

## Compilar o paper

```bash
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```

## Regenerar plots/amostra

```bash
python scripts/prepare_artifacts.py
```
