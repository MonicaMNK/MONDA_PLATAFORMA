#!/usr/bin/env python3
"""RNF-04: script de respaldo de base de datos.

Vuelca el esquema y datos de la base de datos de pruebas a un archivo SQL.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Respaldo de base de datos RNF-04.")
    parser.add_argument("--db-url", default="sqlite:///data/test_entrega2.db",
                        help="URL de la base de datos (SQLite por defecto).")
    parser.add_argument("--output", type=Path,
                        default=Path("data/backup_monda_20261109.sql"),
                        help="Archivo de respaldo de salida.")
    args = parser.parse_args()

    # Extraer ruta del archivo SQLite desde la URL.
    if args.db_url.startswith("sqlite:///"):
        db_path = args.db_url[len("sqlite:///"):]
    else:
        print(f"URL de base de datos no soportada para respaldo directo: {args.db_url}",
              file=sys.stderr)
        sys.exit(1)

    src = Path(db_path)
    if not src.exists():
        print(f"Base de datos no encontrada: {src}", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    header = f"-- Respaldo Monda Plataforma\n-- Fecha: {ts}\n-- Origen: {src}\n\n"
    with src.open("rb") as fin, args.output.open("w", encoding="utf-8") as fout:
        fout.write(header)
        fout.write(fin.read().decode("utf-8", errors="replace"))

    print(f"Respaldo generado: {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
