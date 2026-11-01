# Privacidad y aceptaciones en Monda

La plataforma solicita la aceptacion de las condiciones vigentes despues del inicio de sesion. Hasta que la persona las acepte, las rutas autenticadas de la aplicacion devuelven `TERMS_ACCEPTANCE_REQUIRED`. La aceptacion queda en la tabla `auditoria` con la cuenta, la version y la fecha; una nueva version exige una nueva aceptacion.

Antes de que un docente o administrador cargue materiales, la pantalla presenta una declaracion versionada. La persona confirma que puede compartir el archivo con el curso, que lo reviso para evitar datos personales de estudiantes y que se indexara para las consultas del tutor. El servidor exige esa confirmacion y su version y registra la aceptacion asociada al curso y al material en la auditoria.

Gemini permanece bloqueado por defecto aunque exista `GEMINI_API_KEY`. Para habilitar el envio a ese proveedor, la institucion debe aprobar expresamente el procesamiento y configurar `GEMINI_EXTERNAL_PROCESSING_AUTHORIZED=1` en el entorno de ejecucion. En Docker Compose, el valor se toma del `.env` del despliegue. La aplicacion no comprueba el plan ni las condiciones de la cuenta de Google; el responsable debe verificarlos antes de activar la bandera. Sin autorizacion, el sistema usa fallback local si esta habilitado; no construye ni llama al proveedor Gemini. El panel de proveedores muestra si la clave esta configurada y si el procesamiento externo esta habilitado.

Estas pantallas y registros son controles del artefacto. No sustituyen la autorizacion escrita de la direccion del colegio, el consentimiento informado de padres o tutores ni el asentimiento de estudiantes menores de edad. Esos documentos y la aprobacion institucional deben estar completos antes de reclutar participantes o usar datos reales. La institucion y el asesor deben revisar el texto de las condiciones antes de cualquier piloto.

## Verificacion incorporada

`tests/test_basic_fixes.py` contiene casos para comprobar que las rutas exigen la aceptacion vigente, que el servidor registra las declaraciones de carga y que la fabrica de proveedores no construye Gemini cuando la autorizacion externa esta desactivada. La ejecucion de esa suite depende del entorno Python del proyecto.
