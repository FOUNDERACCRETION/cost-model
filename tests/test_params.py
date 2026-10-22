"""Tests for src/params.py and the structure of params/parameters.yaml."""

import copy

import pytest

from src.funnel import funnel
from src.params import LEVELS, REQUIRED_FIELDS, load, records, resolve, resolve_with_sources, validate


@pytest.fixture(scope="module")
def doc():
    return load()


def test_every_record_complete(doc):
    for rec in doc["parameters"]:
        for field in REQUIRED_FIELDS:
            assert field in rec, (rec["name"], field)
        assert rec["source_note"].strip()
        if rec["evidence_grade"] not in ("assumption", "missing"):
            assert rec["source_url"].strip(), rec["name"]


def test_every_record_is_used_or_a_cross_check(doc):
    """No orphan numbers: each record feeds the model under some choice, is a cross-check,
    or belongs to a generator recorded for stage 2."""
    used = set()
    for gen in ("ion_exchange", "mattergen"):
        for model in ("chgnet", "mace-mp-0", "m3gnet"):
            for basis in ("on_demand", "spot"):
                choices = {"pool_method": gen, "generator_c": gen, "mlip_model": model, "price_basis": basis,
                           "mlip_filter_basis": "measured" if model == "chgnet" else "matbench"}
                used |= resolve_with_sources(doc, overrides=choices)[1]
    stage2 = ("gen.crystallm.", "gen.cdvae.", "gen.ftcp.", "gen.ion_exchange.frac_stable_100meV",
              "gen.mattergen.frac_stable_100meV")
    for rec in doc["parameters"]:
        name = rec["name"]
        if rec.get("role") == "analysis":
            source = "".join(open(f, encoding="utf-8").read() for f in ("src/analysis.py", "src/sampling.py"))
            assert name in source, f"{name} has role analysis but the analysis code never reads it"
            continue
        if rec.get("role") == "cross_check" or name.startswith(stage2):
            assert name not in used, f"{name} is marked cross-check/stage 2 but the model reads it"
        else:
            assert name in used, f"{name} is never read by the model"


@pytest.mark.parametrize("level", LEVELS)
def test_resolve_every_level(doc, level):
    p = resolve(doc, level)
    assert all(v is not None for v in p.values())
    funnel(p)


@pytest.mark.parametrize("overrides", [
    {"mlip_model": "chgnet"},
    {"mlip_model": "mace-mp-0", "mlip_filter_basis": "matbench"},
    {"mlip_model": "m3gnet", "mlip_filter_basis": "matbench"},
    {"generator_c": "ion_exchange"}, {"generator_c": "mattergen"},
    {"dft_cost_basis": "first_hand"}, {"price_basis": "spot"}, {"mlip_filter_basis": "matbench"},
    {"cost_basis": "bench"}, {"fa_base_includes_service_fees": True},
])
def test_resolve_every_choice(doc, overrides):
    funnel(resolve(doc, overrides=overrides))


def test_measured_purity_needs_chgnet(doc):
    with pytest.raises(ValueError):
        resolve(doc, overrides={"mlip_model": "mace-mp-0", "mlip_filter_basis": "measured"})


def test_price_basis_switches_one_number(doc):
    on, spot = resolve(doc), resolve(doc, overrides={"price_basis": "spot"})
    changed = {k for k in on if on[k] != spot[k]}
    assert changed == {"price_per_core_hour", "price_per_gpu_hour"}


def test_gpu_generator_has_no_cpu_cost(doc):
    p = resolve(doc, overrides={"generator_c": "mattergen"})
    assert p["gen_core_s"] == 0 and p["gen_gpu_s"] > 0
    p = resolve(doc, overrides={"generator_c": "ion_exchange"})
    assert p["gen_gpu_s"] == 0 and p["gen_core_s"] > 0


def test_unsupported_choices_raise(doc):
    with pytest.raises(NotImplementedError):
        resolve(doc, overrides={"stability_threshold": "100meV"})
    with pytest.raises(ValueError):
        resolve(doc, overrides={"generator_c": "crystallm"})


def test_validate_catches_bad_records(doc):
    bad = copy.deepcopy(doc)
    bad["parameters"][0]["low"] = bad["parameters"][0]["base"] + 1
    with pytest.raises(ValueError):
        validate(bad)
    bad = copy.deepcopy(doc)
    bad["parameters"][0]["evidence_grade"] = "vibes"
    with pytest.raises(ValueError):
        validate(bad)
    bad = copy.deepcopy(doc)
    bad["parameters"].append(copy.deepcopy(bad["parameters"][0]))
    with pytest.raises(ValueError):
        validate(bad)
    bad = copy.deepcopy(doc)
    del bad["parameters"][0]["source_url"]
    with pytest.raises(ValueError):
        validate(bad)


def test_distribution_base_is_mean(doc):
    rec = records(doc)["mlip.steps_per_relaxation"]
    values = rec["distribution"]["values"]
    assert rec["base"] == pytest.approx(sum(values) / len(values), abs=0.005)
    assert rec["low"] == min(values) and rec["high"] == max(values)


def test_correlations_reference_real_parameters(doc):
    names = set(records(doc))
    for corr in doc["correlations"]:
        for field in ("name", "parameters", "sign", "reason", "stage2_handling"):
            assert field in corr, (corr.get("name"), field)
        for name in corr["parameters"]:
            assert name in names, (corr["name"], name)


def test_scenarios_within_ranges(doc):
    recs = records(doc)
    assert set(doc["scenarios"]) == {"optimistic_alab", "middle_prein", "pessimistic_leeman"}
    for key, sc in doc["scenarios"].items():
        for name, value in sc["values"].items():
            assert recs[name]["low"] <= value <= recs[name]["high"], (key, name, value)
    middle = doc["scenarios"]["middle_prein"]["values"]
    for name, value in middle.items():
        assert recs[name]["base"] == value, name


def test_scenarios_are_ordered_in_success_not_in_cost(doc):
    """The three readings are named for how optimistic their SUCCESS reading is, and that ordering
    holds. Their resulting COSTS are not ordered the same way, and the names must not be read as
    if they were: Prein et al. report a lower success rate than A-Lab but attempted each target
    once, and the lower recipe multiplicity outweighs the lower success rate.
    """
    sc = doc["scenarios"]
    shared = set(sc["pessimistic_leeman"]["values"]) & set(sc["optimistic_alab"]["values"])
    # Recipes per target are deliberately NOT monotone across the readings: they are a fact each
    # campaign reports, not a view that can be more or less optimistic. Asserting monotonicity on
    # them is what an earlier version of this test did, and it enforced exactly the splice the
    # model now avoids.
    graded = (shared & set(sc["middle_prein"]["values"])) - {"synth.recipes_per_target"}
    assert graded, "the readings must still share at least one graded quantity"
    for name in graded:
        lo, mid, hi = (sc[k]["values"][name] for k in ("pessimistic_leeman", "middle_prein", "optimistic_alab"))
        if name == "dft.wrong_verdict_frac":
            assert hi <= mid <= lo, name
        else:
            assert lo <= mid <= hi, name
    # Every reading pins its own recipe multiplicity, and the two readings of the SAME campaign sit
    # within 2% of each other while the separate campaign is several times lower. That pattern is
    # the point: recipes travel with the campaign, not with the reading's optimism.
    r = {k: sc[k]["values"]["synth.recipes_per_target"] for k in sc}
    assert r["middle_prein"] == 1.0
    assert abs(r["optimistic_alab"] / r["pessimistic_leeman"] - 1) < 0.02
    assert r["pessimistic_leeman"] / r["middle_prein"] > 5
