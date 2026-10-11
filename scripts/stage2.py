"""Stage 2: tornado, Monte Carlo with named scenarios, kill-condition check, marginal returns, break-evens.

Run: uv run python scripts/stage2.py [--draws N]
Writes results/stage2.md, results/tornado.csv, results/monte_carlo_draws.csv, and regenerates the blocks of
README.md between <!-- generated:NAME:begin --> and <!-- generated:NAME:end --> markers, so every number in
those blocks comes from params/parameters.yaml and data/.
"""

import argparse
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import analysis as an  # noqa: E402
from src.funnel import funnel  # noqa: E402
from src.params import load, records, resolve  # noqa: E402

LEVEL_NAMES = {
    "dft_confirmed_stable": "Level 1: per DFT-confirmed stable",
    "experimentally_validated": "Level 2: per validated material",
    "validated_new": "Level 3: per validated new material (lower-bound quantity; see README)",
}
SHORT = {"dft_confirmed_stable": "L1", "experimentally_validated": "L2", "validated_new": "L3"}
WORLDVIEW = {"optimistic_alab": "optimistic (A-Lab)", "middle_prein": "middle (Prein)",
             "pessimistic_leeman": "pessimistic (Leeman)"}
READING_SHORT = {"optimistic_alab": "A-Lab", "middle_prein": "Prein", "pessimistic_leeman": "Leeman"}
# Analysis criteria (not model parameters): what counts as "compute matters" and "materially different".
COMPUTE_SHARE = 0.10
SPREAD = 1.10
MATERIAL = 0.10
ORDER_SURVIVES = 0.95
MATERIAL_MAJORITY = 0.50
TOP_SHARE = 0.80


def money(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if math.isinf(x):
        return "unbounded"
    return f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"


def pct(x, digits=0):
    return "n/a" if x is None or math.isnan(x) else f"{100 * x:.{digits}f}%"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- sections


def daf_section(doc, p):
    e = an.enrichment(doc, p)
    pool, gen, wbm = e["pool"], e["gen"], e["wbm"]
    rows = [
        ["WBM (Matbench Discovery, reported)", pct(wbm["prevalence"], 1), "", f"{wbm['daf_reported']:.2f}×", ""],
        ["ion-exchange pool (Szymanski & Bartel)", pct(pool["prevalence"], 1), pct(pool["purity"], 1),
         f"**{pool['daf_measured']:.2f}×**", f"{pool['daf_matbench_rates_at_this_prevalence']:.2f}×"],
        ["MatterGen pool (Szymanski & Bartel)", pct(gen["prevalence"], 1), pct(gen["purity"], 1),
         f"**{gen['daf_measured']:.2f}×**", f"{gen['daf_matbench_rates_at_this_prevalence']:.2f}×"],
    ]
    ml = an.funnel(p)["pipelines"]["B"]["mlip"]
    mlc = an.funnel(p)["pipelines"]["C"]["mlip"]
    return f"""### Named finding: CHGNet's discovery acceleration factor is {pool['daf_measured']:.2f}× on a realistic ion-exchange pool, against {wbm['daf_reported']:.2f}× on WBM

The discovery acceleration factor (DAF) is the ratio of the filter's precision to the pool's prevalence: how many
times more often a filter-passed candidate is stable than a random one. Matbench Discovery defines it exactly so
("Formally the DAF is the ratio of the precision to the prevalence"). On Szymanski & Bartel's pools it is the
measured post-filter purity divided by the measured unfiltered stable fraction. That is the same quantity on both
sides, so the comparison needs no assumption about which classifier rate transfers.

{md_table(["Pool", "Stable fraction", "Purity after CHGNet", "DAF", "DAF if Matbench rates held at this prevalence"], rows)}

On the ion-exchange pool CHGNet's enrichment is {pool['daf_measured']:.2f}×. On MatterGen's pool it is
{gen['daf_measured']:.2f}×: the filter barely enriches at all. DAF depends on prevalence (its ceiling is
1 / prevalence), so the last column applies Matbench's recall and false-positive rate at each pool's own
prevalence. That makes the like-for-like comparison {pool['daf_measured']:.2f}× against
{pool['daf_matbench_rates_at_this_prevalence']:.2f}×, a larger gap than against the reported
{wbm['daf_reported']:.2f}×.

**Mechanism (rests on an assumption).** If Matbench's recall ({p['mlip_tpr']:.2f}) transfers to these pools,
the measured purity implies a false-positive rate of {ml['implied_fpr']:.2f} on the ion-exchange pool
({mlc['implied_fpr']:.2f} on MatterGen's), against {ml['matbench_fpr']:.2f} on WBM. The other attribution is
that Matbench's false-positive rate transfers and recall collapses. That would need recall of
{ml['recall_implied_by_purity_and_matbench_fpr']:.2f} and
{mlc['recall_implied_by_purity_and_matbench_fpr']:.2f}, which are implausible. The DAF result above does not
depend on this attribution.

**Why the gap: two explanations, one unresolved.**

1. *Distribution shift is weak as an explanation.* WBM was "generated via chemical similarity-based elemental
   substitution of MP source structures" over five rounds (Matbench Discovery, section 2.1.2). That is the same
   construction as Szymanski & Bartel's data-driven ion exchange. If anything, Matbench's unique-prototype subset
   removes structures whose protostructure matches MP, while ion exchange only reuses MP prototypes (0% novel
   prototypes). So the WBM test set is not the more conservative pool.
2. *The stability criteria differ, an unresolved competing explanation.* Matbench labels a structure stable if
   it is "on or below the convex hull of the MP training set" (MP v2022.10.28). It explicitly rejects using the
   joint MP + WBM hull, and it notes that only about 20k of the about 33k WBM structures below the MP hull remain
   on the joint hull. Szymanski & Bartel compute ΔE_d ≤ 0 against phase diagrams that "included all entries from
   MP (as of June 2025) as well as the entries generated from each AI model or baseline approach". That is a
   newer MP and a hull that also contains the other generated candidates, close to the joint-hull formulation
   Matbench rejected. The two criteria agree on the threshold (on or below the hull) but not on the hull. A
   stricter hull lowers both prevalence and the share of passed candidates that count as stable, so part of the
   gap may be definitional rather than a weakness of the filter. Public data can resolve this: recompute CHGNet's
   DAF on WBM against the joint MP + WBM hull. Until then the DAF gap is a measured fact, but its cause is open.
"""


def distributions_section(doc):
    mc = doc["monte_carlo"]
    recs = records(doc)
    rows = []
    for name, spec in mc["distributions"].items():
        rec = recs[name]
        if spec["type"] in ("triangular", "log_triangular"):
            params = f"{rec['low']:g} / {rec['base']:g} / {rec['high']:g}"
        elif spec["type"] in ("log_uniform", "uniform"):
            params = f"{rec['low']:g} to {rec['high']:g}"
        elif spec["type"] == "beta_counts":
            params = f"{spec['k']} of {spec['n']}"
        else:
            params = f"{len(spec['values'])} values, {min(spec['values']):g}–{max(spec['values']):g}"
        rows.append([f"`{name}`", spec["type"], params, spec["reason"]])
    j = mc["joint"]
    joint_rows = [["pool stability, novelty, filter purity", j["pools"]["method"], j["pools"]["reason"]],
                  ["synthesis success, novelty, wrong-verdict share",
                   "; ".join(f"{WORLDVIEW[k]}: success {v['success']['k']}/{v['success']['n']}, novelty "
                             f"{v['novelty']['k']}/{v['novelty']['n']}, wrong verdict "
                             + (f"{v['wrong_verdict']['k']}/{v['wrong_verdict']['n']}" if v['wrong_verdict']['type'] == 'beta_counts'
                                else f"uniform {v['wrong_verdict']['low']}–{v['wrong_verdict']['high']}")
                             for k, v in j["worldview"]["readings"].items()) + f". {j['worldview']['weights_reason']}",
                   j["worldview"]["reason"]],
                  ["recipes per target", j["recipes"]["method"], j["recipes"]["reason"]]]
    return ("**Sampled parameters** (all others held at base; triangular parameters are low / mode / high = the "
            "record's low / base / high):\n\n"
            + md_table(["Parameter", "Distribution", "Parameters", "Why"], rows)
            + "\n\n**Joint draws** (the documented correlations, not sampled independently):\n\n"
            + md_table(["Drawn together", "How", "Why"], joint_rows))


def tornado_section(tor, top=8):
    parts, top_rows = [], []
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            rows = tor[lvl][k]
            names = an.top_share(rows, TOP_SHARE)
            top_rows.append([f"{SHORT[lvl]} {k}", ", ".join(f"`{n}`" for n in names)
                             + "".join(f"; `{r['name']}` {r['status']}" for r in rows if r["status"] != "ok")])
    l1 = tor["dft_confirmed_stable"]["B"][0]
    l2 = tor["experimentally_validated"]["B"][0]
    parts.insert(0, f"**Read this tornado as a map of where the evidence is weakest, not of where the leverage is.** "
                    f"One parameter carries almost all of the one-at-a-time variance at each level: `{l1['name']}` "
                    f"({pct(l1['share'], 1)} at level 1, B) and `{l2['name']}` ({pct(l2['share'], 1)} at level 2, B). "
                    "They dominate because they have the widest ranges (3–1,000 core-h; 5–70% success), not because "
                    "the cost responds more strongly to them. For leverage per unit change, see the marginal returns, "
                    "where three synthesis levers are tied at unit elasticity. The two quantities the paper most needs "
                    "better measurements of are DFT cost per candidate on modern hardware and synthesis success on "
                    "independent campaigns.")
    parts.append(f"**Parameters that account for the top {TOP_SHARE:.0%} of variance** (one-at-a-time, "
                 "share = swing² / Σ swing²; parameters whose one end makes the inputs contradict each other, or makes "
                 "the cost unbounded, are listed after the semicolon and left out of the shares):\n\n"
                 + md_table(["Output", "Parameters"], top_rows))
    for k in an.PIPELINES:
        rows = [r for r in tor["experimentally_validated"][k] if r["status"] != "ok" or r["swing"] > 0][:top]
        parts.append(f"**Tornado, level 2, pipeline {k}** (top {top}; full tables in `results/stage2.md`):\n\n"
                     + md_table(["Parameter", "cost at low", "cost at high", "swing", "variance share"],
                                [[f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                                  money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 1)]
                                 for r in rows]))
    rows = [r for r in tor["dft_confirmed_stable"]["B"] if r["status"] != "ok" or r["swing"] > 0][:top]
    parts.append(f"**Tornado, level 1, pipeline B** (top {top}):\n\n"
                 + md_table(["Parameter", "cost at low", "cost at high", "swing", "variance share"],
                            [[f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                              money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 1)]
                             for r in rows]))
    return "\n\n".join(parts)


def tornado_full(tor):
    parts = []
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            rows = tor[lvl][k]
            acc, table = 0.0, []
            for r in rows:
                if r["status"] == "ok":
                    acc += r["share"] if not math.isnan(r["share"]) else 0
                table.append([f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                              money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 2),
                              pct(acc, 1) if r["status"] == "ok" else ""])
            parts.append(f"#### {LEVEL_NAMES[lvl]}, pipeline {k}\n\n"
                         + md_table(["Parameter", "cost at low", "cost at high", "swing", "share", "cumulative"], table))
    return "\n\n".join(parts)


def mc_section(mc, summ, scen, mc_weights, sensitivity):
    n, rej = len(mc["draws"]), mc["rejected"]
    rows = []
    for lvl in ("dft_confirmed_stable", "experimentally_validated"):
        for k in an.PIPELINES:
            q = summ[lvl][k]
            rows.append([SHORT[lvl], k, money(q[5]), money(q[50]), money(q[95])]
                        + [money(scen[s]["costs"][lvl][k]) for s in WORLDVIEW])
    lvl3 = []
    for k in an.PIPELINES:
        q = summ["validated_new"][k]
        lvl3.append(["L3", k, money(q[5]), money(q[50]), money(q[95])]
                    + [money(scen[s]["costs"]["validated_new"][k]) for s in WORLDVIEW])
    recipes = ", ".join(f"{WORLDVIEW[s]} {scen[s]['recipes']:.2f}" for s in WORLDVIEW)
    by_wv = {}
    for d in mc["draws"]:
        by_wv.setdefault(d["worldview"], []).append(d["costs"]["experimentally_validated"]["B"])
    wv_rows = [[WORLDVIEW[w], len(by_wv[w]), money(an.percentile(by_wv[w], 50)),
                money(an.percentile(by_wv[w], 5)), money(an.percentile(by_wv[w], 95))] for w in WORLDVIEW]
    return (f"{n:,} draws (seed {MC_SEED}); {rej:,} draws rejected and redrawn because their inputs contradicted "
            f"each other (MLIP purity below prevalence × recall), {pct(rej / (n + rej), 1)} of all draws. Rejection "
            "enforces the recall–purity constraint from the correlations block; it trims draws where a high recall "
            "meets a low MatterGen purity, so the accepted draws lean slightly towards lower recall for C.\n\n"
            + md_table(["Level", "Pipeline", "MC 5th pct", "MC median", "MC 95th pct", *WORLDVIEW.values()], rows)
            + f"\n\nScenario columns: each named reading with every other parameter at base, recipes from the budget "
              f"model ({recipes} recipes per target). Base case (stage 1) uses A-Lab's observed 6.19.\n\n"
            + "Level 3, shown only for completeness and never as a headline. Its Monte Carlo spread is dominated by "
              "the prior on a 0-of-36 count:\n\n"
            + md_table(["Level", "Pipeline", "MC 5th pct", "MC median", "MC 95th pct", *WORLDVIEW.values()], lvl3)
            + "\n\nLevel 2, pipeline B, by worldview (the mixture is the main source of level-2 spread):\n\n"
            + md_table(["Worldview", "draws", "median", "5th pct", "95th pct"], wv_rows)
            + f"\n\n**The upper tail is an assumption, not a measurement.** The level-2 95th percentile "
              f"({money(summ['experimentally_validated']['B'][95])} for B) exists because the Leeman reading gets "
              "weight one third. It is a statement about whose re-analysis to believe. With the Leeman reading at "
              f"weight zero it falls to {money(an.reweighted(mc, {'optimistic_alab': 0.5, 'middle_prein': 0.5, 'pessimistic_leeman': 0.0}, mc_weights, 'experimentally_validated', 'B', 95))}.\n\n"
            + "**How the mixture moves with the weights** (level 2, pipeline B; same draws, importance-reweighted):\n\n"
            + md_table(["Weights: A-Lab / Prein / Leeman", "median", "95th percentile"],
                       [[" / ".join(f"{w[n]:.2f}" for n in WORLDVIEW),
                         money(an.reweighted(mc, w, mc_weights, "experimentally_validated", "B", 50)),
                         money(an.reweighted(mc, w, mc_weights, "experimentally_validated", "B", 95))]
                        for w in [mc_weights] + sensitivity]))


def kill_section(kill):
    rows = []
    for lvl in an.LEVELS:
        k = kill[lvl]
        rows.append([SHORT[lvl], pct(k["p_lt"][("B", "A")], 1), pct(k["p_lt"][("C", "B")], 1),
                     pct(k["p_lt"][("C", "A")], 1), pct(k["overlap"][("B", "A")]), pct(k["overlap"][("C", "B")]),
                     pct(k["p_material"][("B", "A")]), pct(k["p_material"][("C", "B")])])
    def verdict_for(lvl):
        k = kill[lvl]
        bits = []
        for x, y in (("B", "A"), ("C", "B")):
            p_lt = k["p_lt"][(x, y)]
            ordered = p_lt >= ORDER_SURVIVES or p_lt <= 1 - ORDER_SURVIVES
            material = k["p_material"][(x, y)] >= MATERIAL_MAJORITY
            cheaper, dearer = (x, y) if p_lt >= 0.5 else (y, x)
            if ordered and material:
                state = f"**separates**: {cheaper} is cheaper than {dearer} in {pct(max(p_lt, 1 - p_lt), 1)} of draws and they differ by more than {MATERIAL:.0%} in {pct(k['p_material'][(x, y)])}"
            elif ordered:
                state = f"**ordered but immaterial**: {cheaper} is cheaper in {pct(max(p_lt, 1 - p_lt), 1)} of draws, but they differ by more than {MATERIAL:.0%} in only {pct(k['p_material'][(x, y)])}"
            else:
                state = f"**no ordering survives**: {x} is cheaper than {y} in {pct(p_lt, 1)} of draws"
            bits.append(f"{x} vs {y} {state}")
        return "; ".join(bits)

    l1, l2 = kill["dft_confirmed_stable"], kill["experimentally_validated"]
    verdict = (
        f"**Verdict** (an ordering survives if it holds in at least {ORDER_SURVIVES:.0%} of paired draws; it is "
        f"material if the two differ by more than {MATERIAL:.0%} in at least {MATERIAL_MAJORITY:.0%} of draws).\n\n"
        f"- Level 1: {verdict_for('dft_confirmed_stable')}.\n"
        f"- Level 2: {verdict_for('experimentally_validated')}.\n"
        f"- Level 3: {verdict_for('validated_new')}.\n\n"
        "The expectation going in (level 1 separates, level 2 does not) is confirmed in a specific sense. At level 2 the "
        "ordering B < A still holds draw by draw, because the synthesis term is shared and the compute term is "
        "not, but the difference is immaterial. **The marginal distributions overlap heavily at every level, "
        f"level 1 included (B–A overlap {pct(l1['overlap'][('B', 'A')])}).** The absolute cost is dominated by "
        "uncertainty that all pipelines share: the 3–1,000 core-h DFT span at level 1, and the synthesis worldview "
        "at level 2. So the pipelines cannot be told apart by comparing their absolute cost ranges. Only the "
        "paired comparison, the same world under each pipeline, separates them, and only at level 1.")
    return (md_table(["Level", "P(B < A)", "P(C < B)", "P(C < A)", "overlap B–A", "overlap C–B",
                      f"P(B, A differ > {MATERIAL:.0%})", f"P(C, B differ > {MATERIAL:.0%})"], rows)
            + "\n\nP(x < y) is paired: both pipelines see the same drawn world. Overlap is the overlap coefficient of "
              "the two marginal cost distributions (histogram on log cost), 100% = identical.\n\n" + verdict)


def returns_section(p, mc_ret):
    base = an.log_elasticities(p)
    groups = {n: lv["group"] for n, lv in an.levers().items()}
    synth = [n for n in groups if groups[n] == "synthesis"]
    comp = [n for n in groups if groups[n] == "compute"]
    rows = []
    for name in synth + comp:
        rows.append([("tied, synthesis" if name in synth else "compute"), name,
                     *(f"{base[name][k]['return'] + 0.0:.3f}" for k in an.PIPELINES),
                     *(f"{mc_ret[name][k]['median']:.3f} ({mc_ret[name][k]['p5']:.3f}–{mc_ret[name][k]['p95']:.3f})"
                       for k in an.PIPELINES)])
    synth_min = {k: min(base[n][k]["return"] for n in synth) for k in an.PIPELINES}
    comp_max = {k: max(base[n][k]["return"] for n in comp) for k in an.PIPELINES}
    ratio = {k: synth_min[k] / comp_max[k] for k in an.PIPELINES}
    mc_ratio = {k: min(mc_ret[n][k]["median"] for n in synth) / max(mc_ret[n][k]["median"] for n in comp)
                for k in an.PIPELINES}
    return ("Return = % fall in cost per validated material per 1% PROPORTIONAL improvement in the lever: the log-elasticity "
            "d ln(cost) / d ln(lever) at the evaluation point, signed so that a positive number means the improvement "
            "lowers cost. It is scale-free, so levers in different units compare directly.\n\n"
            + md_table(["Group", "Lever", "A base", "B base", "C base", "A MC median (5–95%)", "B MC median (5–95%)",
                        "C MC median (5–95%)"], rows)
            + "\n\n**The synthesis levers are tied at unit elasticity; they are not ranked.** Level-2 synthesis cost is "
              "recipes × cost per attempt / success, so each of the three has elasticity one by "
              "construction. Success is exactly 1 because it also divides the compute term. Recipes and cost per "
              "attempt equal the synthesis share of level-2 cost ("
            + ", ".join(f"{base['recipes per target'][k]['return']:.3f} for {k}" for k in an.PIPELINES)
            + "). The gap between them is the compute share, not a difference in leverage. `tests/test_stage2.py` "
              "asserts this structure.\n\n"
            + "**The finding is the magnitude gap.** A 1% improvement on the synthesis side lowers cost per validated "
              "material by at least "
            + ", ".join(f"{synth_min[k]:.2f}% ({k})" for k in an.PIPELINES)
            + ". The best computational lever lowers it by at most "
            + ", ".join(f"{comp_max[k]:.3f}% ({k})" for k in an.PIPELINES)
            + ". That is a ratio of "
            + ", ".join(f"{ratio[k]:.0f}× ({k})" for k in an.PIPELINES)
            + " at the base point, and "
            + ", ".join(f"{mc_ratio[k]:.0f}× ({k})" for k in an.PIPELINES)
            + f" at the Monte Carlo medians. Proportionally, synthesis is worth "
              f"{min(min(ratio.values()), min(mc_ratio.values())):.0f}–{max(max(ratio.values()), max(mc_ratio.values())):.0f} "
              "times compute, depending on the pipeline and the evaluation point.")


def spot_section(doc, p, mc_ret):
    sp = an.spot_switch(doc, p)
    base = sp["change"]
    under = all(abs(base[k]) < 0.01 for k in an.PIPELINES)
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    size = ("by less than one percent" if under else
            f"by {min(abs(v) for v in base.values()):.1%}–{max(abs(v) for v in base.values()):.1%}")
    return (f"**The only free lever moves cost per validated material {size}.** Switching compute from "
            f"on-demand to spot prices is available today at no research cost: {sp['cpu_discount']:.0%} off CPU and "
            f"{sp['gpu_discount']:.0%} off A100 time. It changes level-2 cost per validated material by "
            + ", ".join(f"{base[k]:+.2%} ({k})" for k in an.PIPELINES)
            + " at the base point, with Monte Carlo medians of "
            + ", ".join(f"{mc_ret['spot'][k]['median']:+.2%} ({k})" for k in an.PIPELINES)
            + f". So the only lever whose cost is known (zero) moves the result {size}"
              + ("" if under else f" (under one percent only for {', '.join(k for k in an.PIPELINES if abs(base[k]) < 0.01)})")
              + f". The levers worth {r_lo:.0f}–{r_hi:.0f} times more per percentage point are synthesis success, recipes per target and "
              "cost per attempt, and improving any of them requires synthesis research whose cost nobody has measured.")


def compute_ratio_range(p, mc_ret):
    """Range of (weakest synthesis lever) / (strongest compute lever) over pipelines, at base and MC medians."""
    base = an.log_elasticities(p)
    groups = {n: lv["group"] for n, lv in an.levers().items()}
    synth = [n for n in groups if groups[n] == "synthesis"]
    comp = [n for n in groups if groups[n] == "compute"]
    ratios = []
    for k in an.PIPELINES:
        ratios.append(min(base[n][k]["return"] for n in synth) / max(base[n][k]["return"] for n in comp))
        ratios.append(min(mc_ret[n][k]["median"] for n in synth) / max(mc_ret[n][k]["median"] for n in comp))
    return min(ratios), max(ratios)


def headline_section(doc, p, mc, scen, mc_ret, tor):
    wv = doc["monte_carlo"]["joint"]["worldview"]
    readings = wv["readings"]
    lvl = "experimentally_validated"
    med, rows = {}, []
    for name, rd in readings.items():
        draws = [d for d in mc["draws"] if d["worldview"] == name]
        med[name] = {k: an.percentile([d["costs"][lvl][k] for d in draws], 50) for k in an.PIPELINES}
        cells = []
        for k in an.PIPELINES:
            xs = [d["costs"][lvl][k] for d in draws]
            cells.append(f"**{money(med[name][k])}** ({money(an.percentile(xs, 5))}–{money(an.percentile(xs, 95))})")
        rows.append([WORLDVIEW[name], rd["source"], rd["standing"],
                     f"{rd['success']['k']} of {rd['success']['n']}", *cells])
    lo_name, mid_name, hi_name = "optimistic_alab", "middle_prein", "pessimistic_leeman"
    factor = {k: med[hi_name][k] / med[lo_name][k] for k in an.PIPELINES}
    within = {name: max(med[name].values()) / min(med[name].values()) for name in readings}
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    spot = an.spot_switch(doc, p)["change"]
    s_lo, s_hi = min(abs(v) for v in spot.values()), max(abs(v) for v in spot.values())
    b = "B"
    top2 = {k: tor[lvl][k][0] for k in an.PIPELINES}
    top2_name = {r["name"] for r in top2.values()}
    top2_share = min(r["share"] for r in top2.values())
    return (
        "**Headline: cost per experimentally validated material depends on which reading of the synthesis evidence "
        "is right, not on the pipeline.** Each row below is the Monte Carlo conditional on one reading: median, and "
        f"90% interval in brackets ({len(mc['draws']):,} draws in total, about a third per reading).\n\n"
        + md_table(["Reading", "Source", "Standing", "Targets made (success)", "Level 2, A", "Level 2, B", "Level 2, C"], rows)
        + f"\n\nCost per experimentally validated material ranges from about {money(med[lo_name][b])} under A-Lab's own "
          f"reading to about {money(med[hi_name][b])} under Leeman et al.'s (pipeline B), with Prein et al.'s middle "
          f"reading at {money(med[mid_name][b])}. Between the extreme readings that is a factor of "
          + ", ".join(f"{factor[k]:.0f}× ({k})" for k in an.PIPELINES)
          + ". Within any one reading, pipeline choice moves the median by at most "
          + ", ".join(f"{within[n]:.2f}× ({READING_SHORT[n]})" for n in readings)
          + ". The spread is driven by synthesis success, which arrives with each reading together with its "
            "wrong-verdict share and, through the recipe budget, its recipes per target. In the one-at-a-time "
            f"tornado, `{', '.join(sorted(top2_name))}` carries at least {pct(top2_share, 1)} of level-2 variance in "
            "every pipeline.\n\n"
          + f"**The factor of about {statistics.median(factor.values()):.0f} between the extreme readings is not "
            "measurement uncertainty.** A-Lab and Leeman et al. read the same experiment, the A-Lab campaign, "
            "and disagree about what was made. Prein et al. is a separate, smaller campaign that lands between them. "
            "No reanalysis of existing data closes this gap; resolving it requires new synthesis data: independent "
            "campaigns with phase identification that both sides accept.\n\n"
          + f"**No compute-side improvement moves this.** The best compute lever is {r_lo:.0f} to {r_hi:.0f} times "
            "weaker per percentage point than the synthesis levers (marginal returns below). The only free compute "
            f"lever, moving from on-demand to spot prices, changes the result by {s_lo:.1%} to {s_hi:.1%}.\n\n"
          + f"**Where a single number is unavoidable** (an abstract, a title slide), quote the Prein-reading median "
            f"with the spread beside it, never alone: \"about {money(med[mid_name][b])} per validated material "
            f"(range {money(med[lo_name][b])}–{money(med[hi_name][b])} across three readings of the "
            "synthesis evidence)\". The Prein reading is the middle one, not the best-established: it rests on an "
            "arXiv preprint with 16 targets, while the other two readings are peer-reviewed (Nature; PRX Energy).\n\n"
          + "For comparison, the deterministic base case (A-Lab's observed 6.19 recipes per target paired with "
            f"Prein's success) gives {money(an.costs(p)[lvl][b])} for B. It understates, because 6.19 was observed at "
            f"A-Lab's higher success; with consistent recipes ({scen[mid_name]['recipes']:.2f}) the Prein point "
            f"scenario gives {money(scen[mid_name]['costs'][lvl][b])}. An equal-weight mixture of the three readings "
            "is reported under Monte Carlo below. Its median and tail depend on weights nobody has measured, so it is "
            "not a headline."
    )


def breakeven_section(doc, p):
    recs = records(doc)
    fc = an.fixed_cost_payback(doc, p)
    rows, v_num, v_now = [], [], []
    for lvl_name in ("low", "base", "high"):
        q = {**p, "dft_cost_per_candidate": recs["dft.cost_per_candidate"][lvl_name]}
        t = an.attempt_cost_thresholds(q, COMPUTE_SHARE, SPREAD)
        v_num.append(t["attempt_for_compute_share"])
        v_now.append(t["attempt_usd"])
        rows.append([f"{recs['dft.cost_per_candidate'][lvl_name]:g} core-h ({lvl_name})", money(t["attempt_usd"]),
                     *(money(t["attempt_for_compute_share"][k]) for k in an.PIPELINES), money(t["attempt_for_spread"])])
    parity_b = an.purity_for_parity(p, "B")
    parity_a = an.purity_for_parity(p, "A")
    return (
        "**1. Screening scale at which the MLIP filter's fixed cost pays for itself: a non-result.** No such scale "
        "exists: there is no batch size at which the filter fails to pay for itself. B's extra fixed cost over A is "
        f"loading CHGNet once ({recs['mlip.chgnet.model_load_s']['base']:.2f} s, first-hand) plus relaxing the "
        f"reference phases with it ({p['reference_phases']:g} at base; the count is still missing), "
        f"{fc['extra_fixed_core_h']:.2g} core-h in all. The filter saves {fc['saving_core_h_per_candidate']:.1f} core-h "
        f"({money(fc['saving_usd_per_candidate'])}) on every MP-novel candidate, so the first candidate repays it "
        f"{1 / fc['payback_candidates']:,.0f} times over. The informative quantity is the per-candidate saving: any "
        f"other fixed cost X core-h, such as fine-tuning, pays back after X / {fc['saving_core_h_per_candidate']:.1f} "
        "candidates.\n\n"
        f"**2. Synthesis cost per attempt below which compute starts to matter for level 2.** Compute 'matters' here "
        f"means it is at least {COMPUTE_SHARE:.0%} of a pipeline's level-2 cost, or the level-2 spread reaches "
        f"{SPREAD:.2f}×.\n\n"
        + md_table(["DFT cost", "attempt cost now", f"A: compute ≥ {COMPUTE_SHARE:.0%} below",
                    f"B: compute ≥ {COMPUTE_SHARE:.0%} below", f"C: compute ≥ {COMPUTE_SHARE:.0%} below",
                    f"spread ≥ {SPREAD:.2f}× below"], rows)
        + "\n\nAt today's attempt cost, compute is at least " + f"{COMPUTE_SHARE:.0%}" + " of level 2 only where the "
          "threshold in its row exceeds the attempt cost now: " + "; ".join(
              f"{r[0]}: " + (", ".join(k for k, v in zip(an.PIPELINES, r[2:5]) if v_num[i][k] > v_now[i]) or "none")
              for i, r in enumerate(rows))
          + "."
        + f"\n\n**3. MLIP purity at which C becomes competitive.** C matches B at level 1 when CHGNet's purity on "
          f"MatterGen's pool reaches {pct(parity_b['purity'], 1)}, {parity_b['ratio_to_measured']:.1f}× the "
          f"measured {pct(parity_b['measured'], 1)}. Equivalently, enrichment on that pool would need to be "
          f"{parity_b['purity'] / p['gen_frac_stable']:.1f}× instead of {p['gen_filter_purity'] / p['gen_frac_stable']:.2f}×. "
          f"C matches A (no filter, ion-exchange pool) at {pct(parity_a['purity'], 1)}, "
          f"{parity_a['ratio_to_measured']:.1f}× the measured value. Parity at level 1 implies parity at level 2, "
          "because the synthesis term is shared. The purity cannot fall below "
          f"{pct(parity_b['floor'], 2)} (prevalence × recall).")


# ---------------------------------------------------------------- stage-1 blocks (base case, cost basis, DFT span)

FA_VARIANTS = (("`bench`: direct costs only", "bench", False),
               ("`funder`, fees outside the indirect-cost base (**default**)", "funder", False),
               ("`funder`, fees inside the indirect-cost base", "funder", True))


def _l2(res):
    return [res["pipelines"][k]["outputs"]["experimentally_validated"] for k in an.PIPELINES]


def stage1_numbers(doc, p):
    """Every stage-1 number quoted in prose: base case, attempt cost, cost bases, DFT span, multipliers."""
    recs = records(doc)
    res = funnel(p)
    out = {k: res["pipelines"][k]["outputs"] for k in an.PIPELINES}
    att = res["unit_costs"]["synthesis_attempt"]
    l2 = _l2(res)
    bases = []
    for label, cb, fees in FA_VARIANTS:
        r = funnel({**p, "synth_cost_basis": cb, "fa_on_service_fees": fees})
        a = r["unit_costs"]["synthesis_attempt"]
        v = [o["usd_per"] for o in _l2(r)]
        bases.append({"label": label, "attempt": a["usd"], "indirect": a["parts"]["indirect (F&A)"], "l2": v,
                      "spread": max(v) / min(v)})
    span = []
    for lvl in ("low", "base", "high"):
        dft = recs["dft.cost_per_candidate"][lvl]
        r = funnel({**p, "dft_cost_basis": "span", "dft_cost_per_candidate": dft})
        l1 = [r["pipelines"][k]["outputs"]["dft_confirmed_stable"]["usd_per"] for k in an.PIPELINES]
        o2 = _l2(r)
        v2 = [o["usd_per"] for o in o2]
        share = [o["synthesis_usd_per"] / o["usd_per"] for o in o2]
        span.append({"level": lvl, "dft": dft, "l1": l1, "l2": v2, "spread": max(v2) / min(v2),
                     "share_lo": min(share), "share_hi": max(share)})
    mult = {t: an.multiplier_for_level2_spread(p, t) for t in (1.5, 2.0)}
    l1 = {k: out[k]["dft_confirmed_stable"]["usd_per"] for k in an.PIPELINES}
    return {"out": out, "att": att, "l2": l2, "bases": bases, "span": span, "mult": mult, "l1": l1,
            "rate": p["synth_indirect_rate"], "rate_rec": recs["synth.indirect_rate"]}


def basecase_section(s1):
    out = s1["out"]
    rows = [["1. per DFT-confirmed stable material", *(money(out[k]["dft_confirmed_stable"]["usd_per"]) for k in an.PIPELINES)],
            ["2. per experimentally validated material", *(money(o["usd_per"]) for o in s1["l2"])],
            ["of which compute", *(money(o["compute_usd_per"]) for o in s1["l2"])],
            ["of which synthesis", *(money(o["synthesis_usd_per"]) for o in s1["l2"])]]
    return md_table(["Output", "A: DFT only", "B: CHGNet → DFT", "C: MatterGen → CHGNet → DFT"], rows)


def costbasis_section(s1):
    rows = [[b["label"], money(b["attempt"]), money(b["indirect"]), " / ".join(money(v) for v in b["l2"]),
             f"{b['spread']:.2f}×"] for b in s1["bases"]]
    lo, hi = s1["bases"][0]["l2"][0], s1["bases"][2]["l2"][0]
    return (md_table(["Basis", "$ per attempt", "of which indirect cost", "Level 2: A / B / C", "Spread"], rows)
            + f"\n\nBetween `bench` and fees-inside-base the choice moves level 2 by {hi / lo - 1:.0%} "
              f"({money(lo)} against {money(hi)} for A), but not the spread.")


def dftspan_section(s1):
    names = {"low": "(our measurement)", "base": "(geometric midpoint)", "high": "(MP 2012, upper)"}
    rows = [[f"{r['dft']:g} {names[r['level']]}", " / ".join(money(v) for v in r["l1"]),
             " / ".join(money(v) for v in r["l2"]), f"{r['spread']:.2f}×",
             (f"{r['share_lo']:.0%}" if round(r['share_lo'], 2) == round(r['share_hi'], 2)
              else f"{r['share_lo']:.0%}–{r['share_hi']:.0%}")] for r in s1["span"]]
    return md_table(["DFT core-h per candidate", "Level 1: A / B / C", "Level 2: A / B / C", "Level 2 spread",
                     "Synthesis share of level 2"], rows)


def attempt_section(s1):
    parts = s1["att"]["parts"]
    rr = s1["rate_rec"]
    return (f"A-Lab tried about six recipes per target (353 for 57), so each target is charged six attempts, and "
            f"targets that fail still pay for all their attempts. At base an attempt costs {money(s1['att']['usd'])}. "
            f"XRD ({money(parts['xrd'])}) and furnace ({money(parts['furnace'])}) are the largest items, then labour "
            f"({money(parts['labour'])}), tuition ({money(parts['tuition'])}) and indirect cost "
            f"({money(parts['indirect (F&A)'])}, at the {rr['base']:.0%} effective indirect cost recovery rate). "
            f"Precursors are {money(parts['precursors'])}.")


def level3_section(s1):
    v = [s1["out"][k]["validated_new"]["usd_per"] for k in an.PIPELINES]
    return (f"At base, the lower bounds are about {money(round(statistics.median(v), -3))} for each of A, B and C ("
            + ", ".join(f"{k} ≥ {money(x)}" for k, x in zip(an.PIPELINES, v)) + ").")


def multiplier_section(s1, p):
    rows = []
    for t, r in s1["mult"].items():
        rows.append([f"{t:g}×", f"{r['multiplier']:.2f}", pct(r["filtered_success"]),
                     pct(p["synth_success_unconditional"])])
    r2 = s1["mult"][2.0]
    return (md_table(["Level-2 spread", "Multiplier needed", "Success in B and C", "Success in A"], rows)
            + f"\n\nFor pipeline choice to double the cost per validated material, an MLIP pre-filter would have to "
              f"roughly double synthesis success, from {pct(p['synth_success_unconditional'])} to "
              f"{pct(r2['filtered_success'])}.")


def key_numbers(doc, p, s1, mc, summ, scen, kill, mc_ret, tor):
    """Formatted numbers the paper draft quotes, written to results/key_numbers.json (the draft's single source)."""
    P = an.PIPELINES
    l1, l2 = s1["l1"], [o["usd_per"] for o in s1["l2"]]
    k = {}
    for i, x in enumerate(P):
        k[f"l1_{x}"] = money(l1[x])
        k[f"l2_{x}"] = money(l2[i])
        k[f"l2_compute_{x}"] = money(s1["l2"][i]["compute_usd_per"])
        k[f"l2_synthesis_{x}"] = money(s1["l2"][i]["synthesis_usd_per"])
        k[f"l3_{x}"] = money(s1["out"][x]["validated_new"]["usd_per"])
    k["l1_ratio_A_B"] = f"{l1['A'] / l1['B']:.2f}"
    k["l1_B_cheaper_pct"] = f"{1 - l1['B'] / l1['A']:.0%}"
    k["l1_ratio_C_B"] = f"{l1['C'] / l1['B']:.1f}"
    base_span = s1["span"][1]
    k["l2_spread_base"] = f"{base_span['spread']:.2f}"
    k["l2_spread_base_pct"] = f"{base_span['spread'] - 1:.0%}"
    k["l2_spread_high"] = f"{s1['span'][2]['spread']:.2f}"
    for r in s1["span"]:
        n = r["level"]
        k[f"span_{n}_l1"] = " / ".join(money(v) for v in r["l1"])
        k[f"span_{n}_l2"] = " / ".join(money(v) for v in r["l2"])
        k[f"span_{n}_spread"] = f"{r['spread']:.2f}"
        k[f"span_{n}_share"] = (f"{r['share_lo']:.0%}" if round(r['share_lo'], 2) == round(r['share_hi'], 2)
                                else f"{r['share_lo']:.0%}–{r['share_hi']:.0%}")
    comp_share = [o["compute_usd_per"] / o["usd_per"] for o in s1["l2"]]
    for r in s1["span"]:
        for i, x in enumerate(P):
            k[f"span_{r['level']}_l1_{x}"] = money(r["l1"][i])
            k[f"span_{r['level']}_l2_{x}"] = money(r["l2"][i])
        k[f"span_{r['level']}_share_lo"] = f"{r['share_lo']:.0%}"
        k[f"span_{r['level']}_share_hi"] = f"{r['share_hi']:.0%}"
    k["compute_share_lo"], k["compute_share_hi"] = f"{min(comp_share):.0%}", f"{max(comp_share):.0%}"
    k["synthesis_share_base"] = k["span_base_share"]
    parts = s1["att"]["parts"]
    k["attempt"] = money(s1["att"]["usd"])
    for name in ("xrd", "furnace", "labour", "tuition", "precursors"):
        k[f"attempt_{name}"] = money(parts[name])
    k["attempt_indirect"] = money(parts["indirect (F&A)"])
    k["indirect_rate"] = f"{s1['rate']:.0%}"
    for b, tag in zip(s1["bases"], ("bench", "funder", "funder_fees_in")):
        k[f"basis_{tag}_attempt"] = money(b["attempt"])
        k[f"basis_{tag}_l2"] = " / ".join(money(v) for v in b["l2"])
    for b, tag in zip(s1["bases"], ("bench", "funder", "funder_fees_in")):
        for i, x in enumerate(P):
            k[f"basis_{tag}_l2_{x}"] = money(b["l2"][i])
    for name in ("xrd", "furnace", "labour", "tuition"):
        k[f"attempt_{name}_r"] = f"${parts[name]:,.0f}"
    k["attempt_indirect_r"] = f"${parts['indirect (F&A)']:,.0f}"
    rr = s1["rate_rec"]
    k["indirect_rate_high"], k["indirect_rate_low"] = f"{rr['high']:.0%}", f"{rr['low']:.0%}"
    # Three distinct variants. These were conflated before 2026-10-11: "at_negotiated" used the
    # record's high value, which the same repair had changed from 0.58 to 0.45, so a row labelled
    # 58% was reporting 45%. They are now computed and named separately.
    hi = funnel({**p, "synth_indirect_rate": rr["high"]})           # 45%, top of the EFFECTIVE range
    neg = funnel({**p, "synth_indirect_rate": 0.58})                # 58%, the NEGOTIATED average
    mtdc = funnel({**p, "indirect_base": "mtdc"})                   # 42% on the narrowed base
    for tag, run in (("high_effective", hi), ("negotiated", neg), ("mtdc", mtdc)):
        ll = [o["usd_per"] for o in _l2(run)]
        k[f"attempt_at_{tag}"] = money(run["unit_costs"]["synthesis_attempt"]["usd"])
        k[f"l2_B_at_{tag}"] = money(ll[1])
        k[f"{tag}_l2_rise_pct"] = f"{ll[1] / l2[1] - 1:.0%}"
        for i, x in enumerate(P):
            k[f"l2_{x}_at_{tag}"] = money(ll[i])
    k["basis_move_pct"] = f"{s1['bases'][2]['l2'][0] / s1['bases'][0]['l2'][0] - 1:.0%}"
    # Monte Carlo and readings
    lvl = "experimentally_validated"
    med = {}
    for name in WORLDVIEW:
        xs = {x: [d["costs"][lvl][x] for d in mc["draws"] if d["worldview"] == name] for x in P}
        med[name] = {x: an.percentile(xs[x], 50) for x in P}
        k[f"reading_{name}_B"] = money(med[name]["B"])
        k[f"reading_{name}_B_interval"] = f"{money(an.percentile(xs['B'], 5))}–{money(an.percentile(xs['B'], 95))}"
    factor = {x: med["pessimistic_leeman"][x] / med["optimistic_alab"][x] for x in P}
    k["reading_factor_B"] = f"{factor['B']:.0f}"
    k["reading_factor_median"] = f"{statistics.median(factor.values()):.0f}"
    k["within_reading_max"] = f"{max(max(m.values()) / min(m.values()) for m in med.values()):.2f}"
    for lv, tag in (("dft_confirmed_stable", "l1"), ("experimentally_validated", "l2"), ("validated_new", "l3")):
        kk = kill[lv]
        k[f"kill_{tag}_p_B_lt_A"] = pct(kk["p_lt"][("B", "A")], 1)
        k[f"kill_{tag}_material_BA"] = pct(kk["p_material"][("B", "A")])
        k[f"kill_{tag}_overlap_BA"] = pct(kk["overlap"][("B", "A")])
    k["mc_draws"] = f"{len(mc['draws']):,}"
    k["mc_l2_B_p95"] = money(summ[lvl]["B"][95])
    k["mc_l2_B_p95_thousands"] = f"${summ[lvl]['B'][95] / 1000:,.0f},000"
    w = doc["monte_carlo"]["joint"]["worldview"]["weights"]
    k["mc_l2_B_p95_no_leeman"] = money(an.reweighted(
        mc, {"optimistic_alab": 0.5, "middle_prein": 0.5, "pessimistic_leeman": 0.0}, w, lvl, "B", 95))
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    k["returns_ratio_lo"], k["returns_ratio_hi"] = f"{r_lo:.0f}", f"{r_hi:.0f}"
    base_el = an.log_elasticities(p)
    for x in P:
        k[f"el_recipes_{x}"] = f"{base_el['recipes per target'][x]['return']:.3f}"
        k[f"el_attempt_{x}"] = f"{base_el['cost per synthesis attempt'][x]['return']:.3f}"
        k[f"el_success_{x}"] = f"{base_el['synthesis success rate'][x]['return']:.3f}"
        comp = max(base_el[n][x]["return"] for n, lv_ in an.levers().items() if lv_["group"] == "compute")
        k[f"el_compute_{x}"] = f"{comp:.3f}"
    sp = an.spot_switch(doc, p)
    k["spot_lo"] = f"{min(abs(v) for v in sp['change'].values()):.1%}"
    k["spot_hi"] = f"{max(abs(v) for v in sp['change'].values()):.1%}"
    k["spot_cpu_discount"] = f"{sp['cpu_discount']:.0%}"
    t1 = tor["dft_confirmed_stable"]["B"][0]
    t2 = tor[lvl]["B"][0]
    k["tornado_l1_share"], k["tornado_l2_share"] = pct(t1["share"], 1), pct(t2["share"], 1)
    fc = an.fixed_cost_payback(doc, p)
    k["fixed_extra_core_h"] = f"{fc['extra_fixed_core_h']:.2g}"
    k["fixed_saving_core_h"] = f"{fc['saving_core_h_per_candidate']:.1f}"
    t = an.attempt_cost_thresholds(p, COMPUTE_SHARE, SPREAD)
    k["threshold_lo"] = money(min(t["attempt_for_compute_share"].values()))
    k["threshold_hi"] = money(max(t["attempt_for_compute_share"].values()))
    par = an.purity_for_parity(p, "B")
    k["parity_purity"], k["parity_ratio"] = pct(par["purity"], 1), f"{par['ratio_to_measured']:.1f}"
    k["mult_2x_success_from"] = pct(p["synth_success_unconditional"])
    k["mult_2x_success_to"] = pct(s1["mult"][2.0]["filtered_success"])
    return k


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- generated:{name}:begin -->\n).*?(<!-- generated:{name}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"README has no generated:{name} block")
    return pattern.sub(lambda m: m.group(1) + body.strip() + "\n" + m.group(2), text)


MC_SEED = None


def main():
    global MC_SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int)
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()

    doc = load()
    p = resolve(doc)
    MC_SEED = doc["monte_carlo"]["seed"]
    tor = an.tornado(doc)
    mc = an.monte_carlo(doc, n=args.draws)
    summ = an.summarise(mc)
    scen = an.scenarios(doc)
    kill = an.kill_condition(mc, material=MATERIAL)
    mc_ret = an.returns_summary(mc)

    sections = {
        "headline": headline_section(doc, p, mc, scen, mc_ret, tor),
        "spot": spot_section(doc, p, mc_ret),
        "daf": daf_section(doc, p),
        "tornado": tornado_section(tor),
        "distributions": distributions_section(doc),
        "montecarlo": mc_section(mc, summ, scen, doc["monte_carlo"]["joint"]["worldview"]["weights"],
                                 doc["monte_carlo"]["joint"]["worldview"]["weight_sensitivity"]),
        "kill": kill_section(kill),
        "returns": returns_section(p, mc_ret),
        "breakevens": breakeven_section(doc, p),
    }
    s1 = stage1_numbers(doc, p)
    sections.update({
        "basecase": basecase_section(s1),
        "costbasis": costbasis_section(s1),
        "dftspan": dftspan_section(s1),
        "attempt": attempt_section(s1),
        "level3": level3_section(s1),
        "multiplier": multiplier_section(s1, p),
    })

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    report = ["# Stage 2 results", "", "Generated by `scripts/stage2.py` from `params/parameters.yaml` and `data/`.", ""]
    for title, key in (("Headline figures", "headline"), ("The only free lever", "spot"),
                       ("Discovery acceleration factor", "daf"), ("Marginal returns", "returns"),
                       ("Kill-condition check", "kill"), ("Monte Carlo and named scenarios", "montecarlo"),
                       ("Distributions", "distributions"), ("Break-evens", "breakevens"),
                       ("Tornado (summary)", "tornado")):
        report += [f"## {title}", "", sections[key], ""]
    report += ["## Tornado (full)", "", tornado_full(tor), ""]
    (out_dir / "stage2.md").write_text("\n".join(report))
    keys = key_numbers(doc, p, s1, mc, summ, scen, kill, mc_ret, tor)
    (out_dir / "key_numbers.json").write_text(json.dumps(keys, indent=1, ensure_ascii=False) + "\n")

    with open(out_dir / "tornado.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["level", "pipeline", "parameter", "cost_at_low", "cost_at_high", "swing", "variance_share", "status"])
        for lvl in an.LEVELS:
            for k in an.PIPELINES:
                for r in tor[lvl][k]:
                    w.writerow([lvl, k, r["name"], r["low_cost"], r["high_cost"], r["swing"], r["share"], r["status"]])
    # Per-draw output is large and regenerable (same seed), so it is git-ignored; the summary is committed.
    with open(out_dir / "monte_carlo_draws.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "worldview", "dft_core_h", *(f"{SHORT[l]}_{k}" for l in an.LEVELS for k in an.PIPELINES)])
        for i, d in enumerate(mc["draws"]):
            w.writerow([i, d["worldview"], d["dft_cost"], *(d["costs"][l][k] for l in an.LEVELS for k in an.PIPELINES)])
    qs = (5, 25, 50, 75, 95)
    with open(out_dir / "monte_carlo_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# seed", MC_SEED, "draws", len(mc["draws"]), "rejected", mc["rejected"],
                    "regenerate", "uv run python scripts/stage2.py"])
        w.writerow(["worldview", "level", "pipeline", "n", *(f"p{q}" for q in qs), "mean"])
        groups = {"all (equal weights)": mc["draws"]}
        for name in WORLDVIEW:
            groups[name] = [d for d in mc["draws"] if d["worldview"] == name]
        for g, ds in groups.items():
            for lvl in an.LEVELS:
                for k in an.PIPELINES:
                    xs = [d["costs"][lvl][k] for d in ds]
                    w.writerow([g, lvl, k, len(xs), *(an.percentile(xs, q) for q in qs), sum(xs) / len(xs)])

    if not args.no_readme:
        readme = ROOT / "README.md"
        text = readme.read_text()
        for key, body in sections.items():
            text = replace_block(text, key, body)
        readme.write_text(text)

    print("\n\n".join(f"== {k}\n{v}" for k, v in sections.items()))


if __name__ == "__main__":
    main()
