# VirtualMuni — Agente Inteligente con RAG para la Municipalidad de Puente Alto

Chatbot de asistencia municipal que **responde consultas** sobre trámites usando
**RAG** (Recuperación Aumentada por Generación) y **automatiza acciones** como
agendar citas, consultar el estado de trámites y generar formularios.

---

## 1. Descripción del caso

La Municipalidad de Puente Alto recibe cientos de consultas ciudadanas diarias
por teléfono y de forma presencial, lo que genera largas filas, tiempos de
respuesta altos e información inconsistente. **VirtualMuni** es un agente de IA
que atiende estas consultas 24/7 con respuestas precisas, trazables y con
capacidad de ejecutar trámites simples automáticamente.

### Objetivos
- Reducir el tiempo de atención en consultas frecuentes.
- Entregar respuestas precisas y con trazabilidad (citando la fuente documental).
- Automatizar tareas simples (agendar citas, consultar estado, generar formularios).

### Fuentes de datos
| Tipo | Fuente | Tecnología |
|------|--------|-----------|
| Interna | Manuales de trámites, guías y horarios (`data/documentos/`) | RAG + ChromaDB |
| Interna (transaccional) | Registro de citas y trámites (`data/citas.json`, `data/tramites.json`) | Simulación de BD |
| Externa | Búsqueda web (clima, noticias, horarios oficiales) | DuckDuckGo |

---

## 2. Arquitectura de la solución

```
+----------------+    +----------------------------------------------+
|   Ciudadano    | --> |        AGENTE VIRTUALMUNI (LLM)              |
| (pregunta /    |    |  Decide qué herramienta usar (ReAct)         |
|  solicitud)    |    +----------------------+-----------------------+
+----------------+                           |
                                             | usa
        +----------------+-------------------+----------------+
        |                |                                   |
        v                v                                   v
+---------------+ +------------------+            +---------------------+
| RECUPERACIÓN  | | RECUPERACIÓN     |            | AUTOMATIZACIONES    |
| INTERNA (RAG) | | EXTERNA (WEB)    |            +---------------------+
|               | |                  |            | - agendar_cita      |
| documentos -> | | DuckDuckGo       |            | - consultar_estado  |
| embeddings -> | |                  |            | - generar_solicitud |
| ChromaDB     | +------------------+            +---------------------+
+---------------+                                   |  escribe
        |                                           v
        +---------->  LLM genera respuesta  <--+ data/*.json , solicitudes_*
                    (prompt del sistema)
```

### Componentes clave
1. **Pipeline RAG** (`src/rag_pipeline.py`): carga documentos, los divide en
   fragmentos, genera embeddings y los indexa en **ChromaDB**.
2. **Agente LLM** (`src/agente.py`): decide qué herramienta usar según la
   consulta (modelo ReAct) y controla el contexto conversacional.
3. **Herramientas de automatización** (`src/automatizaciones.py`): agendar cita,
   consultar estado y generar solicitudes.
4. **Prompts optimizados** (`src/prompts.py`): centralizados para revisión y
   mantenimiento.

---

## 3. Estructura del repositorio

```
ChatBot Puente Alto/
├── data/
│   ├── documentos/           # Fuente interna del RAG (manuales de trámites)
│   ├── citas.json            # Registro de citas (simulado)
│   ├── tramites.json         # Registro de trámites (simulado)
│   └── solicitudes_generadas/# Formularios generados
├── src/
│   ├── config.py             # Configuración (modelos, rutas)
│   ├── prompts.py            # Prompts optimizados (sistema, RAG, agente)
│   ├── rag_pipeline.py       # Pipeline RAG (indexado + recuperación)
│   ├── automatizaciones.py   # Herramientas de automatización
│   ├── agente.py             # Agente LLM con control de contexto
│   └── main.py               # Punto de entrada (CLI)
├── pruebas/                  # Evidencia de pruebas ejecutadas
├── diagrama/                 # Diagramas de arquitectura
├── VirtualMuni_RAG_Agente.ipynb  # Versión para Google Colab (sin API key)
└── requirements.txt
```

---

## 4. Instalación y ejecución (local, requiere API key OpenAI)

### Requisitos
- Python 3.10 or superior.
- Una clave de API de OpenAI (`OPENAI_API_KEY`).

### Pasos
```bash
# 1. Ir a la carpeta del proyecto
cd "ChatBot Puente Alto"

# 2. Crear y activar un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar la clave de API (crear archivo .env)
#    Contenido del archivo .env:
#    OPENAI_API_KEY=tu_clave_aqui

# 5. Ejecutar la demo de automatizaciones (no requiere API key)
python src/main.py --automatizar

# 6. Ejecutar el agente RAG (requiere API key)
python src/main.py --demo
# o en modo chat interactivo:
python src/main.py
```

---

## 5. Ejecución en Google Colab (gratis, sin API key)

Si no tienes API key de OpenAI, abre
[`VirtualMuni_RAG_Agente.ipynb`](VirtualMuni_RAG_Agente.ipynb) en
[Google Colab](https://colab.research.google.com) y ejecuta las celdas en orden.
Usa modelos gratuitos de Hugging Face (embeddings multilingües y un LLM
instructivo en español), por lo que **no requiere pago**.

---

## 6. Pruebas realizadas (evidencia)

En la carpeta `pruebas/` se incluye la evidencia generada:
- `evidencia_automatizaciones.txt`: prueba de agendar cita, consultar estado
  (incluido folio inexistente) y generar solicitud.

### Ejemplo de salida (automatizaciones):
```
[AGENDAR CITA]
Cita agendada correctamente. Folio: CITA-0001. Trámite: Certificado de
Nacimiento para Ana Pérez el 2025-06-10 a las 10:30.

[CONSULTAR ESTADO]
Trámite PA-2025-0002 (Permiso de Circulación): estado = Aprobado.
Oficina responsable: Tesorería.

[GENERAR SOLICITUD]
Solicitud generada y guardada en data\solicitudes_generadas\...
```

---

## 7. Tecnologías y justificación

| Componente | Tecnología | Justificación |
|-----------|-----------|---------------|
| Framework de agentes/RAG | LangChain | Estándar de la industria, extenso ecosistema de integraciones |
| Almacén vectorial | ChromaDB | Local, persistente y fácil de operar; ideal para prototipos |
| Embeddings | OpenAI / Hugging Face | Soporte multilingüe (español) y calidad de similitud semántica |
| LLM generador | GPT / Zephyr | Equilibrio entre calidad de respuesta y costo |
| Búsqueda externa | DuckDuckGo | Gratuita y sin claves, para recuperación de información pública |

---

## 8. Referencias

- LangChain Documentation. https://python.langchain.com
- ChromaDB Documentation. https://docs.trychroma.com
- OpenAI API. https://platform.openai.com
- Hugging Face. https://huggingface.co
