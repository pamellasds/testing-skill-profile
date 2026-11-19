"""Fase 6 — números e dados de figuras do paper, lidos de results/ e data/derived/.

Gera:
  paper/numeros.tex                   macros LaTeX (todo número do paper vem daqui)
  paper/figures/camadas_lexicas.pdf   sinais lexicais por camada: pool x amostra (IC 95% de Wilson)
  paper/figures/grupos_tamanho.pdf    skills do pool por tamanho do grupo de quase-duplicatas
  results/fase6_descritivo.json       os valores dos gráficos, para auditoria

Os sinais lexicais são casamentos de termos do filtro de teste, NÃO a classificação das Fases 4/5.

Uso:
    python src/fase6_paper.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from comum import DERIVED, RESULTS, ROOT, SEED, log_run, wilson, write_json

csv.field_size_limit(10**8)
FIG = ROOT / "paper/figures"
POOL_BLUE, SAMPLE_ORANGE, INK, GRID = "#2a78d6", "#eb6834", "#333333", "#e3e3e3"  # paleta validada (CVD-safe)
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "mathtext.fontset": "stix", "font.size": 7.5, "axes.edgecolor": "#999999",
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "pdf.fonttype": 42})
COL_W = 3.5  # largura de uma coluna IEEEtran (pol.)

# termos de config/termos_teste.json -> camada do checklist (os demais são genéricos e ficam fora)
LAYER_TERMS = {
    "Q1 Unit": ["unit[- ]?(tests?|testing)"],
    "Q2 Integration": ["integration (tests?|testing)"],
    "Q3 Contract": ["contract (tests?|testing)", "consumer[- ]driven contracts?", "pact (tests?|testing)"],
    "Q4 UI": ["ui (tests?|testing)", "playwright", "cypress"],
    "Q5 E2E": ["e2e( tests?| testing)?", "end[- ]to[- ]end (tests?|testing)"],
    "Q6 Acceptance": ["acceptance (tests?|testing)", "bdd", "behaviou?r[- ]driven", "gherkin",
                      "given[ /,-]+when[ /,-]+then"],
    "Q7 Exploratory": ["exploratory (tests?|testing)"],
    "Q8 Automation": ["test automation", "automated (tests?|testing)", "run (the )?tests", "forge (test|coverage|snapshot)",
                      "hardhat test", "anchor test", "truffle test", "brownie test", "ape test", "pytest", "jest",
                      "vitest", "mocha"],
    "Q9 Web3-specific": ["fuzz(ing|er|ed)?", "fuzz (tests?|testing)", "invariant (tests?|testing)",
                         "property[- ]based (tests?|testing)", "echidna", "halmos", "certora", "formal verification",
                         "symbolic execution", "fork (tests?|testing)", "forked tests?", "mainnet fork(ing|s)?",
                         "--fork-url", "fork[- ]block[- ]number", "gas (snapshots?|reports?)"],
}
SIZE_BINS = [("1", 1, 1), ("2", 2, 2), ("3--5", 3, 5), ("6--20", 6, 20), ("21+", 21, 10**9)]


def fmt(v) -> str:
    return f"{v:,}" if isinstance(v, int) else str(v)


def pct(k: int, n: int) -> float:
    return round(100 * k / n, 1)


def lexical_layers() -> list[dict]:
    with (DERIVED / "fase1_pool.jsonl").open(encoding="utf-8") as f:
        hits = {r["file_sha"]: set(r["test"]) for r in map(json.loads, f)}
    with (DERIVED / "fase3_amostra_principal_384.csv").open(encoding="utf-8-sig") as f:
        sample = [r["file_sha"] for r in csv.DictReader(f)]
    rows = []
    for layer, terms in LAYER_TERMS.items():
        kp = sum(bool(h & set(terms)) for h in hits.values())
        ks = sum(bool(hits[s] & set(terms)) for s in sample)
        lo, hi = wilson(ks, len(sample))
        rows.append({"camada": layer, "pool_n": kp, "pool_pct": pct(kp, len(hits)), "amostra_n": ks,
                     "amostra_pct": pct(ks, len(sample)), "amostra_ic95": [round(100 * lo, 1), round(100 * hi, 1)]})
    return rows


def group_sizes() -> list[dict]:
    with (DERIVED / "fase3_grupos_minhash.csv").open(encoding="utf-8-sig") as f:
        sizes = [int(r["tamanho_grupo"]) for r in csv.DictReader(f)]
    c = Counter(next(lbl for lbl, lo, hi in SIZE_BINS if lo <= s <= hi) for s in sizes)
    return [{"tamanho": lbl, "skills": c[lbl], "pct": pct(c[lbl], len(sizes))} for lbl, _, _ in SIZE_BINS]


def style(ax, grid_axis: str) -> None:
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=2, width=0.6)


def plot_layers(layers: list[dict], n_pool: int, n_sample: int) -> None:
    fig, ax = plt.subplots(figsize=(COL_W, 2.5))
    y = list(range(len(layers)))[::-1]  # Q1 no topo
    h = 0.36
    ax.barh([v + h / 2 for v in y], [r["pool_pct"] for r in layers], h, color=POOL_BLUE,
            label=f"Pool (n = {n_pool:,})", edgecolor="white", linewidth=0.5)
    ax.barh([v - h / 2 for v in y], [r["amostra_pct"] for r in layers], h, color=SAMPLE_ORANGE,
            label=f"Main sample (n = {n_sample}; 95% CI)", edgecolor="white", linewidth=0.5,
            xerr=[[r["amostra_pct"] - r["amostra_ic95"][0] for r in layers],
                  [r["amostra_ic95"][1] - r["amostra_pct"] for r in layers]],
            error_kw={"ecolor": "#555555", "elinewidth": 0.6, "capsize": 1.5, "capthick": 0.6})
    ax.set_yticks(y, [r["camada"] for r in layers])
    ax.set_xlabel("Skills with ≥ 1 matching phrase (%)")
    ax.set_xlim(0, 45)
    style(ax, "x")
    ax.tick_params(axis="y", length=0)
    ax.legend(loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=2, frameon=False, handlelength=1, columnspacing=1.2)
    fig.savefig(FIG / "camadas_lexicas.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plot_groups(groups: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(COL_W, 1.55))
    labels = [g["tamanho"].replace("--", "–") for g in groups]
    bars = ax.bar(labels, [g["pct"] for g in groups], 0.55, color=POOL_BLUE)
    ax.bar_label(bars, labels=[f"{g['pct']:.1f}" for g in groups], padding=1.5, fontsize=7, color=INK)
    ax.set_xlabel("Near-duplicate group size (Jaccard ≥ 0.8)")
    ax.set_ylabel("Pool skills (%)")
    ax.set_ylim(0, 70)
    style(ax, "y")
    ax.tick_params(axis="x", length=0)
    fig.savefig(FIG / "grupos_tamanho.pdf", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def main() -> None:
    f1 = json.loads((RESULTS / "fase1_selecao.json").read_text())
    f3 = json.loads((RESULTS / "fase3_amostragem.json").read_text())
    layers, groups = lexical_layers(), group_sizes()
    write_json(RESULTS / "fase6_descritivo.json", {"camadas_lexicas": layers, "grupos_tamanho": groups})

    FIG.mkdir(parents=True, exist_ok=True)
    plot_layers(layers, f1["pool_candidatas"], f3["amostra_principal"])
    plot_groups(groups)

    singletons = next(g for g in groups if g["tamanho"] == "1")
    big = next(g for g in groups if g["tamanho"] == "21+")
    macros = {
        "Seed": str(SEED),
        "NScanned": f1["skills_distintas_escaneadas"], "NDomain": f1["recorte_dominio"],
        "NDomainStrong": f1["recorte_por_regra"]["com_forte"], "NDomainWeak": f1["recorte_por_regra"]["so_fracos_ge2"],
        "NStrongTerms": f1["n_termos"]["fortes"], "NWeakTerms": f1["n_termos"]["fracos"], "NTestTerms": f1["n_termos"]["teste"],
        "NPool": f1["pool_candidatas"], "NPoolRepos": f1["pool_repos_distintos_representante"],
        "NPoolCopies": f1["pool_copias_total"], "NPoolWithCopies": f1["pool_conteudos_com_copias"],
        "NPoolMaxCopies": f1["pool_max_copias"],
        "NGroups": f3["grupos_quase_dup"], "NInGroups": f3["skills_em_grupos_com_2_ou_mais"],
        "PctInGroups": f"{100 * f3['skills_em_grupos_com_2_ou_mais'] / f3['pool']:.1f}\\%",
        "NMaxGroup": f3["maior_grupo"], "NMain": f3["amostra_principal"], "NCal": f3["calibracao"],
        "NSub": f3["subamostra_humana"], "NTrunc": f3["skills_truncadas_na_amostra"],
        "PctTrunc": f"{100 * f3['skills_truncadas_na_amostra'] / f3['amostra_principal']:.1f}\\%",
        "NPerm": f3["minhash"]["permutacoes"], "NBands": f3["minhash"]["bandas"],
        "NShingle": f3["minhash"]["shingle_palavras"], "JaccardMin": f3["minhash"]["jaccard_min"],
        "NBigGroupSkills": big["skills"], "PctBigGroupSkills": f"{big['pct']}\\%",
        "PctSingletons": f"{singletons['pct']}\\%",
    }
    for r in layers:  # ex.: \LexPoolQone, \LexSampleQnine
        q = "Q" + ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][int(r["camada"][1]) - 1]
        macros[f"LexPool{q}"] = f"{r['pool_pct']}\\%"
        macros[f"LexSample{q}"] = f"{r['amostra_pct']}\\%"
    lines = ["% Gerado por src/fase6_paper.py a partir de results/ e data/derived/. Não editar à mão."]
    lines += [rf"\newcommand{{\{k}}}{{{fmt(v)}\xspace}}" for k, v in macros.items()]
    (ROOT / "paper/numeros.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    outs = [ROOT / "paper/numeros.tex", FIG / "camadas_lexicas.pdf", FIG / "grupos_tamanho.pdf",
            RESULTS / "fase6_descritivo.json"]
    log_run({"macros": len(macros)}, outs)
    print(json.dumps({"camadas_lexicas": layers, "grupos_tamanho": groups}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
