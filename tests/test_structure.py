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
    # Both decisions now cross 10% inside the modelled span. That is a CHANGE: while the base
    # case carried A-Lab's recipe budget the filter decision stayed under 10% throughout, and the
    # paper said so. With the middle reading's own single recipe per target the synthesis bill is
    # about a sixth as large, compute is a correspondingly larger share, and both crossings move
    # down by roughly the same factor. The ordering claim survives; the immateriality claim does
    # not, and the manuscript no longer makes it.
    assert sw["crossings"]["CB"][0.10] < sw["crossings"]["AB"][0.10] < 1000, (
        "both decisions cross 10% inside the span, generative first")


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
    for S in (0.051724, 0.20, 0.2916666667, 0.631579):
        c = dft_threshold_sweep({**p, "synth_success": S}, points=(54.5,))["crossings"]
        for key in ("CB", "AB"):
            for tau in (0.05, 0.10, 0.20):
                if base[key][tau] is None:
                    assert c[key][tau] is None
                else:
                    assert c[key][tau] == pytest.approx(base[key][tau], rel=1e-12), (
                        f"crossing for {key} at tau={tau} moved with S={S}; S must cancel")

    # by contrast it does move with recipes per target, which does not cancel
    # Bracketing values must straddle the BASE recipe count, which is the middle reading's own
    # multiplicity of 1.0 per target, not A-Lab's 6.19.
    r_lo = dft_threshold_sweep({**p, "synth_recipes_per_target": 0.5}, points=(54.5,))["crossings"]
    r_hi = dft_threshold_sweep({**p, "synth_recipes_per_target": 3.0}, points=(54.5,))["crossings"]
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

    # p1-final.md is the submission manuscript when it exists; otherwise the highest revision.
    # The appendices and supplements live in a companion document, so both are audited together:
    # a figure is stranded only if it appears in NEITHER, and splitting the manuscript must not
    # silently turn every appendix figure into a waiver.
    final = root / "paper" / "p1-final.md"
    if final.exists():
        current = [final]
    else:
        papers = sorted(root.glob("paper/p1-revision*.md"),
                        key=lambda q: int(re.search(r"revision(\d+)", q.name).group(1)))
        assert papers, "no manuscript found"
        current = [papers[-1]]
    companion = root / "paper" / "p1-appendices.md"
    if companion.exists():
        current.append(companion)
    assert audit(current, root / "results" / "key_numbers.json") == 0, (
        f"{[q.name for q in current]} disagrees with results/key_numbers.json; regenerate or waive")


def test_the_manuscript_revision_label_matches_its_filename():
    """Revision 11 shipped with a title page reading "revision 10". Cheap to prevent."""
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    for q in root.glob("paper/p1-revision*.md"):
        n = int(re.search(r"revision(\d+)", q.name).group(1))
        head = q.read_text(encoding="utf-8")[:2000]
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
    text = (root / "results" / "RECONSTRUCTION.md").read_text(encoding="utf-8")
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


def test_fee_schedule_lists_every_input_to_the_attempt_cost():
    """The fee schedule is headed "every input to the $271 attempt estimate", and that claim has to
    hold three ways.

    It failed all three for several revisions. FEE_ALLOCATION named `synth.precursor_mass_g` while
    the record is `synth.precursor_mass_g_per_attempt`; the writer skipped names it could not
    resolve, so the row disappeared silently; and the paper then quoted the short count, claiming
    fourteen inputs. A file promising completeness omitted the precursor mass that is half of its
    own precursors line.
    """
    import sys, pathlib as _p, csv, importlib.util, inspect, re, subprocess
    root = _p.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from src.params import load, records
    from src import funnel

    spec = importlib.util.spec_from_file_location("_manifest", root / "scripts" / "manifest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    recs = records(load())

    # 1. every allocation key is a real parameter record
    unresolved = [k for k in mod.FEE_ALLOCATION if k not in recs]
    assert not unresolved, f"FEE_ALLOCATION names records that do not exist: {unresolved}"

    # 2. every record the attempt cost reads is in the allocation table. The function takes the
    # resolved namespace, whose names are stripped of their section prefix and sometimes renamed
    # (`synth.indirect_rate` arrives as `synth_indirect_rate`), so the mapping is read out of
    # resolve() rather than guessed from the spelling.
    from src import params as _params
    resolve_map = dict(re.findall(r'"([a-z_0-9]+)":\s*v\("([a-z_0-9.]+)"\)',
                                  inspect.getsource(_params.resolve_with_sources)))
    assert resolve_map.get("precursor_mass_g") == "synth.precursor_mass_g_per_attempt", (
        "the resolve mapping could not be read, so this check would pass vacuously")
    src = inspect.getsource(funnel.synthesis_cost_per_attempt)
    consumed = set(re.findall(r'p\[\"([a-z_]+)\"\]', src))
    # accounting switches select which basis is reported; they are not priced inputs
    consumed -= {"indirect_base", "fa_on_service_fees", "synth_cost_basis"}
    for short in sorted(consumed):
        record = resolve_map.get(short)
        assert record, f"{short!r} is read by the attempt cost but is not resolved from a record"
        assert record in mod.FEE_ALLOCATION, (
            f"synthesis_cost_per_attempt reads {short!r} (record {record!r}) but no "
            f"FEE_ALLOCATION entry covers it, so the fee schedule is incomplete")

    # 3. the written file has one row per entry, and the paper states that count
    subprocess.run([sys.executable, str(root / "scripts" / "manifest.py")], cwd=root, check=True,
                   capture_output=True)
    # read through csv, not by splitting lines: a source_passage field can carry a newline inside
    # its quotes, so physical lines outnumber records
    with open(root / "results" / "fee_schedule_manifest.csv", newline="", encoding="utf-8") as fh:
        records_read = [r for r in csv.reader(fh) if r and not r[0].startswith("#")]
    rows = records_read[1:]                     # drop the header row
    assert len(rows) == len(mod.FEE_ALLOCATION), (
        f"{len(rows)} rows written for {len(mod.FEE_ALLOCATION)} allocation entries")
    words = {14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen"}
    assert f"{words[len(rows)]} attempt-cost inputs" in (root / "paper" / "p1-final.md").read_text(encoding="utf-8"), (
        f"the paper does not say there are {words[len(rows)]} attempt-cost inputs")


def test_the_generator_draws_no_unseeded_randomness():
    """Everything in results/ must reproduce from the pinned seed, and two new sampling loops were
    added on 2026-10-18 that could have broken that silently.

    The bootstrap behind 5.7's precision figures and the attempt-cost median loop both construct
    their own RNG. Seeded off MC_SEED they are reproducible; left bare they would make every
    regeneration differ in its last digits, so the replication package would stop matching the
    paper for reasons no reader could diagnose. Running stage2.py twice and comparing is the direct
    check, but it costs two and a half minutes, so this reads the source instead: every RNG must be
    constructed with an argument, and the module-level generator -- which is seeded by the clock --
    must not be used at all.
    """
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    for name in ("scripts/stage2.py", "src/sampling.py", "src/analysis.py"):
        src = (root / name).read_text(encoding="utf-8")
        body = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))
        bare = re.findall(r"\brandom\.Random\(\s*\)", body)
        assert not bare, f"{name} constructs an unseeded Random()"
        # the module-level functions draw from the global clock-seeded generator
        globals_used = re.findall(r"(?<![\w.])random\.(choice|choices|random|uniform|betavariate"
                                  r"|triangular|shuffle|sample|gauss|normalvariate)\(", body)
        assert not globals_used, (
            f"{name} uses the module-level random generator ({sorted(set(globals_used))}), which is "
            f"seeded from the clock, so results/ would not reproduce")


def test_every_path_the_readme_names_exists():
    """The README is the replication package's front door, and it pointed at three dead files.

    It told a reader to run `scripts/fill_draft.py`, which does not exist: it was deleted on
    2026-10-11 in a commit about recipe counts, with no mention in the message. The layout table
    also listed `tests/test_draft.py`, deleted in the same commit, and `paper/p1-full-draft.md`,
    which the manuscript split replaced months earlier -- while omitting audit_numbers.py,
    manifest.py and test_stage2.py, which do exist and are central.

    The deleted test file is worth a note. It held `test_no_stale_overhead_figures` -- "values from
    before the effective-rate fix must not survive untagged" -- which is the same guard rebuilt
    today as test_no_document_quotes_a_retired_value_as_current. In between, README.md,
    DIAGNOSTICS.md and NOT-FIXED.md all went stale in exactly the way it existed to prevent. Its
    mechanism was stronger than today's, too: the draft carried `<!--k:name-->` tags binding each
    printed figure to one key, so a figure could not be satisfied by another key's value. That is
    the collision problem audit_numbers.py now has to report around.
    """
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    named = set(re.findall(r"`([A-Za-z0-9_./-]+\.(?:py|md|yaml|json|bib|csv|txt))`",
                           (root / "README.md").read_text(encoding="utf-8")))
    assert len(named) > 15, "README paths did not parse, so this check would pass vacuously"

    # Files git ignores are generated, not shipped, so a fresh clone does not have them until the
    # pipeline runs. results/monte_carlo_draws.csv is the case: about 4 MB of per-draw output that
    # the README itself describes as git-ignored and regenerated from the pinned seed. Requiring it
    # made this test fail on a clean checkout until stage2.py had been run once -- which would have
    # been the first thing a replicator saw, for a reason that has nothing to do with the paper.
    import subprocess
    def git_ignored(rel: str) -> bool:
        try:
            return subprocess.run(["git", "check-ignore", "-q", rel], cwd=root).returncode == 0
        except OSError:          # no git on the machine; fall back to requiring the file
            return False

    missing = []
    for name in sorted(named):
        if (root / name).exists():
            continue
        # a bare filename is allowed when it is listed inside a directory's own row, so resolve it
        # against the directories the README documents before calling it absent
        candidates = [name] + [f"{d}/{name}" for d in ("scripts", "src", "tests", "results", "paper",
                                                       "params", "data", "sources")]
        if any((root / c).exists() for c in candidates):
            continue
        if any(git_ignored(c) for c in candidates):
            continue
        missing.append(name)
    assert not missing, (
        "the README names files that do not exist, so a reader following it hits a dead end: "
        + ", ".join(missing))


def test_no_new_key_rides_on_another_keys_quotation():
    """A key the paper never quotes can pass the audit by sharing a value with one it does.

    xp_filter_material_dft_median was 485 and was satisfied only by the digits of thr_alpha_A's
    0.485. The paper had never quoted it, and nothing noticed until the value moved to 473 and the
    match vanished. Four more were found the same way on 2026-10-18 -- two directional materiality
    figures that live in DIAGNOSTICS.md rather than the paper, and the two overlap reference medians,
    where S2 quotes the range and the measured coefficient but not the median.

    The audit's old self-report ("202 of 477 checkable keys share a value") overstated this by a
    factor of twenty: a shared value is harmless when it occurs as often as there are keys claiming
    it. What matters is over-subscription. The eight that remain are all one quantity under two
    names -- span_high_l1 and its _2sf twin, the base row and the boundary that reads off it, levels
    2 and 3 where the figure is identical by construction -- so the ceiling is set at today's count
    and any NEW one has to be looked at and either waived with a reason or quoted.
    """
    import sys, pathlib as _p, json
    root = _p.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "scripts"))
    from audit_numbers import over_subscribed, normalise, load_waivers

    keys = json.loads((root / "results" / "key_numbers.json").read_text(encoding="utf-8"))
    body = normalise("\n".join((root / "paper" / p).read_text(encoding="utf-8")
                               for p in ("p1-final.md", "p1-appendices.md")))
    shared, over, deficit = over_subscribed(keys, load_waivers(), body)
    assert shared, "no checkable values found, so this check would pass vacuously"
    assert deficit <= 8, (
        "a generated figure is being counted as present only because another key put the same "
        "value in the manuscript. Quote it, or waive it with a reason:\n"
        + "\n".join(f"  {v!r}: {body.count(v)} occurrence(s) for {sorted(names)}"
                    for v, names in over.items()))


def test_no_document_quotes_a_retired_value_as_current():
    """Supporting documents were checked by nothing, and one of them was a whole superseded run.

    README.md carried level 2 at $3,653 / $3,625 / $3,756 against the current $1,019 / $983 /
    $1,149, a 1.04x pipeline spread against 1.17x, a synthesis share of 95-99% against 81-94%, the
    pre-correction success rates 38/54 and 7/16, and a novelty value of 25%. All of it had been
    right before 2026-10-11. audit_numbers.py never looked at the file, so the errors sat beside
    generated tables that contradicted them.

    This guards the documents the numeric audit does not cover, against the specific values the
    model has stopped producing. It is narrower than the audit -- a curated list, not a complete
    check -- so paper/retired-values.txt has to be extended whenever a quoted figure is superseded.
    """
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]

    # Current-state documents: these describe the model as it now stands.
    current = [root / "README.md", root / "results" / "RECONSTRUCTION.md",
               root / "paper" / "p1-final.md", root / "paper" / "p1-appendices.md",
               # DIAGNOSTICS.md describes the model as it stands, despite holding historical
               # material: 27 of its figures had gone stale by 2026-10-18, including a block of
               # threshold roots computed from a synthesis bill 6.2x too large. Its genuinely
               # historical tables name their old values on lines that say so, which the
               # `historical` pattern below exempts.
               root / "paper" / "DIAGNOSTICS.md"]
    # Historical by design: a dated snapshot and two records of what was changed and why. Recording
    # a superseded value is their purpose, so they are not scanned.
    #   paper/OVERNIGHT_CHANGES.md, paper/NOT-FIXED.md, paper/VERIFICATION.md

    retired = {}
    for line in (root / "paper" / "retired-values.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        value, _, why = line.partition(":")
        retired[value.strip()] = why.strip()
    assert len(retired) > 20, "retired-values.txt did not parse, so this check would pass vacuously"

    # A line that says a figure CHANGED is allowed to name the old figure.
    historical = re.compile(r"CHANGED|previously|used to|was\s|formerly|corrected|retired|superseded"
                            r"|rejected variant", re.I)

    offenders = []
    for doc in current:
        if not doc.exists():
            continue
        for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if historical.search(line):
                continue
            norm = line.replace("×", "x").replace("–", "-").replace("—", "-")
            for value, why in retired.items():
                # Boundary-aware: a bare substring match fires on "$19.06" for the retired 9.06 and
                # on "57/166" for the retired 7/16, so a retired value must not be flanked by a
                # digit or a decimal point.
                for m in re.finditer(re.escape(value), norm):
                    before = norm[m.start() - 1] if m.start() else " "
                    after = norm[m.end()] if m.end() < len(norm) else " "
                    if before.isdigit() or before == "." or after.isdigit() or after == ".":
                        continue
                    offenders.append((doc.name, i, value, why))
                    break
    assert not offenders, (
        "a document quotes a value the model no longer produces:\n"
        + "\n".join(f"  {d}:{i}  {v!r} -- {w}" for d, i, v, w in offenders))


def test_parameter_notes_do_not_claim_absolute_nonexistence():
    """The paper's negative claims are all scoped to what we searched; the parameter file's were
    not, and the parameter file ships.

    `results/parameter_manifest.csv` carries every source_note verbatim, so a reader of the
    replication package read six flat assertions -- "No source reports a direct error rate against
    experiment", "no source measures recall on them" -- while Limitation 1 of the manuscript says
    the searches were not exhaustive. Worse, `dft.wrong_verdict_frac` said no source breaks the flip
    rate down by chemistry while the very next record IS a chemistry breakdown of the same
    recompute; the paper had been corrected on that point and the note had not.

    A note is prose that no figure check can see, which is why this is a test and not a review step.
    """
    import pathlib as _p, sys, re
    root = _p.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from src.params import load, records

    # an unscoped opener: a claim that nothing exists, stated about the world rather than about
    # what we looked at
    openers = re.compile(
        r"\b(no (?:source|published \w+|national average|study|data|figure)[^.;]{0,100}"
        r"|no \w+ (?:gives|reports|measures|breaks)[^.;]{0,100}"
        r"|NO PUBLISHED [A-Z ]+(?:EXISTS|EXIST)[^.;]{0,60})", re.I)
    # any of these in the same clause makes it a statement about our search instead
    scoped = re.compile(r"we found|was found|were found|our search|in sources/|we could|we looked"
                        r"|not yet|at the time of writing|check\)|within the search scope", re.I)

    offenders = []
    for name, rec in sorted(records(load()).items()):
        note = (rec.get("source_note") or "").replace("\n", " ")
        for m in openers.finditer(note):
            clause = m.group(0)
            if not scoped.search(clause):
                offenders.append((name, clause.strip()[:110]))
    assert not offenders, (
        "parameter notes assert that something does not exist, rather than that we did not find "
        "it. Scope each to the search, as the manuscript does:\n"
        + "\n".join(f"  {n}: ...{c}..." for n, c in offenders))


def test_instrument_fee_facility_count_matches_the_parameter_file():
    """The paper reported eleven US university fee schedules behind the attempt cost. There are
    three.

    The claim entered at revision 6 and survived to revision 15 in the abstract, the contributions
    list and Section 3.5, which also said the parameter file lists each facility "with its facility,
    date, URL, internal and external rate, unit and the quantity we charge" -- a table that did not
    exist. Nothing could catch it: the numeric audit matches only percentages and dollar amounts, so
    a count written as a word was unguarded, and no artifact held the facilities to compare against.
    An inflated evidence base in an abstract is worse than a wrong figure in a table, because it is
    the part a reader uses to decide how much the headline number is worth.

    The table now exists, as `fee_facilities` on the instrument-time records, and this pins the
    paper's count to it.
    """
    import pathlib as _p, yaml, collections, re
    root = _p.Path(__file__).resolve().parents[1]
    doc = yaml.safe_load((root / "params" / "parameters.yaml").read_text(encoding="utf-8"))

    facilities = collections.OrderedDict()
    for rec in doc["parameters"]:
        for f in rec.get("fee_facilities") or []:
            for field in ("facility", "url", "internal_rate", "unit", "charged", "schedule_date"):
                assert field in f, f"{rec['name']} fee_facilities entry lacks {field!r}"
            facilities.setdefault(f["facility"], []).append(rec["name"])
    assert facilities, "no fee_facilities entries found, so this check would pass vacuously"

    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
             8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
    n = len(facilities)
    paper = (root / "paper" / "p1-final.md").read_text(encoding="utf-8")
    assert f"fee schedules of {words[n]} US university facilities" in paper, (
        f"the parameter file carries {n} distinct instrument-fee facilities; Section 3.5 does not "
        f"say {words[n]}")
    assert f"{words[n]} US university recharge schedules" in paper, (
        f"the abstract and contributions list do not say {words[n]} university recharge schedules")
    # and the old inflated count must be gone from the manuscript entirely
    assert not re.search(r"\beleven\b", paper), "the discredited 'eleven' count is back in the paper"

    # each facility's host must actually appear in the record that cites it, so the table cannot
    # drift away from the provenance it claims to summarise
    for rec in doc["parameters"]:
        for f in rec.get("fee_facilities") or []:
            host = f["url"].split("/")[2]
            blob = f"{rec.get('source_url', '')} {rec.get('source_note', '')}"
            assert host in blob, (
                f"{rec['name']} lists facility at {host} but neither its source_url nor its "
                f"source_note mentions that host")


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
    # The two boundaries must be clearly separated, which is the point of reporting both. How far
    # apart depends on the synthesis bill: the ratio was above ten while the base case carried
    # A-Lab's recipe budget, and is smaller now that the base case uses the middle reading's own
    # single recipe per target, because compute is then a larger share of the total.
    assert base["recipes_AB_mat"] > 3 * base["recipes_AB"], (
        "parity and materiality must remain clearly distinct boundaries")


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
    # Which variants are infeasible depends on the baseline success rate, because the ceiling on
    # the ratio is 1/S. Assert the RELATIONSHIP rather than a fixed list, so the test survives a
    # change of reading: a variant is infeasible exactly when its implied rate exceeds one.
    for n, v in by.items():
        assert v["feasible"] == (v["implied_S_C"] <= 1.0), n
        assert v["implied_S_C"] == pytest.approx(S * v["success_CB"], rel=1e-9)
    # the hundredfold-price variant is always the most demanding of those carried
    assert max(by.values(), key=lambda v: v["success_CB"])["variant"] == "compute price 100x"


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


def test_waiver_notes_that_quote_the_manuscript_still_match_it():
    """A waiver that describes prose outlives the prose it describes.

    audit-waivers.txt waived overlap_l1_BA_range as 'quoted in S2 descending, "from 90% to 87% at
    level 1"'. The Monte Carlo draws changed on 2026-10-18 and the key became 88%-91%; the
    manuscript kept saying 90% to 87% (and spans of 3.4 and 1.3 points against 3.1 and 1.9), and
    the audit passed, because the waiver said the figure was quoted in another form and nothing
    asked whether that form was still there. The two span keys passed on their own because "3.1"
    and "1.9" occur in the paper as section numbers.

    So every double-quoted phrase in a waiver line has to appear verbatim in the manuscript. A
    phrase with an ellipsis is a paraphrase, not a quotation, and is skipped.
    """
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    body = "\n".join((root / "paper" / p).read_text(encoding="utf-8") for p in ("p1-final.md", "p1-appendices.md"))
    gone = []
    for line in (root / "paper" / "audit-waivers.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or ":" not in line:
            continue
        for q in re.findall(r'"([^"]+)"', line):
            if "..." not in q and q not in body:
                gone.append((line.split(":")[0], q))
    assert not gone, ("a waiver quotes manuscript text that is no longer there -- the figure it "
                      "waives is probably stale:\n" + "\n".join(f"  {k}: {q!r}" for k, q in gone))


def test_short_bare_number_keys_are_not_matched_by_section_numbers():
    """overlap_l1_BA_span_pp = 3.1 was 'present' because Section 3.1 exists.

    Any key whose value is a bare one-decimal number under 10 can be matched by a section number
    or a figure of speech. For those keys this requires at least one occurrence that is not
    immediately preceded by a heading marker, 'Section', 'Supplement', 'Appendix' or 'A.' and not
    part of a longer number.
    """
    import pathlib as _p, re, json
    root = _p.Path(__file__).resolve().parents[1]
    body = "\n".join((root / "paper" / p).read_text(encoding="utf-8") for p in ("p1-final.md", "p1-appendices.md"))
    keys = json.loads((root / "results" / "key_numbers.json").read_text(encoding="utf-8"))
    waived = {l.split(":")[0].strip() for l in (root / "paper" / "audit-waivers.txt").read_text(encoding="utf-8").splitlines()
              if l and not l.startswith("#") and ":" in l}
    bad = []
    for name, val in keys.items():
        if name in waived or not re.fullmatch(r"\d\.\d", str(val)):
            continue
        real = [m for m in re.finditer(rf"(?<![\d.])({re.escape(str(val))})(?![\d])", body)
                if not re.search(r"(^|\n)#+\s*$|(Section|Supplement|Appendix|S|A\.|§)\s*$",
                                 body[max(0, m.start() - 12):m.start()])]
        if not real:
            bad.append((name, val))
    assert not bad, ("these keys match the manuscript only at a section number or not at all:\n"
                     + "\n".join(f"  {n} = {v}" for n, v in bad))


def test_short_figures_are_quoted_in_the_sentence_that_owns_them():
    """The numeric audit checks presence anywhere; for short figures that proves nothing.

    On 2026-10-22, 5.4 quoted the 5% threshold distribution as "10 to 382 with a median of 78;
    at 20%, 43 to 1,877 with a median of 328. In 14 of 1,500 draws" against generated 338, 41,
    329 and 12; 5.6 quoted 60 and 999 against 73 and 1,000; 5.7 quoted 1.07 against 1.08 (behind
    a waiver saying "quoted as 1.07"); 5.8 quoted 16, 37 and 61 against 17, 39 and 64. Every
    stale figure's replacement occurred somewhere else in the manuscript, so the audit passed.

    paper/audit-anchors.txt pins each such key to the phrase that quotes it. The phrase, with
    the key's current value substituted, must occur verbatim. "--" is read as an en dash.
    """
    import pathlib as _p, json
    root = _p.Path(__file__).resolve().parents[1]
    keys = json.loads((root / "results" / "key_numbers.json").read_text(encoding="utf-8"))
    body = "\n".join((root / "paper" / p).read_text(encoding="utf-8") for p in ("p1-final.md", "p1-appendices.md"))
    body = body.replace("--", "–")
    missing, unknown = [], []
    n = 0
    for line in (root / "paper" / "audit-anchors.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, tpl = (s.strip() for s in line.split("||", 1))
        if key not in keys:
            unknown.append(key)
            continue
        n += 1
        phrase = tpl.replace("{v}", str(keys[key]))
        if phrase not in body:
            missing.append((key, phrase))
    assert not unknown, f"anchors name keys the model no longer produces: {unknown}"
    assert n >= 30, "the anchor file has lost most of its lines"
    assert not missing, ("a short figure is stale in its own sentence (the audit's anywhere-match "
                         "would not have caught this):\n"
                         + "\n".join(f"  {k}: expected {p!r}" for k, p in missing))


def test_every_text_file_access_names_its_encoding():
    """The package failed on its first Windows run, 2026-10-22, with 5 of 765 tests.

    Every read went through the platform default encoding, which on Windows is cp1252, so each
    en dash in the manuscript became three characters, '1.17x' with a multiplication sign did not
    match, and DIAGNOSTICS.md raised UnicodeDecodeError at byte 0x81. The model was untouched; the
    checks around it were unreadable. Every open(), read_text() and write_text() in src/, scripts/
    and tests/ now names utf-8, and the suite is run under LC_ALL=C before a release.
    """
    import pathlib as _p, re
    root = _p.Path(__file__).resolve().parents[1]
    import ast
    bad = []
    for d in ("src", "scripts", "tests"):
        for f in sorted((root / d).glob("*.py")):
            src = f.read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(src)):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
                if name not in ("open", "read_text", "write_text"):
                    continue
                kws = {k.arg for k in node.keywords}
                modes = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                if "encoding" in kws or any("b" in m for m in modes):
                    continue
                bad.append(f"{f.relative_to(root)}:{node.lineno}: {ast.get_source_segment(src, node)[:80]}")
    assert not bad, "text file access without an explicit encoding:\n" + "\n".join(bad)
