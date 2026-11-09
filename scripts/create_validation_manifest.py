from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[1]


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sanitize_database_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme:
        return "configured"
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(files: list[Path], hardware_notes: str = "", network_notes: str = "") -> dict:
    from backend.app.core.config import settings
    from backend.app.db.session import SessionLocal
    from backend.app.models import Config

    dirty_entries = git_output("status", "--porcelain", "--untracked-files=normal").splitlines()
    alembic = AlembicConfig(str(ROOT / "alembic.ini"))
    migrations = ScriptDirectory.from_config(alembic)
    with SessionLocal() as db:
        rag_row = db.get(Config, "rag")
        rag_config = rag_row.valor if rag_row else {}
    effective_rag = {
        "mode": rag_config.get("mode", settings.rag_mode),
        "topK": rag_config.get("topK", settings.rag_top_k),
        "umbral": rag_config.get("umbral", settings.rag_similarity_threshold),
        "margenMinimo": rag_config.get("margenMinimo", settings.rag_minimum_score_margin),
        "modelo": rag_config.get("modelo", settings.gemini_llm_model),
        "modelosRespaldo": rag_config.get("modelosRespaldo", settings.gemini_llm_fallback_models),
    }
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "commit": git_output("rev-parse", "HEAD"),
            "branch": git_output("branch", "--show-current"),
            "working_tree_clean": not dirty_entries,
            "dirty_paths": [entry[3:] for entry in dirty_entries],
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": __import__("os").cpu_count(),
            "hardware_notes": hardware_notes,
            "network_notes": network_notes,
        },
        "application": {
            "environment": settings.environment,
            "database": sanitize_database_url(settings.database_url),
            "alembic_head": migrations.get_current_head(),
            "rag_mode": effective_rag["mode"],
            "rag_top_k": effective_rag["topK"],
            "rag_similarity_threshold": effective_rag["umbral"],
            "rag_minimum_score_margin": effective_rag["margenMinimo"],
            "llm_model": effective_rag["modelo"],
            "llm_fallback_models": effective_rag["modelosRespaldo"],
            "gemini_embedding_model": settings.gemini_embedding_model,
        },
        "files_sha256": {
            str(path.resolve().relative_to(ROOT)): sha256_file(path)
            for path in files
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Registra la configuración reproducible de una campaña Monda.")
    parser.add_argument("--file", action="append", type=Path, default=[],
                        help="Fixture o material de referencia; puede repetirse.")
    parser.add_argument("--output", type=Path, default=Path("validation_manifest.json"))
    parser.add_argument("--hardware-notes", default="")
    parser.add_argument("--network-notes", default="")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Permite documentar una copia de trabajo sucia; no usar para congelar campaña.")
    args = parser.parse_args()
    files = [path if path.is_absolute() else ROOT / path for path in args.file]
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("No existen los archivos declarados: " + ", ".join(missing))
    manifest = build_manifest(files, args.hardware_notes, args.network_notes)
    if not manifest["repository"]["working_tree_clean"] and not args.allow_dirty:
        raise SystemExit("La copia de trabajo tiene cambios. Congela el commit o usa --allow-dirty solo para diagnóstico.")
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifiesto guardado en {output.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
