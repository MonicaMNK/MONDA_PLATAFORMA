from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9:/])((?:docs|data|tests|backend|frontend|scripts)/[A-Za-z0-9_./\-\[\]]+\.(?:docx|pdf|md|txt|json|png|csv|py))"
)


def extract_document_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        from docx import Document

        document = Document(path)
        pieces = [paragraph.text for paragraph in document.paragraphs]
        pieces.extend(cell.text for table in document.tables
                      for row in table.rows for cell in row.cells)
        return "\n".join(pieces)
    return path.read_text(encoding="utf-8", errors="replace")


def find_references(text: str) -> list[str]:
    return sorted(set(REFERENCE_PATTERN.findall(text)))


def audit_references(documents: list[Path], root: Path = ROOT) -> dict:
    results = []
    for document in documents:
        text = extract_document_text(document)
        for reference in find_references(text):
            resolved = (root / reference).resolve()
            results.append({
                "source": str(document),
                "reference": reference,
                "exists": resolved.is_file(),
            })
    return {
        "documents_checked": len(documents),
        "references_checked": len(results),
        "missing": [item for item in results if not item["exists"]],
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detecta rutas de evidencia locales que faltan en Markdown o DOCX.")
    parser.add_argument("documents", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("evidence_reference_audit.json"))
    args = parser.parse_args()
    documents = [path if path.is_absolute() else ROOT / path for path in args.documents]
    missing_documents = [str(path) for path in documents if not path.is_file()]
    if missing_documents:
        raise SystemExit("No existen los documentos a revisar: " + ", ".join(missing_documents))
    result = audit_references(documents)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Referencias revisadas: {result['references_checked']}; faltantes: {len(result['missing'])}.")
    if result["missing"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
