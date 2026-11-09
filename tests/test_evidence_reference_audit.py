from scripts.audit_evidence_references import audit_references, find_references


def test_reference_scanner_finds_repo_paths_and_ignores_urls():
    text = (
        "Usa docs/evidencias/run.txt y tests/test_basic_fixes.py. "
        "No interpretes https://example.org/docs/fake.pdf como archivo local."
    )

    assert find_references(text) == [
        "docs/evidencias/run.txt",
        "tests/test_basic_fixes.py",
    ]


def test_audit_reports_existing_and_missing_references(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "present.txt").write_text("evidence", encoding="utf-8")
    source = tmp_path / "plan.md"
    source.write_text(
        "See docs/present.txt and docs/absent.docx.", encoding="utf-8"
    )

    result = audit_references([source], root=tmp_path)

    assert result["references_checked"] == 2
    assert [item["reference"] for item in result["missing"]] == ["docs/absent.docx"]
