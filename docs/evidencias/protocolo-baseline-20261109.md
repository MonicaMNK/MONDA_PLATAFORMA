# Protocolo de medición — Línea base empírica (tiempos manual vs Monda)

**Versión:** 1.0  
**Fecha:** 2026-11-01  
**Autor:** Mónica Paola Mendoza Melo (T9)  
**Revisor:** Daniel Leonardo Escribas Alan (T5)

## Objetivo

Medir el tiempo que tarda un participante en completar una tarea de consulta y extracción de información del material del curso, comparando el método manual (búsqueda en PDF sin herramienta) contra el método con Monda (búsqueda asistida por RAG).

## Tarea concreta

Cada participante recibe el mismo PDF del curso (`material-sintetico-e1.pdf`) y debe responder tres preguntas de comprensión que requieren localizar información en el documento:

1. ¿Cuáles son las dos divisiones principales del sistema nervioso y qué estructuras componen cada una?
2. ¿Qué diferencia la nutrición autótrofa de la heterótrofa en las células?
3. ¿Cómo colaboran el encéfalo y la médula espinal para integrar información y producir una respuesta?

## Definición de tiempos

- **Tiempo manual:** transcurre desde que el participante abre el PDF hasta que entrega sus tres respuestas escritas, sin usar Monda ni ninguna herramienta de búsqueda asistida.
- **Tiempo con Monda:** transcurre desde que el participante abre la interfaz de Monda hasta que obtiene y verifica las tres respuestas generadas por el sistema RAG.

## Materiales

- PDF del curso: `docs/evidencias/material-sintetico-e1.pdf`
- Tres preguntas de comprensión (idénticas para todos los participantes)
- Computadora con navegador web y acceso a la instancia local de Monda

## Diseño experimental

- Diseño intra-sujeto: cada participante realiza la tarea con ambos métodos.
- Orden alternado AB/BA para reducir efecto de aprendizaje:
  - Participantes impares (P001, P003, P005, P007, P009): orden A (manual primero, luego Monda)
  - Participantes pares (P002, P004, P006, P008, P010): orden B (Monda primero, luego manual)
- Se registra el orden real en el campo `orden_ab` del CSV.

## Reclutamiento de participantes

- Cantidad: 10 participantes (muestra piloto de conveniencia)
- Rol pertinente: 5 docentes, 5 estudiantes del curso relacionado
- Criterio de selección: disponibilidad para participar y familiaridad básica con navegación web
- Tamaño muestral: declarado como piloto exploratorio, no representativo de la población total

## Ética y privacidad

- Cada participante firmó consentimiento informado antes de iniciar.
- Los datos seudonimizados con identificadores P001–P010; no se registran nombres ni correos en el CSV de resultados.
- Los consentimientos se archivan según las reglas de la universidad.

## Evidencia primaria

Por participante y método se registra:
- ID seudonimizado (P001–P010)
- Rol pertinente (docente/estudiante)
- Tarea (tres preguntas de comprensión)
- Material (`material-sintetico-e1.pdf`)
- Orden (A o B)
- Inicio y fin o duración (segundos)
- Fecha de medición
- Incidencias (si las hubo)
- Si completó la tarea (sí/no)

Las hojas de observación originales están en `data/observacion-baseline-20261109.json`. El CSV seudonimizado se generó transcribiendo esas hojas.

## Análisis estadístico

- n efectivo por método
- Mediana e intervalo intercuartílico de tiempos por método
- Diferencias pareadas (manual − Monda)
- Cambio porcentual medio
- Intervalo de confianza del 95 % para la diferencia pareada
- Prueba pareada apropiada (Wilcoxon signed-rank o t de Student para muestras pareadas, según normalidad)
- Número de participantes que mejoraron, empeoraron o mantuvieron tiempo

Los umbrales de aceptación se definieron antes de ver los resultados y no se modificaron después.

## Vinculación con fuentes

- Hash del CSV real: registrado en `data/validation_manifest.json`
- Commit del código: `c1f033861c280f12f9ed63792c06b1eef7ce8a84`
- Versión del protocolo: 1.0 (este documento)
