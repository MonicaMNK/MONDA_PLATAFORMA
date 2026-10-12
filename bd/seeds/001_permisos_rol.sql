BEGIN;
SET LOCAL search_path = monda, public;

INSERT INTO permisos_rol (rol, permiso, version) VALUES
('administrador','admin:users',1),
('administrador','admin:roles',1),
('administrador','admin:config',1),
('administrador','admin:audit',1),
('administrador','course:read',1),
('administrador','rag:query',1),
('docente','course:read',1),
('docente','course:write',1),
('docente','enrollment:write',1),
('docente','content:read',1),
('docente','content:write',1),
('docente','rag:query',1),
('docente','assessment:write',1),
('docente','analytics:read',1),
('docente','report:export',1),
('estudiante','course:read',1),
('estudiante','content:read',1),
('estudiante','rag:query',1),
('estudiante','assessment:solve',1)
ON CONFLICT (rol, permiso) DO NOTHING;

COMMIT;
