"""Monte Carlo sampling of the parameter set, respecting the documented correlations.

Pure functions: the random generator is passed in. The distributions, counts and joint structures are read
from the `monte_carlo` block of params/parameters.yaml; nothing numeric is defined here.
"""

from __future__ import annotations

import math
import random

from src.params import records, resolve


def beta_counts(rng: random.Random, k: float, n: float) -> float:
    """Jeffreys posterior draw for a proportion with k successes in n."""
    return rng.betavariate(k + 0.5, n - k + 0.5)


def log_triangular(rng: random.Random, low: float, mode: float, high: float) -> float:
    return math.exp(rng.triangular(math.log(low), math.log(high), math.log(mode)))


def log_uniform(rng: random.Random, low: float, high: float) -> float:
    return math.exp(rng.uniform(math.log(low), math.log(high)))


def bootstrap_mean(rng: random.Random, values: list[float]) -> float:
    return sum(rng.choice(values) for _ in values) / len(values)


def draw_marginal(rng: random.Random, spec: dict, rec: dict) -> float:
    kind = spec["type"]
    if kind == "triangular":
        return rng.triangular(rec["low"], rec["high"], rec["base"])
    if kind == "log_triangular":
        return log_triangular(rng, rec["low"], rec["base"], rec["high"])
    if kind == "log_uniform":
        return log_uniform(rng, rec["low"], rec["high"])
    if kind == "uniform":
        return rng.uniform(spec.get("low", rec["low"]), spec.get("high", rec["high"]))
    if kind == "beta_counts":
        return beta_counts(rng, spec["k"], spec["n"])
    if kind == "bootstrap_mean":
        return bootstrap_mean(rng, spec["values"])
    if kind == "empirical":
        return rng.choice(spec["values"])
    raise ValueError(f"unknown distribution type {kind}")


def draw_pool(rng: random.Random, c: dict) -> dict:
    """Joint draw of one method's stability, novelty and filter purity (see monte_carlo.joint.pools)."""
    prevalence = beta_counts(rng, c["stable"], c["n_stable"])
    novel_mp = beta_counts(rng, c["n_stable"], c["generated"])
    all_db = novel_mp * beta_counts(rng, c["all_db"], c["n_stable"])
    p_hat, pi_hat = c["purity"], c["stable"] / c["n_stable"]
    var_ln = (1 - p_hat) / (c["n_purity"] * p_hat) + (1 - pi_hat) / (c["n_stable"] * pi_hat)
    var_ln += (c["plot_error"] / math.sqrt(3) / p_hat) ** 2  # uniform plot-reading error, relative
    enrichment = math.exp(rng.gauss(math.log(p_hat / pi_hat), math.sqrt(var_ln)))
    return {"prevalence": prevalence, "novel_mp": novel_mp, "all_db": all_db, "purity": min(1.0, enrichment * prevalence)}


def draw_worldview(rng: random.Random, wv: dict) -> tuple[str, dict]:
    names = list(wv["weights"])
    name = rng.choices(names, weights=[wv["weights"][n] for n in names])[0]
    reading = wv["readings"][name]
    out = {}
    for key in ("success", "novelty", "wrong_verdict"):
        spec = reading[key]
        if spec["type"] == "beta_counts":
            out[key] = beta_counts(rng, spec["k"], spec["n"])
        elif spec["type"] == "uniform":
            out[key] = rng.uniform(spec["low"], spec["high"])
        else:
            raise ValueError(f"unsupported worldview distribution {spec['type']}")
    # A campaign-reported recipe multiplicity is a fixed property of that reading, not a drawn
    # quantity, so it is carried through rather than sampled. Without this the Monte Carlo and the
    # deterministic scenarios disagree: the scenarios would use Prein's one recipe per target and
    # the simulation would silently fall back to A-Lab's budget model for the same reading.
    if reading.get("recipes") is not None:
        out["recipes"] = float(reading["recipes"])
    return name, out


def recipes_for_success(p_target: float, budget: float) -> float:
    """Expected recipes per target when each recipe succeeds with q and at most `budget` are tried."""
    if p_target <= 0:
        return budget
    if p_target >= 1:
        return 1.0
    q = 1 - (1 - p_target) ** (1 / budget)
    return p_target / q


def apply_worldview(p: dict, reading: dict, budget: float) -> dict:
    """Set success, novelty, wrong-verdict share and the recipes they imply (scenarios and Monte Carlo)."""
    out = {
        **p,
        "synth_success_unconditional": reading["success"],
        "novelty_science_frac": reading["novelty"],
        "dft_wrong_verdict_frac": reading["wrong_verdict"],
    }
    # CHANGED 2026-10-11: was (1 - wrong_verdict) * success. Success is now the campaign-observed
    # unconditional rate, and the method note says it reproduces A-Lab's 6.19 recipes at p = 36/57,
    # which IS that unconditional rate -- so keying on it makes the calibration self-consistent and
    # stops the recipe budget being charged for computational failure a second time.
    # A campaign that REPORTS its own recipe multiplicity overrides the budget model. Prein et al.
    # attempted each target once, so deriving ~8 recipes per target for that reading from A-Lab's
    # budget inflated its synthesis bill roughly eightfold. The budget model remains the fallback
    # for readings that report no multiplicity of their own.
    if reading.get("recipes") is not None:
        out["synth_recipes_per_target"] = float(reading["recipes"])
    else:
        out["synth_recipes_per_target"] = recipes_for_success(reading["success"], budget)
    return out


def record_to_input(doc: dict, names) -> dict[str, str]:
    """Which funnel input each record sets under the base choices, found by perturbing the record."""
    import copy

    base_p = resolve(doc)
    mapping = {}
    for name in names:
        probe = copy.deepcopy(doc)
        rec = next(r for r in probe["parameters"] if r["name"] == name)
        rec["base"] = rec["base"] + 0.123456789  # a value no other input takes
        changed = [k for k, v in resolve(probe).items() if v != base_p[k]]
        if len(changed) != 1:
            raise ValueError(f"{name} maps to {changed} funnel inputs, expected exactly one")
        mapping[name] = changed[0]
    return mapping


def sampler(doc: dict):
    """Return draw(rng) -> (params, info). Funnel inputs not sampled stay at base."""
    mc = doc["monte_carlo"]
    recs = records(doc)
    base = resolve(doc)
    mapping = record_to_input(doc, mc["distributions"])
    budget = recs["synth.recipe_budget"]["base"]
    pools = mc["joint"]["pools"]["counts"]
    pool_name, gen_name = doc["choices"]["pool_method"], doc["choices"]["generator_c"]

    def draw(rng: random.Random) -> tuple[dict, dict]:
        p = dict(base)
        for name, spec in mc["distributions"].items():
            p[mapping[name]] = draw_marginal(rng, spec, recs[name])
        for prefix, method in (("pool", pool_name), ("gen", gen_name)):
            d = draw_pool(rng, pools[method])
            p[f"{prefix}_frac_stable"] = d["prevalence"]
            p[f"{prefix}_frac_novel_mp"] = d["novel_mp"]
            p[f"{prefix}_frac_novel_all_db"] = d["all_db"]
            p[f"{prefix}_filter_purity"] = d["purity"]
        worldview, reading = draw_worldview(rng, mc["joint"]["worldview"])
        p = apply_worldview(p, reading, budget)
        return p, {"worldview": worldview}

    return draw
