-- Plataforma Monda PI7 | PostgreSQL 16 | Diseño 04/10/2026

-- Parámetros y estructuras detalladas propuestos; no representa una BD institucional instalada.

BEGIN;

CREATE SCHEMA IF NOT EXISTS monda;

SET LOCAL search_path = monda, public;

CREATE TABLE usuarios (
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

CREATE TABLE cursos (
  id uuid PRIMARY KEY,
  docente_id uuid NOT NULL REFERENCES usuarios(id),
  nombre varchar(150) NOT NULL,
  estado varchar(12) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','archivado')),
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE matriculas (
  curso_id uuid NOT NULL REFERENCES cursos(id),
  estudiante_id uuid NOT NULL REFERENCES usuarios(id),
  estado varchar(12) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','inactiva')),
  creado_en timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (curso_id, estudiante_id)
);

CREATE TABLE contenidos (
  id uuid PRIMARY KEY,
  documento_id uuid NOT NULL,
  curso_id uuid NOT NULL REFERENCES cursos(id),
  version integer NOT NULL CHECK (version > 0),
  s3_key text NOT NULL UNIQUE,
  hash_sha256 char(64) NOT NULL,
  autor_id uuid NOT NULL REFERENCES usuarios(id),
  estado_indexacion varchar(15) NOT NULL DEFAULT 'pendiente' CHECK (estado_indexacion IN ('pendiente','procesando','indexado','error')),
  activo boolean NOT NULL DEFAULT false,
  modelo_embedding varchar(100) NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (documento_id, version),
  CHECK (NOT activo OR estado_indexacion = 'indexado')
);

CREATE TABLE conversaciones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  curso_id uuid NOT NULL REFERENCES cursos(id),
  estado varchar(10) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa','cerrada')),
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE mensajes (
  id uuid PRIMARY KEY,
  conversacion_id uuid NOT NULL REFERENCES conversaciones(id),
  autor varchar(10) NOT NULL CHECK (autor IN ('usuario','tutor')),
  contenido text NOT NULL,
  fuentes jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(fuentes) = 'array'),
  score_max double precision CHECK (score_max BETWEEN -1 AND 1),
  evidencia_suficiente boolean NOT NULL DEFAULT false,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE valoraciones (
  id uuid PRIMARY KEY,
  mensaje_id uuid NOT NULL REFERENCES mensajes(id),
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  util boolean NOT NULL,
  comentario varchar(500),
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (mensaje_id, usuario_id)
);

CREATE TABLE evaluaciones (
  id uuid PRIMARY KEY,
  curso_id uuid NOT NULL REFERENCES cursos(id),
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

CREATE TABLE reactivos (
  id uuid PRIMARY KEY,
  evaluacion_id uuid NOT NULL REFERENCES evaluaciones(id),
  enunciado text NOT NULL,
  opciones jsonb NOT NULL CHECK (jsonb_typeof(opciones) = 'object' AND opciones <> '{}'::jsonb),
  clave_correcta varchar(10) NOT NULL,
  justificacion text NOT NULL,
  nivel_bloom varchar(15) NOT NULL CHECK (nivel_bloom IN ('recordar','comprender','aplicar','analizar','evaluar','crear')),
  dificultad varchar(8) NOT NULL CHECK (dificultad IN ('baja','media','alta')),
  contenido_id uuid NOT NULL REFERENCES contenidos(id),
  fragmento_id text NOT NULL,
  estado_revision varchar(10) NOT NULL DEFAULT 'borrador' CHECK (estado_revision IN ('borrador','aprobado','rechazado')),
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  revisado_por uuid REFERENCES usuarios(id),
  fecha_revision timestamptz,
  UNIQUE (id, evaluacion_id),
  CHECK (opciones ? clave_correcta),
  CHECK (estado_revision <> 'aprobado' OR (revisado_por IS NOT NULL AND fecha_revision IS NOT NULL))
);

CREATE TABLE intentos (
  id uuid PRIMARY KEY,
  evaluacion_id uuid NOT NULL REFERENCES evaluaciones(id),
  estudiante_id uuid NOT NULL REFERENCES usuarios(id),
  fecha_inicio timestamptz NOT NULL DEFAULT now(),
  fecha_cierre timestamptz,
  puntaje numeric(5,2) CHECK (puntaje BETWEEN 0 AND 20),
  estado varchar(10) NOT NULL DEFAULT 'abierto' CHECK (estado IN ('abierto','cerrado')),
  UNIQUE (evaluacion_id, estudiante_id),
  UNIQUE (id, evaluacion_id),
  CHECK ((estado = 'abierto' AND fecha_cierre IS NULL AND puntaje IS NULL) OR (estado = 'cerrado' AND fecha_cierre IS NOT NULL AND puntaje IS NOT NULL))
);

CREATE TABLE respuestas (
  id uuid PRIMARY KEY,
  intento_id uuid NOT NULL,
  reactivo_id uuid NOT NULL,
  evaluacion_id uuid NOT NULL,
  opcion_elegida varchar(10),
  es_correcta boolean NOT NULL,
  UNIQUE (intento_id, reactivo_id),
  FOREIGN KEY (intento_id, evaluacion_id) REFERENCES intentos(id, evaluacion_id),
  FOREIGN KEY (reactivo_id, evaluacion_id) REFERENCES reactivos(id, evaluacion_id)
);

CREATE TABLE eventos (
  id uuid PRIMARY KEY,
  usuario_seudonimo uuid NOT NULL REFERENCES usuarios(seudonimo),
  curso_id uuid NOT NULL REFERENCES cursos(id),
  tipo varchar(40) NOT NULL,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE alertas (
  id uuid PRIMARY KEY,
  estudiante_id uuid NOT NULL REFERENCES usuarios(id),
  curso_id uuid NOT NULL REFERENCES cursos(id),
  regla varchar(40) NOT NULL,
  evidencia jsonb NOT NULL,
  estado varchar(10) NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta','revisada')),
  revisado_por uuid REFERENCES usuarios(id),
  fecha_revision timestamptz,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auditoria (
  id uuid PRIMARY KEY,
  actor_id uuid REFERENCES usuarios(id),
  accion varchar(60) NOT NULL,
  objeto text NOT NULL,
  resultado varchar(30) NOT NULL,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE configuracion (
  clave varchar(60) PRIMARY KEY,
  valor jsonb NOT NULL,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  actualizado_por uuid NOT NULL REFERENCES usuarios(id),
  actualizado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sesiones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  familia_id uuid NOT NULL,
  token_hash char(64) NOT NULL UNIQUE,
  expira_en timestamptz NOT NULL,
  revocada boolean NOT NULL DEFAULT false,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE recuperaciones (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  token_hash char(64) NOT NULL UNIQUE,
  expira_en timestamptz NOT NULL,
  usado_en timestamptz
);

CREATE TABLE permisos_rol (
  rol varchar(20) NOT NULL CHECK (rol IN ('administrador','docente','estudiante')),
  permiso varchar(80) NOT NULL,
  version integer NOT NULL DEFAULT 1,
  PRIMARY KEY (rol, permiso)
);

CREATE TABLE sincronizaciones (
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  accion_id uuid NOT NULL,
  payload_hash char(64) NOT NULL,
  resultado jsonb NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (usuario_id, accion_id)
);

CREATE TABLE trabajos (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id),
  curso_id uuid NOT NULL REFERENCES cursos(id),
  tipo varchar(15) NOT NULL CHECK (tipo IN ('ingesta','generacion')),
  estado varchar(15) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente','procesando','completado','error')),
  resultado jsonb,
  correlation_id uuid NOT NULL,
  creado_en timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX ux_usuarios_correo ON usuarios (lower(correo));

CREATE UNIQUE INDEX ux_contenido_activo ON contenidos(documento_id) WHERE activo;

CREATE UNIQUE INDEX ux_alerta_abierta ON alertas(estudiante_id, curso_id, regla) WHERE estado = 'abierta';

CREATE INDEX ix_contenidos_curso ON contenidos(curso_id, estado_indexacion);

CREATE INDEX ix_mensajes_conversacion ON mensajes(conversacion_id, creado_en);

CREATE INDEX ix_eventos_curso_fecha ON eventos(curso_id, creado_en);

CREATE INDEX ix_auditoria_fecha ON auditoria(creado_en);

CREATE FUNCTION bloquear_mutacion_auditoria() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Auditoria de solo insercion'; END; $$;

CREATE TRIGGER auditoria_inmutable BEFORE UPDATE OR DELETE ON auditoria FOR EACH ROW EXECUTE FUNCTION bloquear_mutacion_auditoria();

-- RN-14 a RN-17 requieren servicio transaccional y pruebas de integración.

-- El rol de aplicación tendrá permisos mínimos; el propietario del esquema se reserva para migraciones.

COMMIT;
