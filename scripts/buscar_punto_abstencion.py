"""Busca, sobre los VECTORES YA CALCULADOS, la regla de decisión que maximice
la abstención correcta de controles sin que la cobertura de respondibles baje
del 70 %.

No re-vectoriza nada: reusa document_vectors y query_vectors del artefacto
existente.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data" / "rag_calibration_gemini_20261101.json"


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    ln = math.sqrt(sum(v * v for v in left))
    rn = math.sqrt(sum(v * v for v in right))
    return dot / (ln * rn) if ln and rn else -1.0


def load_ranked():
    artifact = json.loads(ART.read_text(encoding="utf-8"))
    queries = artifact["queries"]
    fragments = artifact["fragments"]
    doc_vectors = artifact["document_vectors"]
    query_vectors = artifact["query_vectors"]
    ranked = []
    for query, qv in zip(queries, query_vectors):
        rows = []
        for fragment, dv in zip(fragments, doc_vectors):
            if fragment["course"] == query["course"]:
                rows.append((cosine(qv, dv), fragment["filename"], fragment["ordinal"]))
        ranked.append(sorted(rows, reverse=True))
    return artifact, queries, ranked


def decide(rule, param, cos):
    if rule == "top1":
        t = param
        return bool(cos and cos[0][0] >= t)
    if rule == "count":
        t, m = param
        return sum(1 for c, _, _ in cos if c >= t) >= m
    if rule == "meantopk":
        k, t = param
        if not cos:
            return False
        kk = min(max(k, 1), len(cos))
        return sum(c for c, _, _ in cos[:kk]) / kk >= t
    raise ValueError(rule)


def metrics(rule, param, queries, ranked):
    n_ans = sum(1 for q in queries if q["answerable"])
    n_ctl = len(queries) - n_ans
    covered = abst = 0
    for i, query in enumerate(queries):
        accepted = decide(rule, param, ranked[i])
        if query["answerable"] and accepted:
            covered += 1
        if not query["answerable"] and not accepted:
            abst += 1
    return covered / n_ans, abst / n_ctl


def main():
    artifact, queries, ranked = load_ranked()
    n_ctl = sum(1 for q in queries if not q["answerable"])
    n_ans = sum(1 for q in queries if q["answerable"])

    resultados = []
    # top1
    for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
        cov, ab = metrics("top1", t, queries, ranked)
        resultados.append((f"top1 t={t:.2f}", cov, ab))
    # count
    for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
        for m in (2, 3, 4):
            cov, ab = metrics("count", (t, m), queries, ranked)
            resultados.append((f"count t={t:.2f} m={m}", cov, ab))
    # meantopk
    for k in (1, 2, 3, 4, 5, 6, 8):
        for t in [round(x / 100, 2) for x in range(56, 81, 2)]:
            cov, ab = metrics("meantopk", (k, t), queries, ranked)
            resultados.append((f"mean{k} t={t:.2f}", cov, ab))

    validos = [r for r in resultados if r[1] >= 0.70]
    validos.sort(key=lambda r: r[2], reverse=True)

    print("=== Reglas con cobertura >= 70 %, ordenadas por abstención ===\n")
    print(f"{'regla':22s} {'cobertura':>10s} {'abstencion':>11s}")
    for regla, cov, ab in validos[:20]:
        print(f"{regla:22s} {cov*100:>8.1f}% ({round(cov*n_ans)}/80)  {ab*100:>9.1f}% ({round(ab*n_ctl)}/20)")

    if not validos:
        print("(ninguna regla alcanza cobertura >= 70 %)")
        return

    mejor = validos[0]
    print(f"\nMEJOR PUNTO (cobertura>=70%): {mejor[0]} -> cobertura={mejor[1]*100:.1f}% abstención={mejor[2]*100:.1f}%")


if __name__ == "__main__":
    main()
