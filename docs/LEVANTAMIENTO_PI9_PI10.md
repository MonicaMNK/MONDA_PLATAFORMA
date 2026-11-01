# Levantamiento de observaciones PI9 y PI10

Esta matriz separa cambios implementados en el repositorio de evidencias que todavía requieren ejecutar el sistema o realizar actividades con la institución. No se declaran aprobadas pruebas o actividades que no se ejecutaron.

| Observación | Estado en el proyecto | Pendiente para cerrar |
|---|---|---|
| Aceptación de condiciones del usuario | Implementado: pantalla después del inicio de sesión, control de acceso por versión y registro inmutable en auditoría. | Revisar el texto con la institución y aplicar una nueva versión si cambia. |
| Aceptación del docente al compartir material | Implementado: declaración versionada en Materiales; API exige aceptación y asocia el registro al curso y al archivo. | Revisar los permisos de autor y el texto con el colegio. |
| Autorización de Gemini | Implementado: desactivado por defecto; API y Docker requieren `GEMINI_EXTERNAL_PROCESSING_AUTHORIZED=1`. Sin la bandera, se usa fallback cuando está habilitado. | Obtener autorización institucional, configurar una cuenta/proyecto permitido y realizar una llamada de demostración sin datos personales. |
| Prueba del bloqueo de Gemini | Añadida en `tests/test_basic_fixes.py`: el proveedor no debe construirse sin autorización. | Ejecutarla en el entorno Python del proyecto y guardar evidencia del resultado. |
| Modelo Gemini | Los identificadores `gemini-3.8-flash` y `gemini-embedding-2` figuran en la documentación oficial de Gemini API. | Comprobar que ambos estén habilitados para la cuenta y el proyecto que se usará en la demostración. |
| Suite PostgreSQL y pgvector | El repositorio contiene migraciones y configuración de PostgreSQL. | Ejecutar los casos contra PostgreSQL + pgvector; la suite local de este entorno no pudo ejecutarse por falta de `pytest` y SQLAlchemy. |
| Flujos E1, E2 y E3 en ejecución | La interfaz y los módulos están presentes en el proyecto. | Grabar resultados reales: carga y aislamiento por curso; respuesta Gemini con fuente y abstención; evaluación, nota y seguimiento. Añadir minutos del video y evidencia capturada. |
| Consentimiento de menores | La aplicación explica que las condiciones de uso no sustituyen consentimiento ni asentimiento. | Obtener autorización escrita de dirección, consentimiento de padres/tutores y asentimiento individual antes del piloto. |
| Muestra y métricas | El código no puede producir la validación humana. | Confirmar tamaño y selección de participantes; relacionar cada criterio con instrumento, muestra y resultado observado. |
| Calibración RAG | El proyecto permite configurar top-k y umbral. | Recopilar preguntas reales con fragmento de referencia y medir recall@k y abstención con distractores del mismo curso. |
| Atribución individual y Git | No se reescribió el historial ni se crearon commits de autoría. | Acordar ramas y pull requests por tesista y registrar cambios pequeños atribuibles desde este avance. |
| AWS | El entorno AWS sigue siendo objetivo documentado, no una integración desplegada. | Mantenerlo como trabajo futuro o desplegarlo y aportar evidencia real. |

## Evidencia de código

La interfaz React se recompiló y se actualizó `frontend/monda-dashboard.html`, que es el HTML empaquetado servido por el arranque local. Los nuevos casos de prueba quedaron en el repositorio, pero no se ejecutaron en esta máquina porque faltan `pytest` y SQLAlchemy en el Python disponible.
