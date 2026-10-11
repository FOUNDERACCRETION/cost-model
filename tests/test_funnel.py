"""Unit tests for src/funnel.py.

The HAND CASES use round numbers so the arithmetic can be checked on paper; each
test's docstring shows the working.
"""

import math

import pytest

from src.funnel import (
    dft_cost_per_candidate,
    funnel,
    mlip_cost_per_candidate,
    mlip_pass_rate,
    synthesis_cost_per_attempt,
)
from src.params import load, resolve


def hand_params(**overrides) -> dict:
    """Round-number parameters. Synthesis costs only XRD at $100 per attempt; price $1 per core-hour."""
    p = {
        "n_candidates": 100, "n_atoms": 10,
        "pool_frac_stable": 0.1, "pool_frac_novel_mp": 1.0, "pool_frac_novel_all_db": 0.5,
        "pool_gen_core_s": 0.0, "pool_gen_gpu_s": 0.0, "pool_filter_purity": 0.08 / 0.17,
        "gen_frac_stable": 0.1, "gen_frac_novel_mp": 1.0, "gen_frac_novel_all_db": 0.5, "gen_core_s": 0.0, "gen_gpu_s": 0.0, "gen_filter_purity": 0.08 / 0.17,
        "mlip_step_cost_per_atom": 1.0, "mlip_steps": 36, "mlip_step_cap": 360, "mlip_nonconv_frac": 0.2,
        "mlip_tpr": 0.8, "mlip_fpr": 0.1, "dft_fraction_sent": 1.0, "mlip_filter_basis": "matbench",
        "dft_cost_basis": "span", "dft_cost_per_candidate": 10.0,
        "dft_scf_cost_at_ref": 100.0, "dft_scf_size_exponent": 2.0, "dft_scf_ref_atoms": 20,
        "dft_scf_per_ionic": 10, "dft_ionic_steps": 9,
        "dft_wrong_verdict_frac": 0.2,
        "reference_phases": 0,
        "synth_recipes_per_target": 2, "synth_success_unconditional": 0.5, "synth_success_multiplier_filtered": 1.0,
        "xrd_cost_per_sample": 100.0, "furnace_fixed_fee": 0.0, "furnace_hourly": 0.0,
        "furnace_hours_per_attempt": 0.0, "labour_annual_salary": 0.0, "labour_fringe_rate": 0.0, "labour_tuition_remission": 0.0,
        "synth_indirect_rate": 0.0, "synth_cost_basis": "funder", "fa_on_service_fees": True, "labour_attempts_per_week": 1, "weeks_per_year": 52,
        "crucible_cost": 0.0, "attempts_per_crucible": 1, "precursor_mass_g": 0.0, "precursor_usd_per_g": 0.0,
        "other_consumables_per_attempt": 0.0,
        "novelty_science_frac": 0.5,
        "price_per_core_hour": 1.0, "price_per_gpu_hour": 1.0,
    }
    p.update(overrides)
    return p


def stage(pipeline: dict, name: str) -> dict:
    return next(s for s in pipeline["stages"] if s["stage"] == name)


# ---------------------------------------------------------------- hand case 1: pipeline A


def test_hand_case_1_pipeline_a():
    """100 candidates, 10% DFT-stable, 10 core-h each at $1 -> $1,000 compute, 10 verdicts.
    20% of verdicts wrong -> 8 correct -> $125 per DFT-confirmed stable ($100 naive).
    Synthesis: 10 targets x 2 recipes x $100 = $2,000. Made = 10 x 0.5 = 5 -> $3,000 / 5 = $600.
    New = 5 x 0.5 x 0.5 = 1.25 -> $2,400.
    CHANGED 2026-10-11: made was 10 x 0.8 x 0.5 = 4 at $750; (1 - w) no longer enters level 2.
    Wrong verdicts: 2 -> 20 DFT core-h wasted, 4 synthesis attempts ($400) wasted.
    """
    a = funnel(hand_params())["pipelines"]["A"]
    out = a["outputs"]
    assert stage(a, "DFT check")["core_h"] == pytest.approx(1000)
    assert out["naive_per_dft_stable_verdict"]["count"] == pytest.approx(10)
    assert out["naive_per_dft_stable_verdict"]["usd_per"] == pytest.approx(100)
    assert out["dft_confirmed_stable"]["count"] == pytest.approx(8)
    assert out["dft_confirmed_stable"]["usd_per"] == pytest.approx(125)
    assert out["experimentally_validated"]["count"] == pytest.approx(5)
    assert out["experimentally_validated"]["usd_per"] == pytest.approx(600)
    assert out["validated_new"]["count"] == pytest.approx(1.25)
    assert out["validated_new"]["usd_per"] == pytest.approx(2400)
    lr = a["label_reliability"]
    assert lr["wrong_verdicts"] == pytest.approx(2)
    assert lr["dft_core_h_on_wrong_verdicts"] == pytest.approx(20)
    assert lr["synthesis_attempts_on_wrong_verdicts"] == pytest.approx(4)
    assert lr["synthesis_usd_on_wrong_verdicts"] == pytest.approx(400)


# ---------------------------------------------------------------- hand case 2: pipeline B (MLIP)


def test_hand_case_2_pipeline_b():
    """Step cost 1 core-s/atom x 10 atoms = 10 core-s per step.
    Expected steps = 0.8 x 36 + 0.2 x 360 = 100.8 -> 1,008 core-s = 0.28 core-h per candidate, 28 core-h for 100.
    Flagged = 0.1 x 0.8 + 0.9 x 0.1 = 0.17; of converged (80) -> 13.6 go to DFT at 10 core-h = 136 core-h.
    DFT-stable = 100 x 0.8 x 0.1 x 0.8 = 6.4 (precision 0.08 / 0.17).
    Compute $164 / 6.4 = $25.625 per verdict.
    Non-converged: 20 candidates x (10 x 360 / 3600 = 1 core-h) = 20 core-h, with no output.
    """
    b = funnel(hand_params())["pipelines"]["B"]
    assert stage(b, "MLIP relax + classify")["core_h"] == pytest.approx(28)
    assert stage(b, "MLIP relax + classify")["surviving"] == pytest.approx(13.6)
    assert stage(b, "DFT check")["core_h"] == pytest.approx(136)
    assert stage(b, "DFT check")["pass_rate"] == pytest.approx(0.08 / 0.17)
    assert stage(b, "DFT check")["surviving"] == pytest.approx(6.4)
    assert b["outputs"]["naive_per_dft_stable_verdict"]["usd_per"] == pytest.approx(164 / 6.4)
    assert b["mlip"]["nonconverged_candidates"] == pytest.approx(20)
    assert b["mlip"]["nonconverged_core_h"] == pytest.approx(20)


# ---------------------------------------------------------------- hand case 3: fixed cost amortisation


def test_hand_case_3_fixed_cost_amortised():
    """5 reference phases x 10 core-h DFT = 50 core-h ($50) fixed for pipeline A.
    Marginal compute $1,000 over 8 correct verdicts = $125; with fixed, $1,050 / 8 = $131.25.
    Pipeline B fixed = 5 x (10 + 0.28) = 51.4 core-h (MLIP and DFT hulls).
    """
    r = funnel(hand_params(reference_phases=5))["pipelines"]
    a = r["A"]
    assert a["fixed"]["core_h"] == pytest.approx(50)
    assert a["fixed"]["usd_per_candidate"] == pytest.approx(0.5)
    level1 = a["outputs"]["dft_confirmed_stable"]
    assert level1["marginal_usd_per"] == pytest.approx(125)
    assert level1["usd_per"] == pytest.approx(131.25)
    assert r["B"]["fixed"]["core_h"] == pytest.approx(51.4)


def test_fixed_cost_per_output_falls_with_batch_size():
    """Fixed share per output is fixed / count, and count scales with the batch, so it halves as N doubles."""
    def fixed_share(n):
        lvl = funnel(hand_params(reference_phases=5, n_candidates=n))["pipelines"]["A"]["outputs"]["dft_confirmed_stable"]
        return lvl["usd_per"] - lvl["marginal_usd_per"]

    assert fixed_share(200) == pytest.approx(fixed_share(100) / 2)
    assert fixed_share(10_000) == pytest.approx(fixed_share(100) / 100)


def test_marginal_cost_independent_of_batch_size():
    small = funnel(hand_params(n_candidates=100))
    large = funnel(hand_params(n_candidates=7_919))
    for key in "ABC":
        for level, out in small["pipelines"][key]["outputs"].items():
            assert large["pipelines"][key]["outputs"][level]["marginal_usd_per"] == pytest.approx(out["marginal_usd_per"])


def test_zero_fixed_cost_means_total_equals_marginal():
    for pl in funnel(hand_params(reference_phases=0))["pipelines"].values():
        for out in pl["outputs"].values():
            assert out["usd_per"] == pytest.approx(out["marginal_usd_per"])


# ---------------------------------------------------------------- unit-cost equations


def test_synthesis_cost_per_attempt_bottom_up():
    """Labour 52,000 x 1.25 / 52 weeks / 10 per week = $125; furnace 6 + 3 x 10 = $36; XRD $80;
    crucible 40 / 4 = $10; precursors 2 g x $2/g = $4; other consumables $5. Direct $260.
    Tuition 5,200 / 520 attempts = $10. Under the default total-direct-cost base the indirect
    base is 260 + 10 = $270 and indirect (F&A) 20% of that = $54. Total $324.

    CHANGED 2026-10-11: the base was MTDC-like ($260, tuition excluded) giving $52 and $322.
    The 42% effective rate is defined over TOTAL direct costs, so that was a rate/base mismatch."""
    p = hand_params(
        labour_annual_salary=52_000, labour_fringe_rate=0.25, synth_indirect_rate=0.2, labour_attempts_per_week=10,
        furnace_fixed_fee=6, furnace_hourly=3, furnace_hours_per_attempt=10, xrd_cost_per_sample=80,
        crucible_cost=40, attempts_per_crucible=4, precursor_mass_g=2, precursor_usd_per_g=2,
        other_consumables_per_attempt=5, labour_tuition_remission=5_200,
    )
    s = synthesis_cost_per_attempt(p)
    assert s["parts"] == pytest.approx({
        "labour": 125, "furnace": 36, "xrd": 80, "crucible": 10, "precursors": 4, "other consumables": 5,
        "tuition": 10, "indirect (F&A)": 54,
    })
    assert s["direct_usd"] == pytest.approx(270)
    assert s["fa_base_usd"] == pytest.approx(270)
    assert s["usd"] == pytest.approx(324)


def test_fa_base_and_cost_basis():
    """Same inputs as above, under the retained MTDC scenario (indirect_base = "mtdc").
    Fees out of the base: base = 260 - 80 XRD - 36 furnace = $144, F&A 20% = $28.80,
    total 260 + 10 + 28.80 = $298.80. Fees in: base $260, F&A $52, total $322.
    Matched default (total_direct): base $270, F&A $54, total $324. Bench basis: no F&A, $270."""
    p = hand_params(
        labour_annual_salary=52_000, labour_fringe_rate=0.25, synth_indirect_rate=0.2, labour_attempts_per_week=10,
        furnace_fixed_fee=6, furnace_hourly=3, furnace_hours_per_attempt=10, xrd_cost_per_sample=80,
        crucible_cost=40, attempts_per_crucible=4, precursor_mass_g=2, precursor_usd_per_g=2,
        other_consumables_per_attempt=5, labour_tuition_remission=5_200,
    )
    mtdc = {**p, "indirect_base": "mtdc"}
    no_fees = synthesis_cost_per_attempt({**mtdc, "fa_on_service_fees": False})
    assert no_fees["fa_base_usd"] == pytest.approx(144)
    assert no_fees["parts"]["indirect (F&A)"] == pytest.approx(28.8)
    assert no_fees["usd"] == pytest.approx(298.8)
    with_fees = synthesis_cost_per_attempt({**mtdc, "fa_on_service_fees": True})
    assert with_fees["fa_base_usd"] == pytest.approx(260)
    assert with_fees["usd"] == pytest.approx(322)
    matched = synthesis_cost_per_attempt(p)
    assert matched["fa_base_usd"] == pytest.approx(270)
    assert matched["usd"] == pytest.approx(324)
    bench = synthesis_cost_per_attempt({**p, "synth_cost_basis": "bench"})
    assert bench["parts"]["indirect (F&A)"] == 0
    assert bench["usd"] == pytest.approx(270)


def test_first_hand_dft_cost():
    """100 core-s per SCF at 20 atoms, exponent 2, 40 atoms -> 400 core-s; x 10 SCF x 9 ionic = 36,000 core-s = 10 core-h."""
    d = dft_cost_per_candidate(hand_params(n_atoms=40, dft_cost_basis="first_hand"))
    assert d["scf_core_s"] == pytest.approx(400)
    assert d["first_hand_core_h"] == pytest.approx(10)
    assert d["core_h"] == pytest.approx(10)
    assert dft_cost_per_candidate(hand_params(n_atoms=40))["core_h"] == 10.0  # span value, also 10 here


def test_mlip_nonconvergence_costs_cap():
    all_fail = mlip_cost_per_candidate(hand_params(mlip_nonconv_frac=1.0))
    assert all_fail["core_h"] == pytest.approx(all_fail["core_h_capped_run"])
    none_fail = mlip_cost_per_candidate(hand_params(mlip_nonconv_frac=0.0))
    assert none_fail["core_h"] == pytest.approx(none_fail["core_h_converged_run"])


def test_mlip_precision_recovers_benchmark_precision():
    """At the Matbench prevalence, recall and FPR give back the published precision."""
    prevalence, tpr, fpr = 0.15487637362637363, 0.7584646730988195, 0.13153848688184325
    assert mlip_pass_rate(prevalence, tpr, fpr)["precision"] == pytest.approx(0.514, abs=5e-4)


def test_perfect_classifier_passes_exactly_the_stable():
    p = hand_params(mlip_tpr=1.0, mlip_fpr=0.0, mlip_nonconv_frac=0.0)
    b = funnel(p)["pipelines"]["B"]
    assert stage(b, "MLIP relax + classify")["surviving"] == pytest.approx(10)
    assert stage(b, "DFT check")["pass_rate"] == pytest.approx(1.0)


# ---------------------------------------------------------------- composition


@pytest.mark.parametrize("params", [hand_params(), hand_params(dft_fraction_sent=0.5, reference_phases=3)])
def test_pass_rates_compose(params):
    """Each stage takes in what the previous one let through, and survivors = N x product of pass rates."""
    for pl in funnel(params)["pipelines"].values():
        product = 1.0
        for prev, cur in zip(pl["stages"], pl["stages"][1:]):
            assert cur["entering"] == pytest.approx(prev["surviving"])
        for s in pl["stages"]:
            product *= s["pass_rate"]
            assert s["surviving"] == pytest.approx(pl["stages"][0]["entering"] * product)


def test_dft_fraction_sent_scales_spend_and_yield_together():
    full = funnel(hand_params())["pipelines"]["B"]
    half = funnel(hand_params(dft_fraction_sent=0.5))["pipelines"]["B"]
    assert stage(half, "DFT check")["core_h"] == pytest.approx(stage(full, "DFT check")["core_h"] / 2)
    assert half["outputs"]["dft_confirmed_stable"]["count"] == pytest.approx(full["outputs"]["dft_confirmed_stable"]["count"] / 2)


def test_cumulative_cost_adds_up():
    for pl in funnel(hand_params(reference_phases=2))["pipelines"].values():
        total = pl["fixed"]["usd"] + pl["marginal"]["compute_usd"] + pl["marginal"]["synthesis_usd"]
        assert pl["stages"][-1]["cumulative_usd"] == pytest.approx(total)


def test_label_reliability_zero_and_one():
    perfect = funnel(hand_params(dft_wrong_verdict_frac=0.0))["pipelines"]["A"]["outputs"]
    assert perfect["dft_confirmed_stable"]["usd_per"] == pytest.approx(perfect["naive_per_dft_stable_verdict"]["usd_per"])
    useless = funnel(hand_params(dft_wrong_verdict_frac=1.0))["pipelines"]["A"]
    # w = 1 makes LEVEL 1 unbounded: no verdict survives the cross-functional check.
    assert useless["outputs"]["dft_confirmed_stable"]["usd_per"] == math.inf
    # Level 2 stays finite: the campaign-observed success rate is unconditional and does not
    # depend on w. CHANGED 2026-10-11 -- level 2 used to go to infinity here, which was the
    # double-charge showing up at the limit.
    assert math.isfinite(useless["outputs"]["experimentally_validated"]["usd_per"])
    assert useless["label_reliability"]["synthesis_usd_on_wrong_verdicts"] == pytest.approx(useless["marginal"]["synthesis_usd"])


def test_price_converts_only_at_the_end():
    on = funnel(hand_params(price_per_core_hour=1.0))["pipelines"]["A"]
    spot = funnel(hand_params(price_per_core_hour=0.25))["pipelines"]["A"]
    assert spot["marginal"]["compute_core_h"] == on["marginal"]["compute_core_h"]
    assert spot["marginal"]["compute_usd"] == pytest.approx(on["marginal"]["compute_usd"] / 4)
    assert spot["marginal"]["synthesis_usd"] == on["marginal"]["synthesis_usd"]


def test_gpu_generation_priced_at_gpu_rate():
    """3,600 GPU-s per structure = 1 GPU-h; 100 structures at $3 = $300."""
    c = funnel(hand_params(gen_gpu_s=3600, price_per_gpu_hour=3.0))["pipelines"]["C"]
    assert stage(c, "generate")["gpu_h"] == pytest.approx(100)
    assert stage(c, "generate")["usd"] == pytest.approx(300)


# ---------------------------------------------------------------- zero survivors


@pytest.mark.parametrize("overrides, inf_from", [
    ({"pool_frac_stable": 0.0, "gen_frac_stable": 0.0}, "naive_per_dft_stable_verdict"),
    ({"n_candidates": 0}, "naive_per_dft_stable_verdict"),
    ({"mlip_tpr": 0.0, "mlip_fpr": 0.0, "pool_frac_stable": 0.0, "gen_frac_stable": 0.0}, "naive_per_dft_stable_verdict"),
    ({"synth_success_unconditional": 0.0}, "experimentally_validated"),
    ({"novelty_science_frac": 0.0}, "validated_new"),
])
def test_zero_survivors_give_inf_not_error(overrides, inf_from):
    levels = ["naive_per_dft_stable_verdict", "dft_confirmed_stable", "experimentally_validated", "validated_new"]
    result = funnel(hand_params(**overrides))
    for pl in result["pipelines"].values():
        for lvl in levels[levels.index(inf_from):]:
            assert pl["outputs"][lvl]["usd_per"] == math.inf
            assert pl["outputs"][lvl]["marginal_usd_per"] == math.inf


def test_mlip_rejects_everything():
    b = funnel(hand_params(mlip_tpr=0.0, mlip_fpr=0.0))["pipelines"]["B"]
    assert stage(b, "DFT check")["entering"] == 0
    assert stage(b, "DFT check")["core_h"] == 0
    assert b["outputs"]["dft_confirmed_stable"]["usd_per"] == math.inf
    assert stage(b, "MLIP relax + classify")["core_h"] > 0  # the MLIP spend still happened


def test_all_mlip_runs_fail():
    b = funnel(hand_params(mlip_nonconv_frac=1.0))["pipelines"]["B"]
    assert stage(b, "MLIP relax + classify")["surviving"] == 0
    assert b["outputs"]["validated_new"]["usd_per"] == math.inf


# ---------------------------------------------------------------- input checks and purity


@pytest.mark.parametrize("key, value", [
    ("pool_frac_stable", 1.5), ("dft_wrong_verdict_frac", -0.1), ("price_per_core_hour", -1),
    ("attempts_per_crucible", 0), ("dft_cost_basis", "guess"), ("mlip_steps", 1000),
    ("mlip_filter_basis", "guess"), ("synth_success_multiplier_filtered", 2.5), ("pool_filter_purity", 1.2),
    ("synth_cost_basis", "guess"), ("fa_on_service_fees", "no"),
])
def test_bad_inputs_rejected(key, value):
    with pytest.raises(ValueError):
        funnel(hand_params(**{key: value}))


def test_funnel_does_not_mutate_input():
    p = hand_params()
    before = dict(p)
    funnel(p)
    assert p == before


def test_base_parameters_run_and_compose():
    """The real base case: finite outputs and composing stages for all three pipelines."""
    p = resolve(load())
    result = funnel(p)
    for pl in result["pipelines"].values():
        for out in pl["outputs"].values():
            assert 0 < out["usd_per"] < math.inf
        product = 1.0
        for s in pl["stages"]:
            product *= s["pass_rate"]
        assert pl["stages"][-1]["surviving"] == pytest.approx(pl["stages"][0]["entering"] * product)
        assert stage(pl, "new to MP")["surviving"] == pytest.approx(p["n_candidates"])


def test_mp_novelty_screen():
    """MP-novel share 0.5: generate 100 / 0.5 = 200 structures, 100 survive the free database check.
    Level 3 uses the share of MP-novel candidates also absent elsewhere: 0.4 / 0.5 = 0.8."""
    p = hand_params(pool_frac_novel_mp=0.5, pool_frac_novel_all_db=0.4, pool_gen_core_s=36)
    a = funnel(p)["pipelines"]["A"]
    assert stage(a, "generate")["entering"] == pytest.approx(200)
    assert stage(a, "generate")["core_h"] == pytest.approx(2)  # 200 x 36 s
    assert stage(a, "new to MP")["surviving"] == pytest.approx(100)
    assert stage(a, "new to MP")["core_h"] == 0
    assert stage(a, "new to science")["pass_rate"] == pytest.approx(0.8 * 0.5)


def test_all_db_novelty_cannot_exceed_mp_novelty():
    with pytest.raises(ValueError):
        funnel(hand_params(pool_frac_novel_mp=0.5, pool_frac_novel_all_db=0.6))
