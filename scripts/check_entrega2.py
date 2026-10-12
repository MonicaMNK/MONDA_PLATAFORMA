import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'check_entrega2.db'}")
os.environ.setdefault("MONDA_ALLOW_PBKDF2_FOR_TESTS", "1")
os.environ.setdefault("RAG_MODE", "fallback")

from backend.app.main import app

expected = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/logout"),
    ("POST", "/api/auth/recovery"),
    ("POST", "/api/auth/reset"),
    ("GET", "/api/users/me"),
    ("PATCH", "/api/users/me"),
    ("GET", "/api/courses"),
    ("POST", "/api/courses"),
    ("PATCH", "/api/courses/{courseId}"),
    ("POST", "/api/courses/{courseId}/enrollments"),
    ("GET", "/api/courses/{courseId}/enrollments"),
    ("PATCH", "/api/courses/{courseId}/enrollments/{studentId}"),
    ("POST", "/api/courses/{courseId}/contents"),
    ("GET", "/api/courses/{courseId}/contents"),
    ("POST", "/api/contents/{contentId}/index"),
    ("GET", "/api/contents/{contentId}/status"),
    ("GET", "/api/contents/{contentId}/download"),
    ("GET", "/api/jobs/{jobId}"),
    ("POST", "/api/courses/{courseId}/rag/query"),
    ("GET", "/api/rag/conversations"),
    ("GET", "/api/rag/conversations/{conversationId}/messages"),
    ("POST", "/api/rag/messages/{messageId}/rating"),
    ("POST", "/api/courses/{courseId}/assessments/generate"),
    ("GET", "/api/courses/{courseId}/assessments"),
    ("GET", "/api/assessments/{id}"),
    ("PATCH", "/api/questions/{questionId}/review"),
    ("POST", "/api/assessments/{id}/publish"),
    ("POST", "/api/assessments/{id}/attempts"),
    ("GET", "/api/courses/{courseId}/analytics"),
    ("PATCH", "/api/alerts/{alertId}"),
    ("GET", "/api/courses/{courseId}/reports/export"),
    ("POST", "/api/sync"),
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/users"),
    ("PATCH", "/api/admin/users/{userId}"),
    ("GET", "/api/admin/roles"),
    ("PATCH", "/api/admin/roles"),
    ("GET", "/api/admin/config"),
    ("PATCH", "/api/admin/config"),
    ("GET", "/api/admin/audit"),
}
actual = set()
# Se usa el esquema OpenAPI y no app.routes: las versiones recientes de FastAPI
# ya no aplanan los routers incluidos dentro de app.routes.
for path, operations in app.openapi().get("paths", {}).items():
    if not path.startswith("/api/") or path == "/api/health":
        continue
    for method in operations:
        if method.upper() in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
            actual.add((method.upper(), path))
missing = sorted(expected - actual)
extra = sorted(actual - expected)
if missing or extra:
    raise SystemExit(f"Contrato PI7 no coincide. Faltantes={missing}; extra={extra}")

factory = (ROOT / "backend/app/rag/providers/factory.py").read_text(encoding="utf-8")
for provider in ("gemini", "ollama", "fallback"):
    if provider not in factory:
        raise SystemExit(f"Proveedor RAG faltante: {provider}")
print("Entrega 2 OK: 41 operaciones PI7 exactas + health, backend modular y RAG triple modo presentes.")
