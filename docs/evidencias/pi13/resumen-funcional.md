# Registro funcional y correspondencia de casos — PI13

Los identificadores canónicos CP01–CP12 conservan las definiciones del PI11–PI12, tabla 2.3. Las ampliaciones usan CP13–CP24 y ES12–ES23. Véanse `casos-canonicos.csv` y `correspondencia-casos.csv`.

## Alcance del registro

`cp-ejecucion.csv` separa `estado_ejecucion` (Ejecutado / Bloqueado / No ejecutado) de `cumple` (Sí / No / Parcial / No verificado). Las fechas y los ejecutores trasladados son declaraciones del registro anterior, conservado en `historico/`. Esta conciliación documental no acredita nuevas corridas. «No ejecutado» indica que no hay una ejecución individual acreditada en este registro; no afirma ausencia de implementación.

La cifra anterior de 14 casos y 12/14 logrados describía otra codificación. No se compara con el inventario ampliado ni se conserva como porcentaje de cumplimiento integral. Una referencia a un test acredita su existencia; para aceptación de campaña se requiere su salida de ejecución.

## Correspondencia por componente

| Componente | Casos canónicos | Alcance |
|---|---|---|
| Contenidos y acceso | CP01, CP02, CP12, CP13, CP22, CP23 | PDF/DOCX, permisos, lectura autorizada y OCR requerido |
| Tutor y calidad RAG | CP03, CP04, CP07, CP15 | Respuesta, abstención, evaluación independiente y latencia |
| Evaluaciones y analítica | CP05, CP06, CP14, CP18–CP21 | Nota, publicación, revisión, promedio, alertas y exportación |
| Sincronización | CP10 | Acción idempotente y permisos |
| Carga y entorno | CP08, CP11 | Rendimiento transaccional y recorrido D07; no son equivalentes |
| Usuarios y calidad | CP09, CP16, CP17, CP24 | SUS, accesibilidad, cobertura y disponibilidad |

## Resultados previamente registrados

- Suite histórica: 78 pruebas aprobadas; no equivale a 78 casos del plan ni a una nueva ejecución.
- CP08: p95 739,61 ms a 25 usuarios virtuales y 785,40 ms a 50; errores 0 % y degradación 6,19 %.
- CP07: calibración complementaria de 60 consultas, diferenciada de la evaluación final. Cobertura factual 85 %, integración 66,67 %, abstención 53,85 % (no lograda), adversariales 75 %. Citas 81/94 = 86,17 %, no verificadas sin registro recuperable.
- CP15: cien duraciones; mediana 1396,55 ms y p95 55732,48 ms. La mediana cumple y el p95 no cumple.
- CP09: media SUS 86,25; muestra efectiva de seis docentes y cuatro estudiantes; participación y sesiones requieren conciliación.
- CP16 y CP24: accesibilidad y disponibilidad no verificadas con la evidencia actual.

Los detalles estadísticos permanecen en PI14. Esta corrección solo concilia la identificación y el alcance de los casos.
