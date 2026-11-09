from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = json.loads((ROOT / "data/acceptance_thresholds.json").read_text(encoding="utf-8"))
REQUIREMENTS = ACCEPTANCE["requirements"]
