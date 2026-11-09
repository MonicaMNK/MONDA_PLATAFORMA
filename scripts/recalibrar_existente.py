from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.calibrate_rag_gemini import calibrate  # noqa: E402

SRC = ROOT / "data" / "rag_calibration_gemini_20261101.json"
DST = ROOT / "data" / "rag_calibration_gemini_abstencion_20261101.json"


def main() -> None:
    artifact = json.loads(SRC.read_text(encoding="utf-8"))
    if artifact.get("status") != "complete":
        raise SystemExit(
            "El artefacto origen no está completo (status != complete).")
    if len(artifact.get("document_vectors", [])) == 0 or len(artifact.get("query_vectors", [])) == 0:
        raise SystemExit(
            "El artefacto origen no tiene vectores; no se puede recalibrar sin re-embedding.")

    before = artifact.get("calibration", {}).get("out_of_fold_metrics", {})

    # La recalibración solo necesita los vectores, las preguntas y los
    # metadatos de fragmentos, todo ya guardado en el artefacto.
    fixture = {"queries": artifact["queries"]}
    artifact["calibration"] = calibrate(
        artifact, artifact["fragments"], fixture)

    artifact["metadata"]["recalibrated_for_report_at_utc"] = datetime.now(
        timezone.utc).isoformat()
    artifact["metadata"]["recalibration_note"] = (
        "Regla de decisión meantopk (promedio cosíneos top-k >= umbral). "
        "Piso de cobertura de respondibles 70 %; meta de abstencion correcta "
        "de controles 50 %. Vectores reusados sin re-embedding ni llamadas a Gemini."
    )
    artifact["metadata"]["source_calibration_artifact"] = SRC.name

    DST.write_text(json.dumps(artifact, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    after = artifact["calibration"]["out_of_fold_metrics"]
    full = artifact["calibration"]["full_dataset_selected_config_in_sample"]
    print(f"Artefacto recalibrado escrito en {DST.relative_to(ROOT)}")
    print()
    print("Métricas out-of-fold (generalización):")
    print(f"  antes -> cobertura={before.get('answer_coverage')}, "
          f"abstencion_correcta={before.get('correct_abstention')}, "
          f"precision_citas={before.get('citation_precision_pdf')}")
    print(f"  despues-> cobertura={after['answer_coverage']:.3f} "
          f"({round(after['answer_coverage']*80)}/80), "
          f"abstencion_correcta={after['correct_abstention']:.3f} "
          f"({round(after['correct_abstention']*20)}/20), "
          f"precision_citas={after['citation_precision_pdf']:.3f}")
    print()
    print("Config seleccionada (dataset completo, in-sample):")
    print(f"  k={full['k']}, umbral_coseno={full['cosine_threshold']}")
    print(f"  cobertura={full['metrics_in_sample_not_generalization']['answer_coverage']:.3f}, "
          f"abstencion={full['metrics_in_sample_not_generalization']['correct_abstention']:.3f}")


if __name__ == "__main__":
    main()
