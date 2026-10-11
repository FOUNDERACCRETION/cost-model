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


def test_recipes_negatively_correlated_with_success(draws):
    p_target = [(1 - p["dft_wrong_verdict_frac"]) * p["synth_success_unconditional"] for p, _ in draws]
    recipes = [p["synth_recipes_per_target"] for p, _ in draws]
    assert corr(p_target, recipes) < -0.9


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


def test_success_and_novelty_drawn_together(draws):
    """Within the mixture, high-success draws come with high novelty (both from the same reading)."""
    success = [p["synth_success_unconditional"] for p, _ in draws]
    novelty = [p["novelty_science_frac"] for p, _ in draws]
    assert corr(success, novelty) > 0.3
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


def test_scenarios(doc):
    sc = an.scenarios(doc)
    b = {k: v["costs"]["experimentally_validated"]["B"] for k, v in sc.items()}
    assert b["optimistic_alab"] < b["middle_prein"] < b["pessimistic_leeman"]
    assert sc["pessimistic_leeman"]["costs"]["validated_new"]["B"] == math.inf
    assert sc["optimistic_alab"]["recipes"] < sc["pessimistic_leeman"]["recipes"]


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
    text = open("README.md").read()
    names = re.findall(r"<!-- generated:(\w+):begin -->", text)
    assert set(names) == {"headline", "spot", "daf", "returns", "kill", "montecarlo", "tornado", "breakevens",
                          "distributions", "basecase", "costbasis", "dftspan", "attempt", "level3", "multiplier"}
    for name in names:
        body = re.search(rf"<!-- generated:{name}:begin -->\n(.*?)<!-- generated:{name}:end -->", text, re.S).group(1)
        assert body.strip(), f"generated block {name} is empty: run scripts/stage2.py"


def test_readme_headline_numbers_match_model(doc):
    """The hand-written stage-1 findings quote the model's current base-case numbers."""
    text = open("README.md").read()
    c = an.costs(resolve(doc))

    def money(x):
        return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}"

    for lvl in ("dft_confirmed_stable", "experimentally_validated"):
        for k in an.PIPELINES:
            assert money(c[lvl][k]) in text, (lvl, k, money(c[lvl][k]))


def test_readme_scoped_level2_sentence(doc):
    """The level-2 headline quotes the spread at the base and at the top of the DFT span."""
    text = open("README.md").read()
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
    text = open("README.md").read()
    block = re.search(r"<!-- generated:headline:begin -->\n(.*?)<!-- generated:headline:end -->", text, re.S).group(1)
    for reading in ("optimistic (A-Lab)", "middle (Prein)", "pessimistic (Leeman)"):
        assert reading in block
    assert "not measurement uncertainty" in block
    assert "never alone" in block


def test_readme_quotes_current_indirect_rate(doc):
    """Hand-written README text quotes the indirect cost recovery rate the model actually uses."""
    text = open("README.md").read()
    rec = records(doc)["synth.indirect_rate"]
    assert f"{rec['base']:.0%}" in text
    assert f"The rate is {rec['base']:.0%}" in text


def test_key_numbers_match_model(doc):
    """results/key_numbers.json (the paper draft's source of model numbers) is current."""
    import json

    keys = json.load(open("results/key_numbers.json"))
    c = an.costs(resolve(doc))

    def money(x):
        return f"${x:,.0f}" if x >= 100 else f"${x:,.2f}"

    for k in an.PIPELINES:
        assert keys[f"l1_{k}"] == money(c["dft_confirmed_stable"][k])
        assert keys[f"l2_{k}"] == money(c["experimentally_validated"][k])
    assert keys["indirect_rate"] == f"{records(doc)['synth.indirect_rate']['base']:.0%}"
