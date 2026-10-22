"""Derive model parameters from the first-hand benchmark data in data/.

Pure functions over rows (lists of dicts as read by csv.DictReader) plus thin
loaders. scripts/derive_benchmark_params.py prints every derived value, and
tests/test_traceability.py checks that params/parameters.yaml agrees with them,
so each benchmark-sourced number in the YAML can be regenerated from raw data.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MLIP_CSV = ROOT / "data" / "mlip_benchmark" / "timings.csv"
DFT_CSV = ROOT / "data" / "dft_benchmark" / "timings.csv"
MATBENCH_DIR = ROOT / "data" / "matbench_discovery"

MLIP_MODELS = ("chgnet", "mace-mp-0", "m3gnet")
MATBENCH_FILES = {"chgnet": "chgnet-0.3.0.yml", "mace-mp-0": "mace-mp-0.yml", "m3gnet": "m3gnet.yml"}


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _true(value: str) -> bool:
    return value.strip().lower() == "true"


def wilson_interval(successes: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- MLIP


def mlip_primary_rows(rows: list[dict], model: str) -> list[dict]:
    """One row per structure: primary 1-thread config, main run (not repeats)."""
    return [r for r in rows if r["config"] == "primary_1thread" and r["run_kind"] == "main" and r["model"] == model]


def mlip_step_cost_per_atom(rows: list[dict], model: str) -> dict:
    """Core-seconds per ionic step per atom.

    Native candidates only (the 56-atom supercell is excluded, as in the
    benchmark's headline). Base = pooled ratio sum(core-s per step) / sum(atoms),
    low/high = smallest/largest per-structure ratio.
    """
    sel = [r for r in mlip_primary_rows(rows, model) if _true(r["native_candidate"])]
    per_step = [float(r["core_seconds_per_ionic_step"]) for r in sel]
    atoms = [int(r["n_atoms"]) for r in sel]
    ratios = [s / n for s, n in zip(per_step, atoms)]
    return {"base": sum(per_step) / sum(atoms), "low": min(ratios), "high": max(ratios), "n": len(sel)}


def mlip_steps_distribution(rows: list[dict], models=("chgnet", "mace-mp-0")) -> dict:
    """Ionic steps per converged relaxation, pooled over the given models (all 7 structures).

    M3GNet is excluded by that default, and the reason belongs here rather than in the caller's
    head: it converged on only 1 of its 7 structures, and that single relaxation took 191 steps
    against the 18-to-81 range of the other two models. One outlier from a model that mostly fails
    to converge is not a step count, and pooling it would widen the distribution on the strength of
    a single run while saying nothing about size dependence.

    It is NOT excluded for hitting the step cap. The cap is 500 -- every non-converged row reports
    exactly 500, which is how mlip_step_cap derives it -- and the 191-step rows are flagged
    converged. paper/VERIFICATION.md asserted the cap explanation until 2026-10-18; its
    non-convergence is already carried by mlip.m3gnet.nonconv_frac, 6 of 7.
    """
    values = sorted(
        int(r["n_ionic_steps"])
        for m in models
        for r in mlip_primary_rows(rows, m)
        if _true(r["converged"])
    )
    return {"values": values, "base": statistics.fmean(values), "low": min(values), "high": max(values)}


def mlip_nonconvergence(rows: list[dict], model: str) -> dict:
    """Fraction of relaxations that hit the step cap without converging (all 7 structures)."""
    sel = mlip_primary_rows(rows, model)
    failed = sum(1 for r in sel if not _true(r["converged"]))
    lo, hi = wilson_interval(failed, len(sel))
    return {"failed": failed, "n": len(sel), "base": failed / len(sel), "low": lo, "high": hi}


def mlip_step_cap(rows: list[dict]) -> int:
    """Step cap = step count of relaxations that stopped without converging."""
    capped = {int(r["n_ionic_steps"]) for r in rows if r["config"] == "primary_1thread" and not _true(r["converged"])}
    if len(capped) != 1:
        raise ValueError(f"expected one cap value, got {capped}")
    return capped.pop()


# ---------------------------------------------------------------- DFT


def dft_scf_cost_by_size(rows: list[dict]) -> list[tuple[int, float]]:
    """(n_atoms, median core-seconds per SCF iteration) for the primary 4-rank single points."""
    groups: dict[int, list[float]] = {}
    for r in rows:
        if r["config"] == "primary_4rank" and r["calc_type"] == "scf" and r["status"] == "ok":
            core_s = float(r["core_hours"]) * 3600 / int(r["n_scf_steps"])
            groups.setdefault(int(r["n_atoms"]), []).append(core_s)
    return sorted((n, statistics.median(v)) for n, v in groups.items())


def fit_power_law(points: list[tuple[int, float]], ref_atoms: float) -> tuple[float, float]:
    """Least squares on log c = log a + b log(N / ref_atoms). Returns (a, b)."""
    xs = [math.log(n / ref_atoms) for n, _ in points]
    ys = [math.log(c) for _, c in points]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return math.exp(my - b * mx), b


def dft_scf_fit(rows: list[dict], ref_atoms: float, native_max_atoms: int = 32) -> dict:
    """Power-law fit of SCF-iteration cost against size.

    Base fit uses all 7 sizes. The exponent range is the fit on all 7 vs the fit on
    the 6 native candidates (<= native_max_atoms). The prefactor range is the
    smallest/largest ratio of observed to fitted cost.
    """
    pts = dft_scf_cost_by_size(rows)
    a, b = fit_power_law(pts, ref_atoms)
    _, b_native = fit_power_law([p for p in pts if p[0] <= native_max_atoms], ref_atoms)
    ratios = [c / (a * (n / ref_atoms) ** b) for n, c in pts]
    return {
        "points": pts,
        "a": a,
        "a_low": a * min(ratios),
        "a_high": a * max(ratios),
        "b": b,
        "b_low": min(b, b_native),
        "b_high": max(b, b_native),
    }


def dft_relax_factors(rows: list[dict]) -> dict:
    """SCF iterations per ionic step and ionic steps, from converged vc-relaxes."""
    sel = [r for r in rows if r["calc_type"] == "vc-relax" and _true(r["converged"]) and r["status"] == "ok"]
    scf_per_ionic = [int(r["n_scf_steps"]) / int(r["n_ionic_steps"]) for r in sel]
    ionic = [int(r["n_ionic_steps"]) for r in sel]
    return {
        "n": len(sel),
        "scf_per_ionic": {"base": statistics.median(scf_per_ionic), "low": min(scf_per_ionic), "high": max(scf_per_ionic)},
        "ionic_steps": {"base": statistics.median(ionic), "low": min(ionic), "high": max(ionic)},
    }


def native_size_range(rows: list[dict]) -> dict:
    """Atom counts of the native benchmark candidates (median, min, max)."""
    sizes = sorted({int(r["n_atoms"]) for r in rows if _true(r["native_candidate"])})
    return {"values": sizes, "base": statistics.median(sizes), "low": min(sizes), "high": max(sizes)}


# ---------------------------------------------------------------- Matbench Discovery


def matbench_rates(model: str) -> dict:
    """Recall (TPR), false-positive rate and prevalence on the unique-prototype WBM set."""
    with open(MATBENCH_DIR / MATBENCH_FILES[model], encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    m = doc["metrics"]["discovery"]["unique_prototypes"]
    tp, fp, tn, fn = m["TP"], m["FP"], m["TN"], m["FN"]
    return {
        "precision": m["Precision"],
        "recall": m["Recall"],
        "tpr": tp / (tp + fn),
        "fpr": fp / (fp + tn),
        "prevalence": (tp + fn) / (tp + fp + tn + fn),
    }


def derive_all(ref_atoms: float = 20) -> dict:
    mlip = read_csv(MLIP_CSV)
    dft = read_csv(DFT_CSV)
    return {
        "mlip_step_cost": {m: mlip_step_cost_per_atom(mlip, m) for m in MLIP_MODELS},
        "mlip_steps": mlip_steps_distribution(mlip),
        "mlip_nonconv": {m: mlip_nonconvergence(mlip, m) for m in MLIP_MODELS},
        "mlip_step_cap": mlip_step_cap(mlip),
        "dft_scf_fit": dft_scf_fit(dft, ref_atoms),
        "dft_relax": dft_relax_factors(dft),
        "n_atoms": native_size_range(mlip),
        "matbench": {m: matbench_rates(m) for m in MLIP_MODELS},
        "precursors": derive_precursors(),
    }


# ---------------------------------------------------------------- precursor prices

PRECURSOR_DIR = ROOT / "data" / "precursors"
PRICES_CSV = PRECURSOR_DIR / "fisher_prices_2026-10-10.csv"
ROUTES_CSV = PRECURSOR_DIR / "routes.csv"

# Standard atomic weights (IUPAC, abridged), g/mol.
ATOMIC_WEIGHT = {
    "H": 1.008, "Li": 6.94, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Na": 22.990, "Si": 28.085,
    "P": 30.974, "S": 32.06, "Ti": 47.867, "Mn": 54.938, "Zn": 65.38, "In": 114.818, "Ba": 137.327,
}


def molar_mass(formula: str) -> float:
    """Molar mass of a formula without brackets, e.g. 'NH4H2PO4'."""
    import re

    total = 0.0
    for element, count in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        total += ATOMIC_WEIGHT[element] * (int(count) if count else 1)
    return total


def pack_prices(rows: list[dict], base_min_pack_g: float = 100) -> dict[str, dict]:
    """USD per gram for each precursor at three pack choices.

    low  = largest pack listed (bulk buying)
    base = smallest pack of at least base_min_pack_g (or the largest if none is that big)
    high = smallest pack listed
    """
    packs: dict[str, list[tuple[float, float]]] = {}
    for r in rows:
        packs.setdefault(r["precursor"], []).append((float(r["pack_g"]), float(r["list_usd"]) / float(r["pack_g"])))
    out = {}
    for name, items in packs.items():
        items.sort()
        big_enough = [it for it in items if it[0] >= base_min_pack_g]
        out[name] = {"low": items[-1][1], "base": (big_enough[0] if big_enough else items[-1])[1], "high": items[0][1]}
    return out


def precursor_blends(price_rows: list[dict], route_rows: list[dict]) -> dict:
    """Blended USD per gram of precursor mix for each target, by stoichiometric mass, at each pack level.

    Returns per-target blends and the summary used in parameters.yaml: low = cheapest target at bulk
    prices, base = median target at base packs, high = dearest target at smallest packs.
    """
    prices = pack_prices(price_rows)
    formula = {r["precursor"]: r["formula"] for r in price_rows}
    targets: dict[str, list[tuple[str, float]]] = {}
    for r in route_rows:
        targets.setdefault(r["target"], []).append((r["precursor"], float(r["moles_per_formula_unit"])))
    blends = {}
    for target, parts in targets.items():
        grams = {pre: mol * molar_mass(formula[pre]) for pre, mol in parts}
        total = sum(grams.values())
        blends[target] = {lvl: sum(g * prices[pre][lvl] for pre, g in grams.items()) / total for lvl in LEVEL_NAMES}
    return {
        "per_target": blends,
        "low": min(b["low"] for b in blends.values()),
        "base": statistics.median(b["base"] for b in blends.values()),
        "high": max(b["high"] for b in blends.values()),
    }


LEVEL_NAMES = ("low", "base", "high")


def derive_precursors() -> dict:
    return precursor_blends(read_csv(PRICES_CSV), read_csv(ROUTES_CSV))
