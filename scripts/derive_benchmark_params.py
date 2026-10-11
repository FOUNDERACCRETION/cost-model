"""Print every parameter value derived from the benchmark data and published counts.

Run: uv run python scripts/derive_benchmark_params.py
The values printed here are the ones recorded in params/parameters.yaml;
tests/test_traceability.py checks that the two agree.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.derive import derive_all, wilson_interval  # noqa: E402

out = derive_all()
print(json.dumps(out, indent=2, default=str))

# Binomial counts behind the Wilson ranges (Szymanski & Bartel 2025 v2; Leeman et al. 2024). Stability counts
# are out of 500 MP-novel structures; novelty counts are out of the structures generated to obtain them
# (500 / MP-novel share); filter purity is out of 300 filtered structures (non-integer counts from the
# published percentages).
COUNTS = {}
SB = {  # method: (strict, <=100 meV, generated, absent from all databases)
    "ion exchange": (46, 292, 691, 434), "MatterGen": (15, 89, 545, 453), "CrystaLLM": (12, 64, 509, 433),
    "CDVAE": (9, 56, 521, 479), "FTCP": (10, 100, 1309, 458),
}
for method, (strict, near, generated, all_db) in SB.items():
    COUNTS[f"S&B {method}, strict stable"] = (strict, 500)
    COUNTS[f"S&B {method}, <=100 meV"] = (near, 500)
    COUNTS[f"S&B {method}, new to MP"] = (500, generated)
    COUNTS[f"S&B {method}, absent from MP + Alexandria + ICSD"] = (all_db, generated)
COUNTS["S&B ion exchange, CHGNet filter purity"] = (0.152 * 300, 300)
COUNTS["S&B MatterGen, CHGNet filter purity"] = (0.038 * 300, 300)
COUNTS["Leeman et al., new to science"] = (0, 36)
for label, (k, n) in COUNTS.items():
    lo, hi = wilson_interval(k, n)
    print(f"{label}: {k:g}/{n} = {k / n:.4f}, Wilson 95% [{lo:.4f}, {hi:.4f}]")
