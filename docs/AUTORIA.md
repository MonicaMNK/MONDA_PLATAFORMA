# Autoría y atribución de tareas

## Alcance y criterio

Este registro resume la autoría que puede verificarse en el historial Git disponible al 9 de noviembre de 2026. Se revisaron las referencias locales `main` (`ac6ca30`), `develop` (`2fae9cb`) y `fix/midterm-exam-corrections` (`85a23d8`), junto con sus commits alcanzables.

La columna «responsable principal según Git» identifica a la persona que figura como autora de los commits citados para esa tarea. Es una atribución de cambios registrados; por sí sola no prueba quién diseñó una decisión, hizo trabajo no comprometido, revisó el cambio o participó en la ejecución manual. Los commits de merge y los snapshots automáticos no se cuentan como contribuciones de implementación. Los archivos locales sin seguimiento y los cambios aún no comprometidos tampoco se atribuyen mediante este historial.

## Integrantes e identidades Git

| Integrante | Identidad universitaria | Identidades históricas relacionadas |
|---|---|---|
| Daniel Leonardo Escribas Alan (T5) | `daniel.escribas@unmsm.edu.pe` | `DanielLeonardo23 <daniel.escribas@unmsm.edu.pe>` |
| Mónica Paola Mendoza Melo (T9) | `monica.mendoza2@unmsm.edu.pe` | `Monica <User@MONICALAPTOP>`; `MonicaMNK <monica.mendoza2@unmsm.edu.pe>` |

La relación entre identidades consta en [`.mailmap`](../.mailmap). El mapa facilita la presentación unificada en herramientas compatibles; no reescribe los objetos Git originales ni certifica por sí solo la identidad de quien realizó trabajo fuera del repositorio.

## Matriz de contribuciones verificables

| ID | Tarea o entregable | Responsable principal según los commits citados | Contribución registrada | Evidencia Git principal |
|---|---|---|---|---|
| A-01 | Implementación inicial de componentes backend, API, modelos y frontend | Mónica | Commit amplio de implementación de componentes y commits posteriores sobre sesión y API de analítica, evaluaciones, contenidos, RAG y sincronización. | `998edbd`, `cb19b28`, `360a254` |
| A-02 | Implementación funcional e integración de módulos de la plataforma | Daniel | Commit funcional que modifica routers, servicios, repositorios, migraciones, frontend y documentación. La amplitud del commit no permite asignar cada archivo individual a una sola persona fuera de lo registrado. | `da62c98` |
| A-03 | Carga de materiales de curso y semillas asociadas | Mónica | Cambio de cursos, datos semilla y pruebas de carga de materiales. | `458731f` |
| A-04 | Extracción de contenidos, OCR y verificación de indexación de formatos | Daniel | Implementación y pruebas de extracción/indexación para PDF y DOCX. | `7096a0c` |
| A-05 | Autorización de procesamiento externo, aceptación legal y acceso a Gemini | Daniel | Cambios en autorización, condiciones, dependencias, rutas legales y controles para impedir Gemini sin autorización. | `b07ebc8`, `d1ac94a`, `6ab8ac3`, `a000b57` |
| A-06 | Recuperación RAG, abstención, umbral de evidencia y citas fundamentadas | Daniel | Cambios en recuperación, margen de evidencia, rechazo de citas no fundamentadas y pruebas correspondientes. | `41ce615`, `30266b3`, `a99018e`, `ad6fb19`, `f6e4ee6` |
| A-07 | Calibración RAG con Gemini y análisis de umbrales | Mónica | Commits de calibración inicial, endpoint Gemini, ajustes y resultados de calibración; también cambios posteriores en el servicio/configuración RAG y pruebas. | `a562da4`, `c40f04f`, `722886c`, `ab41f85`, `b4a3294` |
| A-08 | Banco final de preguntas y evaluación live | Mónica | Commits de banco de preguntas y evaluación; la autoría del commit no sustituye la revisión docente individual de cada reactivo. | `dfbfaff`, `2fae9cb` |
| A-09 | Evaluador de métricas OE2, trazabilidad y pruebas del evaluador | Daniel | Ajuste del artefacto de calibración explícito y cobertura de métricas/pruebas de aceptación. | `6dfb05f`, `dc92129` |
| A-10 | PWA, borradores offline y sincronización con verificación de permisos | Daniel | Implementación del service worker, interfaz de sincronización, rutas y pruebas asociadas. | `9a9b36a` |
| A-11 | Correcciones de PI11–PI12 en pruebas de administración, RAG y flujo de aprendizaje | Mónica | Commit de correcciones que modifica pruebas de administración, fixes básicos y flujo de aprendizaje. | `dbc5916` |
| A-12 | Instrumentación de pruebas de carga, comparación y perfil k6 reproducible | Daniel | Comparador de corridas, perfil k6, configuración reproducible y centralización de umbrales. | `a90f7fe`, `44b9496`, `b2f89ab`, `e72457b` |
| A-13 | Registro documental de resultados k6 25/50 VU y repetición con pool 30/30 | Daniel | Commits que incorporan los JSON de ejecución y el informe de resultados. El historial documenta el registro; la medición se respalda en los artefactos de ejecución enlazados desde el informe. | `a895d7d`, `5aba8c8`, `ecf613a` |
| A-14 | Validación PostgreSQL/pgvector y resultados de la suite | Daniel | Cambios de evidencia de integración PostgreSQL/pgvector y resultados de suite. | `c7642ed`, `df2fc97`, `5c07837` |
| A-15 | Instrumentación de análisis pareado y asignación balanceada AB | Daniel | Implementación del análisis de efectos pareados y generador de asignaciones balanceadas. Estos commits acreditan el código, no la participación de personas ni la autenticidad de tiempos cargados después. | `0a3c181`, `04c1879` |
| A-16 | Análisis de calificaciones de expertos y concordancia | Daniel | Implementación del análisis estadístico y de sus entradas/salidas. La captura de calificaciones y la identidad de evaluadores requieren respaldo independiente. | `58bbdaf` |
| A-17 | Evidencia y documentación de entregas PI9–PI10 y ES06–ES10 | Daniel | Registro de resultados, capturas, evidencias sintéticas y documentación de escenarios. | `8015a37`, `4fd7cf5`, `39400b6`, `3afbb48`, `b0ce2e0` |
| A-18 | Correcciones de tesis y consolidación documental del equipo | Mónica y Daniel, en commits separados | Mónica registró una actualización de tesis y correcciones PI11–PI12; Daniel registró la integración del informe y una actualización posterior del borrador final. No se atribuye revisión mutua sin un registro explícito de revisión. | Mónica: `e125a17`, `dbc5916`; Daniel: `4b7cc4c`, `ac6ca30` |
| A-19 | Registro inicial de autoría del equipo | Mónica | Añadió el registro de participación del equipo que dio origen a este documento. | `85a23d8` |

## Tareas sin atribución individual suficiente

El historial consultado no permite determinar de forma fiable quién dirigió o ejecutó cada una de estas actividades. Deben asignarse con respaldo del equipo —por ejemplo, actas, PR con revisión registrada, bitácora de sesión u observación firmada— y no inferirse solo de que alguien escribió el código relacionado:

- revisión cruzada y aprobación de cambios;
- aplicación de encuestas SUS y reclutamiento/consentimiento de participantes;
- ejecución manual de pruebas desde navegador;
- toma de tiempos manuales y con Monda;
- revisión docente de reactivos de calibración o evaluación;
- capturas o videos de demostración;
- actividades realizadas fuera de Git o en commits compartidos sin `Co-authored-by`.

En la revisión del repositorio no se encontró el archivo MP4 indicado por el índice local `docs/evidencias/video-indice-20261109.md`. Por ello, ese índice no acredita que el video exista ni valida sus minutajes o el reparto descrito. Para cerrar la evidencia audiovisual, incorporar la grabación real, comprobar que abre, registrar duración y fecha, y verificar cada intervalo y participante contra el contenido. Hasta entonces, el componente de video queda **pendiente de evidencia verificable**.

## Límites de interpretación

- La fecha de un commit indica cuándo se registró en Git, no necesariamente cuándo se realizó toda la tarea.
- Un autor Git identifica quién creó el commit según la configuración local; no prueba por sí solo autoría intelectual, ejecución manual ni revisión por otra persona.
- Un commit de merge integra historiales, pero no convierte al autor del merge en autor de cada cambio integrado.
- La matriz se debe actualizar cuando se incorporen commits nuevos o evidencia externa verificable. Las contribuciones no respaldadas se deben dejar como no determinadas hasta documentarlas.
