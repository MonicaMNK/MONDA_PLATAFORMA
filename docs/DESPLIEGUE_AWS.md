# Migración y despliegue de Monda en AWS

## Objetivo

Pasar de la instalación local a una arquitectura cloud coherente con PI6/PI7 sin cambiar los contratos principales de la aplicación.

## Arquitectura objetivo

- **Frontend React:** S3 privado + CloudFront o servido por el mismo contenedor durante una primera prueba.
- **API FastAPI:** imagen Docker en ECR y ejecución en ECS/Fargate detrás de un Application Load Balancer HTTPS.
- **Datos transaccionales:** Amazon RDS for PostgreSQL 16 en subredes privadas.
- **Materiales:** bucket S3 privado con cifrado, versionado y acceso por IAM.
- **Ingesta:** para la primera migración puede ejecutarse en FastAPI; en la arquitectura final se mueve a Lambda/cola para desacoplar trabajos largos.
- **Recuperación vectorial:** OpenSearch Service según PI6; `fragmentos_rag` sirve como modo de transición/local.
- **Secretos:** AWS Secrets Manager, nunca `.env` dentro de la imagen.
- **Logs/métricas:** CloudWatch; las trazas RAG pueden enviarse a MLflow según la arquitectura de tesis.

## Fase 1 — preparar el código

1. Copia `.env.example` a un archivo privado y cambia `MONDA_SECRET_KEY`.
2. Establece `MONDA_DEMO=0` y `COOKIE_SECURE=1`.
3. No subas `data/monda.db`, archivos de usuarios ni contraseñas al repositorio.
4. Ejecuta `pytest -q` y verifica `GET /api/health`.

## Fase 2 — RDS PostgreSQL

1. Crea una instancia PostgreSQL 16 en una VPC con acceso solo desde la API.
2. Crea dos identidades de base de datos: una de **migración** y otra de **aplicación** con privilegios mínimos.
3. Ejecuta primero `bd/001_schema_pi7.sql` y luego `bd/002_tablas_operativas_rag_sync.sql` con la identidad de migración.
4. Define en Secrets Manager una URL equivalente a:

```text
postgresql+psycopg://monda_app:***@host-rds:5432/monda
```

5. Inyecta ese secreto al contenedor como `DATABASE_URL`.

> En una migración real desde SQLite, exporta únicamente datos válidos y transforma UUID/fechas explícitamente. No copies el archivo `monda.db` a RDS.

## Fase 3 — S3 para materiales

1. Crea un bucket privado con bloqueo de acceso público, cifrado y versionado.
2. Sustituye el almacenamiento de `data/uploads` por un adaptador S3 manteniendo `s3_key` en la tabla `contenidos`.
3. El navegador no debe recibir credenciales AWS. La API entrega un stream o una URL prefirmada de corta vigencia.
4. Mantén los controles PI7: formato permitido, máximo 20 MiB, autorización de curso y activación de una versión solo tras indexación completa.

## Fase 4 — imagen y API

Construcción local:

```bash
docker build -t monda-api:1.0 .
```

Flujo de despliegue:

1. Crea un repositorio ECR.
2. Autentica Docker contra ECR, etiqueta y publica la imagen.
3. Crea una Task Definition de ECS/Fargate con secretos, CPU/RAM según la carga medida y puerto 8000.
4. Coloca el servicio en subredes privadas; el ALB público termina TLS/HTTPS.
5. Configura health check hacia `/api/health`.
6. Restringe el Security Group de RDS para aceptar PostgreSQL únicamente desde el Security Group del servicio API.

## Fase 5 — frontend

La carpeta `frontend/` incluida aquí ya funciona sin CDN. Para desacoplarla:

1. Publica los archivos estáticos en un bucket S3 privado.
2. Sirve el bucket mediante CloudFront.
3. Configura un dominio HTTPS.
4. Define el origen `/api/*` hacia el ALB o ajusta la URL base de `api()` en `frontend/app.js`.

## Fase 6 — RAG cloud

Ruta recomendada para conservar PI6:

1. Carga del documento → S3.
2. Evento/cola → Lambda de extracción, limpieza y fragmentación.
3. Embeddings → índice vectorial en OpenSearch.
4. Consulta → API valida sesión/matrícula → recupera top K → aplica umbral → solo entonces llama al LLM.
5. Guarda fuentes, score, `evidenceSufficient` y `correlationId`.
6. Si el score es menor que el umbral, responde con abstención sin inventar contenido.

El modo local TF‑IDF puede mantenerse para desarrollo y pruebas automáticas. La interfaz `backend/rag.py` está separada para reemplazar la recuperación sin cambiar la UI.

## Fase 7 — seguridad antes de producción

- HTTPS obligatorio.
- `MONDA_DEMO=0`.
- Clave de firma aleatoria en Secrets Manager.
- Rotación de secretos y credenciales de BD.
- WAF/rate limiting delante de los endpoints públicos si el entorno lo requiere.
- S3 y RDS sin acceso público.
- Cookies `Secure`, `HttpOnly`, `SameSite=Strict` y CSRF para operaciones con cookie.
- Logs sin contraseñas, tokens, claves de reactivos ni contenido personal innecesario.
- Backups y restauración de RDS probados.
- Retención de auditoría definida antes de recolectar datos reales.

## Fase 8 — comprobación posterior al despliegue

1. `/api/health` responde por HTTPS.
2. Login de los tres roles de prueba en un entorno de staging.
3. Un estudiante no puede acceder a un curso sin matrícula.
4. Un documento queda activo solo después de terminar la indexación.
5. El tutor muestra fuentes y se abstiene sin evidencia.
6. No se publica una evaluación con reactivos sin aprobar.
7. La calificación se calcula en el servidor.
8. El último administrador activo no puede desactivarse.
9. Exportaciones seudonimizadas y auditoría visibles solo a roles autorizados.
10. Prueba de carga y disponibilidad se registra como evidencia; no se infiere a partir de un despliegue exitoso.

## Orden práctico de migración

**Local SQLite → RDS → S3 → ECS/ALB → frontend/CloudFront → ingesta Lambda → OpenSearch → observabilidad/MLflow.**

Este orden permite validar cada dependencia antes de introducir la siguiente.
