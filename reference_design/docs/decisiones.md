# Decisiones PI7

- M1: Acceso y usuarios; RF-01 a RF-03; OE1, OE2, OE3. Se concretan rotación de sesión y recuperación de un solo uso.
- M2: Administración; RF-02; OE1, OE2, OE3. Se detalla concurrencia de cambios y protección del último administrador.
- M3: Cursos y contenidos; RF-04 a RF-06; OE1. Se separan documento lógico, versión e idempotencia de ingesta.
- M4: Servicio de embeddings; RF-06 a RF-08 y RF-10; OE1, OE2. Se validan dimensión, norma y versión del modelo.
- M5: Tutor RAG; RF-07 a RF-09; OE2. Se verifica coseno real y se controla acceso a cada fuente.
- M6: Evaluaciones inteligentes; RF-10 a RF-12; OE2. Se fija revisión humana, transacción e inmutabilidad.
- M7: Seguimiento y reportes; RF-13 y RF-14; OE3. Se fijan fórmulas, fecha de corte y revisión docente.
- M8: PWA y sincronización; RF-15; OE1, OE2, OE3. Se delimita qué acciones pueden encolarse y cómo resolver conflictos.

## Aceptación
- CA-M1-01: Dado usuario activo con contraseña correcta, cuando inicia y cierra sesión, entonces recibe JWT de 30 min; tras cierre el refresh deja de funcionar. [RF-01]
- CA-M1-02: Dado estudiante autenticado, cuando invoca una ruta administrativa, entonces recibe 403 y no cambia ningún registro. [RF-02]
- CA-M1-03: Dado token de recuperación usado o vencido, cuando intenta reutilizarlo, entonces se rechaza y no se modifica contraseña; nunca se registra el token. [RNF-03]
- CA-M2-01: Dado administrador con versión vigente, cuando cambia una configuración válida, entonces se incrementa la versión y se audita actor, fecha, objeto y resultado. [RF-02]
- CA-M2-02: Dado un único administrador activo, cuando intenta desactivarse, entonces recibe 409 y conserva su estado. [RN-04]
- CA-M2-03: Dado diez cambios administrativos autorizados, cuando se consulta la bitácora, entonces existen diez registros críticos con correlationId y sin secretos. [RNF-05]
- CA-M3-01: Dado docente propietario con PDF extraíble, cuando carga e indexa una nueva versión, entonces consulta estado indexado y recupera solo su versión activa. [RF-05,06]
- CA-M3-02: Dado archivo sin texto o formato no permitido, cuando intenta indexarlo, entonces obtiene error específico y sigue disponible la versión anterior. [RF-06]
- CA-M3-03: Dado 50 usuarios concurrentes en rutas de metadatos, cuando se ejecuta Artillery, entonces p95 ≤ 800 ms, errores < 1 % y sin pérdida de datos. [RNF-01]
- CA-M4-01: Dado dos textos y modelo configurado, cuando solicita vectorización, entonces recibe dos vectores de 1536 valores finitos, en el mismo orden. [RF-06,07,10]
- CA-M4-02: Dado proveedor devuelve dimensión incorrecta, cuando se valida el lote, entonces se rechaza todo el lote y no se escriben vectores inválidos. [RN-09]
- CA-M4-03: Dado texto con identidad personal no necesaria, cuando se prepara la solicitud, entonces el payload minimizado y los logs excluyen esa identidad y las credenciales. [RNF-03]
- CA-M5-01: Dado matrícula activa y contexto con coseno ≥ 0,35, cuando consulta el tutor, entonces obtiene respuesta con fuentes recuperables del curso e historial. [RF-07 a 09]
- CA-M5-02: Dado pregunta sin evidencia suficiente, cuando se consulta el tutor, entonces devuelve evidenceSufficient=false y cero llamadas al generador. [RF-08]
- CA-M5-03: Dado 100 consultas sobre corpus congelado, cuando se mide de envío a respuesta, entonces mediana ≤ 3 s y p95 ≤ 5 s; se reporta además la latencia del proveedor. [RNF-02]
- CA-M6-01: Dado docente con todos los reactivos aprobados, cuando publica y un estudiante resuelve, entonces conserva versión y califica según claves del servidor. [RF-10 a 12]
- CA-M6-02: Dado evaluación con un reactivo en borrador, cuando intenta publicar, entonces recibe 409 y la evaluación permanece en borrador. [RF-11]
- CA-M6-03: Dado estudiante con intento abierto, cuando solicita la evaluación o reenvía cierre, entonces no recibe claves antes del cierre y el reenvío no duplica calificación. [RNF-03]
- CA-M7-01: Dado datos con dos intentos de 10 y 14, cuando consulta indicadores al mismo corte, entonces muestra promedio 12/20 y conteos reconciliados con RDS. [RF-13]
- CA-M7-02: Dado estudiante sin intentos cerrados, cuando se calcula alerta por nota, entonces muestra sin datos y no emite alerta por promedio cero. [RF-14]
- CA-M7-03: Dado docente autorizado de un curso, cuando exporta resultados, entonces CSV contiene seudónimos y corte; no filtra cursos ajenos ni fórmulas ejecutables. [RNF-03]
- CA-M8-01: Dado vista cargada y borrador permitido, cuando se interrumpe la conexión, entonces puede leer contenido permitido y ve estado pendiente del borrador. [RF-15]
- CA-M8-02: Dado misma actionId con carga distinta, cuando se sincroniza, entonces devuelve conflicto y conserva el borrador para decisión del usuario. [RN-21]
- CA-M8-03: Dado una cola de 50 acciones válidas con reenvío, cuando se restablece la red dos veces, entonces cada acción se aplica una vez y el reporte web alcanza accesibilidad ≥ 90. [RNF-06]