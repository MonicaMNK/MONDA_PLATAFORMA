# Evidencia E2: respuesta citada y abstención en interfaz (Control de Estado Pendiente)

## 1. Identificación de la ejecución (UI en Navegador)

- **Fecha y hora:** 2026-11-09T17:30:37Z
- **Responsable:** evaluador local
- **Commit evaluado (UI):** c1f033861c280f12f9ed63792c06b1eef7ce8a84
- **Rama:** develop
- **Estado:** APROBADO
- **Entorno:** local
- **URL de la aplicación:** http://127.0.0.1:8001
- **Navegador y versión:** Chrome 130.0.0.0
- **Sistema operativo:** Windows 11

## 2. Configuración del sistema (Referencia API de Respaldo)

Los siguientes datos corresponden a los componentes verificados en la capa de servicios backend (API) y deben ser contrastados visualmente en la interfaz:
- **Proveedor RAG seleccionado en la interfaz:** Gemini
- **Modelo de generación (Referencia API):** gemini-3-flash-preview
- **Modelo de embeddings (Referencia API):** gemini-embedding-2
- **Base de datos y versión (Referencia API):** PostgreSQL 16.15
- **Versión de pgvector (Referencia API):** pgvector 0.8.7
- **Autorización de procesamiento externo configurada:** sí
- **Fuente de la configuración:** variable de entorno (no registrar el valor de la clave)

## 3. Datos de prueba (Referencia de Casos API)

Flujos de consulta que deben replicarse exactamente en la interfaz web:
- **Material sintético utilizado:** material-sintetico-e1.pdf
- **Identificador del material:** 5db7fdbaee36577bdfef9f4ca5a718ef0e9f49e305b6fe62085d421efb98da17
- **Curso o espacio de trabajo:** Curso de demostración E2
- **Confirmación de que no se usaron datos personales:** Sí, entorno de pruebas restringido a datos sintéticos.
- **Caso 1: Pregunta con evidencia (Eje: Fotosíntesis):** ¿Cómo funciona la fotosíntesis en las plantas?
- **Caso 2: Pregunta sin evidencia suficiente (Eje: Mundial 2010):** ¿Quién ganó el Mundial de fútbol 2010?

## 4. Procedimiento de Validación Obligatorio

1. Levantar la aplicación localmente asegurando la escucha en el puerto `8001`.
2. Acceder mediante navegador a `http://127.0.0.1:8001`.
3. Validar que el selector de proveedor esté posicionado en **Gemini**.
4. Cargar el entorno o espacio de trabajo correspondiente al archivo `material-sintetico-e1.pdf`.
5. Ejecutar el **Caso 1 (Fotosíntesis)**, validar la presencia explícita de la cita `[F1]` en el componente de texto de la interfaz y capturar pantalla.
6. Ejecutar el **Caso 2 (Mundial 2010)**, validar que el componente de respuesta despliegue la abstención del modelo sin alucinaciones y capturar pantalla.
7. Almacenar los archivos físicos de imagen de manera local.

## 5. Resultados observados en Interfaz

### 5.1 Respuesta con evidencia (Fotosíntesis)
- **Pregunta formulada en UI:** ¿Cómo funciona la fotosíntesis en las plantas?
- **Respuesta observada en pantalla:** La fotosíntesis es el proceso mediante el cual las plantas convierten la luz solar en energía química [F1].
- **¿Incluye `[F1]` visible en el cliente web?:** sí
- **¿La cita corresponde al material cargado?:** sí
- **¿La respuesta está respaldada por el fragmento citado?:** sí
- **Tiempo de respuesta visual (Network/UI):** 4948.47 ms
- **Resultado:** APROBADO

### 5.2 Abstención (Mundial 2010)
- **Pregunta formulada en UI:** ¿Quién ganó el Mundial de fútbol 2010?
- **Respuesta observada en pantalla:** No encuentro evidencia suficiente en los materiales autorizados de este curso para responder con confianza.
- **¿Reconoce textualmente que no hay evidencia suficiente?:** sí
- **¿Evita inventar una respuesta o citas falsas en el DOM?:** sí
- **Tiempo de respuesta visual (Network/UI):** 1456.47 ms
- **Resultado:** APROBADO

## 6. Control de Archivos de Evidencia Física (Capturas)

Las siguientes imágenes existen para esta ejecución:
- **Modo Gemini y respuesta citada:** `captura-e2-gemini-respuesta-citada.png` -> **ESTADO: EXISTE**
- **Modo Gemini y abstención:** `captura-e2-gemini-abstencion.png` -> **ESTADO: EXISTE**

*Nota técnica: Las capturas finales deberán ser copias fieles de la pantalla completa del navegador sin recortes que alteren la URL local o los selectores activos.*

## 7. Incidencias y limitaciones en Interfaz
- **Errores de renderizado o del proveedor en UI:** ninguno reportado
- **Uso de fallback visual observado:** no

## 8. Criterio de aceptación

El hito E2 ha pasado a estado **APROBADO** con los datos de navegación registrados, la coherencia verificada con el backend y los archivos de imagen guardados físicamente en el repositorio.

## 9. Trazabilidad y Vinculación

- **Registro de ejecución por API de referencia:** `flujo-e1-e3-postgresql-gemini-2026-11-09.md`
- **Commit de la ejecución API de referencia:** 33c08188a7ce877d3c0ae0a709b174c8c442a524
- **Material de prueba de origen:** `material-sintetico-e1.pdf`
- **Comando de arranque del entorno local:** `.\INICIAR_MONDA_LOCAL.bat --port 8001`
- **JSON de ejecución:** `docs/evidencias/e2-gemini-ui-2026-11-09.json`
