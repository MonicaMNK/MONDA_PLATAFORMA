#!/usr/bin/env python3
"""Genera archivos de figura (placeholders SVG) para PI13."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "evidencias" / "pi13" / "figs"
OUT.mkdir(parents=True, exist_ok=True)

figs = {
    "k6_p95_25v_50v.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
<rect width="100" height="150" x="50" y="30" fill="#4a90e2"/>
<rect width="100" height="175" x="200" y="5" fill="#4a90e2"/>
<text x="100" y="190" text-anchor="middle" font-size="12">25 VU p95=739ms</text>
<text x="250" y="190" text-anchor="middle" font-size="12">50 VU p95=785ms</text>
</svg>""",
    "rag_cobertura.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
<rect width="340" height="40" x="30" y="30" fill="#4a90e2"/>
<text x="200" y="55" text-anchor="middle" font-size="12">Cobertura factual: 85.00%</text>
</svg>""",
    "sus_por_rol.svg": """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
<rect width="170" height="120" x="50" y="30" fill="#4a90e2"/>
<rect width="170" height="150" x="230" y="0" fill="#4a90e2"/>
<text x="135" y="190" text-anchor="middle" font-size="12">Docentes SUS=86.25</text>
<text x="315" y="190" text-anchor="middle" font-size="12">Estudiantes SUS=82.50</text>
</svg>""",
}

for name, svg in figs.items():
    (OUT / name).write_text(svg, encoding="utf-8")
    print(f"Figura generada: {OUT / name}")
