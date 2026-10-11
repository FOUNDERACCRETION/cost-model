"""Cost funnel: parameter dict in, result dict out. No I/O, no globals.

Pipelines
  A  DFT only:                       generate (pool) -> new to MP -> DFT check -> synthesis -> novelty
  B  MLIP filter, then DFT:          generate (pool) -> new to MP -> MLIP relax -> sent to DFT -> DFT check
                                     -> synthesis -> novelty
  C  generative model, MLIP, DFT:    generate (generator) -> new to MP -> MLIP relax -> ... (as B)

n_candidates counts MP-novel candidates: structures already in Materials Project are dropped by a
database check before any calculation, as in Szymanski & Bartel, whose stability rates are
measured on MP-novel structures. Generating n_candidates novel ones takes n / (MP-novel share).

A and B screen the candidate pool (ion exchange by default) and are charged its
generation cost; C screens the output of a generative model and pays for that.

Compute is counted in core-hours (CPU) and GPU-hours and converted to dollars
only at the end, with one price per compute type. Synthesis is costed in
dollars directly. Equation numbers refer to the README.

Ratios with a zero denominator (no survivors) are returned as math.inf.
"""

from __future__ import annotations

import math

FRACTIONS = (
    "pool_frac_stable", "pool_frac_novel_mp", "pool_frac_novel_all_db",
    "gen_frac_stable", "gen_frac_novel_mp", "gen_frac_novel_all_db",
    "mlip_nonconv_frac", "mlip_tpr", "mlip_fpr", "dft_fraction_sent",
    "dft_wrong_verdict_frac", "synth_success_unconditional", "novelty_science_frac",
    "pool_filter_purity", "gen_filter_purity",
)
NON_NEGATIVE = (
    "n_candidates", "n_atoms", "pool_gen_core_s", "pool_gen_gpu_s", "gen_core_s", "gen_gpu_s",
    "mlip_step_cost_per_atom", "mlip_steps",
    "mlip_step_cap", "dft_cost_per_candidate", "dft_scf_cost_at_ref", "dft_scf_per_ionic", "dft_ionic_steps",
    "reference_phases", "synth_recipes_per_target", "synth_success_multiplier_filtered", "xrd_cost_per_sample",
    "furnace_fixed_fee", "furnace_hourly", "furnace_hours_per_attempt", "labour_annual_salary",
    "labour_fringe_rate", "labour_tuition_remission", "synth_indirect_rate", "crucible_cost", "precursor_mass_g",
    "precursor_usd_per_g",
    "other_consumables_per_attempt", "price_per_core_hour", "price_per_gpu_hour",
)
GENERATION_COST_KEYS = {"pool": ("pool_gen_core_s", "pool_gen_gpu_s"), "gen": ("gen_core_s", "gen_gpu_s")}
POSITIVE = ("dft_scf_ref_atoms", "labour_attempts_per_week", "weeks_per_year", "attempts_per_crucible")


def ratio(numerator: float, denominator: float) -> float:
    """numerator / denominator, or inf when there is nothing to divide by."""
    return numerator / denominator if denominator > 0 else math.inf


def _check(p: dict) -> None:
    for k in FRACTIONS:
        if not 0.0 <= p[k] <= 1.0:
            raise ValueError(f"{k} must be in [0, 1], got {p[k]}")
    for k in NON_NEGATIVE:
        if p[k] < 0:
            raise ValueError(f"{k} must be >= 0, got {p[k]}")
    for k in POSITIVE:
        if p[k] <= 0:
            raise ValueError(f"{k} must be > 0, got {p[k]}")
    if p["mlip_steps"] > p["mlip_step_cap"]:
        raise ValueError("mlip_steps (mean converged steps) cannot exceed mlip_step_cap")
    if p["dft_cost_basis"] not in ("span", "first_hand"):
        raise ValueError(f"dft_cost_basis must be 'span' or 'first_hand', got {p['dft_cost_basis']}")
    for src in ("pool", "gen"):
        if p[f"{src}_frac_novel_all_db"] > p[f"{src}_frac_novel_mp"]:
            raise ValueError(f"{src}: share new to all databases cannot exceed share new to MP")
    if p["synth_cost_basis"] not in ("funder", "bench"):
        raise ValueError(f"synth_cost_basis must be 'funder' or 'bench', got {p['synth_cost_basis']}")
    if not isinstance(p["fa_on_service_fees"], bool):
        raise ValueError("fa_on_service_fees must be True or False")
    if p["mlip_filter_basis"] not in ("measured", "matbench"):
        raise ValueError(f"mlip_filter_basis must be 'measured' or 'matbench', got {p['mlip_filter_basis']}")
    if p["synth_success_unconditional"] * p["synth_success_multiplier_filtered"] > 1:
        raise ValueError("synthesis success x filtered multiplier exceeds 1")


# ---------------------------------------------------------------- unit costs


def mlip_cost_per_candidate(p: dict) -> dict:
    """Eq. 1. Expected MLIP core-hours per candidate, non-converged runs charged at the cap."""
    step_core_s = p["mlip_step_cost_per_atom"] * p["n_atoms"]
    q = p["mlip_nonconv_frac"]
    expected_steps = (1 - q) * p["mlip_steps"] + q * p["mlip_step_cap"]
    return {
        "core_s_per_step": step_core_s,
        "expected_steps": expected_steps,
        "core_h": step_core_s * expected_steps / 3600,
        "core_h_converged_run": step_core_s * p["mlip_steps"] / 3600,
        "core_h_capped_run": step_core_s * p["mlip_step_cap"] / 3600,
    }


def dft_cost_per_candidate(p: dict) -> dict:
    """Eq. 2. DFT core-hours per candidate: a value from the 3-1,000 core-h span (primary), or the
    size-dependent first-hand estimate."""
    scf_core_s = p["dft_scf_cost_at_ref"] * (p["n_atoms"] / p["dft_scf_ref_atoms"]) ** p["dft_scf_size_exponent"]
    first_hand = scf_core_s * p["dft_scf_per_ionic"] * p["dft_ionic_steps"] / 3600
    span_value = p["dft_cost_per_candidate"]
    used = span_value if p["dft_cost_basis"] == "span" else first_hand
    return {
        "scf_core_s": scf_core_s,
        "first_hand_core_h": first_hand,
        "span_core_h": span_value,
        "basis": p["dft_cost_basis"],
        "core_h": used,
    }


def synthesis_cost_per_attempt(p: dict) -> dict:
    """Eq. 6. Dollars per recipe attempt, built bottom-up.

    cost_basis "bench": direct costs only, as a lab's own budget sees them.
    cost_basis "funder": plus institutional F&A on the F&A base. Service-centre fees (XRD, furnace) are left
    out of that base unless fa_on_service_fees is set, because recharge rates already carry the centre's
    share of indirect costs (2 CFR 200.468(b)(2)), so F&A on top would count it twice.
    """
    labour_per_year = p["labour_annual_salary"] * (1 + p["labour_fringe_rate"])
    attempts_per_year = p["weeks_per_year"] * p["labour_attempts_per_week"]
    direct = {
        "xrd": p["xrd_cost_per_sample"],
        "furnace": p["furnace_fixed_fee"] + p["furnace_hourly"] * p["furnace_hours_per_attempt"],
        "labour": labour_per_year / attempts_per_year,
        "crucible": p["crucible_cost"] / p["attempts_per_crucible"],
        "precursors": p["precursor_mass_g"] * p["precursor_usd_per_g"],
        "other consumables": p["other_consumables_per_attempt"],
    }
    direct_usd = sum(direct.values())
    # Tuition is a direct cost. Under MTDC it sits outside the base (2 CFR 200.1 excludes tuition
    # remission); under a total-direct-cost base it is inside it.
    tuition = p["labour_tuition_remission"] / attempts_per_year
    service_fees = direct["xrd"] + direct["furnace"]
    # The effective indirect rate is defined by its source as recovered indirect cost over TOTAL
    # DIRECT COSTS. Pairing it with a narrowed base understates recovery against that definition,
    # so total_direct is the matched default. mtdc reproduces the pre-2026-10-11 behaviour and is
    # kept as an accounting scenario.
    if p.get("indirect_base", "total_direct") == "total_direct":
        fa_base = direct_usd + tuition
    else:
        fa_base = direct_usd if p["fa_on_service_fees"] else direct_usd - service_fees
    indirect = fa_base * p["synth_indirect_rate"] if p["synth_cost_basis"] == "funder" else 0.0
    parts = {**direct, "tuition": tuition, "indirect (F&A)": indirect}
    return {"parts": parts, "direct_usd": direct_usd + tuition, "fa_base_usd": fa_base, "usd": sum(parts.values())}


def mlip_pass_rate(prevalence: float, tpr: float, fpr: float) -> dict:
    """Eq. 3b (Matbench path). Fraction of converged candidates the MLIP flags stable, and precision at this prevalence."""
    true_pos = prevalence * tpr
    flagged = true_pos + (1 - prevalence) * fpr
    return {"flagged": flagged, "precision": ratio(true_pos, flagged) if flagged > 0 else 0.0}


def mlip_filter(prevalence: float, purity: float, p: dict) -> dict:
    """Eq. 3. What the MLIP filter lets through, on the selected basis, with consistency diagnostics.

    measured: purity (DFT-stable share of what passes) is measured for this pool; recall comes from
              Matbench, so the pass fraction is prevalence x recall / purity.
    matbench: recall and false-positive rate both from Matbench (eq. 3b).
    """
    tpr, fpr = p["mlip_tpr"], p["mlip_fpr"]
    true_pos = prevalence * tpr
    matbench = mlip_pass_rate(prevalence, tpr, fpr)
    if p["mlip_filter_basis"] == "matbench":
        flagged, precision = matbench["flagged"], matbench["precision"]
    else:
        if purity > 0:
            flagged = true_pos / purity
        elif true_pos == 0:
            flagged = 0.0
        else:
            raise ValueError("measured filter purity is 0 but prevalence x recall > 0: inconsistent")
        if flagged > 1:
            raise ValueError(
                f"inconsistent: prevalence {prevalence} x recall {tpr} / purity {purity} = pass fraction {flagged} > 1"
            )
        precision = purity
    # Diagnostics: what the measured purity implies if one of the Matbench rates were right.
    implied_fpr = (flagged - true_pos) / (1 - prevalence) if prevalence < 1 else math.nan
    if 0 < prevalence < 1 and 0 < purity < 1:
        recall_if_matbench_fpr = purity * (1 - prevalence) * fpr / (prevalence * (1 - purity))
    else:
        recall_if_matbench_fpr = math.nan
    return {
        "basis": p["mlip_filter_basis"],
        "flagged": flagged,
        "precision": precision,
        "recall_used": tpr,
        "measured_purity": purity,
        "matbench_precision_at_prevalence": matbench["precision"],
        "implied_fpr": implied_fpr,
        "matbench_fpr": fpr,
        "recall_implied_by_purity_and_matbench_fpr": recall_if_matbench_fpr,
    }


# ---------------------------------------------------------------- funnel


def _stage(name, entering, pass_rate, core_h_each=0.0, gpu_h_each=0.0, usd_each=0.0, note=""):
    return {
        "stage": name,
        "entering": entering,
        "pass_rate": pass_rate,
        "surviving": entering * pass_rate,
        "core_h": entering * core_h_each,
        "gpu_h": entering * gpu_h_each,
        "direct_usd": entering * usd_each,
        "note": note,
    }


def _price(core_h: float, gpu_h: float, direct_usd: float, p: dict) -> float:
    return core_h * p["price_per_core_hour"] + gpu_h * p["price_per_gpu_hour"] + direct_usd


def _pipeline(p: dict, name: str, source: str, use_mlip: bool, mlip: dict, dft: dict, synth: dict) -> dict:
    """source is "pool" (A, B) or "gen" (C): which candidate source's yields and generation cost apply."""
    n = p["n_candidates"]
    prevalence = p[f"{source}_frac_stable"]
    novel_mp = p[f"{source}_frac_novel_mp"]
    # Of MP-novel candidates, the share also absent from Alexandria and ICSD (both shares are of all generated).
    novel_beyond_mp = ratio(p[f"{source}_frac_novel_all_db"], novel_mp) if novel_mp > 0 else 0.0
    w = p["dft_wrong_verdict_frac"]
    # Sensitivity switch: synthesis success for MLIP-filtered pipelines (B, C) relative to A.
    success = p["synth_success_unconditional"] * (p["synth_success_multiplier_filtered"] if use_mlip else 1.0)
    recipes = p["synth_recipes_per_target"]

    stages = []
    core_key, gpu_key = GENERATION_COST_KEYS[source]
    generated = n / novel_mp if novel_mp > 0 else n
    stages.append(_stage("generate", generated, 1.0, core_h_each=p[core_key] / 3600, gpu_h_each=p[gpu_key] / 3600))
    stages.append(_stage("new to MP", generated, novel_mp if novel_mp > 0 else 0.0, note="database lookup, no cost"))
    screened = stages[-1]["surviving"]  # MP-novel candidates entering calculation (= n when novel_mp > 0)

    if use_mlip:
        rates = mlip_filter(prevalence, p[f"{source}_filter_purity"], p)
        q = p["mlip_nonconv_frac"]
        stages.append(_stage(
            "MLIP relax + classify", stages[-1]["surviving"], (1 - q) * rates["flagged"], core_h_each=mlip["core_h"],
            note=f"converged {1 - q:.3f} x flagged stable {rates['flagged']:.4f}",
        ))
        stages.append(_stage("sent to DFT", stages[-1]["surviving"], p["dft_fraction_sent"]))
        dft_pass = rates["precision"]
        mlip_info = {
            **rates,
            "nonconverged_candidates": screened * q,
            "nonconverged_core_h": screened * q * mlip["core_h_capped_run"],
        }
    else:
        dft_pass = prevalence
        mlip_info = None

    dft_in = stages[-1]["surviving"]
    stages.append(_stage("DFT check", dft_in, dft_pass, core_h_each=dft["core_h"], note="pass = DFT-stable verdict"))
    verdicts = stages[-1]["surviving"]

    # Unconditional synthesis success: the campaign-observed rate already embeds whatever
    # computational failure that campaign experienced, so (1 - w) must NOT be applied here.
    # Applying both charged computational failure twice on the readings that were never
    # conditioned. w is still computed and reported, as a separate transition-rate diagnostic
    # and for the level-1 output, but it no longer enters the level-2 or level-3 denominators.
    stages.append(_stage(
        "synthesis", verdicts, success, usd_each=recipes * synth["usd"],
        note=f"unconditional success {success:.3f}",
    ))
    made = stages[-1]["surviving"]
    stages.append(_stage(
        "new to science", made, novel_beyond_mp * p["novelty_science_frac"],
        note=f"also absent from Alexandria + ICSD {novel_beyond_mp:.3f} x new to science {p['novelty_science_frac']:.4f}",
    ))

    # Fixed cost per chemistry: reference phases relaxed with every computational method used (eq. 7).
    fixed_core_h = p["reference_phases"] * (dft["core_h"] + (mlip["core_h"] if use_mlip else 0.0))
    fixed_usd = _price(fixed_core_h, 0.0, 0.0, p)

    cumulative = fixed_usd
    for s in stages:
        s["usd"] = _price(s["core_h"], s["gpu_h"], s["direct_usd"], p)
        cumulative += s["usd"]
        s["cumulative_usd"] = cumulative
        s["cumulative_usd_per_survivor"] = ratio(cumulative, s["surviving"])

    compute_stages = [s for s in stages if s["stage"] not in ("synthesis", "new to science")]
    marginal_compute_core_h = sum(s["core_h"] for s in compute_stages)
    marginal_compute_gpu_h = sum(s["gpu_h"] for s in compute_stages)
    marginal_compute_usd = sum(s["usd"] for s in compute_stages)
    synth_usd = next(s["usd"] for s in stages if s["stage"] == "synthesis")

    correct_verdicts = verdicts * (1 - w)
    new = stages[-1]["surviving"]

    def level(count, synthesis_usd):
        """Cost per output, split into compute (incl. fixed) and synthesis parts (eq. 9)."""
        compute_usd = marginal_compute_usd + fixed_usd
        return {
            "count": count,
            "usd_per": ratio(compute_usd + synthesis_usd, count),
            "marginal_usd_per": ratio(marginal_compute_usd + synthesis_usd, count),
            "compute_usd_per": ratio(compute_usd, count),
            "synthesis_usd_per": ratio(synthesis_usd, count),
            "core_h_per": ratio(marginal_compute_core_h + fixed_core_h, count),
            "gpu_h_per": ratio(marginal_compute_gpu_h, count),
        }

    return {
        "pipeline": name,
        "prevalence": prevalence,
        "synthesis_success": success,
        "stages": stages,
        "fixed": {"core_h": fixed_core_h, "usd": fixed_usd, "usd_per_candidate": ratio(fixed_usd, n)},
        "marginal": {
            "compute_core_h": marginal_compute_core_h,
            "compute_gpu_h": marginal_compute_gpu_h,
            "compute_usd": marginal_compute_usd,
            "synthesis_usd": synth_usd,
            "usd_per_candidate": ratio(marginal_compute_usd + synth_usd, n),
        },
        "mlip": mlip_info,
        "label_reliability": {
            "dft_stable_verdicts": verdicts,
            "wrong_verdicts": verdicts * w,
            "dft_core_h_on_wrong_verdicts": verdicts * w * dft["core_h"],
            "dft_usd_on_wrong_verdicts": _price(verdicts * w * dft["core_h"], 0.0, 0.0, p),
            "synthesis_attempts_on_wrong_verdicts": verdicts * w * recipes,
            "synthesis_usd_on_wrong_verdicts": verdicts * w * recipes * synth["usd"],
        },
        "outputs": {
            "naive_per_dft_stable_verdict": level(verdicts, 0.0),
            "dft_confirmed_stable": level(correct_verdicts, 0.0),
            "experimentally_validated": level(made, synth_usd),
            # Lower bound only: the novelty share's base is an upper bound on 0 of 36 (README, level 3).
            "validated_new": {**level(new, synth_usd), "bound": "lower"},
        },
    }


def funnel(p: dict) -> dict:
    """Run pipelines A, B and C on one parameter dict. Returns the full breakdown."""
    _check(p)
    mlip = mlip_cost_per_candidate(p)
    dft = dft_cost_per_candidate(p)
    synth = synthesis_cost_per_attempt(p)
    return {
        "unit_costs": {
            "mlip": mlip,
            "dft": dft,
            "synthesis_attempt": synth,
            "synthesis_per_target_usd": p["synth_recipes_per_target"] * synth["usd"],
        },
        "pipelines": {
            "A": _pipeline(p, "A: DFT only", source="pool", use_mlip=False, mlip=mlip, dft=dft, synth=synth),
            "B": _pipeline(p, "B: MLIP then DFT", source="pool", use_mlip=True, mlip=mlip, dft=dft, synth=synth),
            "C": _pipeline(p, "C: generate, MLIP, DFT", source="gen", use_mlip=True, mlip=mlip, dft=dft, synth=synth),
        },
    }
