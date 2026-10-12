# Probar Monda sin Docker

Desde la raíz del proyecto en Windows, ejecuta:

```powershell
.\INICIAR_MONDA_LOCAL.bat
```

Abre http://127.0.0.1:8000. El contrato interactivo está en http://127.0.0.1:8000/docs.
Para detener el servidor pulsa Ctrl+C en la terminal. Si el puerto está ocupado:

```powershell
.\INICIAR_MONDA_LOCAL.bat --port 8001
```

El entorno `.venv-local` ya está preparado en esta máquina. En otra máquina con Python 3.12 instalado:

```powershell
py -3.12 -m venv .venv-local
.\.venv-local\Scripts\python.exe -m pip install -r requirements.txt
.\INICIAR_MONDA_LOCAL.bat
```

El lanzador crea las tablas SQLite y carga las cuentas demo sin borrar datos existentes.
Utiliza `data/monda_local.db`, almacenamiento local y una clave aleatoria persistida en
`data/.local_secret`; no necesita editar `.env`. Sirve el frontend estático incluido
si no existe un build de Vite. Está enlazado únicamente a `127.0.0.1`.

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | admin@monda.local | Admin123! |
| Docente | docente@monda.local | Docente123! |
| Estudiante | estudiante@monda.local | Estudiante123! |

## Recorrido funcional

1. Como docente, abre el curso de demostración, carga un DOCX/PDF con texto y solicita su indexación. Comprueba estado y descarga.
2. Consulta al tutor sobre ese material y revisa las fuentes; prueba una pregunta fuera del tema.
3. Genera una evaluación, revisa y aprueba cada reactivo. Publica con un rango de fechas que incluya el momento actual.
4. Como estudiante, abre el curso, resuelve la evaluación y cierra el intento. Comprueba nota y restricción de segundo intento.
5. Como docente, revisa los indicadores y exporta CSV.
6. Como administrador, revisa usuarios, permisos, configuración y auditoría.
7. Prueba recuperación/reset y sincronización desde `/docs`: pulsa Authorize con el `accessToken` obtenido en `/api/auth/login`.
8. Para comprobar renovación automática, elimina `monda_token` de sessionStorage y recarga mientras la cookie de sesión siga vigente.

El lanzador carga `data/.gemini.env` si existe. En esta máquina Gemini está configurado
con `gemini-3.1-flash-lite` para generación y `gemini-embedding-2` para embeddings.
La clave se mantiene fuera de Git y de la imagen Docker. Sin ese archivo, usa modo auto.
En Administración puedes elegir Gemini, Ollama o fallback y cambiar el modelo de generación.
Al cambiar el modelo de embeddings, reindexa los materiales desde Contenidos.
Gemini requiere una clave válida; Ollama requiere su servicio y modelos instalados.
SQLite permite probar los flujos de aplicación; no valida las migraciones, índices HNSW,
triggers de auditoría ni comportamiento de concurrencia de PostgreSQL.

Como administrador, usa Mis cursos para crear cursos, seleccionar o reasignar docentes
y matricular estudiantes por nombre. En Administración puedes crear usuarios con
contraseña inicial y editar su nombre, correo, rol y estado.

## Chat privado y biblioteca por semanas

El historial del tutor pertenece al usuario y al curso: docentes y administradores
no pueden abrir chats de otros usuarios. Al cambiar de cuenta o curso se limpia
la conversación visible; el historial propio se recupera desde el servidor.

En Materiales, docentes y administradores pueden crear carpetas como Semana 1,
entrar en ellas, crear subcarpetas, subir varios PDF/DOCX y mover archivos.
Los estudiantes matriculados pueden navegar, ver el texto y descargar materiales.
No pueden crear carpetas, subir, mover ni reindexar, tampoco mediante la API.

Al actualizar una base SQLite anterior, el lanzador conserva los datos y guarda
una copia en `data/monda_local.before_folders.db` antes de añadir el campo de carpeta.
En PostgreSQL aplica `alembic upgrade head` para instalar la revisión 0004.

Para usar el proveedor local consulta [Ollama sin Docker](OLLAMA_LOCAL.md).

## Pruebas automatizadas

Usa una base separada de la demo, porque los tests reconstruyen sus tablas:

```powershell
$env:DATABASE_URL = 'sqlite:///./data/test_local.db'
.\.venv-local\Scripts\python.exe -m pytest -q
Remove-Item Env:DATABASE_URL
```
