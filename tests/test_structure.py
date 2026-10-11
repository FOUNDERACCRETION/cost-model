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
    recipes x cost per attempt / ((1 - w) x success): nothing pipeline-specific."""
    pipelines = funnel(p)["pipelines"]
    expected = p["synth_recipes_per_target"] * synthesis_cost_per_attempt(p)["usd"] / (
        (1 - p["dft_wrong_verdict_frac"]) * p["synth_success_given_correct"]
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
    """Compute per validated material = compute per DFT-confirmed stable / synthesis success."""
    for pl in funnel(p)["pipelines"].values():
        out = pl["outputs"]
        assert out["experimentally_validated"]["compute_usd_per"] == pytest.approx(
            out["dft_confirmed_stable"]["usd_per"] / p["synth_success_given_correct"], rel=1e-9
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
