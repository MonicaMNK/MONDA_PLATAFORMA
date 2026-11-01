"""Versioned terms shown to users before they use the learning platform."""

PLATFORM_TERMS_VERSION = "2026-10-v1"
CONTENT_SHARING_TERMS_VERSION = "2026-10-v1"

PLATFORM_TERMS = {
    "version": PLATFORM_TERMS_VERSION,
    "title": "Condiciones de uso de Monda",
    "sections": [
        {
            "title": "Uso de la plataforma",
            "text": "Usa Monda para actividades de tus cursos y respeta las indicaciones de docentes y administradores. No compartas contraseñas ni intentes acceder a cursos o materiales que no te hayan sido autorizados.",
        },
        {
            "title": "Asistente de inteligencia artificial",
            "text": "El tutor puede equivocarse. Contrasta sus respuestas con los materiales y consulta a tu docente cuando tengas dudas. No ingreses nombres, datos de contacto, calificaciones, información de salud ni otros datos personales o sensibles en tus preguntas.",
        },
        {
            "title": "Privacidad y tratamiento externo",
            "text": "Monda conserva la actividad necesaria para prestar el servicio y mejorar su funcionamiento. Una consulta o material solo se envía a un proveedor externo de inteligencia artificial cuando la institución haya habilitado expresamente ese procesamiento. La aceptación de estas condiciones no reemplaza las autorizaciones y consentimientos requeridos para participar en una investigación.",
        },
        {
            "title": "Uso responsable",
            "text": "No uses la plataforma para publicar contenido ilegal, vulnerar derechos de terceros, acosar o perjudicar a otras personas. Los materiales y evaluaciones generados con IA requieren revisión docente antes de su uso académico.",
        },
    ],
}

CONTENT_SHARING_TERMS = {
    "version": CONTENT_SHARING_TERMS_VERSION,
    "title": "Declaración para compartir materiales del curso",
    "items": [
        "Tengo autorización para cargar este material y compartirlo con los participantes matriculados en este curso.",
        "He revisado el archivo y no contiene datos personales o sensibles de estudiantes u otras personas.",
        "Entiendo que el material podrá almacenarse e indexarse para que el tutor del curso recupere fragmentos y responda consultas.",
        "Entiendo que un proveedor externo de IA solo recibirá material o consultas si la institución habilita expresamente ese procesamiento.",
    ],
}
