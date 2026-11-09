import hashlib

from scripts.create_validation_manifest import build_manifest, sanitize_database_url, sha256_file


def test_database_url_manifest_removes_user_password_and_query_values():
    sanitized = sanitize_database_url(
        "postgresql+psycopg://monda:secret@db.example:5432/monda?sslmode=require"
    )

    assert sanitized == "postgresql+psycopg://db.example:5432/monda"
    assert "secret" not in sanitized
    assert "sslmode" not in sanitized


def test_file_hash_matches_sha256(tmp_path):
    item = tmp_path / "fixture.json"
    item.write_text("synthetic", encoding="utf-8")

    assert sha256_file(item) == hashlib.sha256(b"synthetic").hexdigest()


def test_manifest_records_commit_runtime_and_cleanliness_without_secrets():
    manifest = build_manifest([])

    assert manifest["repository"]["commit"]
    assert manifest["runtime"]["python"]
    assert manifest["application"]["alembic_head"]
    assert "password" not in manifest["application"]["database"].lower()
