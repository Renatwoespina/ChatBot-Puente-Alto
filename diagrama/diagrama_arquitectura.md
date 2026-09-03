# Diagrama de Arquitectura - VirtualMuni (Municipalidad de Puente Alto)

Este diagrama puede renderizarse como diagrama Mermaid en GitHub, en
mermaid.live, o en editores como Typora/Obsidian.

## Diagrama Mermaid

```mermaid
flowchart TD
    A[Ciudadano] -->|pregunta / solicitud| B[Agente VirtualMuni - LLM]
    B --> C{Pregunta / Accion?}

    C -->|consulta de trámite| D[Recuperación Interna - RAG]
    C -->|información externa| E[Recuperación Externa - Web]
    C -->|acción: agendar / estado / formulario| F[Automatizaciones]

    D --> D1[Documentos municipales<br>data/documentos]
    D1 --> D2[Embeddings + ChromaDB]
    D2 --> D3[Fragmentos relevantes]

    E --> E1[DuckDuckGo Search]

    F --> F1[agendar_cita]
    F --> F2[consultar_estado]
    F --> F3[generar_solicitud]
    F1 --> G[(data/citas.json)]
    F2 --> H[(data/tramites.json)]
    F3 --> I[(data/solicitudes_generadas)]

    D3 --> B
    E1 --> B
    F --> B
    B -->|respuesta con fuentes| A

    subgraph Control de Contexto
        M[(Memoria conversacional)] --> B
    end
```

## Descripción de flujo

1. **El ciudadano** envía una pregunta o solicitud al agente VirtualMuni (LLM).
2. **El agente (ReAct)** decide qué ruta seguir:
   - **Consulta de trámite** → recuperación interna RAG (documentos + embeddings + ChromaDB).
   - **Información externa** → búsqueda web vía DuckDuckGo.
   - **Acción** → ejecuta una herramienta de automatización.
3. **El LLM** combina la información recuperada con el **control de contexto**
   (memoria conversacional) y genera una respuesta trazable, citando la fuente.
4. **La respuesta** se entrega al ciudadano.
