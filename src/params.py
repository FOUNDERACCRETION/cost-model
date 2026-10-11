"""Load params/parameters.yaml and resolve it into the flat dict that funnel() takes.

All file I/O for parameters lives here so that src/funnel.py stays pure.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PARAMS_YAML = ROOT / "params" / "parameters.yaml"

REQUIRED_FIELDS = ("name", "low", "base", "high", "unit", "source_url", "source_note", "evidence_grade")
EVIDENCE_GRADES = {"first_hand", "published", "figure_read", "derived", "proxy", "assumption", "missing"}
ROLES = {"primary", "first_hand_comparison", "cross_check", "analysis"}
LEVELS = ("low", "base", "high")
SELECTABLE_GENERATORS = ("ion_exchange", "mattergen")


def load(path: Path = PARAMS_YAML) -> dict:
    with open(path) as fh:
        doc = yaml.safe_load(fh)
    validate(doc)
    return doc


def validate(doc: dict) -> None:
    seen = set()
    for rec in doc["parameters"]:
        missing = [f for f in REQUIRED_FIELDS if f not in rec]
        if missing:
            raise ValueError(f"{rec.get('name', '?')}: missing fields {missing}")
        name = rec["name"]
        if name in seen:
            raise ValueError(f"duplicate parameter {name}")
        seen.add(name)
        if rec["evidence_grade"] not in EVIDENCE_GRADES:
            raise ValueError(f"{name}: unknown evidence_grade {rec['evidence_grade']}")
        if "role" in rec and rec["role"] not in ROLES:
            raise ValueError(f"{name}: unknown role {rec['role']}")
        if "citations" in rec and (not isinstance(rec["citations"], list)
                                   or not all(isinstance(k, str) and k for k in rec["citations"])):
            raise ValueError(f"{name}: citations must be a list of bib keys")
        if not rec["low"] <= rec["base"] <= rec["high"]:
            raise ValueError(f"{name}: need low <= base <= high, got {rec['low']}, {rec['base']}, {rec['high']}")


def records(doc: dict) -> dict[str, dict]:
    return {rec["name"]: rec for rec in doc["parameters"]}


def resolve(doc: dict, level: str = "base", overrides: dict | None = None,
            record_levels: dict[str, str] | None = None) -> dict:
    """Flat funnel inputs at one level (low, base or high) of every parameter.

    `overrides` replaces entries of `choices` (e.g. {"price_basis": "spot"}); `record_levels` sets the level
    of individual records (e.g. {"dft.cost_per_candidate": "high"}), for one-at-a-time sensitivity.
    """
    return resolve_with_sources(doc, level, overrides, record_levels)[0]


def resolve_with_sources(doc: dict, level: str = "base", overrides: dict | None = None,
                         record_levels: dict[str, str] | None = None) -> tuple[dict, set[str]]:
    """As resolve(), also returning the names of the records that were read."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
    choices = {**doc["choices"], **(overrides or {})}
    recs = records(doc)
    used: set[str] = set()

    record_levels = record_levels or {}

    def v(name: str) -> float:
        used.add(name)
        return recs[name][record_levels.get(name, level)]

    if choices["stability_threshold"] != "strict":
        raise NotImplementedError(
            "Matbench Discovery recall and FPR are measured at the 0 meV/atom hull; "
            "a 100 meV pipeline needs classifier rates at that threshold (stage 2)."
        )
    thr = "strict"
    model = choices["mlip_model"]
    pool = choices["pool_method"]
    gen = choices["generator_c"]
    if gen not in SELECTABLE_GENERATORS:
        raise ValueError(f"generator_c must be one of {SELECTABLE_GENERATORS} (others lack generation hardware)")
    if pool not in SELECTABLE_GENERATORS:
        raise ValueError(f"pool_method must be one of {SELECTABLE_GENERATORS}")

    def gen_seconds(method: str, compute: str) -> float:
        """Generation time of `method` if it runs on `compute` (cpu or gpu), else 0."""
        seconds = v(f"gen.{method}.gen_time")
        return seconds if recs[f"gen.{method}.gen_time"]["compute"] == compute else 0.0
    basis = choices["price_basis"]
    filter_basis = choices["mlip_filter_basis"]
    if filter_basis == "measured" and model != "chgnet":
        raise ValueError("measured filter purity exists only for CHGNet (Szymanski & Bartel); use mlip_filter_basis=matbench")

    resolved = {
        "n_candidates": v("batch.candidates_per_chemistry"),
        "n_atoms": v("batch.n_atoms"),
        # candidate pool for A and B
        "pool_frac_stable": v(f"gen.{pool}.frac_stable_{thr}"),
        "pool_frac_novel_mp": v(f"gen.{pool}.frac_novel_vs_mp"),
        "pool_frac_novel_all_db": v(f"gen.{pool}.frac_novel_all_databases"),
        "pool_gen_core_s": gen_seconds(pool, "cpu"),
        "pool_gen_gpu_s": gen_seconds(pool, "gpu"),
        "pool_filter_purity": v(f"gen.{pool}.frac_stable_after_chgnet_filter"),
        # generator for C
        "gen_frac_stable": v(f"gen.{gen}.frac_stable_{thr}"),
        "gen_frac_novel_mp": v(f"gen.{gen}.frac_novel_vs_mp"),
        "gen_frac_novel_all_db": v(f"gen.{gen}.frac_novel_all_databases"),
        "gen_core_s": gen_seconds(gen, "cpu"),
        "gen_gpu_s": gen_seconds(gen, "gpu"),
        "gen_filter_purity": v(f"gen.{gen}.frac_stable_after_chgnet_filter"),
        # MLIP
        "mlip_step_cost_per_atom": v(f"mlip.{model}.step_cost_per_atom"),
        "mlip_steps": v("mlip.steps_per_relaxation"),
        "mlip_step_cap": v("mlip.step_cap"),
        "mlip_nonconv_frac": v(f"mlip.{model}.nonconv_frac"),
        "mlip_tpr": v(f"mlip.{model}.recall"),
        "mlip_fpr": v(f"mlip.{model}.false_positive_rate"),
        "dft_fraction_sent": v("mlip.dft_fraction_sent"),
        "mlip_filter_basis": filter_basis,
        # DFT
        "dft_cost_basis": choices["dft_cost_basis"],
        "dft_cost_per_candidate": v("dft.cost_per_candidate"),
        "dft_scf_cost_at_ref": v("dft.scf_cost_at_ref"),
        "dft_scf_size_exponent": v("dft.scf_size_exponent"),
        "dft_scf_ref_atoms": v("dft.scf_ref_atoms"),
        "dft_scf_per_ionic": v("dft.scf_per_ionic_step"),
        "dft_ionic_steps": v("dft.ionic_steps"),
        "dft_wrong_verdict_frac": v("dft.wrong_verdict_frac"),
        # fixed
        "reference_phases": v("fixed.reference_phases_per_chemistry"),
        # synthesis
        "synth_recipes_per_target": v("synth.recipes_per_target"),
        "synth_success_unconditional": v("synth.success_unconditional"),
        "synth_success_multiplier_filtered": v("synth.success_multiplier_mlip_filtered"),
        "xrd_cost_per_sample": v("synth.xrd_cost_per_sample"),
        "furnace_fixed_fee": v("synth.furnace_fixed_fee"),
        "furnace_hourly": v("synth.furnace_hourly"),
        "furnace_hours_per_attempt": v("synth.furnace_hours_per_attempt"),
        "labour_annual_salary": v("synth.labour_annual_salary"),
        "labour_fringe_rate": v("synth.labour_fringe_rate"),
        "labour_tuition_remission": v("synth.labour_tuition_remission"),
        "synth_indirect_rate": v("synth.indirect_rate"),
        "synth_cost_basis": choices["cost_basis"],
        "fa_on_service_fees": choices["fa_base_includes_service_fees"],
        "indirect_base": choices.get("indirect_base", "total_direct"),
        "labour_attempts_per_week": v("synth.labour_attempts_per_week"),
        "weeks_per_year": v("synth.weeks_per_year"),
        "crucible_cost": v("synth.crucible_cost"),
        "attempts_per_crucible": v("synth.attempts_per_crucible"),
        "precursor_mass_g": v("synth.precursor_mass_g_per_attempt"),
        "precursor_usd_per_g": v("synth.precursor_usd_per_g"),
        "other_consumables_per_attempt": v("synth.other_consumables_per_attempt"),
        # novelty
        "novelty_science_frac": v("novelty.science_frac"),
        # prices: one swappable number per compute type
        "price_per_core_hour": v(f"price.cpu.{basis}"),
        "price_per_gpu_hour": v(f"price.gpu_a100.{basis}"),
    }
    return resolved, used
