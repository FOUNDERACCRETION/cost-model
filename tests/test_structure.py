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


def test_the_crossing_does_not_depend_on_synthesis_success():
    """S cancels from the paired cost ratio, so the threshold cannot depend on it.

    Level-2 cost is C_i = (c0_i + r a)/S with S shared across pipelines, so the ratio
    C_C/C_B = (c0_C + r a)/(c0_B + r a) has no S in it, and neither does the closed form for d*.
    The threshold depends on the synthesis EXPENDITURE r*a and on the compute coefficients --
    not on success.

    This is pinned because the paper has made this class of error twice. Revision 7 withdrew a
    verification-accuracy result after the unconditional-success repair made w cancel the same
    way; revision 11 then reintroduced an S-dependence claim in the prose of the very section
    that proves S cancels, and an external reviewer caught it. A cancelled parameter is easy to
    reintroduce in words, so the invariance is asserted here rather than left to prose review.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import dft_threshold_sweep
    from src.params import load, resolve

    p = resolve(load())
    base = dft_threshold_sweep(p, points=(54.5,))["crossings"]

    # the full documented range of the three readings, low to high
    for S in (0.051724, 0.20, 0.4375, 0.631579):
        c = dft_threshold_sweep({**p, "synth_success": S}, points=(54.5,))["crossings"]
        for key in ("CB", "AB"):
            for tau in (0.05, 0.10, 0.20):
                if base[key][tau] is None:
                    assert c[key][tau] is None
                else:
                    assert c[key][tau] == pytest.approx(base[key][tau], rel=1e-12), (
                        f"crossing for {key} at tau={tau} moved with S={S}; S must cancel")

    # by contrast it does move with recipes per target, which does not cancel
    r_lo = dft_threshold_sweep({**p, "synth_recipes_per_target": 3.0}, points=(54.5,))["crossings"]
    r_hi = dft_threshold_sweep({**p, "synth_recipes_per_target": 12.0}, points=(54.5,))["crossings"]
    assert r_lo["CB"][0.10] < base["CB"][0.10] < r_hi["CB"][0.10]


def test_synthesis_decision_boundaries_solve_to_parity():
    """Section 5.8's boundaries must actually equalise the two pipelines when substituted back.

    Each boundary is a closed-form solve on the general ratio
        C_i/C_j = [(c0_i + r_i a_i)/(c0_j + r_j a_j)] * (S_j/S_i)
    so the test is the obvious one: put the solved value back and the two costs must coincide. A
    boundary that does not reproduce parity is an algebra error, and this is new algebra.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import synthesis_decision_boundaries, upstream_per_target, boundary_sensitivity
    from src.funnel import synthesis_cost_per_attempt
    from src.params import load, resolve

    p = resolve(load())
    a = synthesis_cost_per_attempt(p)["usd"]
    r = p["synth_recipes_per_target"]
    S = p["synth_success_unconditional"]

    for row in synthesis_decision_boundaries(p)["rows"]:
        c0 = upstream_per_target(p, row["dft"])
        # success boundary: C given the solved success advantage costs what B costs
        cost_C = (c0["C"] + r * a) / (S * row["success_CB"])
        cost_B = (c0["B"] + r * a) / S
        assert cost_C == pytest.approx(cost_B, rel=1e-12)
        # recipe boundary: B given the extra recipes costs what A costs
        cost_B2 = (c0["B"] + (r + row["recipes_AB"]) * a) / S
        cost_A = (c0["A"] + r * a) / S
        assert cost_B2 == pytest.approx(cost_A, rel=1e-12)
        # attempt-cost boundary
        cost_C3 = (c0["C"] + r * a) / S
        cost_B3 = (c0["B"] + r * a * row["attempt_CB"]) / S
        assert cost_C3 == pytest.approx(cost_B3, rel=1e-12)
        # every boundary must exceed parity, since C is dearer than B and A dearer than B
        assert row["success_CB"] > 1.0 and row["recipes_AB"] > 0.0

    # monotone in verification cost: dearer DFT widens the gap the assumption must cover
    rows = synthesis_decision_boundaries(p)["rows"]
    assert all(x["success_CB"] < y["success_CB"] for x, y in zip(rows, rows[1:]))
    assert all(x["recipes_AB"] < y["recipes_AB"] for x, y in zip(rows, rows[1:]))


def test_matching_purity_does_not_quite_equalise_the_pipelines():
    """Setting generative purity to pool purity takes the parity ratio CLOSE to one, not to one.

    Revision 13 printed "exactly 1.000" from a rounded display, and an external reviewer pointed
    out that a rounded value does not establish exact equality. It does not: matching purity
    equalises the slope alpha but not the intercept beta, because C pays a generation cost B never
    pays. The residual is small but nonzero and this test pins its size and sign, which the
    earlier version of this test (approx 1.0 to within 5e-4) was too loose to catch.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import boundary_sensitivity, threshold_coefficients
    from src.params import load, resolve

    p = resolve(load())
    by = {v["variant"]: v for v in boundary_sensitivity(p)}
    ratio = by["generative purity at pool purity, 15.2%"]["success_CB"]
    assert ratio > 1.0, "C still pays a generation cost B does not, so parity is not exact"
    assert ratio == pytest.approx(1.0001989, rel=1e-3)
    # The residual is exactly the intercept gap over Q_B = c0_B + ra, NOT over the bill ra alone:
    # (c0_C + ra)/(c0_B + ra) - 1 = (c0_C - c0_B)/(c0_B + ra), and at matched purity the numerator
    # is the beta gap. Using ra as the denominator is wrong by the size of c0_B, about 1%.
    from stage2 import upstream_per_target
    tc = threshold_coefficients(p)
    beta_gap = tc["beta_usd"]["C"] - tc["beta_usd"]["B"]
    assert beta_gap > 0
    q = {**p, "gen_filter_purity": p["pool_filter_purity"]}
    Q_B = upstream_per_target(q, 54.5)["B"] + tc["synthesis_bill_usd"]
    assert (ratio - 1) == pytest.approx(beta_gap / Q_B, rel=1e-6)
    # and the filter boundary does NOT move with generative purity: A and B never see that pool
    assert (by["generative purity at pool purity, 15.2%"]["recipes_AB"]
            == pytest.approx(by["base"]["recipes_AB"], rel=1e-12))
    # compute price scales the boundary, since it scales c0 against a fixed synthesis bill
    assert by["compute price 100x"]["success_CB"] > by["compute price 10x"]["success_CB"] > by["base"]["success_CB"]


def test_the_current_manuscript_passes_the_numeric_audit():
    """Every generated figure appears in the manuscript, or is waived with a reason.

    Four transcription errors reached revision 12 and none was found by rereading: P(B < A) at
    99.5% against the generator's 99.4% in five places, a level-2 overlap of 98% against 99%, a
    tornado share of 98.8% against 98.6%, and revision 11's title page still reading "revision
    10". Prose review does not catch retyped numbers, so the check runs here.
    """
    import sys, pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "scripts"))
    from audit_numbers import audit

    papers = sorted(root.glob("paper/p1-revision*.md"),
                    key=lambda q: int(re.search(r"revision(\d+)", q.name).group(1)))
    assert papers, "no manuscript found"
    current = papers[-1]
    assert audit(current, root / "results" / "key_numbers.json") == 0, (
        f"{current.name} disagrees with results/key_numbers.json; regenerate or waive")


def test_the_manuscript_revision_label_matches_its_filename():
    """Revision 11 shipped with a title page reading "revision 10". Cheap to prevent."""
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    for q in root.glob("paper/p1-revision*.md"):
        n = int(re.search(r"revision(\d+)", q.name).group(1))
        head = q.read_text()[:2000]
        m = re.search(r'^date:.*revision (\d+)', head, re.M)
        assert m, f"{q.name} has no revision number on its title page"
        assert int(m.group(1)) == n, (
            f"{q.name} title page says revision {m.group(1)}, filename says {n}")


def test_reconstruction_worksheet_reproduces_the_attempt_cost():
    """The worksheet is the reviewer's completion test: a reader reconstructs $271 from it without
    running the code. So the arithmetic printed in it must close, and must match the model."""
    import sys, pathlib as _p, re, subprocess
    root = _p.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from src.funnel import synthesis_cost_per_attempt
    from src.params import load, resolve

    subprocess.run([sys.executable, str(root / "scripts" / "manifest.py")], cwd=root, check=True,
                   capture_output=True)
    text = (root / "results" / "RECONSTRUCTION.md").read_text()
    model = synthesis_cost_per_attempt(resolve(load()))["usd"]

    # the printed total must be the model's
    m = re.search(r"\*\*Total per attempt\*\* \| \| \*\*\$([\d,.]+)\*\*", text)
    assert m, "worksheet has no total line"
    assert float(m.group(1).replace(",", "")) == pytest.approx(model, abs=0.005)

    # and the printed component rows must sum to the printed direct subtotal
    rows = re.findall(r"^\| (?!\*\*)(?!Component)([^|]+)\|[^|]*\| \$([\d,.]+) \|$", text, re.M)
    comps = [float(v.replace(",", "")) for _, v in rows]
    m2 = re.search(r"\*\*Direct subtotal\*\* \|[^|]*\| \*\*\$([\d,.]+)\*\*", text)
    printed_direct = float(m2.group(1).replace(",", ""))
    # the component rows are everything before the subtotal; the indirect row follows it
    assert sum(comps[:7]) == pytest.approx(printed_direct, abs=0.02), (
        f"worksheet components {comps[:7]} do not sum to its printed subtotal {printed_direct}")


def test_parity_and_materiality_boundaries_are_distinct_and_both_correct():
    """Revision 13 reported only parity boundaries and described them as the point where the
    pipelines become unequal. Parity is where they cost the SAME; a materiality boundary is where
    the gap reaches 10%, which the rest of the paper uses as its standard. Conflating them was the
    error, so this test checks that each boundary delivers the gap it claims, and that the two are
    far apart.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import synthesis_decision_boundaries, upstream_per_target
    from src.funnel import synthesis_cost_per_attempt
    from src.params import load, resolve

    p = resolve(load())
    a = synthesis_cost_per_attempt(p)["usd"]
    r = p["synth_recipes_per_target"]
    S = p["synth_success_unconditional"]

    for row in synthesis_decision_boundaries(p)["rows"]:
        c0 = upstream_per_target(p, row["dft"])

        def gap(ci, cj):
            return max(ci, cj) / min(ci, cj) - 1

        cost_B = (c0["B"] + r * a) / S
        # at the parity ratio the gap is zero; at the materiality bounds it is exactly 10%
        assert gap((c0["C"] + r * a) / (S * row["success_CB"]), cost_B) == pytest.approx(0, abs=1e-12)
        for key in ("success_CB_mat_lo", "success_CB_mat_hi"):
            cost_C = (c0["C"] + r * a) / (S * row[key])
            assert gap(cost_C, cost_B) == pytest.approx(0.10, rel=1e-9), key
        # the materiality band must straddle parity
        assert row["success_CB_mat_lo"] < row["success_CB"] < row["success_CB_mat_hi"]

        # recipes: parity gives equal cost, the materiality value gives B exactly 10% dearer
        cost_A = (c0["A"] + r * a) / S
        assert ((c0["B"] + (r + row["recipes_AB"]) * a) / S) == pytest.approx(cost_A, rel=1e-12)
        dearer = (c0["B"] + (r + row["recipes_AB_mat"]) * a) / S
        assert dearer / cost_A == pytest.approx(1.10, rel=1e-9)
        # and it takes far more than parity: at least an order of magnitude more recipes at base
        assert row["recipes_AB_mat"] > row["recipes_AB"]

    base = next(x for x in synthesis_decision_boundaries(p)["rows"] if abs(x["dft"] - 54.5) < 0.6)
    assert base["recipes_AB_mat"] / base["recipes_AB"] > 10, (
        "the materiality boundary must be far from parity, which is the whole point")


def test_overlap_reference_is_a_spread_not_a_single_value():
    """Section 5.7 reports a reference RANGE over resampling replicates, because one resampled
    value is itself a random draw and cannot calibrate a measured coefficient. A reviewer made
    this point about revision 13's single "floor"."""
    import sys, pathlib as _p, math, random
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1]))
    from src import analysis as an

    rng = random.Random(9)
    rows = [{"costs": {lv: {"A": v, "B": v * 1.4, "C": v * 3} for lv in an.LEVELS}}
            for v in (math.exp(rng.gauss(0, 1)) for _ in range(1500))]
    ref = an.overlap_reference({"draws": rows}, "dft_confirmed_stable", bins=60, reps=25)
    assert ref["reps"] == 25
    assert ref["min"] < ref["p50"] < ref["max"], "a reference must have spread, or it is one value"
    assert 0.0 < ref["min"] and ref["max"] <= 1.0
    # the reference must be well above a genuinely different pair, which is what makes it useful
    meas = an.kill_condition({"draws": rows}, bins=60)["dft_confirmed_stable"]["overlap"][("B", "A")]
    assert meas < ref["min"]


def test_success_ratio_boundaries_are_checked_against_the_probability_ceiling():
    """A success RATIO is attainable only while the success RATE it implies stays in [0, 1].

    Revision 14 printed a parity ratio of 2.465 for the hundredfold-compute-price variant without
    noting that at the baseline success rate of 43.75% it implies S_C = 107.8%, which no campaign
    can reach. An external reviewer caught it. The ceiling is 1/S_base, and every displayed
    interval has to be intersected with it; an algebraic boundary is not automatically a feasible
    probability.
    """
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import synthesis_decision_boundaries, boundary_sensitivity
    from src.params import load, resolve

    doc = load()
    p = resolve(doc)
    S = p["synth_success_unconditional"]
    bd = synthesis_decision_boundaries(p)

    assert bd["max_feasible_ratio"] == pytest.approx(1.0 / S)
    # the flag must agree with the arithmetic, row by row, for parity and the upper 10% bound
    for row in bd["rows"]:
        assert row["feasible_CB"] == (S * row["success_CB"] <= 1.0)
        assert row["feasible_CB_mat_hi"] == (S * row["success_CB_mat_hi"] <= 1.0)
        assert row["implied_S_CB"] == pytest.approx(S * row["success_CB"])
    # every row of the published table is feasible at this baseline; the paper says so
    assert all(r["feasible_CB"] and r["feasible_CB_mat_hi"] for r in bd["rows"])

    # and exactly one sensitivity variant is not, which is the one the paper labels
    by = {v["variant"]: v for v in boundary_sensitivity(p)}
    infeasible = [n for n, v in by.items() if not v["feasible"]]
    assert infeasible == ["compute price 100x"], infeasible
    assert by["compute price 100x"]["implied_S_C"] > 1.0
    assert by["compute price 100x"]["implied_S_C"] == pytest.approx(1.078, abs=5e-4)


def test_feasibility_ceiling_moves_with_the_reading():
    """The ceiling is 1/S_base, so which boundaries are attainable depends on which reading sets
    the baseline. Section 5.6 states this, so it is pinned: under the optimistic reading the
    span-top upper materiality bound becomes infeasible, and under the pessimistic one nothing is
    constrained."""
    import sys, pathlib as _p
    sys.path.insert(0, str(_p.Path(__file__).resolve().parents[1] / "scripts"))
    from stage2 import synthesis_decision_boundaries
    from src.params import load, resolve, records

    doc = load()
    p = resolve(doc)
    rec = records(doc)["synth.success_unconditional"]
    top = next(r for r in synthesis_decision_boundaries(p)["rows"] if r["dft"] >= 1000)

    assert rec["high"] * top["success_CB_mat_hi"] > 1.0, "optimistic reading: span-top bound infeasible"
    assert rec["low"] * top["success_CB_mat_hi"] < 1.0, "pessimistic reading: unconstrained"
    assert 1.0 / rec["high"] < 1.0 / p["synth_success_unconditional"] < 1.0 / rec["low"]
