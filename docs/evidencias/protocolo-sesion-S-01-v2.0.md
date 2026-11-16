# Protocolo de la sesion S-01 (version 2.0)

## Estado y alcance

Esta ficha separa la sesion S-01 del protocolo historico `protocolo-baseline-20261109.md` y de la campana de aceptacion del 2026-11-09. Se documenta a partir de los archivos disponibles en el repositorio el 2026-11-15; por si sola no demuestra que esta version estuviera aprobada antes de la sesion.

## Sesion y muestra

- Identificador: S-01.
- Fecha declarada: 2026-11-06.
- Participantes declarados: 16 (14 estudiantes de secundaria y 2 docentes).
- Codigos segun el roster actualizado: P001-P014 estudiantes; P015-P016 docentes.
- Duracion declarada: 95 minutos (08:00-09:35, UTC-3), coincidente con data/usuarios/sesiones.csv y el log actualizado.
- Fuente de composicion: `data/usuarios/sesiones.csv`, `output/consentimientos.csv` y `output/observaciones.json`.

## Tarea y tiempos

La tarea declarada fue consulta y extraccion de informacion, comparando tiempo manual con tiempo en Monda. Las filas pareadas estan en `data/usuarios/tiempos_pareados.csv`; la tabla manual correspondiente esta en `data/usuarios/linea_base_manual.csv`.

Los archivos de sesion indican tiempos, pero la observacion narrativa declara que no se dispone de hojas primarias para respaldar los tiempos manuales. `output/observaciones.json` es una tabla derivada y no sustituye esas hojas originales. Hasta incorporar y vincular las hojas, los tiempos deben presentarse como registros transcritos pendientes de verificacion primaria.

## SUS y consentimiento

`data/usuarios/sus_respuestas.csv` contiene valores de 1 a 5. La nota `docs/observaciones/S-01_observaciones.txt` declara que fueron transcritos de cuestionarios originales. Los cuestionarios fuente no estan adjuntos aqui para cotejo independiente; los resultados calculados desde el CSV deben presentarse como pendientes de verificacion primaria.

`output/consentimientos.csv` enlaza P001-P016 con archivos de Drive por ordinal. Las carpetas contienen imagenes numeradas por rol, pero se debe conservar el registro de correspondencia que confirma el vinculo entre cada codigo P y el documento. Los archivos firmados permanecen en Drive y no deben copiarse al repositorio publico si contienen datos identificables. Verificar enlaces y correspondencia de codigos contra los originales.

## Separacion de campanas

- La campana historica descrita por el protocolo 1.0 es de 10 participantes; sus analisis quedan historicos y separados.
- La campana de aceptacion PI13 del 2026-11-09 reporto SUS de 10 participantes (6 docentes y 4 estudiantes) en sus archivos heredados. No es S-01.
- S-01 es la sesion del 2026-11-06 con 16 participantes declarados (14 estudiantes, 2 docentes). Su inclusion en metodologia no valida automaticamente cada instrumento: el denominador analizable se establece por fuente verificable para cada resultado.
