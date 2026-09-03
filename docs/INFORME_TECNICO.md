# Informe Técnico
## VirtualMuni: Agente Inteligente con RAG y Automatización para la Municipalidad de Puente Alto

**Asignatura:** Ingeniería de Soluciones con IA (ISY0101)
**Evaluación Parcial N.º 1:** Encargo con Presentación
**Equipo:**
- Renato Espina - 21.801.161-6
- Javier García - 21.655.097-8
- Benjamín Rojas - 21.796.829-1

**Fecha:** Septiembre de 2026

---

## 1. Análisis del caso organizacional

### 1.1 La organización

La **Municipalidad de Puente Alto** es una institución pública ubicada en la
comuna de Puente Alto, una de las más pobladas de Santiago de Chile. Su rol
es administrar servicios y trámites locales para la comunidad: emisión de
certificados, permisos de circulación, patentes comerciales, entre otros.
Atiende un alto volumen de consultas ciudadanas diarias por distintos canales
(telefónico, presencial y digital).

### 1.2 El problema o desafío

El municipio enfrenta **colas presenciales extensas, tiempos de respuesta
elevados y respuestas inconsistentes** en las consultas frecuentes. El
personal municipal se dedica en gran parte a responder repetidamente las mismas
preguntas (requisitos de trámites, horarios, valores, ubicaciones), lo que
desvía recursos de tareas de mayor valor y degrada la experiencia ciudadana.

### 1.3 Objetivos de la intervención

1. Reducir el tiempo de atención en consultas frecuentes mediante atención
   automatizada 24/7.
2. Entregar respuestas **precisas y trazables**, citando fuentes documentales.
3. **Automatizar tareas simples**: agendar citas, consultar estado de trámites
   y generar formularios.

### 1.4 Datos disponibles

| Tipo | Fuente | Uso |
|------|--------|-----|
| Documentos internos | Manuales de trámites, guías, horarios | Fuente del RAG |
| Datos transaccionales | Registro de citas y trámites (simulado) | Automatizaciones |
| Información externa | Búsqueda web (clima, noticias, horarios) | Recuperación externa |

### 1.5 Restricciones y requerimientos

- Uso responsable de datos personales de los ciudadanos.
- Respuestas fundamentadas en documentación oficial (sin alucinar información).
- Trazabilidad: cada respuesta debe poder asociarse a su fuente.

### 1.6 Motivación del enfoque IA + LLM + RAG

Un **agente LLM** permite conversar en lenguaje natural. El **RAG** garantiza
que las respuestas sobre trámites se basen en documentos reales del municipio,
reduciendo alucinaciones y aportando trazabilidad. Las **herramientas de
automatización** transforman al sistema de un simple chatbot a un **agente
accionable** que ejecuta tareas, alineado con los objetivos planteados.

---

## 2. Formulación de prompts (IE2)

Los prompts se formularon siguiendo las buenas prácticas de *Prompt
Engineering*: definir **rol**, **contexto**, **tarea**, **formato** y
**restricciones**. Se centralizaron en `src/prompts.py`.

### 2.1 Prompt del sistema

```text
Eres "VirtualMuni", un asistente virtual oficial de la Municipalidad ...
Respondes trámites SOLO con los "DOCUMENTOS DE CONTEXTO"; nunca inventes
requisitos ni valores. Usa la búsqueda web solo para información externa.
Indica al final [Fuente: ...] cada respuesta.
```

**Justificación:** establece el **rol** y las **reglas de trazabilidad**,
reduciendo el riesgo de que el modelo invente datos (limitación propia de los
LLM conocida como alucinación).

### 2.2 Prompt de recuperación (query rewriter)

```text
Convierte la consulta del ciudadano en una búsqueda corta con términos clave.
```

**Justificación:** mejora la **recuperación semántica** al normalizar la
pregunta conversacional a términos buscables en el vector store.

### 2.3 Prompt de síntesis RAG

```text
Responde SOLO con los documentos de contexto. Si no está la respuesta, indícalo
y sugiere contactar a la municipalidad. Cita la fuente entre corchetes.
```

**Justificación:** fuerza la **fidelidad al contexto recuperado**, clave para
la precisión y relevancia de las respuestas.

### 2.4 Prompt del agente (ReAct)

```text
Tienes herramientas: recuperar_documentos, buscar_web, agendar_cita,
consultar_estado, generar_solicitud. Decide cuál usar según la consulta.
```

**Justificación:** habilita la **orquestación** entre recuperación interna,
externa y automatización, dando al agente capacidad de decisión autónoma.

---

## 3. Diseño e implementación del pipeline RAG (IE3)

El pipeline se implementó en `src/rag_pipeline.py` y funciona en **cuatro
etapas**:

1. **Carga de documentos internos** (`_load_documents`): lee archivos
   `.txt`, `.md` y `.pdf` desde `data/documentos/`.
2. **División en fragmentos** (`_split_documents`): usa un divisor
   recursivo por párrafos con solapamiento (chunk_size=800, overlap=100) para
   preservar el contexto entre fragmentos.
3. **Generación de embeddings e indexado** (`indexar`): convierte cada
   fragmento en un vector semántico y lo almacena en **ChromaDB** (persistente).
4. **Recuperación por similitud** (`recuperar`): ante una consulta, genera su
   embedding y devuelve los `k` fragmentos más similares (búsqueda coseno).

### Integración de fuentes internas y externas

- **Interna:** los documentos municipales se indexan en ChromaDB.
- **Externa:** la herramienta `buscar_web` (DuckDuckGo) recupera información
  pública actualizada (clima, noticias, horarios).
- **Transaccional:** los registros `citas.json` y `tramites.json` sustentan
  las automatizaciones.

El agente (`src/agente.py`) decide qué ruta tomar según la consulta mediante
el patrón de agente **ReAct** (razonar → actuar → observar).

---

## 4. Arquitectura de la solución (IE4)

La arquitectura (ver `diagrama/diagrama_arquitectura.md`) integra los
siguientes módulos:

1. **Interfaz de usuario** → recibe la consulta del ciudadano.
2. **Agente LLM (VirtualMuni)** → orquesta y decide la ruta.
3. **Módulo de recuperación interna (RAG)** → documentos + embeddings + ChromaDB.
4. **Módulo de recuperación externa** → búsqueda web (DuckDuckGo).
5. **Módulo de automatizaciones** → agendar cita, consultar estado, generar
   solicitud.
6. **Control de contexto** → memoria conversacional que mantiene coherencia
   entre preguntas.
7. **Almacenes de datos** → documentos, vector store, registros transaccionales.

Este diseño permite que la **operación de consulta y la de acción** convivan en
un mismo agente, garantizando precisión (RAG), relevancia (top-k por
similitud) y trazabilidad (citación de fuentes).

---

## 5. Justificación de decisiones de diseño (IE5)

| Decisión | Justificación |
|----------|---------------|
| LangChain | Estándar de la industria, facilita agentes, RAG e integraciones. |
| ChromaDB | Almacén vectorial local y persistente, sin infraestructura adicional. |
| Embeddings multilingües | Precisión en español (lengua del caso). |
| LLM con baja temperatura (0.2) | Respuestas más fieles al contexto, menor variabilidad. |
| Top-k = 4 | Equilibrio entre contexto suficiente y costo de generación. |
| Prompts con rol+restricciones | Control de alucinaciones y trazabilidad. |

### Limitaciones del modelo consideradas

- **Alucinación**: mitigada con prompts que restringen al contexto y con citación.
- **Datos desactualizados**: el RAG se actualiza al reindexar documentos.
- **Calidad de recuperación**: depende del tamaño de fragmentos y del modelo de
  embeddings; se ajusta con el solapamiento.
- **Dependencia de API**: el modo local requiere clave de OpenAI; se ofrece el
  notebook de Colab con modelos gratuitos de Hugging Face para evaluación.

---

## 6. Conclusiones

La solución **VirtualMuni** demuestra la viabilidad de un agente LLM con RAG
para mejorar la atención municipal, combinando respuestas precisas y trazables
con automatización de trámites simples. La arquitectura modular y los prompts
optimizados permiten responder a los requerimientos del caso y controlar las
limitaciones del modelo.

### Reflexiones individuales (a completar por cada integrante sin apoyo de IA)

> **Reflexión - Renato Espina (21.801.161-6):**
> (Redactar aquí, SIN uso de IA, sobre el aprendizaje y contribución personal.)

> **Reflexión - Javier García (21.655.097-8):**
> (Redactar aquí, SIN uso de IA, sobre el aprendizaje y contribución personal.)

> **Reflexión - Benjamín Rojas (21.796.829-1):**
> (Redactar aquí, SIN uso de IA, sobre el aprendizaje y contribución personal.)

---

## 7. Referencias (APA)

- LangChain. (2024). *LangChain documentation*. https://python.langchain.com
- Chroma. (2024). *Chroma DB documentation*. https://docs.trychroma.com
- OpenAI. (2024). *OpenAI API documentation*. https://platform.openai.com
- Hugging Face. (2024). *Hugging Face documentation*. https://huggingface.co

## Declaración de uso de IA

Este informe se elaboró con apoyo de herramientas de IA generativa para la
redacción y estructuración de secciones técnicas. Las decisiones de diseño,
análisis y reflexiones individuales son propias del equipo y han sido revisadas
y validadas según los lineamientos institucionales.
