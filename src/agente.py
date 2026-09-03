# ============================================================================
# AGENTE LLM CON RECUPERACIÓN INTERNA + EXTERNA - VirtualMuni
# ============================================================================
# Este módulo construye el agente inteligente que:
#   - Recupera información de los documentos municipales internos (RAG).
#   - Usa búsqueda web (DuckDuckGo) para información externa pública.
#   - Controla el contexto conversacional (memoria) para mantener la
#     coherencia en conversaciones de varias preguntas.
#   - Formula la respuesta final respetando el prompt del sistema.
# ============================================================================

import os
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.memory import ConversationBufferMemory

from config import LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS
from prompts import SYSTEM_PROMPT, RAG_PROMPT, AGENT_PROMPT
from rag_pipeline import RAGPipeline
from automatizaciones import (
    agendar_cita,
    consultar_estado,
    generar_solicitud,
)


class AgenteMunicipal:
    """Agente inteligente que combina recuperación interna (RAG) y externa
    (web) para responder consultas ciudadanas."""

    def __init__(self, rag: RAGPipeline):
        self.rag = rag
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

    # ------------------------------------------------------------------------
    # HERRAMIENTA 1: RECUPERACIÓN INTERNA (RAG)
    # ------------------------------------------------------------------------
    def _herramienta_rag(self, consulta: str) -> str:
        """Recupera documentos municipales internos y devuelve el contexto."""
        docs = self.rag.recuperar(consulta)
        return self.rag.context_to_text(docs)

    @property
    def _herramienta_retenida_rag(self) -> str:
        return "recuperar_documentos"

    # ------------------------------------------------------------------------
    # HERRAMIENTA 2: RECUPERACIÓN EXTERNA (WEB)
    # ------------------------------------------------------------------------
    def _herramienta_web(self, consulta: str) -> str:
        """Busca información pública actualizada en la web."""
        search = DuckDuckGoSearchRun()
        try:
            return search.run(consulta)[:2000]
        except Exception as e:  # noqa: BLE001
            return f"No se pudo realizar la búsqueda web: {e}"

    # ------------------------------------------------------------------------
    # MÉTODO PRINCIPAL: responder con control de contexto
    # ------------------------------------------------------------------------
    def responder(self, pregunta: str) -> str:
        """Método principal del agente: recupera contexto interno, genera la
        respuesta y guarda la conversación en memoria."""
        # 1. Recuperación interna (RAG) para datos de trámites
        docs = self.rag.recuperar(pregunta)
        contexto = self.rag.context_to_text(docs)

        # 2. Generación con contexto (prompt de síntesis)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", RAG_PROMPT),
        ])
        cadena = prompt | self.llm | StrOutputParser()

        # 3. Historial conversacional (control de contexto)
        historial = self.memory.load_memory_variables({}).get(
            "chat_history", []
        )
        historial_texto = ""
        if historial:
            historial_texto = "\n".join(
                getattr(m, "content", str(m)) for m in historial
            )

        respuesta = cadena.invoke({
            "context": contexto,
            "question": pregunta,
            # El historial se integra vía la conversación del buffer
            "chat_history": historial_texto,
        })

        # 4. Guardar en memoria
        self.memory.save_context({"input": pregunta}, {"output": respuesta})
        return respuesta

    # ------------------------------------------------------------------------
    # VARIANTE CON AGENTE (ReAct) con herramientas de consulta Y automatización
    # ------------------------------------------------------------------------
    def construir_agente_react(self):
        """Construye un agente ReAct que decide entre:
        - recuperar documentos internos (RAG),
        - buscar información externa en la web,
        - EJECUTAR automatizaciones (agendar cita, consultar estado,
          generar solicitud)."""
        herramientas = [
            Tool(
                name="recuperar_documentos",
                func=self._herramienta_rag,
                description=(
                    "Recupera información de los documentos municipales internos. "
                    "Usar para trámites, requisitos, horarios, valores y "
                    "ubicaciones oficiales."
                ),
            ),
            Tool(
                name="buscar_web",
                func=self._herramienta_web,
                description=(
                    "Busca información pública actualizada en internet. "
                    "Usar para clima, noticias locales u horarios externos."
                ),
            ),
            Tool(
                name="agendar_cita",
                func=agendar_cita,
                description=(
                    "Agenda una cita de atención municipal. Argumentos: "
                    "[nombre, trámite, fecha YYYY-MM-DD, hora HH:MM]. "
                    "Usar cuando el ciudadano pida reservar una hora."
                ),
            ),
            Tool(
                name="consultar_estado",
                func=consultar_estado,
                description=(
                    "Consulta el estado de un trámite por su folio. "
                    "Argumento: [folio]. Usar cuando el ciudadano pregunte por "
                    "el estado o avance de un trámite indicando su folio."
                ),
            ),
            Tool(
                name="generar_solicitud",
                func=generar_solicitud,
                description=(
                    "Genera un formulario de solicitud de trámite rellenado. "
                    "Argumentos: [tipo_tramite, nombre, rut, detalle]. "
                    "Usar cuando el ciudadano solicite un formulario o "
                    "solicitud para descargar."
                ),
            ),
        ]
        prompt = ChatPromptTemplate.from_template(AGENT_PROMPT)
        agente = create_react_agent(self.llm, herramientas, prompt)
        executor = AgentExecutor(
            agent=agente,
            tools=herramientas,
            verbose=False,
            handle_parsing_errors=True,
        )
        return executor
