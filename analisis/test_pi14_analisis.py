"""Pruebas unitarias para analisis/pi14_analisis.py."""

from __future__ import annotations

import csv
import json
import statistics
import tempfile
from pathlib import Path

from pi14_analisis import (
    analyze_consistency,
    analyze_paired_times,
    analyze_sus,
    analyze_validation_bank,
    cronbach_alpha,
    mean_std,
)


def test_mean_std_basic():
    result = mean_std([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result["n"] == 5
    assert result["mean"] == 3.0
    assert result["min"] == 1.0
    assert result["max"] == 5.0


def test_mean_std_empty():
    result = mean_std([])
    assert result["n"] == 0


def test_cronbach_alpha_identical_items():
    # Ítems idénticos -> varianza total igual a varianza de ítems, alfa = 1.0
    items = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    assert cronbach_alpha(items) == 1.0


def test_cronbach_alpha_independent_items():
    # Ítems independientes sin correlación -> alfa bajo
    items = [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]
    alpha = cronbach_alpha(items)
    assert 0.0 <= alpha <= 1.0


def test_analyze_validation_bank(tmp_path):
    data = {
        "queries": [
            {"id": "V001", "course": "Biología", "category": "factual",
             "answerable": True, "gold_pdf": "El Sistema Nervioso.pdf"},
            {"id": "V002", "course": "Historia", "category": "integration",
             "answerable": True, "gold_pdf": "El Tahuantinsuyo.pdf"},
            {"id": "V003", "course": "Literatura", "category": "no_evidence",
             "answerable": False},
            {"id": "V004", "course": "Biología", "category": "adversarial",
             "answerable": False},
        ]
    }
    p = tmp_path / "bank.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = analyze_validation_bank(p)
    assert result["total"] == 4
    assert result["answerable"] == 2
    assert result["unanswerable"] == 2
    assert result["category_counts"] == {
        "adversarial": 1, "factual": 1, "integration": 1, "no_evidence": 1,
    }


def test_analyze_paired_times(tmp_path):
    rows = [
        ["participant_id", "rol", "orden", "manual_seconds",
         "monda_seconds", "diference_seconds", "errores_manual",
         "errores_monda", "completo"],
        ["P001", "docente", "A", "185.4", "45.2", "140.2", "0", "0", "true"],
        ["P002", "estudiante", "B", "210.7", "58.3", "152.4", "0", "0", "true"],
    ]
    p = tmp_path / "times.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows(rows)
    result = analyze_paired_times(p)
    assert result["n_participants"] == 2
    assert result["manual"]["n"] == 2
    assert result["monda"]["n"] == 2
    assert result["speedup_factor"] > 1


def test_analyze_sus(tmp_path):
    rows = [
        ["participant_id", "rol", "q1", "q2", "q3", "q4", "q5", "q6",
         "q7", "q8", "q9", "q10"],
        ["P001", "docente", "4", "3", "4", "2", "4", "3", "5", "4", "3", "4"],
        ["P002", "estudiante", "3", "4", "3", "3", "4", "4", "4", "3", "4", "4"],
    ]
    p = tmp_path / "sus.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows(rows)
    result = analyze_sus(p)
    assert result["n_participants"] == 2
    assert result["overall"]["n"] == 2


def test_analyze_consistency(tmp_path):
    rows = [
        ["participant_id", "rol", "q1", "q2", "q3", "q4", "q5", "q6",
         "q7", "q8", "q9", "q10"],
        ["P001", "docente", "4", "3", "4", "2", "4", "3", "5", "4", "3", "4"],
        ["P002", "docente", "3", "4", "3", "3", "4", "4", "4", "3", "4", "4"],
    ]
    p = tmp_path / "sus.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows(rows)
    result = analyze_consistency(p)
    assert "docente" in result
    assert result["docente"]["n_items"] == 10
    assert 0.0 <= result["docente"]["cronbach_alpha"] <= 1.0


def test_speedup_factor_reasonable():
    # Monda siempre debe ser más rápido que manual en los datos observados.
    p = Path("data/usuarios/tiempos_pareados.csv")
    if p.exists():
        result = analyze_paired_times(p)
        assert result["speedup_factor"] > 1.0
        assert result["all_complete"] is True
        assert result["errors_monda_total"] == 0
