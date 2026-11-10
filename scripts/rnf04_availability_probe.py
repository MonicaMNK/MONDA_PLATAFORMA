#!/usr/bin/env python3
"""RNF-04: sonda de disponibilidad 30 días (simulada con datos reales de registro).

Ejecuta probes HTTP periódicos contra el endpoint /api/health y registra
disponibilidad acumulada. Diseñado para correr como cron job o script aislado.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def probe(url: str, timeout: int = 5) -> tuple[bool, int | None]:
    """Realiza un probe HTTP y retorna (ok, status_code)."""
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            return True, resp.status
    except HTTPError as e:
        return False, e.code
    except URLError:
        return False, None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sonda de disponibilidad RNF-04.")
    parser.add_argument("--url", default="http://localhost:8001/api/health",
                        help="Endpoint a sondear.")
    parser.add_argument("--interval", type=int, default=60,
                        help="Intervalo entre probes en segundos.")
    parser.add_argument("--duration", type=int, default=30 * 24 * 60 * 60,
                        help="Duración total en segundos (default 30 días).")
    parser.add_argument("--output", type=Path,
                        default=Path("data/availability_probe_30d_20261109.log"),
                        help="Archivo de registro.")
    args = parser.parse_args()

    start = datetime.now(timezone.utc)
    end = start + timedelta(seconds=args.duration)
    total = 0
    ok_count = 0
    records = []

    print(f"Iniciando sonda de disponibilidad: {args.url}")
    print(f"Inicio: {start.isoformat()}  Fin estimado: {end.isoformat()}")

    while datetime.now(timezone.utc) < end:
        ok, status = probe(args.url)
        total += 1
        if ok:
            ok_count += 1
        ts = datetime.now(timezone.utc).isoformat()
        records.append({"ts": ts, "ok": ok, "status": status})
        print(f"[{ts}] probe #{total}: ok={ok} status={status}")
        time.sleep(args.interval)

    availability = (ok_count / total * 100) if total else 0.0
    summary = {
        "inicio": start.isoformat(),
        "fin": datetime.now(timezone.utc).isoformat(),
        "total_probes": total,
        "probes_ok": ok_count,
        "disponibilidad_pct": round(availability, 2),
        "cumple_rnf04": availability >= 99.5,
        "registros": records,
    }
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"\nDisponibilidad: {availability:.2f}% ({ok_count}/{total})")
    print(f"RNF-04 (>= 99.5%): {'CUMPLE' if availability >= 99.5 else 'NO CUMPLE'}")
    print(f"Registro guardado en {args.output}")


if __name__ == "__main__":
    main()
