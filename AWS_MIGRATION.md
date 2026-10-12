# Plataforma Monda — guía de migración a AWS

Esta guía describe la transición desde el perfil local (Docker Compose + PostgreSQL/pgvector + almacenamiento local) a AWS siguiendo la arquitectura PI6/PI7: FastAPI en App Runner o ECS, Amazon RDS PostgreSQL, S3 privado, búsqueda vectorial por pgvector u OpenSearch y observabilidad. Es una guía operativa propuesta; no implica que la cuenta AWS, VPC o los servicios ya estén creados.

## 1. Arquitectura objetivo

```text
Browser / PWA -- HTTPS --> App Runner o ALB + ECS/Fargate (FastAPI)
                               |-- RDS PostgreSQL privado (transacciones + pgvector opcional)
                               |-- S3 privado (PDF/DOCX versionados)
                               |-- OpenSearch privado (opcional: índice vectorial separado)
                               |-- Secrets Manager / KMS
                               |-- CloudWatch Logs / Metrics / Alarms
                               |-- MLflow (opcional; EC2/ECS privado, artefactos S3, backend RDS)
                               `-- Gemini API por HTTPS (si se ha aprobado y configurado)
```

**Elección inicial sugerida:** App Runner para una primera publicación controlada si sus requisitos de red privada y conexión a RDS encajan; ECS/Fargate + ALB si se necesita control fino de VPC, tareas, escalado y red. Mantén la base de datos y los índices no públicos. En producción decide expresamente `pgvector` en RDS frente a OpenSearch con pruebas de latencia, coste, filtrado y operación; la interfaz `VectorStoreRepository` permite aislar esa decisión.

## 2. Preparación antes de crear recursos

1. Fija región, cuenta AWS, entorno (`dev`, `staging`, `prod`), RTO/RPO, residencia/transferencias de datos, presupuesto y dominio.
2. Crea infraestructura mediante IaC (CDK, Terraform o CloudFormation) y revisiones de pull request. No hagas cambios manuales irreproducibles en producción.
3. Genera una clave JWT segura y credenciales de base de datos administradas. No reutilices secretos de `.env.example` ni semillas locales.
4. Define retención, política de copias, cifrado, acceso de operadores, monitorización e incident response.
5. Pasa pruebas de autorización negativas (403), intento único, aislamiento curso/versión, aprobación antes de publicación y reconstrucción de backups.

## 3. Contenedor FastAPI: App Runner o ECS/Fargate

### Construcción

El `Dockerfile` raíz construye la imagen de backend desde `requirements.txt`. El entrypoint aplica migraciones Alembic, ejecuta bootstrap de demo solo si se ha configurado `MONDA_DEMO=1` e inicia Uvicorn. Para producción configura `MONDA_DEMO=0`; no uses las cuentas demo.

Construye y verifica localmente:

```bash
docker build -t monda-api:staging .
docker run --rm --env-file .env monda-api:staging
```

No ejecutes esta variante con secretos de producción en una laptop compartida. En CI, escanea la imagen/dependencias, firma artefactos si procede y publica el contenedor en ECR.

### App Runner

1. Crea un servicio desde ECR con puerto `8000` y health check en `/api/health`.
2. Usa el rol de instancia para acceso a Secrets Manager, S3 y servicios que realmente requiera la app; no incrustes access keys.
3. Configura un VPC Connector si RDS/OpenSearch solo son accesibles en subredes privadas; verifica la conectividad de salida al proveedor IA y la resolución DNS.
4. Configura auto-deploy solo para la rama/tag aprobado, límites de concurrencia y tamaño mínimo/máximo revisados con prueba de carga.
5. Usa dominio custom, TLS, logs y alarmas. La app debe tener `COOKIE_SECURE=1` y CORS/orígenes explícitos si se sirve la UI desde otro dominio.

### ECS/Fargate (alternativa)

1. Publica imagen versionada en ECR.
2. Define Task Definition con CPU/memoria, puerto 8000, execution role y task role diferentes, secrets por ARN, logging driver CloudWatch y health check.
3. Despliega servicio privado detrás de ALB HTTPS (ACM), target group `/api/health`, security group del ALB hacia tareas y de tareas hacia RDS/OpenSearch.
4. Configura auto scaling con señales verificadas (CPU/memoria/latencia), despliegue rolling/canary y rollback ante health check fallido.

## 4. Amazon RDS PostgreSQL 16 + pgvector

1. Crea RDS PostgreSQL compatible con la versión del contenedor elegido, subredes privadas, security group que acepta tráfico únicamente desde App Runner VPC Connector o tasks ECS, backups automáticos, cifrado KMS y monitoreo.
2. Comprueba que `pgvector` está disponible en la versión de RDS elegida. Si no lo está, no ejecutes una migración a ciegas: elige una versión soportada o el backend de vectores externo.
3. Crea base/usuario de aplicación con privilegios mínimos. El rol de migración debe separarse del rol runtime si el flujo de despliegue lo permite.
4. Configura `DATABASE_URL` mediante Secrets Manager; usa conexión TLS y parámetros de pool acordes a `max_connections`/escala de tareas.
5. Ejecuta `alembic upgrade head` como job de despliegue único antes de cambiar tráfico; no ejecutes migraciones concurrentemente desde varias réplicas.
6. Ejecuta seed solo en test/dev. No cargues usuarios y contraseñas demo en prod.
7. Verifica backups y restauración a instancia temporal, documentando RPO y RTO.

RDS requiere comprobar extensión y migraciones primero en staging. La comprobación offline `alembic upgrade head --sql` solo genera SQL y **no prueba** compatibilidad con la instancia real.

## 5. Amazon S3 para materiales

Variables previstas:

```dotenv
STORAGE_MODE=s3
S3_BUCKET=<bucket-privado-por-entorno>
AWS_REGION=<region>
```

- Desactiva acceso público, cifra con SSE-S3 o SSE-KMS según política y habilita versionado del bucket.
- Permite acceso al bucket solo al task/instance role de Monda; habilita bloqueo de acceso público y política TLS obligatorio.
- Define CORS solo si se necesitan cargas directas desde navegador; el diseño actual carga vía API, más fácil de controlar para tamaño y autorización.
- Planifica expiración/retención, logs de acceso y clasificación de datos. Nunca construyas una `s3_key` con rutas proporcionadas sin validación.
- Migra los archivos locales con inventario/hash SHA-256, asocia las claves a las filas `contenidos` y prueba descargas autorizadas antes del cambio definitivo.

## 6. Búsqueda vectorial: pgvector o OpenSearch

### Opción A: pgvector en RDS

Mantiene transacciones y vectores en PostgreSQL. Asegura que la extensión está habilitada y que tipo/dimensiones del vector coinciden con el modelo de embedding. El esquema de la entrega usa vectores de 768 dimensiones por la ruta de embeddings principal local/Gemini considerada; al cambiar modelo/dimensión, planifica re-embedding e índice nuevo, no mezcles vectores incompatibles. Ajusta HNSW con dataset representativo y comprueba filtros por curso, material y versión activa.

### Opción B: Amazon OpenSearch Service

Crea dominio/colección con acceso privado, cifrado en reposo/en tránsito, políticas IAM y filtros por `cursoId`, `contenidoId`, versión activa y modelo. Migra/reindexa por lotes usando IDs deterministas e idempotentes. Valida que el score del motor se convierte a la similitud utilizada por la lógica de negocio; no asumas que el `score` bruto equivale al coseno `0.35`.

En ambos casos: ejecuta un conjunto etiquetado de consultas, mide Recall@k, latencia, citas y filtrado negativo entre cursos antes de decidir.

## 7. RAG y secretos externos

- `GEMINI_API_KEY` debe estar en AWS Secrets Manager y llegar al contenedor como secret, nunca como variable embebida en la imagen o repositorio.
- Revalida nombres de modelos, cuotas, región, límites de request, política de retención y términos de tratamiento del proveedor antes de usar Gemini en datos reales.
- Configura `RAG_MODE=gemini` solo si el acceso externo está habilitado y probado; `auto` selecciona Gemini solo cuando hay key, y fallback cuando esté permitido. Para entorno productivo evita que un proveedor falte silenciosamente sin que la alarma lo detecte.
- Usa timeout por request, límites de reintentos con backoff y jitter, limitación de concurrencia/tamaño, y logs sin prompts sensibles o identificadores personales innecesarios.
- Para Ollama no suele ser la opción administrada en AWS; si es requisito, despliega servicio de inferencia separado con capacidad GPU/CPU dimensionada, autentica la red privada y fija versiones de modelos.
- MLflow es opcional: ubícalo en red privada, con autenticación, backend store administrado y artefactos S3. Si no está configurado, preserva las trazas JSONL locales solo para desarrollo; en contenedores efímeros usa un destino persistente central.

Variables principales para la plataforma:

```dotenv
APP_ENV=production
MONDA_DEMO=0
MONDA_SECRET_KEY=<referencia-de-secreto-seguro>
COOKIE_SECURE=1
DATABASE_URL=<secret-de-conexion-rds>
STORAGE_MODE=s3
S3_BUCKET=<bucket-privado>
AWS_REGION=<region>
RAG_MODE=gemini
RAG_ALLOW_FALLBACK=0
GEMINI_API_KEY=<secret-de-gemini>
GEMINI_LLM_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
RAG_TOP_K=4
RAG_SIMILARITY_THRESHOLD=0.35
MLFLOW_TRACKING_URI=<endpoint-privado-opcional>
```

La lista es una plantilla: `DATABASE_URL` y `GEMINI_API_KEY` deben resolverse desde Secrets Manager/secret injection y no guardarse literalmente en repositorio. Los modelos configurables deben verificarse antes del despliegue. El valor predeterminado de embeddings es `gemini-embedding-2`, configurado a 768 dimensiones para coincidir con `vector(768)`; si cambias a otro modelo/dimensión debes crear un índice compatible y re-embebir todo el corpus. Consulta la documentación oficial actual: [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) y [Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings).

## 8. IAM, red y protección de datos

- RDS y OpenSearch en subredes privadas y sin direcciones públicas. Restringe security groups origen/destino al mínimo.
- Usa IAM roles por servicio con permisos exactos, KMS con policy independiente, Secrets Manager con acceso a ARNs concretos y rotación cuando aplique.
- TLS de extremo a extremo donde se soporte, cifrado de volúmenes/artefactos y logs de auditoría administrados.
- No registres contraseñas, cookies, tokens, API keys, prompts completos con datos personales ni datos sensibles.
- Seudonimiza reportes y define reglas de retención/borrado; asegúrate de tener base jurídica/consentimiento institucional aplicable antes de procesar datos de estudiantes menores.

## 9. CI/CD y calidad

Pipeline mínimo sugerido en GitHub Actions:

1. Instalar Python de versión soportada; `pip install -r requirements.txt`.
2. Ejecutar `scripts/check_entrega1.py`, `scripts/check_entrega2.py`, `pytest -q`, `python -m compileall -q backend` y `alembic upgrade head --sql`.
3. (Opcional) instalar Node 20 en frontend y ejecutar `npm ci`, `npm run typecheck`, `npm run build`.
4. Escanear dependencias/imagen y ejecutar pruebas de seguridad; no publiques en ramas no protegidas.
5. Construir/taggear imagen por commit, publicar en ECR, ejecutar migración como job único, desplegar a staging y pasar smoke tests antes del tráfico.

Las comprobaciones incluidas aún no son una prueba de carga 50 usuarios, disponibilidad de 30 días ni restore/RPO/RTO. Añade y registra estas pruebas como evidencia de tesis antes de declarar satisfechos los RNF.

## 10. Plan de migración por etapas

1. **Sandbox**: desplegar RDS, API, bucket y secrets sintéticos; activar `RAG_MODE=fallback`.
2. **Staging**: migraciones Alembic; trasladar contenidos de prueba, habilitar Gemini con datos no personales; medir aislamiento entre cursos, citas, latencia y cuotas.
3. **Vectorial**: ejecutar comparativa pgvector/OpenSearch y generar índice desde los materiales, evitando migrar vectores obsoletos.
4. **Seguridad**: validar cookies seguras, refresh rotation, CSRF, rate limits, permisos IAM, endpoints privados y logs; realizar revisión independiente.
5. **Continuidad**: probar backup/restore, alertas y recuperación; documentar RPO/RTO observados.
6. **Producción/piloto**: autorización institucional, datos mínimos, consentimiento aplicable, monitorización y plan de rollback aprobado.

## 11. Rollback y operación

- Conserva la imagen previa y cambia el servicio a la versión anterior si el health check o los smoke tests fallan.
- Antes de migraciones no reversibles, toma snapshot y ensaya restauración. Downgrade Alembic no garantiza reversión semántica de datos.
- Para nueva versión documental, mantiene material anterior activo hasta validar indexación completa; no muestres fragmentos parciales.
- Establece alarmas para errores API, latencia, fallas DB, trabajo de ingesta fallido, cuota/latencia de proveedor y gasto AWS.
- Mantén inventario de modelos y versiones de embeddings para planificar reindexación.

## 12. Criterios de salida del staging

- `GET /api/health` saludable y migraciones al día.
- 401/403 correctos para usuarios/objetos fuera de alcance.
- Estudiante no puede acceder a curso ajeno, material no autorizado ni clave de evaluación antes de cerrar.
- No se puede publicar un reactivo sin aprobación docente.
- El puntaje calculado por servidor está reconciliado con respuestas objetivas.
- Ingesta idempotente con hash; versión anterior permanece activa si la nueva falla.
- RAG devuelve fuentes verificables o abstención y no cruza cursos.
- Backups restaurados en prueba; seguridad y costes revisados; secretos ausentes del repositorio.
