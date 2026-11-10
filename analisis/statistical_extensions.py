#!/usr/bin/env python3
"""Extensiones estadísticas para PI14: intervalos de confianza, prueba t pareada, tamaño del efecto."""

from __future__ import annotations

import math
import statistics
from typing import List


def mean_ci(values: List[float], confidence: float = 0.95) -> dict:
    """Intervalo de confianza de la media (distribución t de Student)."""
    n = len(values)
    if n < 2:
        return {"n": n, "mean": None, "ci_lower": None, "ci_upper": None}
    mean = statistics.mean(values)
    sd = statistics.stdev(values)
    se = sd / math.sqrt(n)
    # Valor t aproximado para 95% con n-1 grados de libertad (tabla simplificada)
    t_crit = _t_critical(n - 1, confidence)
    margin = t_crit * se
    return {
        "n": n,
        "mean": round(mean, 4),
        "sd": round(sd, 4),
        "se": round(se, 4),
        "t_critical": round(t_crit, 4),
        "ci_lower": round(mean - margin, 4),
        "ci_upper": round(mean + margin, 4),
        "confidence": confidence,
    }


def paired_t_test(before: List[float], after: List[float]) -> dict:
    """Prueba t de muestras pareadas (before - after)."""
    n = len(before)
    if n != len(after) or n < 2:
        return {"error": "Muestras deben tener igual longitud y n >= 2"}
    diffs = [b - a for b, a in zip(before, after)]
    mean_diff = statistics.mean(diffs)
    sd_diff = statistics.stdev(diffs) if n > 1 else 0.0
    se_diff = sd_diff / math.sqrt(n) if n > 0 else 0.0
    t_stat = mean_diff / se_diff if se_diff > 0 else 0.0
    df = n - 1
    p_value = _two_tailed_p(t_stat, df)
    ci = mean_ci(diffs)
    cohens_d = mean_diff / sd_diff if sd_diff > 0 else 0.0
    return {
        "n": n,
        "mean_difference": round(mean_diff, 4),
        "sd_difference": round(sd_diff, 4),
        "se_difference": round(se_diff, 4),
        "t_statistic": round(t_stat, 4),
        "degrees_of_freedom": df,
        "p_value": round(p_value, 6),
        "significant_05": p_value < 0.05,
        "ci_95": ci,
        "cohens_d": round(cohens_d, 4),
        "interpretation": _interpret_cohens_d(abs(cohens_d)),
    }


def _t_critical(df: int, confidence: float) -> float:
    """Valor t crítico aproximado (tabla simplificada para df comunes)."""
    table = {
        1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
        6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    }
    return table.get(df, 2.0) if df > 0 else 2.0


def _two_tailed_p(t_stat: float, df: int) -> float:
    """Aproximación del p-valor bilateral (distribución t)."""
    if df <= 0:
        return 1.0
    # Aproximación simple usando la función de distribución acumulativa de t
    x = df / (df + t_stat * t_stat)
    # Aproximación de la beta incompleta simplificada
    p = 1.0 - 0.5 * (1.0 + math.erf(math.sqrt(x * df / 2.0) / math.sqrt(2.0)))
    return min(1.0, max(0.0, 2.0 * p))


def _interpret_cohens_d(d: float) -> str:
    if d < 0.2:
        return "despreciable"
    if d < 0.5:
        return "pequeño"
    if d < 0.8:
        return "mediano"
    return "grande"


def effect_size_ci(d: float, n: int) -> dict:
    """Intervalo de confianza aproximado para d de Cohen."""
    se = math.sqrt((n + d * d / 2) / (n * (n - 3)) if n > 3 else 1.0)
    return {
        "d": round(d, 4),
        "se": round(se, 4),
        "ci_lower": round(d - 1.96 * se, 4),
        "ci_upper": round(d + 1.96 * se, 4),
    }
