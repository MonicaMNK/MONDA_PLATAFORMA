# Resultados detallados de pruebas

> Evidencia histórica del 1 de noviembre de 2026. Sus resultados describen esa versión del código; para las verificaciones actuales, consulta [la validación PostgreSQL + pgvector del 9 de noviembre](validacion-postgresql-pgvector-2026-11-09.md) y [la suite SQLite del 8 de noviembre](resultado-suite-2026-11-08.md).

**Fecha:** 1 de noviembre de 2026
**Entorno:** Windows, Python 3.12.16, pytest 9.2.0.
**SQLite:** 25 aprobadas, 0 fallidas, 1 advertencia; 107,51 s.
**PostgreSQL + pgvector:** 25 aprobadas, 0 fallidas, 1 advertencia; 99,27 s.
**Datos:** bases temporales de prueba y datos sintéticos.

## Resultado de cada caso

| Caso | SQLite | PostgreSQL |
|---|---|---|
| test_admin_creates_edits_users_and_assigns_courses | Aprobada | Aprobada |
| test_csrf_cookie_visible_at_home_and_logout_clears_it | Aprobada | Aprobada |
| test_sync_checks_course_and_full_action_identity | Aprobada | Aprobada |
| test_document_cannot_be_reused_in_another_course | Aprobada | Aprobada |
| test_vector_search_excludes_other_embedding_spaces | Aprobada | Aprobada |
| test_assessment_does_not_use_inactive_material | Aprobada | Aprobada |
| test_reindex_active_material_keeps_it_available | Aprobada | Aprobada |
| test_demo_seed_has_three_courses_and_nine_visible_pdfs | Aprobada | Aprobada |
| test_platform_terms_are_required_and_versioned | Aprobada | Aprobada |
| test_teacher_must_accept_material_sharing_terms_for_each_upload | Aprobada | Aprobada |
| test_full_pi7_backend_flow_fallback_rag | Aprobada | Aprobada |
| test_course_isolation_and_rbac | Aprobada | Aprobada |
| test_sync_idempotency_and_rejects_assessment_offline | Aprobada | Aprobada |
| test_material_upload_version_and_index_fallback | Aprobada | Aprobada |
| test_refresh_rotation_requires_csrf | Aprobada | Aprobada |
| test_rag_provider_modes_are_available_without_starting_servers | Aprobada | Aprobada |
| test_gemini_is_never_constructed_without_external_processing_authorization | Aprobada | Aprobada |
| test_completed_delivery_hidden_grade_teacher_correction_and_release | Aprobada | Aprobada |
| test_rag_scope_includes_subfolders_and_never_broadens_empty_selection | Aprobada | Aprobada |
| test_alerts_track_never_active_students_and_do_not_duplicate_reviewed | Aprobada | Aprobada |
| test_conversations_are_private_for_every_role | Aprobada | Aprobada |
| test_week_folders_upload_preview_move_and_student_read_only | Aprobada | Aprobada |
| test_folders_and_previews_cannot_cross_courses | Aprobada | Aprobada |
| test_provider_status_is_admin_only_and_checks_models | Aprobada | Aprobada |
| test_sqlite_upgrade_preserves_existing_rows_and_is_idempotent | Aprobada | Aprobada (usa SQLite) |

En ambas corridas la única advertencia fue deprecación de httpx con starlette.testclient; no hizo fallar pruebas. La salida individual está en pytest-suite-detallada-2026-11-01.txt y pytest-postgresql-detallada-2026-11-01.txt.

## PostgreSQL + pgvector

Las comprobaciones se hicieron con pgvector/pgvector:pg16 en el proyecto Docker temporal monda-pgtest-20261101, sin datos de usuarios.

- Alembic aplicó las revisiones 20261004_0001 a 20261012_0005.
- PostgreSQL 16 informó pgvector 0.8.7. La columna monda.fragmentos_rag.embedding es vector(768).
- Existe el índice ix_fragmentos_rag_vector_hnsw con vector_cosine_ops.
- El plan de la sonda sintética usó el índice HNSW y recuperó el vecino esperado, id=1.
- La prueba existente test_vector_search_excludes_other_embedding_spaces pasó conectada a PostgreSQL.
- La suite completa pasó 25/25. El test de migración SQLite crea su propio escenario SQLite y también pasó dentro de la corrida PostgreSQL.

El primer intento completo no pudo crear su carpeta temporal bajo el perfil global de Windows; se repitió con --basetemp .pytest-tmp-pg-run2 dentro del proyecto y pasó. En el primer intento puntual faltaba habilitar pgvector en la base separada de pruebas; se habilitó y la repetición pasó.

Evidencias PostgreSQL: pytest-postgresql-detallada-2026-11-01.txt, postgres-alembic-upgrade-2026-11-01.txt, postgres-pgvector-hnsw-2026-11-01.txt y postgres-vector-search-test-2026-11-01.txt. Los primeros intentos se conservan en pytest-postgresql-run1-temp-permission-2026-11-01.txt y postgres-vector-search-setup-failure-2026-11-01.txt.

## Prueba sintética de Gemini

Se enviaron frases sintéticas sin datos personales. La clave no está guardada en los archivos de evidencia. Google devolvió HTTP 200 para la consulta de metadatos de ambos modelos; la generación sigue separadamente fallando con HTTP 503.

| Modelo y operación | Resultado | Detalle |
|---|---|---|
| gemini-3.8-flash, generación | Sin respuesta | Cuatro intentos sintéticos: dos agotaron el timeout de lectura de 45 s y dos devolvieron HTTP 503. No hubo texto generado. |
| gemini-flash-latest, generación | Sin respuesta | Dos intentos con payload válido: uno devolvió HTTP 503 y el cURL corregido agotó 45 s. |
| SDK oficial google-genai, gemini-flash-latest | Sin respuesta; HTTP 503 UNAVAILABLE | Google indicó alta demanda temporal del modelo; el SDK no obtuvo texto generado tras sus reintentos. |
| Metadatos de gemini-flash-latest y gemini-3.8-flash | HTTP 200 | Ambos modelos fueron reconocidos y listan generateContent. Esta consulta de solo lectura no demuestra que la inferencia complete correctamente. |
| gemini-embedding-2, embedding | Aprobada | Devolvió un vector finito de 768 dimensiones. |

Evidencias Gemini: gemini-smoke-sintetica-2026-11-01.txt, gemini-smoke-reintento-2026-11-01.txt, gemini-smoke-clave-nueva-2026-11-01.txt, gemini-flash-latest-curl-2026-11-01.txt, gemini-model-access-2026-11-01.txt, gemini-flash-latest-curl-clave-2026-11-01.txt, gemini-python-sdk-2026-11-01.txt y gemini-embedding-sintetica-2026-11-01.txt.

## Alcance

Las pruebas verifican los flujos locales de esa versión en SQLite y PostgreSQL + pgvector/HNSW. No son una medición de carga ni una prueba del despliegue AWS. En esa fecha la generación de Gemini no completó por HTTP 503; el 9 de noviembre se realizó un recorrido API E1–E3 con Gemini real, documentado en [la evidencia actual](flujo-e1-e3-postgresql-gemini-2026-11-09.md). Fuentes sobre el resultado histórico: https://ai.google.dev/gemini-api/docs/troubleshooting, https://ai.google.dev/gemini-api/docs/generate-content/api-errors y https://ai.google.dev/gemini-api/docs/pricing.

Actualizacion de modelo (2026-11-01): el modelo predeterminado del proyecto se cambio a `gemini-3-flash-preview` tras la llamada sintetica exitosa. El modelo es preview; verificar cuota y disponibilidad en el despliegue.


Administracion de modelos Gemini (2026-11-01): `gemini-3-flash-preview` queda como principal. Se implemento la secuencia configurable de hasta dos respaldos y la interfaz de administracion permite ordenar/cambiar el principal y los respaldos. El servidor avanza al siguiente modelo ante error de generacion o respuesta vacia. Los modelos de respaldo configurados no se consideran probados individualmente.


## Re-ejecucion tras configurar el fallback Gemini

Se volvio a ejecutar la suite completa con el codigo actual. SQLite: 25 aprobadas y 1 advertencia en 96.24 s. PostgreSQL 16 + pgvector: 25 aprobadas y 1 advertencia en 106.40 s. En ambos casos la advertencia corresponde a la deprecacion de Starlette por el uso de httpx con TestClient. Los logs detallados son `pytest-suite-fallback-2026-11-01.txt` y `pytest-postgresql-fallback-2026-11-01.txt`. Esta suite de regresion no incluye una llamada real de failover a traves del servicio RAG; la llamada sintetica confirmada del modelo principal permanece documentada por separado.
