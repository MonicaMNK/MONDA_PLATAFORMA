# Contrato de API PI7

Rutas heredadas de PI6 con extensiones de consulta, recuperación y trabajos asíncronos. UUID en identificadores; ISO 8601 UTC en fechas; UTF-8; JSON salvo archivos. Access token en memoria; refresh rotativo en cookie HttpOnly/Secure/SameSite=Strict. Operaciones con cookie verifican origen y CSRF. Las respuestas nunca exponen hashes, claves de reactivos antes del cierre ni credenciales.

| Método | Ruta | Solicitud | Respuesta | HTTP |
|---|---|---|---|---|
|POST|/api/auth/login|{correo,password}|{accessToken,expiresIn:1800}; cookie refresh|200,401,429|
|POST|/api/auth/refresh|Cookie refresh; token CSRF|{accessToken,expiresIn}; refresh rotado|200,401,403|
|POST|/api/auth/logout|Sesión y CSRF|Sin cuerpo; familia de sesión revocada|204,401|
|POST|/api/auth/recovery|{correo}|{message}; respuesta uniforme|202,422,429|
|POST|/api/auth/reset|{token,password}|Contraseña reemplazada; sesiones revocadas|204,400,422|
|GET|/api/users/me|Sesión|{id,nombre,correo,rol,estado}|200,401|
|PATCH|/api/users/me|{nombre}; no acepta rol|Perfil actualizado|200,401,422|
|GET|/api/courses|page,limit|{items[],page,total}|200,401|
|POST|/api/courses|{nombre}|{courseId,nombre,estado}|201,401,403,422|
|POST|/api/courses/{courseId}/enrollments|{estudianteId}|{courseId,estudianteId,estado}|201,403,409,422|
|POST|/api/courses/{courseId}/contents|multipart: file,documentoId,version|{contentId,estado:pendiente}|201,403,413,415,422|
|POST|/api/contents/{contentId}/index|Idempotency-Key|{jobId,estado}; Location de estado|202,403,409|
|GET|/api/contents/{contentId}/status|Sesión y autorización de curso|{estado,errorCode,fragmentCount}|200,403,404|
|GET|/api/contents/{contentId}/download|Sesión; contentId|URL privada de vigencia breve o stream|200,403,404|
|POST|/api/courses/{courseId}/rag/query|{question,conversationId?}|{answer,sources[],evidenceSufficient,correlationId}|200,403,422,429,503|
|GET|/api/rag/conversations|courseId,page,limit|{items[],page,total}|200,403|
|GET|/api/rag/conversations/{conversationId}/messages|page,limit|{items[],page,total}|200,403,404|
|POST|/api/rag/messages/{messageId}/rating|{util,comentario?}|{ratingId,util}|200,201,403,422|
|POST|/api/courses/{courseId}/assessments/generate|{tema,bloom,dificultad,cantidad,tipo}|{jobId,estado:pendiente}|202,403,422,429|
|GET|/api/jobs/{jobId}|Sesión; dueño del job|{estado,result,errorCode}|200,403,404|
|GET|/api/courses/{courseId}/assessments|page,limit|Evaluaciones visibles sin claves para estudiante|200,403|
|GET|/api/assessments/{id}|Sesión y rol|Evaluación y reactivos según visibilidad del rol|200,403,404|
|PATCH|/api/questions/{questionId}/review|{enunciado?,opciones?,clave?,estado,version}|Reactivo revisado con autor y fecha|200,403,409,422|
|POST|/api/assessments/{id}/publish|{fechaInicio,fechaFin,version}|{id,estado:publicada}|200,403,409,422|
|POST|/api/assessments/{id}/attempts|{accion:iniciar / cerrar,intentoId?,respuestas?}; Idempotency-Key|{attemptId,estado,puntaje?}|200,201,403,409,422|
|GET|/api/courses/{courseId}/analytics|desde,hasta,corte|{indicadores,alertas,fechaCorte}|200,403,422|
|PATCH|/api/alerts/{alertId}|{estado:revisada,comentario}|Alerta con revisor y fecha|200,403,409|
|GET|/api/courses/{courseId}/reports/export|desde,hasta,corte,format=csv|text/csv; nombre y fecha de corte|200,403,422|
|POST|/api/sync|{actions:[{actionId,tipo,payload,version}]}|{results:[{actionId,status,result}]}|200,401,422|
|GET|/api/admin/users|page,limit,rol?,estado?|{items[],page,total}|200,403|
|POST|/api/admin/users|{correo,nombre,rol}|{id,estado:pendiente}; activación por enlace|201,403,409,422|
|PATCH|/api/admin/users/{userId}|{rol?,estado?,version}|Usuario actualizado y auditado|200,403,409,422|
|GET|/api/admin/roles|Sesión administrativa|Matriz permiso–rol|200,403|
|PATCH|/api/admin/roles|{rol,permisos,version}|Matriz actualizada|200,403,409,422|
|GET|/api/admin/config|Sesión administrativa|{topK,umbral,modelo,version}|200,403|
|PATCH|/api/admin/config|{topK,umbral,modelo,version}|Configuración actualizada|200,403,409,422|
|GET|/api/admin/audit|actor?,desde,hasta,page,limit|Registros sin secretos ni contenido personal|200,403,422|
|GET|/api/courses/{courseId}/contents|page,limit|{items[],page,total}; solo versiones autorizadas|200,403,404|
|PATCH|/api/courses/{courseId}|{nombre?,estado:activo / archivado}|Curso actualizado sin eliminar resultados|200,403,404,422|
|GET|/api/courses/{courseId}/enrollments|page,limit|{items[],page,total}; solo docente propietario|200,403,404|
|PATCH|/api/courses/{courseId}/enrollments/{studentId}|{estado:activa / inactiva}|Matrícula actualizada; revocación de acceso efectiva|200,403,404,422|

## Reglas transversales
Error: `{code,message,correlationId,details?}`. 401 sin sesión, 403 sin permiso, 404 recurso inexistente/no visible, 409 conflicto, 422 entrada inválida, 429 cuota y 503 dependencia temporal. Los listados usan page=1, limit=20 (máximo 100). Todas las rutas tienen autorización de objeto, además de rol.

El endpoint de intentos inicia o cierra según accion; un cierre repetido con la misma carga devuelve el resultado persistido. La generación retorna 202 y se consulta en /api/jobs/{jobId}. Las claves de evaluación solo son visibles al docente y, tras cierre, según la retroalimentación habilitada.

M4 es una interfaz interna: embed(texts, model, correlationId) → vectors, model, tokens. No se publica un endpoint de embeddings al navegador.

El prototipo HTML simula estos contratos; el repositorio inicial no es una implementación de producción.