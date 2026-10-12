-- Plataforma Monda - Entrega 1
-- PostgreSQL 16 + pgvector | 22 tablas
-- Fuente funcional: PI6/PI7 T6-T9, adaptada al requisito local de RAG triple modo.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS monda;
SET LOCAL search_path = monda, public;

-- 01. USUARIOS
CREATE TABLE IF NOT EXISTS usuarios (
  id uuid PRIMARY KEY,
  rol varchar(20) NOT NULL CHECK (rol IN ('administrador','docente','estudiante')),
  nombre varchar(150) NOT NULL,
  correo varchar(254) NOT NULL,
  password_hash varchar(100) NOT NULL,
  seudonimo uuid NOT NULL UNIQUE,
  estado varchar(15) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('activo','inactivo','pendiente')),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 02. CURSOS
CREATE TABLE IF NOT EXISTS cursos (
  id uuid PRIMARY KEY,
  docente_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  nombre varchar(150) NOT NULL,
  estado varchar(12) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','archivado')),
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 03. MATRICULAS
CREATE TABLE IF NOT EXISTS matriculas (
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  estudiante_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  estado varchar(12) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','inactiva')),
  creado_en timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (curso_id, estudiante_id)
);

-- 04. CONTENIDOS VERSIONADOS
CREATE TABLE IF NOT EXISTS contenidos (
  id uuid PRIMARY KEY,
  documento_id uuid NOT NULL,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  version integer NOT NULL CHECK (version > 0),
  nombre_original varchar(255) NOT NULL,
  mime_type varchar(100) NOT NULL CHECK (mime_type IN (
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  )),
  tamano_bytes bigint NOT NULL CHECK (tamano_bytes > 0 AND tamano_bytes <= 20971520),
  s3_key text NOT NULL UNIQUE,
  hash_sha256 char(64) NOT NULL,
  autor_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  estado_indexacion varchar(15) NOT NULL DEFAULT 'pendiente'
    CHECK (estado_indexacion IN ('pendiente','procesando','indexado','error')),
  activo boolean NOT NULL DEFAULT false,
  modelo_embedding varchar(100) NOT NULL DEFAULT 'gemini-embedding-2',
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (documento_id, version),
  UNIQUE (id, curso_id),
  CHECK (NOT activo OR estado_indexacion = 'indexado')
);

-- 05. CONVERSACIONES
CREATE TABLE IF NOT EXISTS conversaciones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  estado varchar(10) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','cerrada')),
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 06. MENSAJES
CREATE TABLE IF NOT EXISTS mensajes (
  id uuid PRIMARY KEY,
  conversacion_id uuid NOT NULL REFERENCES conversaciones(id) ON DELETE CASCADE,
  autor varchar(10) NOT NULL CHECK (autor IN ('usuario','tutor')),
  contenido text NOT NULL,
  fuentes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(fuentes) = 'array'),
  score_max double precision CHECK (score_max BETWEEN -1 AND 1),
  evidencia_suficiente boolean NOT NULL DEFAULT false,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 07. VALORACIONES
CREATE TABLE IF NOT EXISTS valoraciones (
  id uuid PRIMARY KEY,
  mensaje_id uuid NOT NULL REFERENCES mensajes(id) ON DELETE CASCADE,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  util boolean NOT NULL,
  comentario varchar(500),
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (mensaje_id, usuario_id)
);

-- 08. EVALUACIONES
CREATE TABLE IF NOT EXISTS evaluaciones (
  id uuid PRIMARY KEY,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  titulo varchar(200) NOT NULL,
  configuracion jsonb NOT NULL CHECK (jsonb_typeof(configuracion) = 'object'),
  estado varchar(12) NOT NULL DEFAULT 'borrador' CHECK (estado IN ('borrador','publicada','cerrada')),
  fecha_inicio timestamptz,
  fecha_fin timestamptz,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  creado_en timestamptz NOT NULL DEFAULT now(),
  CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin > fecha_inicio),
  CHECK (estado = 'borrador' OR (fecha_inicio IS NOT NULL AND fecha_fin IS NOT NULL))
);

-- 09. REACTIVOS
CREATE TABLE IF NOT EXISTS reactivos (
  id uuid PRIMARY KEY,
  evaluacion_id uuid NOT NULL REFERENCES evaluaciones(id) ON DELETE RESTRICT,
  enunciado text NOT NULL,
  opciones jsonb NOT NULL CHECK (jsonb_typeof(opciones) = 'object' AND opciones <> '{}'::jsonb),
  clave_correcta varchar(10) NOT NULL,
  justificacion text NOT NULL,
  nivel_bloom varchar(15) NOT NULL CHECK (nivel_bloom IN ('recordar','comprender','aplicar','analizar','evaluar','crear')),
  dificultad varchar(8) NOT NULL CHECK (dificultad IN ('baja','media','alta')),
  contenido_id uuid NOT NULL REFERENCES contenidos(id) ON DELETE RESTRICT,
  fragmento_id text NOT NULL,
  estado_revision varchar(10) NOT NULL DEFAULT 'borrador'
    CHECK (estado_revision IN ('borrador','aprobado','rechazado')),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  revisado_por uuid REFERENCES usuarios(id) ON DELETE RESTRICT,
  fecha_revision timestamptz,
  UNIQUE (id, evaluacion_id),
  CHECK (opciones ? clave_correcta),
  CHECK (estado_revision <> 'aprobado' OR (revisado_por IS NOT NULL AND fecha_revision IS NOT NULL))
);

-- 10. INTENTOS
CREATE TABLE IF NOT EXISTS intentos (
  id uuid PRIMARY KEY,
  evaluacion_id uuid NOT NULL REFERENCES evaluaciones(id) ON DELETE RESTRICT,
  estudiante_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  fecha_inicio timestamptz NOT NULL DEFAULT now(),
  fecha_cierre timestamptz,
  puntaje numeric(5,2) CHECK (puntaje BETWEEN 0 AND 20),
  estado varchar(10) NOT NULL DEFAULT 'abierto' CHECK (estado IN ('abierto','cerrado')),
  UNIQUE (evaluacion_id, estudiante_id),
  UNIQUE (id, evaluacion_id),
  CHECK (
    (estado = 'abierto' AND fecha_cierre IS NULL AND puntaje IS NULL)
    OR
    (estado = 'cerrado' AND fecha_cierre IS NOT NULL AND puntaje IS NOT NULL)
  )
);

-- 11. RESPUESTAS
CREATE TABLE IF NOT EXISTS respuestas (
  id uuid PRIMARY KEY,
  intento_id uuid NOT NULL,
  reactivo_id uuid NOT NULL,
  evaluacion_id uuid NOT NULL,
  opcion_elegida varchar(10),
  es_correcta boolean NOT NULL,
  UNIQUE (intento_id, reactivo_id),
  FOREIGN KEY (intento_id, evaluacion_id) REFERENCES intentos(id, evaluacion_id) ON DELETE RESTRICT,
  FOREIGN KEY (reactivo_id, evaluacion_id) REFERENCES reactivos(id, evaluacion_id) ON DELETE RESTRICT
);

-- 12. EVENTOS
CREATE TABLE IF NOT EXISTS eventos (
  id uuid PRIMARY KEY,
  usuario_seudonimo uuid NOT NULL REFERENCES usuarios(seudonimo) ON DELETE RESTRICT,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  tipo varchar(40) NOT NULL,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 13. ALERTAS
CREATE TABLE IF NOT EXISTS alertas (
  id uuid PRIMARY KEY,
  estudiante_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  regla varchar(40) NOT NULL,
  evidencia jsonb NOT NULL CHECK (jsonb_typeof(evidencia) = 'object'),
  estado varchar(10) NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta','revisada')),
  revisado_por uuid REFERENCES usuarios(id) ON DELETE RESTRICT,
  fecha_revision timestamptz,
  creado_en timestamptz NOT NULL DEFAULT now(),
  CHECK (estado <> 'revisada' OR (revisado_por IS NOT NULL AND fecha_revision IS NOT NULL))
);

-- 14. AUDITORIA
CREATE TABLE IF NOT EXISTS auditoria (
  id uuid PRIMARY KEY,
  actor_id uuid REFERENCES usuarios(id) ON DELETE RESTRICT,
  accion varchar(60) NOT NULL,
  objeto text NOT NULL,
  resultado varchar(30) NOT NULL,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 15. CONFIGURACION
CREATE TABLE IF NOT EXISTS configuracion (
  clave varchar(60) PRIMARY KEY,
  valor jsonb NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  actualizado_por uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- 16. SESIONES
CREATE TABLE IF NOT EXISTS sesiones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  familia_id uuid NOT NULL,
  token_hash char(64) NOT NULL UNIQUE,
  expira_en timestamptz NOT NULL,
  revocada boolean NOT NULL DEFAULT false,
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 17. RECUPERACIONES
CREATE TABLE IF NOT EXISTS recuperaciones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  token_hash char(64) NOT NULL UNIQUE,
  expira_en timestamptz NOT NULL,
  usado_en timestamptz
);

-- 18. PERMISOS_ROL
CREATE TABLE IF NOT EXISTS permisos_rol (
  rol varchar(20) NOT NULL CHECK (rol IN ('administrador','docente','estudiante')),
  permiso varchar(80) NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  PRIMARY KEY (rol, permiso)
);

-- 19. SINCRONIZACIONES
CREATE TABLE IF NOT EXISTS sincronizaciones (
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  accion_id uuid NOT NULL,
  payload_hash char(64) NOT NULL,
  resultado jsonb NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (usuario_id, accion_id)
);

-- 20. TRABAJOS
CREATE TABLE IF NOT EXISTS trabajos (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE RESTRICT,
  tipo varchar(15) NOT NULL CHECK (tipo IN ('ingesta','generacion')),
  estado varchar(15) NOT NULL DEFAULT 'pendiente'
    CHECK (estado IN ('pendiente','procesando','completado','error')),
  resultado jsonb,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

-- 21. FRAGMENTOS_RAG
-- Vector canónico de 768 dimensiones: compatible con gemini-embedding-2 y
-- con un embedding local de 768d (p.ej. nomic-embed-text). En modo ligero puede ser NULL.
CREATE TABLE IF NOT EXISTS fragmentos_rag (
  id uuid PRIMARY KEY,
  contenido_id uuid NOT NULL,
  curso_id uuid NOT NULL,
  ordinal integer NOT NULL CHECK (ordinal >= 0),
  texto text NOT NULL,
  ubicacion varchar(255),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
  embedding vector(768),
  embedding_model varchar(100),
  embedding_provider varchar(20) CHECK (embedding_provider IS NULL OR embedding_provider IN ('gemini','ollama','fallback')),
  hash_fragmento char(64) NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (contenido_id, ordinal),
  UNIQUE (contenido_id, hash_fragmento),
  FOREIGN KEY (contenido_id, curso_id) REFERENCES contenidos(id, curso_id) ON DELETE CASCADE
);

-- 22. BORRADORES_SYNC
CREATE TABLE IF NOT EXISTS borradores_sync (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  curso_id uuid REFERENCES cursos(id) ON DELETE CASCADE,
  tipo varchar(40) NOT NULL CHECK (tipo IN ('borrador_personal','valoracion')),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
  base_version integer NOT NULL DEFAULT 1 CHECK (base_version > 0),
  accion_id uuid,
  sincronizado boolean NOT NULL DEFAULT false,
  actualizado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (usuario_id, accion_id)
);

-- Indices de integridad / rendimiento.
CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_correo ON usuarios (lower(correo));
CREATE UNIQUE INDEX IF NOT EXISTS ux_contenido_activo ON contenidos(documento_id) WHERE activo;
CREATE UNIQUE INDEX IF NOT EXISTS ux_alerta_abierta ON alertas(estudiante_id, curso_id, regla) WHERE estado = 'abierta';
CREATE INDEX IF NOT EXISTS ix_matriculas_estudiante ON matriculas(estudiante_id, estado);
CREATE INDEX IF NOT EXISTS ix_cursos_docente ON cursos(docente_id, estado);
CREATE INDEX IF NOT EXISTS ix_contenidos_curso ON contenidos(curso_id, estado_indexacion, activo);
CREATE INDEX IF NOT EXISTS ix_mensajes_conversacion ON mensajes(conversacion_id, creado_en);
CREATE INDEX IF NOT EXISTS ix_evaluaciones_curso ON evaluaciones(curso_id, estado);
CREATE INDEX IF NOT EXISTS ix_intentos_estudiante ON intentos(estudiante_id, estado);
CREATE INDEX IF NOT EXISTS ix_eventos_curso_fecha ON eventos(curso_id, creado_en);
CREATE INDEX IF NOT EXISTS ix_auditoria_fecha ON auditoria(creado_en);
CREATE INDEX IF NOT EXISTS ix_trabajos_curso_estado ON trabajos(curso_id, estado);
CREATE INDEX IF NOT EXISTS ix_fragmentos_rag_curso ON fragmentos_rag(curso_id, contenido_id);
CREATE INDEX IF NOT EXISTS ix_fragmentos_rag_fts ON fragmentos_rag USING gin (to_tsvector('spanish', texto));
CREATE INDEX IF NOT EXISTS ix_fragmentos_rag_vector_hnsw
  ON fragmentos_rag USING hnsw (embedding vector_cosine_ops)
  WHERE embedding IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_borradores_sync_usuario ON borradores_sync(usuario_id, sincronizado, actualizado_en);

-- Auditoría append-only (RNF-05).
CREATE OR REPLACE FUNCTION bloquear_mutacion_auditoria()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'AUDITORIA es append-only: UPDATE/DELETE no permitidos';
END;
$$;

DROP TRIGGER IF EXISTS auditoria_inmutable ON auditoria;
CREATE TRIGGER auditoria_inmutable
BEFORE UPDATE OR DELETE ON auditoria
FOR EACH ROW EXECUTE FUNCTION bloquear_mutacion_auditoria();

-- 23. Carpetas de materiales: semanas, unidades y subcarpetas.
ALTER TABLE cursos ADD COLUMN IF NOT EXISTS descripcion text NOT NULL DEFAULT '';
ALTER TABLE conversaciones ADD COLUMN IF NOT EXISTS alcance jsonb NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS carpetas_contenido (
  id uuid PRIMARY KEY,
  curso_id uuid NOT NULL REFERENCES cursos(id),
  padre_id uuid REFERENCES carpetas_contenido(id),
  nombre varchar(100) NOT NULL,
  creado_por uuid NOT NULL REFERENCES usuarios(id),
  creado_en timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE contenidos ADD COLUMN IF NOT EXISTS carpeta_id uuid REFERENCES carpetas_contenido(id);
CREATE INDEX IF NOT EXISTS ix_carpetas_curso ON carpetas_contenido(curso_id);
CREATE INDEX IF NOT EXISTS ix_contenidos_carpeta_id ON contenidos(carpeta_id);

COMMIT;
