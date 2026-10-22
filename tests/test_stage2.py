"""Tests for stage 2: sampling (distributions and joint structures) and the analysis layer."""

import math
import random
import re
import statistics

import pytest

from src import analysis as an
from src.funnel import funnel
from src.params import load, records, resolve
from src.sampling import (
    apply_worldview,
    beta_counts,
    bootstrap_mean,
    draw_pool,
    log_triangular,
    recipes_for_success,
    record_to_input,
    sampler,
)
from tests.test_funnel import hand_params


@pytest.fixture(scope="module")
def doc():
    return load()


@pytest.fixture(scope="module")
def draws(doc):
    draw = sampler(doc)
    rng = random.Random(7)
    return [draw(rng) for _ in range(3000)]


def corr(xs, ys):
    return statistics.correlation(xs, ys)


# ---------------------------------------------------------------- distributions


def test_monte_carlo_block_matches_records(doc):
    """Triangular / log-uniform parameters use the record's low/base/high; empirical lists match the data."""
    from src.derive import derive_all

    recs = records(doc)
    d = derive_all()
    for name, spec in doc["monte_carlo"]["distributions"].items():
        assert name in recs, name
        assert spec["reason"].strip(), name
    dist = doc["monte_carlo"]["distributions"]
    assert dist["mlip.steps_per_relaxation"]["values"] == d["mlip_steps"]["values"]
    assert dist["batch.n_atoms"]["values"] == d["n_atoms"]["values"]
    per_target = d["precursors"]["per_target"]
    assert dist["synth.precursor_usd_per_g"]["values"] == pytest.approx([round(v["base"], 4) for v in per_target.values()])
    blend_median = statistics.median(dist["synth.precursor_usd_per_g"]["values"])
    assert blend_median == pytest.approx(recs["synth.precursor_usd_per_g"]["base"], rel=1e-3)


def test_joint_counts_match_records(doc):
    recs = records(doc)
    for method, c in doc["monte_carlo"]["joint"]["pools"]["counts"].items():
        assert c["stable"] / c["n_stable"] == pytest.approx(recs[f"gen.{method}.frac_stable_strict"]["base"])
        assert c["purity"] == recs[f"gen.{method}.frac_stable_after_chgnet_filter"]["base"]
        assert c["n_stable"] / c["generated"] == pytest.approx(recs[f"gen.{method}.frac_novel_vs_mp"]["base"], abs=1.5e-3)
        assert c["all_db"] / c["generated"] == pytest.approx(recs[f"gen.{method}.frac_novel_all_databases"]["base"], abs=1.5e-3)


def test_worldview_counts_match_records(doc):
    recs = records(doc)
    r = doc["monte_carlo"]["joint"]["worldview"]["readings"]
    s = recs["synth.success_unconditional"]
    assert r["optimistic_alab"]["success"]["k"] / r["optimistic_alab"]["success"]["n"] == pytest.approx(s["high"], rel=1e-3)
    assert r["middle_prein"]["success"]["k"] / r["middle_prein"]["success"]["n"] == pytest.approx(s["base"])
    assert r["pessimistic_leeman"]["success"]["k"] / r["pessimistic_leeman"]["success"]["n"] == pytest.approx(3 / 58)
    w = recs["dft.wrong_verdict_frac"]
    assert r["pessimistic_leeman"]["wrong_verdict"]["k"] / r["pessimistic_leeman"]["wrong_verdict"]["n"] == pytest.approx(w["high"], rel=1e-3)
    # The optimistic and middle readings draw the wrong-verdict share uniformly over the record's
    # published endpoints rather than from counts, since GNoME reports rates without counts.
    for name in ("optimistic_alab", "middle_prein"):
        spec = r[name]["wrong_verdict"]
        assert spec["type"] == "uniform", f"{name} should draw w uniformly over the published range"
        assert spec["low"] == pytest.approx(w["low"]) and spec["high"] == pytest.approx(w["base"])

    # NOVELTY. This test existed to tie the worldview block to the parameter records and had no
    # novelty assertion at all, which is how the optimistic reading went on drawing
    # beta_counts(9, 36) for a week after novelty.science_frac was corrected away from that
    # subtraction. Only one novelty count is published for this campaign and it is zero, so every
    # reading must inherit the same one -- a reading with a count of its own means someone has
    # found a second novelty measurement, which would be a change to the paper, not to a draw.
    nov = recs["novelty.science_frac"]
    assert nov["low"] == pytest.approx(0.0), (
        "the published novelty verdict is zero; the record's low endpoint should say so")
    counts = {name: (rd["novelty"]["k"], rd["novelty"]["n"]) for name, rd in r.items()}
    assert set(counts.values()) == {(0, 36)}, (
        f"every reading must draw novelty from the one published count, 0 of 36; got {counts}")
    assert sum(doc["monte_carlo"]["joint"]["worldview"]["weights"].values()) == pytest.approx(1.0)


def test_record_to_input_one_to_one(doc):
    mapping = record_to_input(doc, doc["monte_carlo"]["distributions"])
    assert len(set(mapping.values())) == len(mapping)


def test_marginal_draws_within_bounds(doc, draws):
    recs = records(doc)
    mapping = record_to_input(doc, doc["monte_carlo"]["distributions"])
    for name, spec in doc["monte_carlo"]["distributions"].items():
        if spec["type"] in ("triangular", "log_triangular", "log_uniform"):
            vals = [p[mapping[name]] for p, _ in draws]
            assert min(vals) >= recs[name]["low"] - 1e-12 and max(vals) <= recs[name]["high"] + 1e-12, name


def test_helpers():
    rng = random.Random(1)
    assert statistics.fmean(beta_counts(rng, 46, 500) for _ in range(4000)) == pytest.approx(46.5 / 501, rel=0.02)
    vals = [log_triangular(rng, 10, 20, 100) for _ in range(4000)]
    assert 10 <= min(vals) and max(vals) <= 100
    assert statistics.median(vals) == pytest.approx(10 ** ((1 + 2) / 2 * 0.5 + 0.5), rel=0.5)  # loose: log-space centre
    assert bootstrap_mean(rng, [5, 5, 5]) == 5


# ---------------------------------------------------------------- joint structures


def test_recipes_budget_model(doc):
    """Reproduces A-Lab's 6.19 recipes per target at A-Lab's 36/57 per-target success; falls as success rises."""
    budget = records(doc)["synth.recipe_budget"]["base"]
    assert recipes_for_success(36 / 57, budget) == pytest.approx(353 / 57, rel=1e-4)  # budget stored to 4 s.f.
    q0 = (36 / 57) / (353 / 57)
    assert budget == pytest.approx(math.log(1 - 36 / 57) / math.log(1 - q0), rel=1e-3)
    assert recipes_for_success(0.0, budget) == budget
    assert recipes_for_success(1.0, budget) == 1.0
    xs = [recipes_for_success(s / 20, budget) for s in range(1, 20)]
    assert all(a > b for a, b in zip(xs, xs[1:]))
    # No reading uses this fallback any more: all three report an experiment count. It stays for a
    # reading that reports a success rate without one. Pinning the size of the error it would have
    # introduced in the pessimistic reading keeps that decision visible: deriving at 3/58 charges
    # more than two extra recipes per target against the 6.12 the campaign actually ran.
    assert recipes_for_success(3 / 58, budget) - 355 / 58 > 2.5


def test_every_reading_pins_its_own_reported_recipe_count(draws):
    """All three readings now report a recipe multiplicity, so none of them derives one. Each draw
    from a reading must carry that reading's published count exactly, whatever success rate the
    draw took: the recipe count is a campaign fact, and tying it to the drawn success rate would
    reintroduce the splice this test exists to catch. The two readings of the A-Lab campaign carry
    its experiment count as each version printed it (353/57 and 355/58); Prein et al. attempted
    each of 24 targets once.
    """
    expected = {"optimistic_alab": 6.193, "middle_prein": 1.0, "pessimistic_leeman": 6.1207}
    by_reading = {}
    for p, info in draws:
        by_reading.setdefault(info["worldview"], []).append(p["synth_recipes_per_target"])

    assert set(by_reading) == set(expected), sorted(by_reading)
    for name, recipes in by_reading.items():
        assert min(recipes) == pytest.approx(expected[name]), name
        assert max(recipes) == pytest.approx(expected[name]), name


def test_purity_drawn_with_prevalence(draws):
    for prefix in ("pool", "gen"):
        prev = [p[f"{prefix}_frac_stable"] for p, _ in draws]
        purity = [p[f"{prefix}_filter_purity"] for p, _ in draws]
        assert corr(prev, purity) > 0.3, prefix


def test_pool_draw_centres(doc):
    rng = random.Random(3)
    c = doc["monte_carlo"]["joint"]["pools"]["counts"]["ion_exchange"]
    ds = [draw_pool(rng, c) for _ in range(5000)]
    assert statistics.median(d["purity"] / d["prevalence"] for d in ds) == pytest.approx(0.152 / 0.092, rel=0.02)
    assert all(d["all_db"] <= d["novel_mp"] for d in ds)


def test_worldview_draws_are_tied_by_reading_but_novelty_carries_no_reading_signal(draws):
    """Each draw takes success and the wrong-verdict share from one reading; novelty cannot.

    This test used to assert corr(success, novelty) > 0.3, and it passed -- because the optimistic
    reading drew novelty from beta_counts(9, 36), Leeman's "9 of 36 not attributed to known
    phases". That 9 is a subtraction of overlapping error categories (18 + 8 + 24 + 3 = 53
    attributions over 36 compounds), so it counts nothing, and novelty.science_frac was corrected
    away from it on 2026-10-11. The Monte Carlo was not, so the test went on certifying a
    correlation that the invalid count had manufactured: a mean novelty of 25.7% for the optimistic
    reading against 1.4% for the other two, while the manuscript told readers every nonzero novelty
    value it uses is a bound on a zero count.

    There is one published novelty count for this campaign and it is zero, so every reading now
    inherits it and novelty carries no reading signal at all. What the worldview tie genuinely
    binds is the wrong-verdict share, which IS reading-dependent -- GNoME's 13.2-16% flip range for
    A-Lab and Prein against An et al.'s 57 of 166 for Leeman -- so low success comes with a high
    wrong-verdict share, strongly and for a reason in the sources.
    """
    success = [p["synth_success_unconditional"] for p, _ in draws]
    novelty = [p["novelty_science_frac"] for p, _ in draws]
    wrong = [p["dft_wrong_verdict_frac"] for p, _ in draws]

    assert abs(corr(success, novelty)) < 0.1, (
        "novelty is correlated with success, so some reading is drawing it from a count of its own. "
        "Only one novelty count exists (0 of 36) and all three readings must inherit it")
    assert corr(success, wrong) < -0.5, (
        "the wrong-verdict share should fall as success rises: it is drawn from the same reading")

    # and the readings stay cleanly separated in the quantity they actually disagree about
    leeman = [p for p, info in draws if info["worldview"] == "pessimistic_leeman"]
    alab = [p for p, info in draws if info["worldview"] == "optimistic_alab"]
    assert max(p["synth_success_unconditional"] for p in leeman) < min(p["synth_success_unconditional"] for p in alab)


def test_apply_worldview(doc):
    p = resolve(doc)
    q = apply_worldview(p, {"success": 0.5, "novelty": 0.1, "wrong_verdict": 0.2}, 9.28)
    assert q["synth_success_unconditional"] == 0.5 and q["novelty_science_frac"] == 0.1
    # recipes now key on unconditional success (0.5), not (1 - w) x success (0.4).
    assert q["synth_recipes_per_target"] == pytest.approx(recipes_for_success(0.5, 9.28))
    assert p["synth_success_unconditional"] != 0.5  # input untouched


# ---------------------------------------------------------------- analysis


def test_daf_definitions(doc):
    p = resolve(doc)
    e = an.enrichment(doc, p)
    assert e["pool"]["daf_measured"] == pytest.approx(p["pool_filter_purity"] / p["pool_frac_stable"])
    assert e["gen"]["daf_measured"] == pytest.approx(p["gen_filter_purity"] / p["gen_frac_stable"])
    recs = records(doc)
    # Matbench's own rates at its own (confusion-matrix) prevalence reproduce its precision / prevalence.
    prev = recs["mlip.matbench_prevalence"]["base"]
    from src.funnel import mlip_pass_rate

    daf = mlip_pass_rate(prev, p["mlip_tpr"], p["mlip_fpr"])["precision"] / prev
    assert daf == pytest.approx(recs["mlip.chgnet.precision"]["base"] / prev, rel=2e-3)
    assert recs["mlip.chgnet.daf_wbm"]["base"] == pytest.approx(
        recs["mlip.chgnet.precision"]["base"] / recs["mlip.matbench_prevalence_paper"]["base"], rel=2e-3)


def test_tornado(doc):
    t = an.tornado(doc)
    p = resolve(doc)
    base = an.costs(p)
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            rows = t[lvl][k]
            ok = [r for r in rows if r["status"] == "ok"]
            assert [r["swing"] for r in ok] == sorted((r["swing"] for r in ok), reverse=True)
            assert sum(r["share"] for r in ok if r["swing"] > 0) == pytest.approx(1.0)
            top = an.top_share(rows)
            assert sum(r["share"] for r in ok if r["name"] in top) >= 0.8
    # A parameter C never reads must not make A's row inconsistent.
    row = next(r for r in t["dft_confirmed_stable"]["A"] if r["name"] == "gen.mattergen.frac_stable_after_chgnet_filter")
    assert row["status"] == "ok" and row["swing"] == 0
    row = next(r for r in t["experimentally_validated"]["B"] if r["name"] == "dft.cost_per_candidate")
    recs = records(doc)
    lo = an.costs({**p, "dft_cost_per_candidate": recs["dft.cost_per_candidate"]["low"]})["experimentally_validated"]["B"]
    assert row["low_cost"] == pytest.approx(lo)
    assert base["experimentally_validated"]["B"] > 0


@pytest.mark.parametrize("overrides", [{}, {"dft_cost_per_candidate": 1000.0}, {"synth_success_unconditional": 0.05}])
def test_synthesis_elasticities_structural(doc, overrides):
    """Level-2 synthesis cost = recipes x cost per attempt / ((1 - w) success): a structural property.

    Success has elasticity exactly -1 (it divides compute too). Recipes and cost per attempt agree with each other
    and equal the synthesis share; they differ from success by exactly the compute share.
    """
    p = {**resolve(doc), **overrides}
    el = an.log_elasticities(p)
    for k in an.PIPELINES:
        lvl2 = funnel(p)["pipelines"][k]["outputs"]["experimentally_validated"]
        synth_share = lvl2["synthesis_usd_per"] / lvl2["usd_per"]
        succ = el["synthesis success rate"][k]["elasticity"]
        rec = el["recipes per target"][k]["elasticity"]
        att = el["cost per synthesis attempt"][k]["elasticity"]
        assert succ == pytest.approx(-1.0, abs=1e-6)
        assert rec == pytest.approx(att, abs=1e-6)
        assert rec == pytest.approx(synth_share, abs=1e-6)
        assert abs(succ) - rec == pytest.approx(1 - synth_share, abs=1e-6)
        for name in ("synthesis success rate", "recipes per target", "cost per synthesis attempt"):
            assert el[name][k]["return"] > 0  # every improvement lowers cost


def test_compute_elasticities(doc):
    p = resolve(doc)
    el = an.log_elasticities(p)
    for k in an.PIPELINES:
        lvl2 = funnel(p)["pipelines"][k]["outputs"]["experimentally_validated"]
        compute_share = lvl2["compute_usd_per"] / lvl2["usd_per"]
        assert el["compute price"][k]["elasticity"] == pytest.approx(compute_share, abs=1e-6)
    assert el["MLIP precision (filter purity)"]["A"]["elasticity"] == 0


def test_spot_switch(doc):
    """Spot changes only compute dollars: the level-2 change equals the compute share times the discount."""
    p = resolve(doc)
    sp = an.spot_switch(doc, p)
    recs = records(doc)
    assert sp["cpu_discount"] == pytest.approx(1 - recs["price.cpu.spot"]["base"] / recs["price.cpu.on_demand"]["base"])
    r = funnel(p)["pipelines"]
    for k in an.PIPELINES:
        lvl2 = r[k]["outputs"]["experimentally_validated"]
        n = lvl2["count"]
        cpu = r[k]["marginal"]["compute_core_h"] * p["price_per_core_hour"] * sp["cpu_discount"]
        gpu = r[k]["marginal"]["compute_gpu_h"] * p["price_per_gpu_hour"] * sp["gpu_discount"]
        assert sp["change"][k] == pytest.approx(-(cpu + gpu) / n / lvl2["usd_per"], rel=1e-9)


def test_reweighting_reproduces_conditional(doc):
    mc = an.monte_carlo(doc, n=600, seed=11)
    bw = doc["monte_carlo"]["joint"]["worldview"]["weights"]
    only = {k: (1.0 if k == "middle_prein" else 0.0) for k in bw}
    xs = [d["costs"]["experimentally_validated"]["B"] for d in mc["draws"] if d["worldview"] == "middle_prein"]
    got = an.reweighted(mc, only, bw, "experimentally_validated", "B", 50)
    assert min(abs(got - x) for x in xs) == 0  # a draw from that reading
    assert abs(sum(x <= got for x in xs) / len(xs) - 0.5) < 0.01


def test_kill_condition_on_synthetic_draws():
    """Two pipelines that always differ by 50% separate; two identical ones do not."""
    rows = []
    rng = random.Random(0)
    for _ in range(2000):
        base = math.exp(rng.gauss(0, 1))
        c = {lvl: {"A": base, "B": base / 1.5, "C": base} for lvl in an.LEVELS}
        rows.append({"costs": c})
    k = an.kill_condition({"draws": rows})
    lvl = k["dft_confirmed_stable"]
    assert lvl["p_lt"][("B", "A")] == 1.0
    assert lvl["p_material"][("B", "A")] == 1.0
    assert lvl["p_lt"][("C", "A")] == 0.0 and lvl["p_material"][("C", "A")] == 0.0
    assert lvl["overlap"][("C", "A")] == pytest.approx(1.0)
    assert 0.5 < lvl["overlap"][("B", "A")] < 1.0  # shared uncertainty makes marginals overlap


def test_monte_carlo_small(doc):
    mc = an.monte_carlo(doc, n=300, seed=5)
    assert len(mc["draws"]) == 300
    s = an.summarise(mc)
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            q = s[lvl][k]
            assert q[5] <= q[50] <= q[95]
    again = an.monte_carlo(doc, n=300, seed=5)
    assert [d["costs"] for d in again["draws"]] == [d["costs"] for d in mc["draws"]]  # reproducible


def test_chemistry_sweep_of_w_moves_level_1_only(doc):
    """Section 3.4's chemistry sweep must move level 1 and leave level 2 exactly where it was.

    The sweep exists to report that the cross-functional flip rate is chemistry-dependent -- a
    companion audit finds disjoint composition cells from 4.0% to 30.7% at fixed element count --
    and it doubles as the clearest demonstration of the cancellation the paper argues for: a
    parameter that moves cost per robust prediction by tens of percent must move cost per
    validated material by nothing at all.

    test_level2_is_independent_of_w covers the cancellation on hand-built parameters. This covers
    it on the REAL parameter file at the REAL cell endpoints, which is what the paper prints, and
    additionally pins that the endpoints come from the parameter record rather than the prose.
    """
    from scripts.stage2 import chemistry_sweep_of_w

    rec = records(doc)["dft.wrong_verdict_chemistry_cells"]
    assert rec["role"] == "cross_check", "the cell range is reported, never fed to the model"
    assert rec["low"] == pytest.approx(0.040) and rec["high"] == pytest.approx(0.307)

    p = resolve(doc)
    sw = chemistry_sweep_of_w(p, [("lo", rec["low"]), ("base", rec["base"]), ("hi", rec["high"])])

    l2 = [r["l2"]["B"] for r in sw["rows"]]
    assert max(l2) == pytest.approx(min(l2), rel=1e-12), "w must cancel from level 2 at every cell"
    assert sw["l2_ratio"] == pytest.approx(1.0, abs=1e-9)

    l1 = [r["l1"]["B"] for r in sw["rows"]]
    assert all(a < b for a, b in zip(l1, l1[1:])), "level 1 must rise with the flip rate"
    # 1/(1-w) is the whole of the dependence, so the ratio across the cells is exactly that.
    assert sw["l1_ratio"] == pytest.approx((1 - rec["low"]) / (1 - rec["high"]), rel=1e-9)
    assert sw["l1_ratio"] > 1.3, "the reported spread is tens of percent, not a rounding effect"


def test_scenarios(doc):
    sc = an.scenarios(doc)
    b = {k: v["costs"]["experimentally_validated"]["B"] for k, v in sc.items()}
    # COST IS NOT ORDERED BY READING. Prein et al. report a lower success rate than A-Lab but
    # attempted each target once, so their single recipe per target outweighs the lower success
    # and makes that reading the cheapest. An earlier version of this test asserted
    # optimistic < middle < pessimistic, which held only while the middle reading was charged
    # A-Lab's recipe budget it never used.
    assert b["middle_prein"] < b["optimistic_alab"] < b["pessimistic_leeman"]
    assert sc["middle_prein"]["recipes"] == pytest.approx(1.0)
    assert sc["pessimistic_leeman"]["costs"]["validated_new"]["B"] == math.inf
    # The two readings of the A-Lab campaign carry its experiment count as each version printed it,
    # so they sit within 2% of each other rather than being ordered by optimism. 353/57 against
    # 355/58: the correction removed one target and two experiments, which raises the mean slightly.
    r_opt, r_pes = sc["optimistic_alab"]["recipes"], sc["pessimistic_leeman"]["recipes"]
    assert r_opt > r_pes
    assert abs(r_opt / r_pes - 1) < 0.02
    # The spread across readings is wider than the success ratio alone, because the cheapest reading
    # is cheap on both counts at once.
    assert max(b.values()) / min(b.values()) > 25


def test_fixed_cost_payback(doc):
    p = resolve(doc)
    fc = an.fixed_cost_payback(doc, p)
    assert fc["payback_candidates"] == pytest.approx(fc["extra_fixed_core_h"] / fc["saving_core_h_per_candidate"])
    assert fc["saving_core_h_per_candidate"] > 0


def test_attempt_cost_thresholds_closed_form():
    """At the returned attempt cost, compute is exactly the requested share and the spread exactly the target."""
    p = hand_params(xrd_cost_per_sample=100.0, dft_cost_per_candidate=200.0)
    t = an.attempt_cost_thresholds(p, 0.10, 1.10)
    for k in an.PIPELINES:
        a = t["attempt_for_compute_share"][k]
        q = {**p, "xrd_cost_per_sample": a}
        lvl2 = funnel(q)["pipelines"][k]["outputs"]["experimentally_validated"]
        assert lvl2["compute_usd_per"] / lvl2["usd_per"] == pytest.approx(0.10)
    a = t["attempt_for_spread"]
    q = {**p, "xrd_cost_per_sample": a}
    c = [funnel(q)["pipelines"][k]["outputs"]["experimentally_validated"]["usd_per"] for k in an.PIPELINES]
    assert max(c) / min(c) == pytest.approx(1.10)


def test_purity_for_parity(doc):
    p = resolve(doc)
    res = an.purity_for_parity(p, "B")
    c = an.costs({**p, "gen_filter_purity": res["purity"]})["dft_confirmed_stable"]
    assert c["C"] == pytest.approx(c["B"], rel=1e-6)
    c2 = an.costs({**p, "gen_filter_purity": res["purity"]})["experimentally_validated"]
    assert c2["C"] == pytest.approx(c2["B"], rel=1e-6)  # parity at level 1 implies parity at level 2


# ---------------------------------------------------------------- README stays generated


def test_readme_generated_blocks_filled():
    text = open("README.md", encoding="utf-8").read()
    names = re.findall(r"<!-- generated:(\w+):begin -->", text)
    assert set(names) == {"headline", "spot", "daf", "returns", "kill", "montecarlo", "tornado", "breakevens",
                          "distributions", "basecase", "costbasis", "dftspan", "attempt", "level3", "multiplier",
                          "boundaries"}
    for name in names:
        body = re.search(rf"<!-- generated:{name}:begin -->\n(.*?)<!-- generated:{name}:end -->", text, re.S).group(1)
        assert body.strip(), f"generated block {name} is empty: run scripts/stage2.py"


def test_readme_headline_numbers_match_model(doc):
    """The hand-written stage-1 findings quote the model's current base-case numbers."""
    text = open("README.md", encoding="utf-8").read()
    c = an.costs(resolve(doc))

    def money(x):
        return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}"

    for lvl in ("dft_confirmed_stable", "experimentally_validated"):
        for k in an.PIPELINES:
            assert money(c[lvl][k]) in text, (lvl, k, money(c[lvl][k]))


def test_readme_scoped_level2_sentence(doc):
    """The level-2 headline quotes the spread at the base and at the top of the DFT span."""
    text = open("README.md", encoding="utf-8").read()
    p = resolve(doc)
    hi = records(doc)["dft.cost_per_candidate"]["high"]
    for dft, label in ((p["dft_cost_per_candidate"], "base"), (hi, "high")):
        c = an.costs({**p, "dft_cost_per_candidate": dft})["experimentally_validated"]
        spread = max(c.values()) / min(c.values())
        assert f"{spread:.2f}×" in text, (label, spread)


def test_readings_carry_sources(doc):
    for name, rd in doc["monte_carlo"]["joint"]["worldview"]["readings"].items():
        assert rd["source"].strip() and rd["standing"].strip(), name


def test_readme_headline_is_conditional():
    """The README headline is the per-reading table, with no single unqualified point estimate."""
    text = open("README.md", encoding="utf-8").read()
    block = re.search(r"<!-- generated:headline:begin -->\n(.*?)<!-- generated:headline:end -->", text, re.S).group(1)
    for reading in ("optimistic (A-Lab)", "middle (Prein)", "pessimistic (Leeman)"):
        assert reading in block
    assert "not measurement uncertainty" in block
    assert "never alone" in block


def test_readme_quotes_current_indirect_rate(doc):
    """Hand-written README text quotes the indirect cost recovery rate the model actually uses."""
    text = open("README.md", encoding="utf-8").read()
    rec = records(doc)["synth.indirect_rate"]
    assert f"{rec['base']:.0%}" in text
    assert f"The rate is {rec['base']:.0%}" in text


def test_key_numbers_match_model(doc):
    """results/key_numbers.json (the paper draft's source of model numbers) is current."""
    import json

    keys = json.load(open("results/key_numbers.json", encoding="utf-8"))
    c = an.costs(resolve(doc))

    def money(x):
        return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}"

    for k in an.PIPELINES:
        assert keys[f"l1_{k}"] == money(c["dft_confirmed_stable"][k])
        assert keys[f"l2_{k}"] == money(c["experimentally_validated"][k])
    assert keys["indirect_rate"] == f"{records(doc)['synth.indirect_rate']['base']:.0%}"


def test_materiality_is_symmetric_and_matches_the_sweep_convention():
    """The denominator fix of revision 11.

    Up to revision 10 the Monte Carlo reported P(|C_B/C_A - 1| > 0.10), with the dearer pipeline
    in the denominator, while the DFT sweep reported each pipeline's gap over the cheaper one. The
    two are not the same question: A exceeding B by 10% is B falling short of A by 9.09%, so the
    simulation's statistic was the stricter of the two and the crossings in the sweep could not be
    compared with it. Both now use analysis._ratio_gap.
    """
    rng = random.Random(7)
    rows = []
    for _ in range(4000):
        base = math.exp(rng.gauss(0, 1))
        # A is dearer than B by exactly 10.5%: material under the symmetric definition
        # ((A-B)/B = 0.105), immaterial under the directional one ((A-B)/A = 0.095).
        c = {lvl: {"A": base * 1.105, "B": base, "C": base * 1.105} for lvl in an.LEVELS}
        rows.append({"costs": c})
    k = an.kill_condition({"draws": rows})["dft_confirmed_stable"]
    assert k["p_material"][("B", "A")] == 1.0
    assert k["p_material_directional"][("B", "A")] == 0.0

    # symmetric in its arguments, which the directional form is not
    assert an._ratio_gap(1.105, 1.0) == an._ratio_gap(1.0, 1.105)
    assert an._ratio_gap(2.0, 1.0) == pytest.approx(1.0)
    # uncomparable pairs count as not material rather than raising
    assert an._ratio_gap(float("inf"), 1.0) == 0.0
    assert an._ratio_gap(0.0, 1.0) == 0.0
    assert an._ratio_gap(float("nan"), 1.0) == 0.0


def test_sweep_and_simulation_agree_on_a_constructed_gap():
    """A pipeline pair sitting just above and just below the 10% line is classified the same way
    by the sweep's comparator and the simulation's materiality test. This is the property the
    unified denominator buys: a crossing in Section 5.5 and a material draw in 5.6 mean the
    same thing."""
    for ratio, expected in ((1.105, 1.0), (1.095, 0.0)):
        rows = [{"costs": {lvl: {"A": 1.0 * ratio, "B": 1.0, "C": 1.0} for lvl in an.LEVELS}}] * 500
        k = an.kill_condition({"draws": rows})["dft_confirmed_stable"]
        assert k["p_material"][("B", "A")] == expected
        assert (an._ratio_gap(ratio, 1.0) > 0.10) == bool(expected)


def test_overlap_decreases_under_nested_refinement_only():
    """Section 5.6 reports one bin count, so the dependence has to be shown, not asserted.

    The monotonicity has a CONDITION: refining bins can only split mass that coarser bins merged
    when the refinement is nested, i.e. each coarse bin divides exactly into fine ones. 20 -> 60
    -> 240 is nested (x3 then x4); 40 -> 60 is not (x1.5), and nothing guarantees its direction.
    Revision 11 stated the monotonicity without the condition and an external reviewer corrected
    it, so the condition is pinned here: the nested chain is asserted, the non-nested step is only
    required to stay in range.
    """
    rng = random.Random(11)
    rows = []
    for _ in range(3000):
        base = math.exp(rng.gauss(0, 1))
        c = {lvl: {"A": base * 1.02, "B": base, "C": base * 3.0} for lvl in an.LEVELS}
        rows.append({"costs": c})
    lvl = "dft_confirmed_stable"
    s = an.overlap_sensitivity({"draws": rows}, counts=(20, 60, 240, 40))
    nested = [s[n][lvl][("B", "A")] for n in (20, 60, 240)]
    assert nested[0] >= nested[1] >= nested[2] - 1e-12
    assert all(0.0 <= s[n][lvl][("B", "A")] <= 1.0 for n in (20, 40, 60, 240))


def test_overlap_does_not_approach_zero_for_identical_samples():
    """The reviewer's counterexample to the claim that overlap falls towards zero as the bin
    count approaches the sample size. Two pipelines with identical costs in every draw have
    identical histograms at EVERY bin count, so their overlap is exactly 1 however fine the bins.

    The decline the paper observes is therefore a property of these draws -- in which A and B
    differ in essentially every draw, so fine enough bins separate them -- and not a general
    property of the statistic. Revision 11 asserted the general version; revision 12 does not.
    """
    rng = random.Random(3)
    rows = [{"costs": {lv: {"A": v, "B": v, "C": v * 2} for lv in an.LEVELS}}
            for v in (math.exp(rng.gauss(0, 1)) for _ in range(2000))]
    s = an.overlap_sensitivity({"draws": rows}, counts=(20, 240, 2000, 20000))
    lvl = "dft_confirmed_stable"
    for n in (20, 240, 2000, 20000):
        assert s[n][lvl][("B", "A")] == pytest.approx(1.0), (
            f"identical samples must retain overlap 1 at {n} bins")
    # and the pipelines that DO differ separate as bins refine, which is the observed behaviour
    assert s[20000][lvl][("C", "A")] < s[20][lvl][("C", "A")]


def test_overlap_null_floor_calibrates_the_coefficient():
    """An overlap coefficient has no absolute scale, so Section 5.6 reports it against a floor.

    Revision 12 explained the fine-bin decline by A and B "differing in nearly every draw". That
    cannot be the reason: the coefficient is built from MARGINAL histograms, which ignore pairing.
    This test asserts that directly -- permuting one pipeline's draws destroys every paired
    relationship and leaves the coefficient unchanged -- and then checks the floor behaves as a
    floor.
    """
    rng = random.Random(5)
    base = [math.exp(rng.gauss(0, 1)) for _ in range(3000)]
    rows = [{"costs": {lv: {"A": x * 1.3, "B": x, "C": x * 2} for lv in an.LEVELS}} for x in base]
    lvl = "dft_confirmed_stable"
    before = an.kill_condition({"draws": rows})[lvl]["overlap"][("B", "A")]

    # permute B's draws across rows: same multiset, so same histogram, so same overlap --
    # but now nothing is paired with anything
    bs = [r["costs"][lvl]["B"] for r in rows]
    rng.shuffle(bs)
    shuffled = [{"costs": {lv: {"A": r["costs"][lv]["A"], "B": b, "C": r["costs"][lv]["C"]}
                           for lv in an.LEVELS}} for r, b in zip(rows, bs)]
    after = an.kill_condition({"draws": shuffled})[lvl]["overlap"][("B", "A")]
    assert after == pytest.approx(before), "marginal overlap must be invariant to pairing"
    # the paired statistic is NOT invariant, which is why the two must not be explained alike
    p_before = an.kill_condition({"draws": rows})[lvl]["p_lt"][("B", "A")]
    p_after = an.kill_condition({"draws": shuffled})[lvl]["p_lt"][("B", "A")]
    assert p_before != pytest.approx(p_after)

    # the floor is what the statistic scores when the true overlap is 1, so it must exceed a
    # measured coefficient for distributions that genuinely differ, and must fall as bins refine
    floor_60 = an.overlap_null_floor({"draws": rows}, lvl, bins=60)
    floor_600 = an.overlap_null_floor({"draws": rows}, lvl, bins=600)
    assert floor_60 > before, "a real difference must read below the no-difference floor"
    assert floor_600 < floor_60, "the floor must itself fall as bins refine"
    assert floor_60 < 1.0, "a finite histogram of two samples does not score 1"


def test_monte_carlo_and_scenarios_agree_on_reported_recipe_counts():
    """A campaign's own recipe multiplicity must reach the simulation, not just the scenarios.

    draw_worldview originally copied only success, novelty and the disagreement rate out of a
    reading, so a reading that pins its own recipe count was honoured in the deterministic
    scenarios and silently ignored in the Monte Carlo, which fell back to A-Lab's budget model.
    The two then disagreed by about eightfold for the middle reading.
    """
    import random as _r
    from src.sampling import draw_worldview
    from src.params import load as _load

    doc = _load()
    wv = doc["monte_carlo"]["joint"]["worldview"]
    seen = {}
    rng = _r.Random(0)
    for _ in range(400):
        name, reading = draw_worldview(rng, wv)
        seen.setdefault(name, reading)
    assert set(seen) == set(wv["readings"]), "all three readings should be drawn"
    for name, reading in seen.items():
        declared = wv["readings"][name].get("recipes")
        if declared is None:
            assert "recipes" not in reading, name
        else:
            assert reading["recipes"] == pytest.approx(float(declared)), name

    # and the simulated median for a reading with a pinned count must track its scenario cost
    mc = an.monte_carlo(doc, n=600)
    lvl = "experimentally_validated"
    med = an.percentile([d["costs"][lvl]["B"] for d in mc["draws"] if d["worldview"] == "middle_prein"], 50)
    sc = an.scenarios(doc)["middle_prein"]["costs"][lvl]["B"]
    assert 0.3 < med / sc < 3.0, f"simulated median {med:,.0f} is far from the scenario cost {sc:,.0f}"


def test_mlip_relaxation_cost_is_negligible_against_dft(doc):
    """5.2's argument rests on the MLIP relaxations costing almost nothing, and the figure it
    quoted for them was wrong by more than an order of magnitude on every denominator.

    The section argues that the level-1 cost ratio between two pipelines approaches their purity
    ratio *because* DFT dominates the compute term. That inference is only valid while the non-DFT
    compute is negligible, so the claim and the number need to move together. It previously said
    "about three cents"; no denominator in the model -- per candidate screened, per DFT-stable hit,
    per robust prediction, per validated material, or per candidate at the worst twelve-thread
    penalty -- produces three cents.

    The replacement figure was wrong too, more subtly. $0.0019 per robust prediction is everything
    upstream of DFT: GENERATING the pool and relaxing it. Generation is the larger half, so the
    sentence written to correct a misattribution of generation cost was still charging generation to
    the relaxations. The relaxations alone are $0.0009, and the two halves are asserted separately
    below so the section cannot quote the bundle as either one of them again.
    """
    p = resolve(doc)
    l1_b = funnel(p)["pipelines"]["B"]["outputs"]["dft_confirmed_stable"]["usd_per"]
    dft_only = (p["dft_cost_per_candidate"] * p["price_per_core_hour"]
                / p["pool_filter_purity"] / (1 - p["dft_wrong_verdict_frac"]))
    non_dft = l1_b - dft_only
    assert non_dft > 0, "the filter and pool must cost something"
    # Negligible, and by a wide margin: if this ever exceeds a per cent of level 1, the purity-ratio
    # approximation in 5.2 stops being safe and the section needs rewriting, not just renumbering.
    assert non_dft / l1_b < 0.01, f"non-DFT compute is {non_dft / l1_b:.2%} of B's level 1"
    assert non_dft < 0.01, f"${non_dft:.4f} is no longer a fraction of a cent"

    # and the bundle splits into generation plus relaxation, with generation the larger part
    B = funnel(p)["pipelines"]["B"]
    stage_usd = {s["stage"]: s["usd"] for s in B["stages"]}
    robust = B["outputs"]["dft_confirmed_stable"]["count"]
    relax, gen = stage_usd["MLIP relax + classify"] / robust, stage_usd["generate"] / robust
    assert relax + gen == pytest.approx(non_dft), (
        "generation + relaxation must reconstruct the pre-DFT compute per robust prediction; if it "
        "does not, a stage has been added and 5.2's two figures no longer account for the bundle")
    assert gen > relax, (
        "generation has been the larger half; if that reverses, 5.2's wording needs checking, since "
        "its history is a misattribution between exactly these two terms")


def test_percentile_returns_infinity_not_nan_in_an_infinite_tail():
    """Every reported median and interval flows through an.percentile, and it returned nan where
    the answer is inf.

    When both bracketing values are infinite the interpolation computes inf - inf, which is nan,
    and nan survives the multiply. The right answer is inf: a quantile sitting in a distribution's
    infinite tail is infinite, not undefined. nan is worse than wrong here because it compares
    false against every threshold, so a materiality or ordering test downstream counts the draw as
    immaterial instead of skipping it -- a silent bias toward "no difference".

    Reachable rather than hypothetical: level 3 is unbounded wherever the novelty share is zero,
    which is precisely what the pessimistic reading asserts, and _ratio_gap in the same module is
    written to expect non-finite costs. It is not live at the current parameters -- the Jeffreys
    posterior never draws exactly zero -- so fixing it moved no figure, checked by regenerating and
    comparing checksums.
    """
    inf = math.inf
    assert an.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == 3.0
    assert an.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 5) == pytest.approx(1.2)
    # a quantile landing inside the infinite tail
    assert an.percentile([1.0, 2.0, 3.0, inf, inf], 95) == inf
    assert an.percentile([1.0, 2.0, inf, inf, inf], 50) == inf
    assert an.percentile([inf] * 5, 50) == inf
    # and the finite side of the same list is unaffected
    assert an.percentile([1.0, 2.0, 3.0, inf, inf], 50) == 3.0
    assert an.percentile([1.0, 2.0, inf, inf, inf], 5) == pytest.approx(1.2)
    assert math.isnan(an.percentile([], 50)), "an empty sample has no percentile"
