#!/usr/bin/env python3
"""Write the reconstruction package: parameter manifest and a hand-checkable worksheet.

An external reviewer of revision 12 set this completion test for the paper:

    "Another person can reconstruct the $271 attempt estimate, the experimental-cost equation,
     and the reported threshold crossings without asking you what an input means."

That is what this script produces. Three outputs, all generated from params/parameters.yaml and
the model, so none of them can drift from the figures the paper prints:

  results/parameter_manifest.csv   every parameter: low/base/high, unit, evidence grade, source
                                   URL and the source passage or derivation note behind it.
  results/fee_schedule_manifest.csv  the attempt-cost inputs only, with the usage allocation that
                                   converts each published rate into dollars per attempt, and the
                                   institution each rate comes from.
  results/RECONSTRUCTION.md        a worksheet that walks the three headline numbers from inputs
                                   to result with the arithmetic shown at each line, so a reader
                                   with a calculator reproduces them without running the code.

Run: python scripts/manifest.py
"""
from __future__ import annotations
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):  # a cp1252 or ASCII console must not crash a UTF-8 report
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.funnel import funnel, synthesis_cost_per_attempt  # noqa: E402
from src.params import load, records, resolve  # noqa: E402
from stage2 import (dft_threshold_sweep, synthesis_decision_boundaries,  # noqa: E402
                    threshold_coefficients, upstream_per_target)

# Which records feed the attempt cost, and how each published rate becomes dollars per attempt.
# The allocation column is the part a reader cannot infer from the fee schedule alone, so it is
# stated here rather than left implicit in the code.
FEE_ALLOCATION = {
    "synth.xrd_cost_per_sample": "one sample charged per attempt",
    "synth.furnace_fixed_fee": "one firing per attempt",
    "synth.furnace_hourly": "x furnace_hours_per_attempt",
    "synth.furnace_hours_per_attempt": "hours per firing (allocation input)",
    "synth.labour_annual_salary": "x (1 + fringe) / (weeks_per_year x attempts_per_week)",
    "synth.labour_fringe_rate": "applied to salary (allocation input)",
    "synth.labour_tuition_remission": "/ (weeks_per_year x attempts_per_week)",
    "synth.labour_attempts_per_week": "throughput denominator (allocation input)",
    "synth.weeks_per_year": "throughput denominator (allocation input)",
    "synth.crucible_cost": "/ attempts_per_crucible",
    "synth.attempts_per_crucible": "crucible reuse (allocation input)",
    "synth.precursor_mass_g_per_attempt": "x precursor_usd_per_g",
    "synth.precursor_usd_per_g": "x precursor_mass_g_per_attempt",
    "synth.other_consumables_per_attempt": "charged once per attempt",
    "synth.indirect_rate": "x F&A base (total direct costs including fees and tuition)",
}


def parameter_manifest(doc, out: Path) -> int:
    recs = records(doc)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "low", "base", "high", "unit", "evidence_grade", "distribution",
                    "source_url", "citations", "source_passage_or_derivation"])
        for name in sorted(recs):
            r = recs[name]
            w.writerow([
                name, r.get("low", ""), r.get("base", ""), r.get("high", ""), r.get("unit", ""),
                r.get("evidence_grade", ""), r.get("type", ""), r.get("source_url", ""),
                "; ".join(r.get("citations", []) or []),
                (r.get("source_note", "") or "").replace("\n", " "),
            ])
    return len(recs)


def fee_manifest(doc, out: Path) -> int:
    recs = records(doc)
    rows = []
    for name, alloc in FEE_ALLOCATION.items():
        r = recs.get(name)
        if r is None:
            # This used to `continue`. A key misspelled against the parameter file then vanished
            # from the manifest without a word: `synth.precursor_mass_g` (the record is
            # `synth.precursor_mass_g_per_attempt`) was dropped for several revisions, so a file
            # headed "every input to the $271 attempt estimate" omitted the precursor mass that is
            # half of its own precursors line, and the paper quoted the resulting short count.
            raise KeyError(
                f"FEE_ALLOCATION names {name!r}, which is not a parameter record. The fee "
                f"schedule must list every input to the attempt cost, so a name that resolves "
                f"to nothing is an error rather than a row to skip."
            )
        note = (r.get("source_note", "") or "").replace("\n", " ")
        rows.append([name, r.get("base", ""), r.get("unit", ""), alloc,
                     r.get("evidence_grade", ""), r.get("source_url", ""), note])
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["# every input to the $271 attempt estimate, with its usage allocation"])
        w.writerow(["# 'allocation input' marks a parameter that converts rates into per-attempt "
                    "cost rather than being a priced rate itself"])
        w.writerow(["parameter", "base", "unit", "allocation to one attempt", "evidence_grade",
                    "source_url", "source_passage"])
        w.writerows(rows)
    return len(rows)


def _base_reading(doc: dict, S: float, r: float) -> dict:
    """Which published reading the deterministic base case is following.

    The worksheet has to name the campaign behind S and r, and hard-coding it went stale the day
    the base case changed reading. This finds the reading whose success count and reported recipe
    multiplicity both match the base values, and raises if none does -- a base case that matches no
    reading would itself be the finding.
    """
    readings = doc["monte_carlo"]["joint"]["worldview"]["readings"]
    for name, rd in readings.items():
        spec = rd.get("success") or {}
        if spec.get("type") != "beta_counts":
            continue
        k, n = float(spec["k"]), float(spec["n"])
        if abs(k / n - S) < 5e-6 and abs(float(rd["recipes"]) - r) < 5e-4:
            label = rd.get("source", name).split(",")[0].strip()
            return {"k": k, "n": n, "recipes": float(rd["recipes"]), "label": label, "name": name}
    raise ValueError(
        f"the base case (S = {S:.6g}, r = {r:g}) matches no reading in monte_carlo.joint.worldview, "
        f"so the worksheet cannot say where those values come from"
    )


def money(x: float) -> str:
    return f"${x:,.2f}"


def worksheet(doc, p, out: Path) -> None:
    recs = records(doc)
    att = synthesis_cost_per_attempt(p)
    parts = att["parts"]
    direct_only = synthesis_cost_per_attempt({**p, "synth_cost_basis": "bench"})["usd"]
    attempts_per_year = p["weeks_per_year"] * p["labour_attempts_per_week"]
    tc = threshold_coefficients(p)
    r = p["synth_recipes_per_target"]
    S = p["synth_success_unconditional"]
    c0 = upstream_per_target(p)
    out_l2 = funnel(p)["pipelines"]["A"]["outputs"]["experimentally_validated"]["usd_per"]
    cross = dft_threshold_sweep(p, points=(54.5,))["crossings"]
    bd = next(x for x in synthesis_decision_boundaries(p)["rows"] if abs(x["dft"] - 54.5) < 0.6)

    L = []
    A = L.append
    A("# Reconstructing the headline numbers by hand")
    A("")
    A("Generated by `scripts/manifest.py` from `params/parameters.yaml`. Every figure below is")
    A("computed by the same code that produces the manuscript, so this worksheet cannot drift from")
    A("the paper. It exists so that a reader can reproduce the three headline results with a")
    A("calculator, without running the model and without having to ask what an input means.")
    A("")
    A("Each line gives the arithmetic, the inputs by parameter name, and where the input came from.")
    A("Full sources are in `results/parameter_manifest.csv`; the attempt-cost inputs with their")
    A("usage allocations are in `results/fee_schedule_manifest.csv`.")
    A("")

    A("## 1. Cost per synthesis attempt")
    A("")
    A("Each line is a published rate times an allocation to one attempt. The allocations are")
    A("assumptions, not measurements, and are named in the fee manifest.")
    A("")
    A(f"Labour and tuition are divided by attempts per year = `synth.weeks_per_year` x "
      f"`synth.labour_attempts_per_week` = {p['weeks_per_year']:g} x "
      f"{p['labour_attempts_per_week']:g} = **{attempts_per_year:g}**.")
    A("")
    A("| Component | Arithmetic | USD |")
    A("|:--|:--|--:|")
    A(f"| XRD | one sample at `synth.xrd_cost_per_sample` = {money(p['xrd_cost_per_sample'])} "
      f"| {money(parts['xrd'])} |")
    A(f"| Furnace | `furnace_fixed_fee` {money(p['furnace_fixed_fee'])} + `furnace_hourly` "
      f"{money(p['furnace_hourly'])} x {p['furnace_hours_per_attempt']:g} h "
      f"| {money(parts['furnace'])} |")
    A(f"| Labour | `labour_annual_salary` {money(p['labour_annual_salary'])} x (1 + "
      f"{p['labour_fringe_rate']:g}) / {attempts_per_year:g} | {money(parts['labour'])} |")
    A(f"| Tuition | `labour_tuition_remission` {money(p['labour_tuition_remission'])} / "
      f"{attempts_per_year:g} | {money(parts['tuition'])} |")
    A(f"| Crucible | `crucible_cost` {money(p['crucible_cost'])} / `attempts_per_crucible` "
      f"{p['attempts_per_crucible']:g} | {money(parts['crucible'])} |")
    A(f"| Precursors | `precursor_mass_g` {p['precursor_mass_g']:g} g x `precursor_usd_per_g` "
      f"{money(p['precursor_usd_per_g'])} | {money(parts['precursors'])} |")
    A(f"| Other consumables | `other_consumables_per_attempt` | {money(parts['other consumables'])} |")
    A(f"| **Direct subtotal** | sum of the rows above | **{money(att['direct_usd'])}** |")
    A(f"| Indirect (F&A) | base {money(att['fa_base_usd'])} x `synth.indirect_rate` "
      f"{p['synth_indirect_rate']:.0%} | {money(parts['indirect (F&A)'])} |")
    A(f"| **Total per attempt** | | **{money(att['usd'])}** |")
    A("")
    A(f"On a direct-cost-only basis (no F&A) the attempt is {money(direct_only)}. The F&A base is")
    A("total direct costs *including* service-centre fees and tuition, because the 42% figure is")
    A("defined by its source over total direct costs; an MTDC-like base is carried as a scenario.")
    A("")

    A("## 2. Cost per experimentally validated material")
    A("")
    A("$$C \\;=\\; \\frac{c_0 + r\\,a}{S}$$")
    A("")
    A("| Symbol | Meaning | Value | Where it comes from |")
    A("|:--|:--|--:|:--|")
    A(f"| $a$ | cost per attempt | {money(att['usd'])} | section 1 above |")
    # The provenance of r and S used to be the hard-coded strings "353 experiments / 57 targets"
    # and "36 of 57 targets" -- A-Lab's campaign. But the base case moved to the middle reading on
    # 2026-10-11, so the worksheet was printing r = 1 and S = 0.2917, which are Prein's, labelled
    # with A-Lab's counts. 353/57 = 6.19 and 36/57 = 0.63, so the stated provenance contradicted
    # the value beside it, which is exactly the rate/count mismatch Section 5.7 warns against.
    # Derived from the reading whose success and recipe count the base case actually follows.
    _reading = _base_reading(doc, S, r)
    A(f"| $r$ | recipes per target | {r:g} | `synth.recipes_per_target`: {_reading['recipes']:g} "
      f"per target as reported by {_reading['label']} |")
    A(f"| $S$ | unconditional synthesis success | {S:g} | `synth.success_unconditional`: "
      f"{_reading['k']:g} of {_reading['n']:g} targets in {_reading['label']}, campaign-observed, "
      f"NOT conditioned on a correct stability label |")
    A(f"| $c_0$ (A) | upstream compute per candidate reaching synthesis | {money(c0['A'])} | "
      f"affine in DFT cost; section 3 below |")
    A("")
    A(f"At base: ({c0['A']:.2f} + {r:g} x {att['usd']:.2f}) / {S:g} = "
      f"({c0['A']:.2f} + {r * att['usd']:,.2f}) / {S:g} = **{money(out_l2)}** for pipeline A.")
    A("")
    A(f"$c_0$ for B and C is {money(c0['B'])} and {money(c0['C'])}, giving "
      f"{money((c0['B'] + r * att['usd']) / S)} and {money((c0['C'] + r * att['usd']) / S)}. The")
    A("three differ only through $c_0$, because $r$, $a$ and $S$ are assumed shared.")
    A("")
    A("**$S$ is unconditional, which matters.** It is the share of *attempted targets* that were")
    A("made, so it already includes targets whose stability label was wrong. Multiplying it by a")
    A("label-accuracy factor would charge those failures twice. A consequence is that the")
    A("stable-to-unstable transition rate $w$ cancels from this equation entirely: level-1 cost is")
    A("per robust prediction, so $c_0 = (1-w)c$ and the factors cancel.")
    A("")

    A("## 3. The threshold crossings")
    A("")
    A("Upstream compute per candidate reaching synthesis is affine in DFT cost $d$ in core-hours:")
    A("")
    A("$$c_{0i}(d) \\;=\\; \\alpha_i d + \\beta_i$$")
    A("")
    A("| Pipeline | $\\alpha$ (USD/core-h) | $\\beta$ (USD) |")
    A("|:--|--:|--:|")
    for k in ("A", "B", "C"):
        A(f"| {k} | {tc['alpha_usd_per_core_h'][k]:.10f} | {tc['beta_usd'][k]:.10f} |")
    A("")
    # Was `compute.price_per_core_hour`, which is not a parameter name -- the record is
    # price.cpu.on_demand -- printed through money(), which rounds 0.0446 to $0.04. A reader
    # reproducing alpha_B from the printed price got 0.04/0.152 = 0.2632 against the 0.2934 printed
    # two lines up. This document exists to be reproduced by hand, so the price is given to the
    # digits the coefficient consumes.
    A(f"$\\alpha$ carries the compute price (`price.cpu.on_demand` = "
      f"\\${p['price_per_core_hour']:.4f}/core-h) and the number of candidates verified per")
    A("candidate reaching synthesis, which is where pool prevalence and filter purity enter.")
    A(f"$\\alpha_C/\\alpha_B$ = {tc['alpha_ratio_C_over_B']:.6f}, exactly the purity ratio "
      f"{p['pool_filter_purity']:.3f}/{p['gen_filter_purity']:.3f}.")
    A("")
    A("Setting $(C_C - C_B)/C_B = \\tau$ and solving for $d$:")
    A("")
    A("$$d^{*} \\;=\\; \\frac{\\tau b + (1+\\tau)\\beta_B - \\beta_C}{\\alpha_C - (1+\\tau)\\alpha_B}"
      "\\;,\\qquad b = ra$$")
    A("")
    A(f"With $b$ = {r:g} x {att['usd']:.2f} = {money(tc['synthesis_bill_usd'])} and $\\tau$ = 0.10:")
    A("")
    num = 0.10 * tc["synthesis_bill_usd"] + 1.10 * tc["beta_usd"]["B"] - tc["beta_usd"]["C"]
    den = tc["alpha_usd_per_core_h"]["C"] - 1.10 * tc["alpha_usd_per_core_h"]["B"]
    A(f"- numerator: 0.10 x {tc['synthesis_bill_usd']:.4f} + 1.10 x {tc['beta_usd']['B']:.7f} "
      f"- {tc['beta_usd']['C']:.7f} = {num:.6f}")
    A(f"- denominator: {tc['alpha_usd_per_core_h']['C']:.10f} - 1.10 x "
      f"{tc['alpha_usd_per_core_h']['B']:.10f} = {den:.6f}")
    A(f"- $d^{{*}}$ = {num:.6f} / {den:.6f} = **{num / den:.4f} core-hours**, which the model's "
      f"bisection also returns as {cross['CB'][0.10]:.4f}.")
    A("")
    A("A positive denominator is necessary but not sufficient: $d^{*}$ must also be nonnegative to")
    A("lie in the domain. The filter crossing, with $\\alpha_A$ in place of $\\alpha_C$, is "
      f"{cross['AB'][0.10]:,.1f} core-hours.")
    A("")

    A("## 4. The synthesis decision boundaries")
    A("")
    A("Relaxing the shared-synthesis assumption, parity between two pipelines needs")
    A("")
    A("$$\\frac{S_i}{S_j} \\;=\\; \\frac{c_{0i} + ra}{c_{0j} + ra}"
      "\\;,\\qquad \\Delta r \\;=\\; \\frac{c_{0i} - c_{0j}}{a}$$")
    A("")
    A(f"- generative vs filtered: ({c0['C']:.2f} + {tc['synthesis_bill_usd']:,.2f}) / "
      f"({c0['B']:.2f} + {tc['synthesis_bill_usd']:,.2f}) = **{bd['success_CB']:.4f}**, so "
      f"{bd['success_CB'] - 1:.1%} better success.")
    A(f"- filter vs none: ({c0['A']:.2f} - {c0['B']:.2f}) / {att['usd']:.2f} = "
      f"**{bd['recipes_AB']:.4f}** extra recipes, {bd['recipes_share_AB']:.2%} of {r:g}.")
    A("")
    A("Both are break-even solves. No source measures a pipeline-specific synthesis difference.")
    A("")

    A("## Regenerating everything")
    A("")
    A("```")
    A("python -m pytest -q                 # the full test suite")
    A("python scripts/stage2.py            # all results/ outputs and the README blocks")
    A("python scripts/manifest.py          # this worksheet and the two manifests")
    A("python scripts/audit_numbers.py paper/<manuscript>.md   # every printed number vs the model")
    A("```")
    A("")
    A("The Monte Carlo is seeded from `monte_carlo.seed` in the parameter file, so the draw-level")
    A("outputs are reproducible byte for byte on the same Python version.")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> None:
    doc = load()
    p = resolve(doc)
    res = ROOT / "results"
    res.mkdir(exist_ok=True)
    n_par = parameter_manifest(doc, res / "parameter_manifest.csv")
    n_fee = fee_manifest(doc, res / "fee_schedule_manifest.csv")
    worksheet(doc, p, res / "RECONSTRUCTION.md")
    print(json.dumps({"parameters": n_par, "fee_inputs": n_fee,
                      "worksheet": "results/RECONSTRUCTION.md"}, indent=1))


if __name__ == "__main__":
    main()
