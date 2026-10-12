from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..core.config import TRACE_DIR, settings

TRACE_FILE = TRACE_DIR / "rag_traces.jsonl"


def trace_rag(payload: dict[str, Any]) -> None:
    safe = dict(payload)
    safe["timestamp"] = datetime.now(timezone.utc).isoformat()
    with TRACE_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe, ensure_ascii=False, default=str) + "\n")
    if settings.mlflow_tracking_uri:
        try:
            import mlflow  # type: ignore
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
            with mlflow.start_run(run_name=f"rag-{safe.get('correlationId', 'query')}"):
                params = {k: v for k, v in safe.items() if isinstance(v, (str, int, float, bool)) and len(str(v)) < 500}
                mlflow.log_params(params)
        except Exception:
            # La traza local nunca se pierde por un fallo opcional de MLflow.
            pass
