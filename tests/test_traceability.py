"""params/parameters.yaml agrees with what src/derive.py computes from the raw data in data/."""

import pytest

from src.derive import (
    DFT_CSV,
    MLIP_CSV,
    derive_all,
    dft_scf_fit,
    fit_power_law,
    read_csv,
    wilson_interval,
)
from src.params import load, records

REL = 1e-3  # YAML values are rounded to 4 significant figures


@pytest.fixture(scope="module")
def recs():
    return records(load())


@pytest.fixture(scope="module")
def derived():
    return derive_all(ref_atoms=load_ref_atoms())


def load_ref_atoms():
    return records(load())["dft.scf_ref_atoms"]["base"]


def check(rec, low, base, high):
    assert rec["low"] == pytest.approx(low, rel=REL), rec["name"]
    assert rec["base"] == pytest.approx(base, rel=REL), rec["name"]
    assert rec["high"] == pytest.approx(high, rel=REL), rec["name"]


@pytest.mark.parametrize("model", ["chgnet", "mace-mp-0", "m3gnet"])
def test_mlip_step_cost(recs, derived, model):
    d = derived["mlip_step_cost"][model]
    check(recs[f"mlip.{model}.step_cost_per_atom"], d["low"], d["base"], d["high"])


@pytest.mark.parametrize("model", ["chgnet", "mace-mp-0", "m3gnet"])
def test_mlip_nonconvergence(recs, derived, model):
    d = derived["mlip_nonconv"][model]
    rec = recs[f"mlip.{model}.nonconv_frac"]
    check(rec, d["low"], d["base"], d["high"])


def test_mlip_steps(recs, derived):
    d = derived["mlip_steps"]
    rec = recs["mlip.steps_per_relaxation"]
    assert rec["distribution"]["values"] == d["values"]
    check(rec, d["low"], d["base"], d["high"])
    assert recs["mlip.step_cap"]["base"] == derived["mlip_step_cap"]


def test_dft_fit(recs, derived):
    d = derived["dft_scf_fit"]
    check(recs["dft.scf_cost_at_ref"], d["a_low"], d["a"], d["a_high"])
    check(recs["dft.scf_size_exponent"], d["b_low"], d["b"], d["b_high"])


def test_dft_relax_factors(recs, derived):
    d = derived["dft_relax"]
    assert d["n"] == 3
    s, i = d["scf_per_ionic"], d["ionic_steps"]
    check(recs["dft.scf_per_ionic_step"], s["low"], s["base"], s["high"])
    check(recs["dft.ionic_steps"], i["low"], i["base"], i["high"])


def test_n_atoms(recs, derived):
    d = derived["n_atoms"]
    check(recs["batch.n_atoms"], d["low"], d["base"], d["high"])


@pytest.mark.parametrize("model", ["chgnet", "mace-mp-0", "m3gnet"])
def test_matbench_rates(recs, derived, model):
    d = derived["matbench"][model]
    assert recs[f"mlip.{model}.recall"]["base"] == pytest.approx(d["tpr"], rel=REL)
    assert recs[f"mlip.{model}.recall"]["base"] == pytest.approx(d["recall"], abs=1e-3)  # file's rounded value
    assert recs[f"mlip.{model}.false_positive_rate"]["base"] == pytest.approx(d["fpr"], rel=REL)
    assert recs[f"mlip.{model}.precision"]["base"] == pytest.approx(d["precision"])
    assert recs["mlip.matbench_prevalence"]["base"] == pytest.approx(d["prevalence"], rel=REL)


# Szymanski & Bartel 2025 v2: stable counts out of 500 MP-novel structures (strict, 100 meV), structures
# generated to obtain 500 MP-novel ones, and how many of those were absent from all databases.
SB_COUNTS = {
    "ion_exchange": (46, 292, 691, 434), "mattergen": (15, 89, 545, 453), "crystallm": (12, 64, 509, 433),
    "cdvae": (9, 56, 521, 479), "ftcp": (10, 100, 1309, 458),
}


@pytest.mark.parametrize("method", SB_COUNTS)
def test_generation_wilson_ranges(recs, method):
    strict, near, generated, all_db = SB_COUNTS[method]
    checks = {
        "frac_stable_strict": (strict, 500), "frac_stable_100meV": (near, 500),
        "frac_novel_vs_mp": (500, generated), "frac_novel_all_databases": (all_db, generated),
    }
    for key, (k, n) in checks.items():
        lo, hi = wilson_interval(k, n)
        rec = recs[f"gen.{method}.{key}"]
        assert rec["base"] == pytest.approx(k / n, abs=1.5e-3), rec["name"]  # published % rounded to 0.1
        assert rec["low"] == pytest.approx(lo, abs=1e-4), rec["name"]
        assert rec["high"] == pytest.approx(hi, abs=1e-4), rec["name"]


@pytest.mark.parametrize("method, purity, plot_error", [("ion_exchange", 0.152, 0.0), ("mattergen", 0.038, 0.003)])
def test_filter_purity_wilson(recs, method, purity, plot_error):
    """Wilson 95% on n = 300, widened by the plot-reading error for the figure-read MatterGen value."""
    lo = wilson_interval((purity - plot_error) * 300, 300)[0]
    hi = wilson_interval((purity + plot_error) * 300, 300)[1]
    rec = recs[f"gen.{method}.frac_stable_after_chgnet_filter"]
    assert rec["base"] == purity
    assert rec["low"] == pytest.approx(lo, abs=1e-4) and rec["high"] == pytest.approx(hi, abs=1e-4)
    assert rec["evidence_grade"] == ("figure_read" if plot_error else "published")


def test_novelty_bound(recs):
    rec = recs["novelty.science_frac"]
    assert rec["base"] == pytest.approx(wilson_interval(0, 36)[1], abs=1e-4)
    assert rec["high"] == pytest.approx(9 / 36)


def test_derived_synthesis_numbers(recs):
    # Both endpoints must pair a numerator and a denominator from the SAME version of the A-Lab
    # paper. VERIFIED 2026-10-11: the corrected article prints 353 recipes and 57 targets; the
    # original 2023 article prints 355 and 58. The previous version of this test asserted
    # high == 355/57, which paired the original numerator with the corrected denominator -- a
    # cross-version splice that this test was pinning rather than catching.
    # BASE is the middle reading's own multiplicity: Prein et al. attempted each target once.
    # HIGH is A-Lab's corrected 353/57. Both are campaign-reported, not derived.
    assert recs["synth.recipes_per_target"]["base"] == pytest.approx(1.0)
    assert recs["synth.recipes_per_target"]["low"] == pytest.approx(1.0)
    assert recs["synth.recipes_per_target"]["high"] == pytest.approx(353 / 57, rel=REL)
    # A-Lab's two published versions must not be spliced: 355 goes with 58, 353 with 57.
    assert 355 / 58 < 353 / 57
    assert recs["synth.furnace_hours_per_attempt"]["base"] == pytest.approx(17 * 24 * 8 / 353, rel=REL)
    # VERIFIED arXiv:2511.01790: 24 targets attempted, 8 uncharacterisable, 7 of 16 made the
    # target phase. 7/24 is the unconditional rate; 7/16 conditions on characterisability and
    # is not comparable with the other two readings, which count against targets attempted.
    assert recs["synth.success_unconditional"]["base"] == pytest.approx(7 / 24)
    assert recs["synth.success_unconditional"]["high"] == pytest.approx(36 / 57, rel=REL)   # unconditional; was 38/54
    assert recs["synth.furnace_hourly"]["base"] == pytest.approx((3.15 + 3.75) / 2)
    assert recs["synth.labour_attempts_per_week"]["base"] == pytest.approx((10 + 20) / 2)


def test_label_reliability_numbers(recs):
    rec = recs["dft.wrong_verdict_frac"]
    assert rec["base"] == pytest.approx(1 - 0.84)
    assert rec["low"] == pytest.approx(1 - 0.868)
    assert rec["high"] == pytest.approx(1 - 109 / 166, rel=REL)


# ---- derive.py unit tests


def test_wilson_known_values():
    lo, hi = wilson_interval(0, 7)
    assert lo == 0 and hi == pytest.approx(3.8415 / (7 + 3.8415), rel=1e-4)
    lo, hi = wilson_interval(5, 10)
    assert lo + hi == pytest.approx(1.0)


def test_power_law_exact():
    a, b = fit_power_law([(10, 25.0), (20, 100.0), (40, 400.0)], ref_atoms=20)
    assert a == pytest.approx(100) and b == pytest.approx(2)


def test_raw_files_present():
    assert len(read_csv(MLIP_CSV)) > 0 and len(read_csv(DFT_CSV)) > 0
    assert len(dft_scf_fit(read_csv(DFT_CSV), 20)["points"]) == 7


def test_dft_span(recs):
    """Low = our first-hand estimate at the base size; high = MP 2012, 5 calculations x 200; base = geometric midpoint."""
    from src.funnel import dft_cost_per_candidate
    from src.params import resolve

    p = resolve(load(), overrides={"dft_cost_basis": "first_hand"})
    span = recs["dft.cost_per_candidate"]
    assert span["low"] == pytest.approx(dft_cost_per_candidate(p)["first_hand_core_h"], rel=REL)
    assert span["high"] == pytest.approx(5 * recs["dft.mp_2012_per_calculation"]["base"])
    assert span["base"] == pytest.approx((span["low"] * span["high"]) ** 0.5, rel=REL)


def test_indirect_and_tuition(recs):
    assert recs["synth.labour_tuition_remission"]["high"] == pytest.approx(63480 - 29364 * 1.075, abs=1)


def test_precursor_price_blend(recs, derived):
    d = derived["precursors"]
    check(recs["synth.precursor_usd_per_g"], d["low"], d["base"], d["high"])


def test_other_consumables_arithmetic(recs):
    import math

    ethanol = 1 * 267.50 / 1000
    dishes = 3 * 147.50 / 500
    gloves = 2 * 27.75 / 100
    ball_g = 10 * (4 / 3) * math.pi * 0.25**3 * 6.0
    balls = ball_g * 246.50 / 250
    rec = recs["synth.other_consumables_per_attempt"]
    assert rec["base"] == pytest.approx(ethanol + dishes + gloves + balls, abs=0.01)
    assert rec["low"] == pytest.approx(ethanol + dishes + gloves, abs=0.01)


def test_molar_mass():
    from src.derive import molar_mass

    assert molar_mass("Li2CO3") == pytest.approx(73.89, abs=0.01)
    assert molar_mass("In2O3") == pytest.approx(277.63, abs=0.01)
