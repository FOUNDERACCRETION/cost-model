"""Derived quantities computed by re-running funnel(). Pure functions, no I/O."""

from __future__ import annotations

from src.funnel import funnel


def level2_spread(p: dict) -> float:
    """Largest / smallest level-2 cost (per experimentally validated material) across A, B and C."""
    costs = [pl["outputs"]["experimentally_validated"]["usd_per"] for pl in funnel(p)["pipelines"].values()]
    return max(costs) / min(costs)


def multiplier_for_level2_spread(p: dict, target: float, steps: int = 2000, tol: float = 1e-9) -> dict:
    """Smallest synthesis-success multiplier for MLIP-filtered pipelines (B, C) that makes the
    level-2 spread reach `target`.

    The multiplier is searched from 1 up to the value at which filtered success reaches 1. A grid
    finds the first crossing (the spread need not be monotonic if B or C start above A), then
    bisection refines it. Returns the multiplier and the success rate it implies, or
    multiplier=None with the largest spread reachable.
    """
    success = p["synth_success_unconditional"]
    if success <= 0:
        return {"multiplier": None, "filtered_success": None, "spread": level2_spread(p)}
    m_max = 1.0 / success

    def spread(m: float) -> float:
        return level2_spread({**p, "synth_success_multiplier_filtered": m})

    lo = 1.0
    if spread(lo) >= target:
        return {"multiplier": lo, "filtered_success": success, "spread": spread(lo)}
    best = spread(lo)
    for i in range(1, steps + 1):
        hi = 1.0 + (m_max - 1.0) * i / steps
        s_hi = spread(hi)
        best = max(best, s_hi)
        if s_hi >= target:
            while hi - lo > tol:
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if spread(mid) < target else (lo, mid)
            return {"multiplier": hi, "filtered_success": success * hi, "spread": spread(hi)}
        lo = hi
    return {"multiplier": None, "filtered_success": None, "spread": best}


# ---------------------------------------------------------------- shared

import math  # noqa: E402
import random  # noqa: E402
import statistics  # noqa: E402

from src.funnel import mlip_pass_rate  # noqa: E402
from src.params import records, resolve, resolve_with_sources  # noqa: E402

PIPELINES = ("A", "B", "C")
LEVELS = ("dft_confirmed_stable", "experimentally_validated", "validated_new")


def costs(p: dict) -> dict:
    """{level: {pipeline: $ per output}} for one parameter set."""
    r = funnel(p)["pipelines"]
    return {lvl: {k: r[k]["outputs"][lvl]["usd_per"] for k in PIPELINES} for lvl in LEVELS}


def percentile(values: list[float], q: float) -> float:
    """Linear-interpolation percentile, q in [0, 100]."""
    xs = sorted(values)
    if not xs:
        return math.nan
    pos = (len(xs) - 1) * q / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


# ---------------------------------------------------------------- discovery acceleration factor


def enrichment(doc: dict, p: dict) -> dict:
    """Discovery acceleration factor (purity / prevalence) measured on each pool, and the Matbench comparison."""
    recs = records(doc)
    out = {}
    for src in ("pool", "gen"):
        prev, purity = p[f"{src}_frac_stable"], p[f"{src}_filter_purity"]
        predicted = mlip_pass_rate(prev, p["mlip_tpr"], p["mlip_fpr"])["precision"] / prev
        out[src] = {"prevalence": prev, "purity": purity, "daf_measured": purity / prev,
                    "daf_matbench_rates_at_this_prevalence": predicted}
    out["wbm"] = {"daf_reported": recs["mlip.chgnet.daf_wbm"]["base"],
                  "prevalence": recs["mlip.matbench_prevalence_paper"]["base"]}
    return out


# ---------------------------------------------------------------- tornado


def tornado(doc: dict, choices: dict | None = None) -> dict:
    """One-at-a-time swings: every record the model reads, low to high, others at base.

    Returns {level: {pipeline: [rows sorted by swing]}} with each row
    {name, low_cost, high_cost, swing, share, status}. share = swing^2 / sum of swing^2 over finite rows,
    the usual OAT approximation to a variance share (linear response, independent inputs).
    """
    recs = records(doc)
    base_p, used = resolve_with_sources(doc, overrides=choices)
    names = sorted(n for n in used if recs[n]["low"] != recs[n]["high"])
    raw = {}
    for name in names:
        ends = {}
        for end in ("low", "high"):
            try:
                ends[end] = costs(resolve(doc, overrides=choices, record_levels={name: end}))
            except ValueError:
                ends[end] = None  # inputs contradict each other (e.g. purity below prevalence x recall)
        raw[name] = ends
    base_costs = costs(base_p)
    out = {}
    for lvl in LEVELS:
        out[lvl] = {}
        for k in PIPELINES:
            rows = []
            for name, ends in raw.items():
                lo = ends["low"][lvl][k] if ends["low"] else None
                hi = ends["high"][lvl][k] if ends["high"] else None
                other = hi if lo is None else lo
                if (lo is None) != (hi is None) and other == base_costs[lvl][k]:
                    # The record does not affect this pipeline; its failing end comes from another pipeline.
                    lo = hi = other
                if lo is None or hi is None:
                    status, swing = "inconsistent at one end", math.nan
                elif math.isinf(lo) or math.isinf(hi):
                    status, swing = "unbounded at one end", math.inf
                else:
                    status, swing = "ok", abs(hi - lo)
                rows.append({"name": name, "low_cost": lo, "high_cost": hi, "swing": swing, "status": status})
            finite = [r for r in rows if r["status"] == "ok" and r["swing"] > 0]
            total = sum(r["swing"] ** 2 for r in finite)
            for r in rows:
                r["share"] = r["swing"] ** 2 / total if r["status"] == "ok" and total > 0 else math.nan
            rows.sort(key=lambda r: (r["status"] != "ok", -(r["swing"] if r["status"] == "ok" else 0)))
            out[lvl][k] = rows
    return out


def top_share(rows: list[dict], share: float = 0.8) -> list[str]:
    """Smallest set of top-ranked finite rows whose variance shares sum to at least `share`."""
    picked, acc = [], 0.0
    for r in rows:
        if r["status"] != "ok" or r["swing"] == 0:
            continue
        picked.append(r["name"])
        acc += r["share"]
        if acc >= share:
            break
    return picked


# ---------------------------------------------------------------- marginal returns

SYNTH_COST_INPUTS = (
    "xrd_cost_per_sample", "furnace_fixed_fee", "furnace_hourly", "labour_annual_salary", "labour_tuition_remission",
    "crucible_cost", "precursor_usd_per_g", "other_consumables_per_attempt",
)


def levers() -> dict:
    """Each lever scales one quantity by a factor f and says which direction is an improvement.

    "cost per synthesis attempt" scales every priced input of an attempt, which scales the attempt cost by f
    exactly (labour and F&A are linear in them).
    """
    def scale(keys, cap=None):
        def f(p, factor):
            q = dict(p)
            for k in keys:
                q[k] = p[k] * factor
                if cap is not None and q[k] > cap(p):
                    raise ValueError("lever pushed a fraction above its cap")
            return q
        return f

    return {
        "synthesis success rate": {"apply": scale(("synth_success_unconditional",),
                                                  cap=lambda p: 1.0 / p["synth_success_multiplier_filtered"]),
                                   "improve": +1, "group": "synthesis"},
        "recipes per target": {"apply": scale(("synth_recipes_per_target",)), "improve": -1, "group": "synthesis"},
        "cost per synthesis attempt": {"apply": scale(SYNTH_COST_INPUTS), "improve": -1, "group": "synthesis"},
        "compute price": {"apply": scale(("price_per_core_hour", "price_per_gpu_hour")), "improve": -1, "group": "compute"},
        "DFT cost per candidate": {"apply": scale(("dft_cost_per_candidate",)), "improve": -1, "group": "compute"},
        "MLIP precision (filter purity)": {"apply": scale(("pool_filter_purity", "gen_filter_purity"), cap=lambda p: 1.0),
                                           "improve": +1, "group": "compute"},
    }


def log_elasticities(p: dict, level: str = "experimentally_validated", h: float = 1e-4) -> dict:
    """d ln(cost) / d ln(parameter) at p, by central difference in log space (one-sided at a cap).

    Scale-free, so levers of different units are comparable. `return` is the % fall in cost per 1% improvement
    in the lever (positive = the improvement lowers cost).
    """
    base = costs(p)[level]
    out = {}
    for name, lv in levers().items():
        try:
            up, dn, width = costs(lv["apply"](p, math.exp(h)))[level], costs(lv["apply"](p, math.exp(-h)))[level], 2 * h
        except ValueError:  # at a cap: backward difference
            up, dn, width = base, costs(lv["apply"](p, math.exp(-h)))[level], h
        out[name] = {}
        for k in PIPELINES:
            if not (math.isfinite(base[k]) and math.isfinite(up[k]) and math.isfinite(dn[k])):
                out[name][k] = {"elasticity": math.nan, "return": math.nan}
                continue
            e = (math.log(up[k]) - math.log(dn[k])) / width
            out[name][k] = {"elasticity": e, "return": -e * lv["improve"]}
    return out


def spot_switch(doc: dict, p: dict, level: str = "experimentally_validated") -> dict:
    """Change in cost from moving compute from on-demand to spot prices, the one lever with a known (zero) cost.

    Applied as the ratio of the base spot to base on-demand price, so it also works on Monte Carlo draws whose
    on-demand price was sampled.
    """
    recs = records(doc)
    cpu = recs["price.cpu.spot"]["base"] / recs["price.cpu.on_demand"]["base"]
    gpu = recs["price.gpu_a100.spot"]["base"] / recs["price.gpu_a100.on_demand"]["base"]
    base = costs(p)[level]
    new = costs({**p, "price_per_core_hour": p["price_per_core_hour"] * cpu,
                 "price_per_gpu_hour": p["price_per_gpu_hour"] * gpu})[level]
    return {"cpu_discount": 1 - cpu, "gpu_discount": 1 - gpu,
            "change": {k: new[k] / base[k] - 1 if math.isfinite(base[k]) else math.nan for k in PIPELINES}}


# ---------------------------------------------------------------- Monte Carlo


def monte_carlo(doc: dict, n: int | None = None, seed: int | None = None) -> dict:
    """Draw parameter sets (src/sampling.py), evaluate A, B, C, and the marginal returns in each draw.

    Draws whose inputs contradict each other (pass fraction > 1) are rejected and redrawn; the rejection
    count is returned.
    """
    from src.sampling import sampler

    mc = doc["monte_carlo"]
    n = n or mc["n_draws"]
    rng = random.Random(mc["seed"] if seed is None else seed)
    draw = sampler(doc)
    rows, rejected = [], 0
    while len(rows) < n:
        p, info = draw(rng)
        try:
            c = costs(p)
            el = log_elasticities(p)
            spot = spot_switch(doc, p)["change"]
        except ValueError:
            rejected += 1
            continue
        rows.append({"worldview": info["worldview"], "costs": c, "elasticities": el, "spot": spot,
                     "dft_cost": p["dft_cost_per_candidate"]})
    return {"draws": rows, "rejected": rejected}


def summarise(mc: dict, qs=(5, 25, 50, 75, 95)) -> dict:
    out = {}
    for lvl in LEVELS:
        out[lvl] = {k: {q: percentile([d["costs"][lvl][k] for d in mc["draws"]], q) for q in qs} for k in PIPELINES}
    return out


def kill_condition(mc: dict, bins: int = 60, material: float = 0.10) -> dict:
    """Does any ordering of A, B, C survive the uncertainty? Per level:

    p_lt[(x, y)]  probability that x is cheaper than y in the same draw (paired: both see the same world);
    overlap[(x, y)]  overlap coefficient of the two marginal cost distributions (histogram on log10 cost);
    p_material[(x, y)]  probability that the two differ by more than `material` (10%) in the same draw.
    """
    out = {}
    pairs = (("B", "A"), ("C", "B"), ("C", "A"))
    for lvl in LEVELS:
        vals = {k: [d["costs"][lvl][k] for d in mc["draws"]] for k in PIPELINES}
        finite = [v for k in PIPELINES for v in vals[k] if math.isfinite(v) and v > 0]
        lo, hi = math.log10(min(finite)), math.log10(max(finite))
        width = (hi - lo) / bins or 1.0

        def hist(xs):
            h = [0] * bins
            for x in xs:
                if math.isfinite(x) and x > 0:
                    h[min(bins - 1, int((math.log10(x) - lo) / width))] += 1
            return [c / len(xs) for c in h]

        hists = {k: hist(vals[k]) for k in PIPELINES}
        res = {"p_lt": {}, "overlap": {}, "p_material": {}}
        for x, y in pairs:
            n = len(vals[x])
            res["p_lt"][(x, y)] = sum(a < b for a, b in zip(vals[x], vals[y])) / n
            res["overlap"][(x, y)] = sum(min(a, b) for a, b in zip(hists[x], hists[y]))
            res["p_material"][(x, y)] = sum(abs(a / b - 1) > material for a, b in zip(vals[x], vals[y])) / n
        out[lvl] = res
    return out


def returns_summary(mc: dict) -> dict:
    """Median and 5-95% of each lever's return per 1% improvement, and of the spot switch, per pipeline."""
    out = {}
    for name in levers():
        out[name] = {}
        for k in PIPELINES:
            xs = [d["elasticities"][name][k]["return"] for d in mc["draws"]]
            xs = [x for x in xs if math.isfinite(x)]
            out[name][k] = {"median": percentile(xs, 50), "p5": percentile(xs, 5), "p95": percentile(xs, 95)}
    out["spot"] = {}
    for k in PIPELINES:
        xs = [d["spot"][k] for d in mc["draws"] if math.isfinite(d["spot"][k])]
        out["spot"][k] = {"median": percentile(xs, 50), "p5": percentile(xs, 5), "p95": percentile(xs, 95)}
    return out


def weighted_percentile(values: list[float], weights: list[float], q: float) -> float:
    pairs = sorted(zip(values, weights))
    total = sum(weights)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= total * q / 100:
            return v
    return pairs[-1][0]


def reweighted(mc: dict, weights: dict, base_weights: dict, level: str, k: str, q: float) -> float:
    """Percentile of a cost under different worldview weights, by importance reweighting the same draws."""
    vals = [d["costs"][level][k] for d in mc["draws"]]
    ws = [weights[d["worldview"]] / base_weights[d["worldview"]] for d in mc["draws"]]
    return weighted_percentile(vals, ws, q)


# ---------------------------------------------------------------- named scenarios


def scenarios(doc: dict) -> dict:
    """Each named reading of the synthesis evidence, other parameters at base; recipes follow the budget model."""
    from src.sampling import apply_worldview

    recs = records(doc)
    base = resolve(doc)
    budget = recs["synth.recipe_budget"]["base"]
    key = {"synth.success_unconditional": "success", "novelty.science_frac": "novelty",
           "dft.wrong_verdict_frac": "wrong_verdict"}
    out = {}
    for name, sc in doc["scenarios"].items():
        reading = {key[k]: v for k, v in sc["values"].items()}
        p = apply_worldview(base, reading, budget)
        out[name] = {"costs": costs(p), "recipes": p["synth_recipes_per_target"], "reading": reading}
    return out


# ---------------------------------------------------------------- break-evens


def fixed_cost_payback(doc: dict, p: dict) -> dict:
    """Candidates screened before the MLIP filter's extra fixed cost is repaid by its per-candidate saving.

    Extra fixed cost of B over A: loading the model once (first-hand) plus relaxing the reference phases with the
    MLIP. Per-candidate saving: A's marginal compute per MP-novel candidate minus B's.
    """
    recs = records(doc)
    r = funnel(p)["pipelines"]
    n = p["n_candidates"]
    load_core_h = recs["mlip.chgnet.model_load_s"]["base"] / 3600
    mlip_core_h = funnel(p)["unit_costs"]["mlip"]["core_h"]
    extra_fixed = load_core_h + p["reference_phases"] * mlip_core_h
    saving_core_h = (r["A"]["marginal"]["compute_core_h"] - r["B"]["marginal"]["compute_core_h"]) / n
    saving_usd = (r["A"]["marginal"]["compute_usd"] - r["B"]["marginal"]["compute_usd"]) / n
    return {"extra_fixed_core_h": extra_fixed, "saving_core_h_per_candidate": saving_core_h,
            "saving_usd_per_candidate": saving_usd,
            "payback_candidates": extra_fixed / saving_core_h if saving_core_h > 0 else math.inf}


def attempt_cost_thresholds(p: dict, compute_share: float, spread: float) -> dict:
    """Synthesis cost per attempt below which compute matters for level 2.

    Level-2 cost of pipeline X is c_X + a k, where a is the cost per attempt, k = recipes / ((1 - w) success)
    attempts per validated material (the same for all pipelines), and c_X its compute per validated material.
    Returns, per pipeline, the a below which compute is at least `compute_share` of its level-2 cost, and the a
    below which the level-2 spread across pipelines reaches `spread`.
    """
    r = funnel(p)
    attempt = r["unit_costs"]["synthesis_attempt"]["usd"]
    lvl2 = {k: r["pipelines"][k]["outputs"]["experimentally_validated"] for k in PIPELINES}
    k_att = lvl2["A"]["synthesis_usd_per"] / attempt
    c = {k: lvl2[k]["compute_usd_per"] for k in PIPELINES}
    share = {k: c[k] * (1 - compute_share) / (compute_share * k_att) for k in PIPELINES}
    num = max(c.values()) - spread * min(c.values())
    a_spread = num / (k_att * (spread - 1)) if num > 0 else 0.0
    return {"attempt_usd": attempt, "attempts_per_validated": k_att, "compute_per_validated": c,
            "attempt_for_compute_share": share, "attempt_for_spread": a_spread}


def purity_for_parity(p: dict, rival: str = "B", level: str = "dft_confirmed_stable", tol: float = 1e-10) -> dict:
    """MLIP filter purity on the generative pool at which C costs the same as `rival` (bisection)."""
    floor = p["gen_frac_stable"] * p["mlip_tpr"]  # below this the pass fraction would exceed 1

    def gap(purity: float) -> float:
        c = costs({**p, "gen_filter_purity": purity})[level]
        return c["C"] - c[rival]

    lo, hi = floor * (1 + 1e-9), 1.0
    if gap(hi) > 0:
        return {"purity": None, "floor": floor}
    if gap(lo) <= 0:
        return {"purity": lo, "floor": floor}
    while hi - lo > tol:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if gap(mid) > 0 else (lo, mid)
    return {"purity": hi, "floor": floor, "measured": p["gen_filter_purity"], "ratio_to_measured": hi / p["gen_filter_purity"]}
