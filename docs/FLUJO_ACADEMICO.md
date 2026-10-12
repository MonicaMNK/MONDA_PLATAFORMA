# Dashboard Equilibrado y flujo académico

La interfaz mantiene cursos, materiales, tutor privado, evaluaciones, seguimiento,
administración y configuración de proveedores. Se añade Mis notas para estudiantes.
Usa Plus Jakarta Sans, Phosphor Icons y Tailwind CDN según las referencias recibidas.
Los dos HTML de referencia son idénticos. Se conservaron los datos reales de Monda,
sin convertir los ejemplos de Ana Martínez, XP o certificados en datos académicos.

## Tutor: todos, carpeta o archivos

En Tutor RAG elige el alcance antes de preguntar. Las carpetas incluyen sus subcarpetas.
Los archivos concretos deben estar activos e indexados. Una selección vacía no busca
en otros documentos. Cambiar la selección abre una conversación nueva para no mezclar
evidencias de materiales distintos. El historial recupera su selección original.

## Documentos

Ver material abre el PDF original en el visor del navegador. El DOCX se renderiza
en un visor aislado con tablas, imágenes, encabezados, pies y estilos.
La paginación DOCX puede variar respecto de Microsoft Word; para fidelidad exacta
descarga el original o publica también su versión PDF. El visor no envía el archivo
a servicios externos para convertirlo.

## Evaluación → entrega → revisión → resultados

1. El docente genera un borrador con tema, Bloom, dificultad y cantidad.
2. Puede editar enunciado, opciones, clave y justificación. Debe aprobar cada pregunta.
3. Publica la evaluación con fechas de inicio y cierre.
4. El alumno inicia su intento, guarda respuestas y entrega. Su estado cambia a Completada.
5. El docente ve estudiantes, estado, inicio, cierre, duración y nota provisional.
6. Puede corregir la clave y justificación antes de publicar resultados; las notas
   se recalculan sobre 20. El enunciado y las opciones ya publicados permanecen fijos.
7. Publicar resultados cierra la evaluación y los intentos abiertos con sus respuestas
   guardadas. La interfaz pide confirmar esta acción e identifica los cierres por docente.
8. El estudiante puede ver su nota, respuesta elegida, clave y justificación revisada
   en Evaluaciones y Mis notas. No puede crear un segundo intento.
9. Comprender con el tutor prepara una pregunta sobre el reactivo y su explicación;
   el alumno decide cuándo enviarla.

Las preguntas y justificaciones pueden proceder de Gemini, Ollama o fallback.
La calificación se calcula de forma determinista en el servidor con las claves
revisadas por el docente; no depende de una nota inventada por el modelo.

## Alertas

La interfaz muestra nombres y evidencia, sin JSON. Se pueden revisar con un comentario.
Las reglas usan la configuración promedioMinimo/inactividadDias. La inactividad contempla
alumnos sin eventos desde su matrícula. Ver y descargar materiales registra actividad.
La evidencia se actualiza, las alertas revisadas no se duplican y las condiciones
resueltas se ocultan salvo que se marque Incluir resueltas.

## Actualización y archivo HTML completo

El arranque local conserva datos y crea `data/monda_local.before_learning_workflow.db`
antes de añadir descripción del curso y alcance de conversaciones.
En PostgreSQL aplica `alembic upgrade head` para la revisión 0005.

```powershell
cd frontend
npm run build
cd ..
.\.venv-local\Scripts\python.exe scripts/package_frontend_html.py
```

El resultado es `frontend/monda-dashboard.html`, con CSS y aplicación JavaScript
integrados en un único HTML. Se sirve en http://127.0.0.1:8000/dashboard.html.
Necesita la API de Monda y conexión para cargar los CDN y la fuente solicitados.
Abrirlo como file:// no sustituye al servidor de autenticación y datos.
