"""Structural results the paper relies on, checked across every parameter level and choice.

Headline: the synthesis cost per experimentally validated material has no
pipeline-dependent term, so level-2 cost differs between pipelines only
through the compute term (README, "Findings").
"""

import itertools
import math

import pytest

from src.analysis import multiplier_for_level2_spread
from src.funnel import funnel, synthesis_cost_per_attempt
from src.params import LEVELS, load, resolve
from tests.test_funnel import hand_params, stage

CHOICES = [
    dict(zip(("mlip_model", "mlip_filter_basis", "generator_c", "dft_cost_basis", "price_basis", "cost_basis"), combo))
    for combo in itertools.product(
        ("chgnet", "mace-mp-0", "m3gnet"), ("measured", "matbench"), ("ion_exchange", "mattergen"),
        ("span", "first_hand"), ("on_demand", "spot"), ("funder", "bench"),
    )
    if combo[0] == "chgnet" or combo[1] == "matbench"  # measured purity exists only for CHGNet
]


def all_cases():
    doc = load()
    for level in LEVELS:
        for choices in CHOICES:
            yield resolve(doc, level, choices)
    yield hand_params(reference_phases=5)  # non-zero fixed cost
    yield hand_params(dft_fraction_sent=0.3, mlip_nonconv_frac=0.6, reference_phases=2)


CASES = list(all_cases())


@pytest.mark.parametrize("p", CASES)
def test_level2_differs_only_through_compute(p):
    """Level-2 synthesis term is the same for A, B and C and equals
    recipes x cost per attempt / success: nothing pipeline-specific.

    CHANGED 2026-10-11: the denominator was (1 - w) x success. Synthesis success is now the
    campaign-observed UNCONDITIONAL rate, which already embeds that campaign's computational
    failures, so dividing by (1 - w) as well charged them twice."""
    pipelines = funnel(p)["pipelines"]
    expected = p["synth_recipes_per_target"] * synthesis_cost_per_attempt(p)["usd"] / (
        p["synth_success_unconditional"]
    )
    for pl in pipelines.values():
        lvl2 = pl["outputs"]["experimentally_validated"]
        assert lvl2["synthesis_usd_per"] == pytest.approx(expected, rel=1e-9)
        assert lvl2["usd_per"] == pytest.approx(lvl2["compute_usd_per"] + lvl2["synthesis_usd_per"], rel=1e-9)
    for x, y in itertools.combinations(pipelines.values(), 2):
        a, b = x["outputs"]["experimentally_validated"], y["outputs"]["experimentally_validated"]
        assert a["usd_per"] - b["usd_per"] == pytest.approx(a["compute_usd_per"] - b["compute_usd_per"], rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("p", CASES)
def test_level2_compute_term_is_level1_over_success(p):
    """Compute per validated material = compute per DFT-confirmed stable x (1 - w) / success.

    Level 1 counts verdicts x (1 - w); level 2 counts verdicts x success. The two output levels
    now use different adjustments on purpose: level 1 asks what a cross-functionally robust
    stable prediction costs, level 2 asks what a material someone actually made costs, and the
    unconditional success rate already contains that campaign's computational failures."""
    for pl in funnel(p)["pipelines"].values():
        out = pl["outputs"]
        factor = (1 - p["dft_wrong_verdict_frac"]) / p["synth_success_unconditional"]
        assert out["experimentally_validated"]["compute_usd_per"] == pytest.approx(
            out["dft_confirmed_stable"]["usd_per"] * factor, rel=1e-9
        )


@pytest.mark.parametrize("p", CASES)
def test_level3_synthesis_term_depends_on_pool_novelty(p):
    """At level 3 the synthesis term is divided by the database-novel share, which differs between
    the pool (A, B) and the generator (C). So level 3 is NOT pipeline-independent when the sources differ."""
    pipelines = funnel(p)["pipelines"]
    shares = {src: p[f"{src}_frac_novel_all_db"] / p[f"{src}_frac_novel_mp"] for src in ("pool", "gen")}
    for key, novel in (("A", shares["pool"]), ("B", shares["pool"]), ("C", shares["gen"])):
        lvl2 = pipelines[key]["outputs"]["experimentally_validated"]
        lvl3 = pipelines[key]["outputs"]["validated_new"]
        share = novel * p["novelty_science_frac"]
        if share == 0:  # low level: Leeman's 0/36 -> no new materials, infinite cost
            assert lvl3["synthesis_usd_per"] == math.inf
        else:
            assert lvl3["synthesis_usd_per"] == pytest.approx(lvl2["synthesis_usd_per"] / share, rel=1e-9)


def test_pools_a_and_b_pay_generation():
    """3,600 core-s per pool structure = 1 core-h; 100 candidates -> 100 core-h in A and B. C uses its own generator."""
    r = funnel(hand_params(pool_gen_core_s=3600, gen_core_s=0.0))["pipelines"]
    for key in "AB":
        assert stage(r[key], "generate")["core_h"] == pytest.approx(100)
        assert r[key]["marginal"]["compute_core_h"] == pytest.approx(
            100 + sum(s["core_h"] for s in r[key]["stages"] if s["stage"] != "generate")
        )
    assert stage(r["C"], "generate")["core_h"] == 0


def test_same_source_makes_b_and_c_identical():
    """With C's generator set to the pool method, B and C are the same pipeline."""
    p = resolve(load(), overrides={"generator_c": "ion_exchange"})
    r = funnel(p)["pipelines"]
    for lvl, out in r["B"]["outputs"].items():
        assert r["C"]["outputs"][lvl]["usd_per"] == pytest.approx(out["usd_per"], rel=1e-12)


@pytest.mark.parametrize("m", [1.0, 1.25, 1.9])
def test_success_multiplier_scales_filtered_level2(m):
    """Multiplier m on B and C success divides their level-2 cost by m (spend unchanged, output x m); A unchanged."""
    p = resolve(load())
    base = funnel(p)["pipelines"]
    scaled = funnel({**p, "synth_success_multiplier_filtered": m})["pipelines"]
    assert scaled["A"]["outputs"]["experimentally_validated"]["usd_per"] == pytest.approx(
        base["A"]["outputs"]["experimentally_validated"]["usd_per"])
    for key in "BC":
        assert scaled[key]["outputs"]["experimentally_validated"]["usd_per"] == pytest.approx(
            base[key]["outputs"]["experimentally_validated"]["usd_per"] / m)
        assert scaled[key]["outputs"]["dft_confirmed_stable"]["usd_per"] == pytest.approx(
            base[key]["outputs"]["dft_confirmed_stable"]["usd_per"])


def test_multiplier_for_2x_spread():
    """The break-even multiplier gives a 2x level-2 spread; with A the most expensive at m = 1 it equals
    2 x min(B, C) / A in closed form."""
    p = resolve(load())
    out = multiplier_for_level2_spread(p, 2.0)
    assert out["spread"] == pytest.approx(2.0, rel=1e-6)
    lvl2 = {k: pl["outputs"]["experimentally_validated"]["usd_per"] for k, pl in funnel(p)["pipelines"].items()}
    if lvl2["A"] >= max(lvl2["B"], lvl2["C"]):
        assert out["multiplier"] == pytest.approx(2 * min(lvl2["B"], lvl2["C"]) / lvl2["A"], rel=1e-6)


def test_multiplier_unreachable_returns_none():
    p = resolve(load())
    out = multiplier_for_level2_spread(p, 1000.0)
    assert out["multiplier"] is None and out["spread"] < 1000


# ---------------------------------------------------------------- DFT threshold sweep (revision 8)


def test_dft_threshold_sweep_is_monotonic_and_ordered():
    """Both pipeline gaps grow with DFT cost, and the generative-pool decision always
    costs more than the filter decision. If either fails, Section 5.5's threshold
    argument does not hold."""
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import dft_threshold_sweep
    from src.params import load, resolve

    sw = dft_threshold_sweep(resolve(load()))
    cb = [r["CB"] for r in sw["rows"]]
    ab = [r["AB"] for r in sw["rows"]]
    assert cb == sorted(cb), "generative-pool gap must grow with DFT cost"
    assert ab == sorted(ab), "filter gap must grow with DFT cost"
    assert all(c >= a for c, a in zip(cb, ab)), "generative gap must exceed filter gap"
    # The threshold claim: the filter decision stays under 10% across the modelled span.
    assert max(ab) < 0.10, "filter decision exceeds 10% inside the span"
    # And the generative decision crosses 10% inside it.
    assert sw["crossings"]["CB"][0.10] < 1000, "generative decision should cross 10% within the span"


def test_threshold_scales_with_synthesis_cost():
    """The materiality crossing is proportional to synthesis expenditure per target, so it
    is accounting-dependent. Revision 9 reports this; if the proportionality broke, the
    Section 5.5 equation d* = tau.r.a / (kC - (1+tau).kB) would no longer hold."""
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import dft_threshold_sweep
    from src.funnel import synthesis_cost_per_attempt
    from src.params import load, resolve

    p = resolve(load())
    variants = [{**p, "synth_cost_basis": "bench"},
                {**p, "indirect_base": "mtdc"},
                p,
                {**p, "synth_indirect_rate": 0.58}]
    ratios = []
    for q in variants:
        cross = dft_threshold_sweep(q, points=(54.5,))["crossings"]["CB"][0.10]
        ratios.append(cross / synthesis_cost_per_attempt(q)["usd"])
    assert max(ratios) / min(ratios) < 1.02, f"crossing not proportional to attempt cost: {ratios}"
    # And the filter crossing is NOT uniformly outside the tested span: under direct-cost
    # accounting it falls inside it, which is why Section 5.5 states that claim conditionally.
    direct = dft_threshold_sweep(variants[0], points=(54.5,))["crossings"]["AB"][0.10]
    assert direct < 1000, "expected the filter crossing to fall inside the span under direct costs"


def test_threshold_equation_coefficients():
    """Section 5.5 prints alpha and beta for the affine compute relation and solves d*.
    This pins both: c0_i(d) = alpha_i d + beta_i must be affine to machine precision, the
    printed coefficients must match, and the closed form must reproduce the numerically
    solved crossing."""
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import dft_threshold_sweep
    from src.funnel import funnel, synthesis_cost_per_attempt
    from src.params import load, resolve

    p = resolve(load())

    def c0(d):
        r = funnel({**p, "dft_cost_per_candidate": d})["pipelines"]
        out = {}
        for k in ("A", "B", "C"):
            pl = r[k]
            o = pl["outputs"]["experimentally_validated"]
            verdicts = next(s["surviving"] for s in pl["stages"] if s["stage"] == "DFT check")
            out[k] = o["compute_usd_per"] * o["count"] / verdicts
        return out

    lo, hi = 10.0, 1000.0
    a, b = c0(lo), c0(hi)
    alpha = {k: (b[k] - a[k]) / (hi - lo) for k in "ABC"}
    beta = {k: a[k] - alpha[k] * lo for k in "ABC"}

    # affine to machine precision
    for d in (3.0, 54.5, 200.0, 500.0):
        act = c0(d)
        for k in "ABC":
            assert abs(alpha[k] * d + beta[k] - act[k]) / act[k] < 1e-12

    # printed coefficients (Section 5.5)
    assert alpha["A"] == pytest.approx(0.485, abs=5e-4)
    assert alpha["B"] == pytest.approx(0.293, abs=5e-4)
    assert alpha["C"] == pytest.approx(1.174, abs=5e-4)
    assert beta["C"] == pytest.approx(0.338, abs=5e-4)

    # closed form reproduces the solved crossing
    tau = 0.10
    bill = p["synth_recipes_per_target"] * synthesis_cost_per_attempt(p)["usd"]
    d_star = (tau * bill + (1 + tau) * beta["B"] - beta["C"]) / (alpha["C"] - (1 + tau) * alpha["B"])
    solved = dft_threshold_sweep(p, points=(54.5,))["crossings"]["CB"][0.10]
    assert d_star == pytest.approx(solved, rel=5e-3)


def test_threshold_coefficient_archive():
    """Revision 11 archives the unrounded coefficients, their residuals and the root comparison.

    Three distinct claims are pinned here, because Section 5.5 makes all three:
      1. the relation is affine to machine precision -- and this is a claim about the UNROUNDED
         coefficients, tested outside the fitted range, not about the printed ones;
      2. the closed form and the model's bisected root are the same number, not merely close;
      3. substituting the printed coefficients moves the root by a stated, small amount.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import threshold_coefficients
    from src.params import load, resolve

    tc = threshold_coefficients(resolve(load()))

    # 1. affine to machine precision, including at 2,000 core-h, twice the top of the swept range
    assert tc["worst_relative_residual"] < 1e-12
    assert max(r["dft_core_h"] for r in tc["residuals"]) >= 2000.0

    # the purity ratio identity of Section 5.3 holds exactly, not approximately
    assert tc["alpha_ratio_C_over_B"] == pytest.approx(4.0, abs=1e-9)

    # 2. closed form == numerical root
    for tau in (0.05, 0.10, 0.20):
        r = tc["roots"][tau]
        assert r["usable"] is True
        assert r["denominator"] > 0
        assert r["closed_form"] >= 0
        assert r["relative_gap"] < 1e-10, "closed form and bisected root must agree to machine precision"

    # 3. rounding the printed coefficients moves the 10% root by well under a core-hour
    shift = abs(tc["roots_from_printed_coefficients"][0.10] - tc["roots"][0.10]["closed_form"])
    assert 0 < shift < 1.0


def test_positive_denominator_is_not_sufficient_for_a_usable_crossing():
    """Section 5.5 says the closed form is valid where the denominator is positive. That is
    necessary, not sufficient: the solution must also be nonnegative to lie in the domain d >= 0.
    With a synthesis bill small enough, the gap already exceeds tau at zero DFT cost and the
    formula returns a negative d* with a positive denominator -- a number to discard, not quote."""
    alpha = {"B": 0.2934210526, "C": 1.1736842105}
    beta = {"B": 0.0015626629, "C": 0.3381360265}
    tau = 0.10
    den = alpha["C"] - (1 + tau) * alpha["B"]
    assert den > 0

    def d_star(bill):
        return (tau * bill + (1 + tau) * beta["B"] - beta["C"]) / den

    assert d_star(1676.05) > 0           # the paper's synthesis bill: a real crossing
    assert d_star(0.0) < 0               # no synthesis spend at all: no crossing in the domain
    # the boundary: the bill at which the crossing sits exactly at d = 0
    bill_zero = (beta["C"] - (1 + tau) * beta["B"]) / tau
    assert d_star(bill_zero) == pytest.approx(0.0, abs=1e-9)
    assert d_star(bill_zero * 0.5) < 0
