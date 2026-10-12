# Plataforma Monda — anexos de diseño PI7

Fecha de elaboración: 4 de octubre de 2026. Base: PI6 v1.1.

## Consultar el prototipo
Abrir `prototipo/index.html` en un navegador. No necesita servidor ni credenciales. Las diez pantallas y sus acciones son simulaciones de diseño con datos ficticios.

## Contenido
- `bd/schema.sql`: 20 tablas PostgreSQL 16 e índices.
- `bd/diccionario.json`: 140 atributos coherentes con el DDL.
- `api/contrato_api.md` y `api/openapi.json`: contrato de interfaces.
- `diagramas/`: fuentes DOT/SVG y PNG de alta resolución.
- `src/contracts.py`: interfaces de integración; no implementa el backend.
- `docs/decisiones.md`: decisiones PI7 y trazabilidad.

## Base de datos
Sobre una base vacía de PostgreSQL 16: `psql -v ON_ERROR_STOP=1 -d monda -f bd/schema.sql`. El esquema monda debe crearse una sola vez. Los UUID son generados por la aplicación. No contiene usuarios ni datos reales. Los roles de aplicación y migración se crean fuera del script con permisos mínimos.

## Repositorio Git inicial
El ZIP conserva el directorio `.git` con un commit inicial local. Ejecutar `git log --oneline` desde esta carpeta. No se configura un remoto ni se atribuye el commit a los tesistas. La construcción de PI8–PI11 parte de estos contratos.

## Alcance
Los controles intertabla de curso, matrícula, publicación y cierre corresponden al servicio transaccional y a sus pruebas de integración. El DDL impone integridad estructural, unicidad, rangos, coherencia intento-reactivo y auditoría de solo inserción. No se ha ejecutado una campaña de validación institucional.
