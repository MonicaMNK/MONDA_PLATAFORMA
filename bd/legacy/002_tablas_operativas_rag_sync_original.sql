-- Extensión operativa de PI7 para implementación ejecutable.
-- Mantiene las 20 tablas del diseño y agrega 2 tablas de soporte local.
BEGIN;
SET LOCAL search_path = monda, public;

-- Columna operativa usada por la UI para conservar el nombre del archivo.
ALTER TABLE contenidos ADD COLUMN IF NOT EXISTS nombre_original varchar(255) NOT NULL DEFAULT 'material';

CREATE TABLE IF NOT EXISTS fragmentos_rag (
  id uuid PRIMARY KEY,
  contenido_id uuid NOT NULL REFERENCES contenidos(id) ON DELETE CASCADE,
  curso_id uuid NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
  ordinal integer NOT NULL CHECK (ordinal > 0),
  texto text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  creado_en timestamptz NOT NULL DEFAULT now(),
  UNIQUE (contenido_id, ordinal)
);
CREATE INDEX IF NOT EXISTS ix_fragmentos_rag_curso ON fragmentos_rag(curso_id);
CREATE INDEX IF NOT EXISTS ix_fragmentos_rag_contenido ON fragmentos_rag(contenido_id);

CREATE TABLE IF NOT EXISTS borradores_sync (
  id uuid PRIMARY KEY,
  usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  tipo varchar(40) NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  version integer NOT NULL DEFAULT 1 CHECK (version > 0),
  sincronizado boolean NOT NULL DEFAULT false,
  actualizado_en timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_borradores_sync_usuario ON borradores_sync(usuario_id, sincronizado);
COMMIT;
