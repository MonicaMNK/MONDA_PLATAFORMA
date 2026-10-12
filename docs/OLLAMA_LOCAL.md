# Usar Ollama con Monda, sin Docker

En esta máquina no se encontró Ollama en PATH ni en la ubicación de instalación habitual.
El servicio tampoco respondió en `http://127.0.0.1:11434`.

1. Instala [Ollama para Windows](https://ollama.com/download/windows) y abre la aplicación.
2. En una nueva terminal PowerShell descarga los dos modelos que usa la configuración actual:

```powershell
ollama pull llama3
ollama pull nomic-embed-text
ollama list
```

`llama3` redacta respuestas; `nomic-embed-text` genera los embeddings del material.
Necesitas espacio adicional para los modelos. La velocidad depende de la RAM, CPU y GPU
disponibles; no se verificó la capacidad de hardware de esta máquina.

3. Comprueba que el servicio está activo:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Si no está activo, ejecuta `ollama serve` en otra terminal. Si la aplicación ya está
sirviendo el puerto 11434, no hace falta arrancar una segunda instancia.

4. En Monda, entra como administrador. En Administración → Gemini y Ollama pulsa
**Comprobar conexión**. Deben aparecer el servicio y ambos modelos disponibles.
5. En Configuración RAG selecciona `ollama`, confirma `llama3` como Modelo Ollama y guarda.
6. En Materiales reindexa cada documento. Los embeddings de Gemini y Ollama no son
intercambiables; Monda filtra por proveedor/modelo para evitar mezclarlos.
7. Abre una conversación nueva en Tutor RAG. La respuesta debe mostrar **Ollama**.

Para cambiar de modelo de generación, descarga primero el modelo nuevo con `ollama pull`
y escribe su nombre exacto en Configuración RAG. El modelo de embeddings se configura
en el servidor con `OLLAMA_EMBEDDING_MODEL`; debe producir vectores de 768 dimensiones.
`OLLAMA_BASE_URL` por defecto apunta a `http://127.0.0.1:11434` en el arranque sin Docker.

El fallback sigue habilitado para mantener operativos los flujos si falla el proveedor.
La interfaz indica cuando una respuesta usa búsqueda local.

Referencias oficiales: [Windows](https://docs.ollama.com/windows),
[API de embeddings](https://docs.ollama.com/api/embed),
[nomic-embed-text](https://ollama.com/library/nomic-embed-text).
