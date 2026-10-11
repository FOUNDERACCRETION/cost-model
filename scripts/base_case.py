"""Print the stage-by-stage base case for pipelines A, B and C.

Run: uv run python scripts/base_case.py [--price spot] [--dft first_hand] [--filter matbench --mlip mace-mp-0]
                                        [--generator ion_exchange]
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis import multiplier_for_level2_spread  # noqa: E402
from src.funnel import funnel  # noqa: E402
from src.params import load, records, resolve  # noqa: E402


def money(x: float) -> str:
    if math.isinf(x):
        return "inf"
    return f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"


def num(x: float, digits: int = 2) -> str:
    if math.isinf(x):
        return "inf"
    return f"{x:,.{digits}f}"


def table(headers, rows):
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    line = "  ".join(h.rjust(w) if i else h.ljust(w) for i, (h, w) in enumerate(zip(headers, widths)))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(c).rjust(w) if i else str(c).ljust(w) for i, (c, w) in enumerate(zip(r, widths))))


labels_short = {
    "dft_confirmed_stable": "1. DFT-confirmed stable",
    "experimentally_validated": "2. experimentally validated",
}
LEVEL3_EVIDENCE = (
    "LOWER BOUND ONLY: new-to-science share {share:.4f} is the Wilson 95% upper bound on Leeman et al.'s"
    " 0 of 36; at the observed 0 the cost is unbounded"
)


def bound(x: float) -> str:
    return "unbounded" if math.isinf(x) else ">= " + money(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", choices=["on_demand", "spot"])
    ap.add_argument("--dft", choices=["span", "first_hand"])
    ap.add_argument("--filter", choices=["measured", "matbench"])
    ap.add_argument("--mlip", choices=["chgnet", "mace-mp-0", "m3gnet"])
    ap.add_argument("--generator", choices=["ion_exchange", "mattergen"])
    args = ap.parse_args()
    overrides = {k: v for k, v in {
        "price_basis": args.price, "dft_cost_basis": args.dft, "mlip_model": args.mlip, "generator_c": args.generator,
        "mlip_filter_basis": args.filter,
    }.items() if v}

    doc = load()
    choices = {**doc["choices"], **overrides}
    p = resolve(doc, "base", overrides)
    r = funnel(p)
    u = r["unit_costs"]

    print("BASE CASE (all parameters at base values; params/parameters.yaml)")
    print("Choices: " + ", ".join(f"{k}={v}" for k, v in choices.items()))
    print(f"Prices: ${p['price_per_core_hour']}/core-h, ${p['price_per_gpu_hour']}/A100 GPU-h ({choices['price_basis']})")
    print(f"Batch: {p['n_candidates']:.0f} MP-novel candidates per chemistry, {p['n_atoms']:.0f} atoms per cell")
    print()
    print("Unit costs")
    m = u["mlip"]
    print(f"  MLIP ({choices['mlip_model']}): {m['core_s_per_step']:.3f} core-s/step x {m['expected_steps']:.1f} expected steps"
          f" = {m['core_h']:.5f} core-h per candidate (capped run {m['core_h_capped_run']:.4f})")
    d = u["dft"]
    recs = records(doc)
    span = recs["dft.cost_per_candidate"]
    print(f"  DFT: {d['core_h']:.1f} core-h per candidate [{d['basis']}]. Span {span['low']} (first-hand) to"
          f" {span['high']} (MP 2012, 5 x 200); base = geometric midpoint. First-hand at {p['n_atoms']:.0f} atoms:"
          f" {d['scf_core_s']:.1f} core-s/SCF x {p['dft_scf_per_ionic']} SCF/step x {p['dft_ionic_steps']} steps"
          f" = {d['first_hand_core_h']:.2f}. MP 2012 per calculation: {recs['dft.mp_2012_per_calculation']['base']}")
    s = u["synthesis_attempt"]
    parts = ", ".join(f"{k} {money(v)}" for k, v in s["parts"].items())
    print(f"  Synthesis: {money(s['usd'])} per attempt ({parts});"
          f" x {p['synth_recipes_per_target']:.2f} recipes = {money(u['synthesis_per_target_usd'])} per target")

    for key, pl in r["pipelines"].items():
        print()
        print("=" * 100)
        print(f"PIPELINE {pl['pipeline']}   (pool stable fraction {pl['prevalence']:.3f})")
        print("=" * 100)
        rows = [["fixed: reference hull", "-", "-", "-", num(pl["fixed"]["core_h"], 1), "-", money(pl["fixed"]["usd"]),
                 money(pl["fixed"]["usd"]), "-"]]
        for st in pl["stages"]:
            rows.append([
                st["stage"], num(st["entering"], 1), num(st["surviving"], 2), num(st["pass_rate"], 4),
                num(st["core_h"], 2), num(st["gpu_h"], 3), money(st["usd"]), money(st["cumulative_usd"]),
                money(st["cumulative_usd_per_survivor"]),
            ])
        table(["stage", "entering", "surviving", "pass", "core-h", "GPU-h", "stage $", "cumul. $", "cumul. $/survivor"], rows)
        notes = [f"{st['stage']}: {st['note']}" for st in pl["stages"] if st["note"]]
        for n in notes:
            print(f"  note  {n}")

        print()
        out = pl["outputs"]
        labels = {
            "naive_per_dft_stable_verdict": "(naive) per DFT-stable verdict",
            "dft_confirmed_stable": "1. per DFT-confirmed stable (correct verdict)",
            "experimentally_validated": "2. per experimentally validated",
            "validated_new": "3. per validated NEW material",
        }
        fmt = {k: (bound if o.get("bound") == "lower" else money) for k, o in out.items()}
        table(["output level", "count", "$ per (incl. fixed)", "compute $ per", "synthesis $ per", "$ per (marginal)",
               "compute core-h per"],
              [[labels[k], num(o["count"], 3), fmt[k](o["usd_per"]), fmt[k](o["compute_usd_per"]),
                fmt[k](o["synthesis_usd_per"]), fmt[k](o["marginal_usd_per"]), num(o["core_h_per"], 1)]
               for k, o in out.items()])
        print("  level 3: " + LEVEL3_EVIDENCE.format(share=p["novelty_science_frac"]))
        lr = pl["label_reliability"]
        print(f"  label reliability: {lr['wrong_verdicts']:.2f} of {lr['dft_stable_verdicts']:.2f} verdicts wrong ->"
              f" {lr['dft_core_h_on_wrong_verdicts']:,.0f} DFT core-h ({money(lr['dft_usd_on_wrong_verdicts'])}) and"
              f" {lr['synthesis_attempts_on_wrong_verdicts']:.1f} synthesis attempts ({money(lr['synthesis_usd_on_wrong_verdicts'])}) yield nothing")
        if pl["mlip"]:
            ml = pl["mlip"]
            print(f"  MLIP non-convergence: {ml['nonconverged_candidates']:.1f} candidates hit the cap,"
                  f" {ml['nonconverged_core_h']:.3f} core-h spent for no output")
            print(f"  synthesis success used: {pl['synthesis_success']:.4f}"
                  f" (multiplier for filtered pipelines {p['synth_success_multiplier_filtered']})")
        comp = pl["marginal"]
        share = comp["synthesis_usd"] / (comp["synthesis_usd"] + comp["compute_usd"] + pl["fixed"]["usd"])
        print(f"  spend: compute {money(comp['compute_usd'])} + synthesis {money(comp['synthesis_usd'])}"
              f" + fixed {money(pl['fixed']['usd'])}; synthesis share {share:.0%}")

    print()
    print("SUMMARY: $ per output (incl. fixed); levels 1 and 2 only")
    rows = []
    for k in labels_short:
        vals = [r["pipelines"][x]["outputs"][k]["usd_per"] for x in "ABC"]
        rows.append([labels_short[k], *(money(v) for v in vals), f"{max(vals) / min(vals):.2f}x"])
    table(["level", "A", "B", "C", "max/min"], rows)
    lvl2 = [r["pipelines"][x]["outputs"]["experimentally_validated"] for x in "ABC"]
    print(f"  level 2 = compute ({', '.join(money(o['compute_usd_per']) for o in lvl2)})"
          f" + synthesis ({', '.join(money(o['synthesis_usd_per']) for o in lvl2)})")
    lvl3 = [r["pipelines"][x]["outputs"]["validated_new"]["usd_per"] for x in "ABC"]
    print(f"  level 3 (not a headline): A {bound(lvl3[0])}, B {bound(lvl3[1])}, C {bound(lvl3[2])}."
          f" {LEVEL3_EVIDENCE.format(share=p['novelty_science_frac'])}.")

    def level(q: dict, key: str, lvl: str) -> float:
        return funnel(q)["pipelines"][key]["outputs"][lvl]["usd_per"]

    print()
    print("FINDING (a): MLIP pre-filter benefit at level 1 (A / B), measured purity vs Matbench-derived rates")
    for basis in ("measured", "matbench"):
        q = {**p, "mlip_filter_basis": basis}
        a_, b_ = level(q, "A", "dft_confirmed_stable"), level(q, "B", "dft_confirmed_stable")
        print(f"  {basis:9s}: A {money(a_)} / B {money(b_)} = {a_ / b_:.2f}x (B is {1 - b_ / a_:.0%} cheaper)")

    print()
    print("FINDING (b): generative pool vs ion exchange at level 1 (C / B), sensitivity to filter purity")
    ion = recs["gen.ion_exchange.frac_stable_after_chgnet_filter"]
    mg = recs["gen.mattergen.frac_stable_after_chgnet_filter"]
    rows = []
    for ion_lvl in ("low", "base", "high"):
        row = [f"ion exchange purity {ion[ion_lvl]}"]
        for mg_lvl in ("low", "base", "high"):
            q = {**p, "pool_filter_purity": ion[ion_lvl], "gen_filter_purity": mg[mg_lvl]}
            try:
                row.append(f"{level(q, 'C', 'dft_confirmed_stable') / level(q, 'B', 'dft_confirmed_stable'):.2f}x")
            except ValueError:  # purity below prevalence x recall: pass fraction would exceed 1
                row.append("inconsistent")
        rows.append(row)
    table(["C / B at level 1", *(f"MatterGen {mg[l]} ({l})" for l in ("low", "base", "high"))], rows)
    gen_share = r["pipelines"]["C"]["stages"][0]["usd"] / r["pipelines"]["C"]["marginal"]["compute_usd"]
    print(f"  generation is {gen_share:.1%} of C's compute spend; MatterGen purity is read from a figure"
          f" (grade {mg['evidence_grade']})")

    print()
    print("COST BASIS: synthesis attempt and level 2 (F&A choices)")
    rows = []
    for label, cb, fees in (("bench (no F&A)", "bench", False), ("funder, fees outside F&A base [default]", "funder", False),
                            ("funder, fees inside F&A base", "funder", True)):
        q = {**p, "synth_cost_basis": cb, "fa_on_service_fees": fees}
        res = funnel(q)
        att = res["unit_costs"]["synthesis_attempt"]
        l2 = [res["pipelines"][x]["outputs"]["experimentally_validated"]["usd_per"] for x in "ABC"]
        rows.append([label, money(att["usd"]), money(att["parts"]["indirect (F&A)"]), *(money(v) for v in l2),
                     f"{max(l2) / min(l2):.2f}x"])
    table(["basis", "$ per attempt", "of which F&A", "L2 A", "L2 B", "L2 C", "L2 spread"], rows)

    print()
    print("DFT SPAN: synthesis still dominates? (level 2 at the span's low, base and high DFT cost)")
    rows = []
    for label in ("low", "base", "high"):
        value = span[label]
        q = {**p, "dft_cost_basis": "span", "dft_cost_per_candidate": value}
        out = {x: pl["outputs"] for x, pl in funnel(q)["pipelines"].items()}
        l1 = [out[x]["dft_confirmed_stable"]["usd_per"] for x in "ABC"]
        l2 = [out[x]["experimentally_validated"] for x in "ABC"]
        synth_share = [o["synthesis_usd_per"] / o["usd_per"] for o in l2]
        rows.append([f"{label}: {value:g} core-h", *(money(v) for v in l1), f"{max(l1) / min(l1):.2f}x",
                     *(money(o["usd_per"]) for o in l2), f"{max(o['usd_per'] for o in l2) / min(o['usd_per'] for o in l2):.2f}x",
                     f"{min(synth_share):.0%}-{max(synth_share):.0%}"])
    table(["DFT cost", "L1 A", "L1 B", "L1 C", "L1 spread", "L2 A", "L2 B", "L2 C", "L2 spread", "synthesis share of L2"],
          rows)

    print()
    print("HEADLINE ASSUMPTION: synthesis success independent of pipeline (multiplier = 1 for B and C)")
    for target in (1.5, 2.0):
        res = multiplier_for_level2_spread(p, target)
        if res["multiplier"] is None:
            print(f"  {target}x level-2 spread: not reachable before filtered success hits 1 (max {res['spread']:.2f}x)")
        else:
            print(f"  {target}x level-2 spread needs multiplier {res['multiplier']:.3f}: filtered pipelines' success"
                  f" {res['filtered_success']:.3f} against A's {p['synth_success_unconditional']:.3f}")

    print()
    print("DISCOVERY ACCELERATION FACTOR (purity / prevalence; no assumption about which classifier rate transfers)")
    from src.analysis import enrichment
    e = enrichment(doc, p)
    print(f"  WBM (Matbench, reported): {e['wbm']['daf_reported']:.2f}x at prevalence {e['wbm']['prevalence']:.3f}")
    for src, label in (("pool", "ion-exchange pool"), ("gen", "MatterGen pool")):
        x = e[src]
        print(f"  {label}: purity {x['purity']:.3f} / prevalence {x['prevalence']:.3f} = {x['daf_measured']:.2f}x"
              f" (Matbench rates at this prevalence would give {x['daf_matbench_rates_at_this_prevalence']:.2f}x)")
    print()
    print("MLIP FILTER CONSISTENCY (purity and recall come from different sources)")
    lo_r, hi_r = recs["mlip.chgnet.recall"]["low"], recs["mlip.chgnet.recall"]["high"]

    def flag(x: float) -> str:
        return "plausible" if lo_r <= x <= hi_r else f"IMPLAUSIBLE (outside {lo_r}-{hi_r})"

    for key in "BC":
        ml = r["pipelines"][key]["mlip"]
        rec_mb = ml["recall_implied_by_purity_and_matbench_fpr"]
        print(f"  {key} ({ml['basis']}): pool stable {r['pipelines'][key]['prevalence']:.3f}, measured purity"
              f" {ml['measured_purity']:.3f} vs Matbench-path precision {ml['matbench_precision_at_prevalence']:.3f}")
        print(f"     recall used {ml['recall_used']:.3f} -> pass fraction {ml['flagged']:.3f}, implied FPR"
              f" {ml['implied_fpr']:.3f} vs Matbench FPR {ml['matbench_fpr']:.3f}")
        print(f"     if Matbench FPR were right, purity implies recall {rec_mb:.3f}: {flag(rec_mb)}")
    v1 = {k: recs[f"gen.ion_exchange.v1_{k}"]["base"] for k in ("filter_acceptance", "frac_stable_strict", "filter_purity")}
    v1_recall = v1["filter_purity"] * v1["filter_acceptance"] / v1["frac_stable_strict"]
    print(f"  S&B v1 (ion exchange, own dataset): purity {v1['filter_purity']} x pass {v1['filter_acceptance']}"
          f" / stable {v1['frac_stable_strict']} = recall {v1_recall:.2f}: {flag(v1_recall)};"
          " v1's figures are not from one population, so recall stays Matbench-based")


if __name__ == "__main__":
    main()
