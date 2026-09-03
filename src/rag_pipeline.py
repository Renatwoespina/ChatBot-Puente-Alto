# ============================================================================
# PIPELINE RAG - Asistente Virtual Municipal (VirtualMuni)
# ============================================================================
# Este módulo implementa el flujo de Recuperación Aumentada por Generación:
#
#   1. INDEXACIÓN:    Carga documentos internos (txt/pdf), los divide en
#                     fragmentos (chunks) y genera embeddings para
#                     almacenarlos en ChromaDB (vector store persistente).
#   2. RECUPERACIÓN:  Dada una consulta, genera su embedding y busca los
#                     fragmentos más similares (búsqueda por similitud
#                     coseno) en el vector store.
#   3. GENERACIÓN:    Envía los fragmentos recuperados al LLM como contexto,
#                     junto con el prompt de síntesis, para producir una
#                     respuesta precisa y trazable.
# ============================================================================

import logging
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import (
    DOCS_DIR, VECTOR_DB_DIR, get_api_key,
    EMBEDDING_MODEL, RAG_K, CHUNK_SIZE, CHUNK_OVERLAP,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Pipeline de Recuperación Aumentada por Generación sobre documentos
    internos de la municipalidad."""

    def __init__(self, persist: bool = True):
        if os.environ.get("OPENAI_API_KEY") is None:
            os.environ["OPENAI_API_KEY"] = get_api_key()
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError(
                "No se encontró la clave OPENAI_API_KEY. "
                "Configúrala como variable de entorno o en un archivo .env "
                "junto al proyecto (ver README.md)."
            )
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        self.persist = persist
        self.vectorstore = None

    # ------------------------------------------------------------------------
    # ETAPA 1: CARGAR DOCUMENTOS INTERNOS
    # ------------------------------------------------------------------------
    def _load_documents(self) -> List:
        """Carga todos los documentos internos (txt, md, pdf) desde DOCS_DIR."""
        docs = []
        supported = [".txt", ".md", ".pdf"]
        for path in sorted(DOCS_DIR.glob("*")):
            if path.suffix.lower() in supported:
                try:
                    if path.suffix.lower() == ".pdf":
                        loader = PyPDFLoader(str(path))
                    else:
                        loader = TextLoader(str(path), encoding="utf-8")
                    loaded = loader.load()
                    for d in loaded:
                        d.metadata["source"] = path.name
                    docs.extend(loaded)
                    logger.info("Cargado: %s (%d páginas/secciones)", path.name, len(loaded))
                except Exception as e:  # noqa: BLE001
                    logger.warning("No se pudo cargar %s: %s", path.name, e)
        if not docs:
            raise FileNotFoundError(
                f"No se encontraron documentos en {DOCS_DIR}. "
                "Agrega archivos .txt, .md o .pdf."
            )
        return docs

    # ------------------------------------------------------------------------
    # ETAPA 2: DIVIDIR EN FRAGMENTOS (CHUNKING)
    # ------------------------------------------------------------------------
    def _split_documents(self, docs: List) -> List:
        """Divide los documentos en fragmentos de tamaño controlado con
        solapamiento para preservar el contexto entre fragmentos."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(docs)
        logger.info("Documentos divididos en %d fragmentos", len(chunks))
        return chunks

    # ------------------------------------------------------------------------
    # ETAPA 3: GENERAR EMBEDDINGS E INDEXAR EN CHROMA
    # ------------------------------------------------------------------------
    def indexar(self, force_reindex: bool = False) -> None:
        """Construye o carga el almacén vectorial con los embeddings de los
        documentos internos."""
        collection = "virtualmuni_docs"

        # Si ya existe el índice y no se fuerza reindexación, cargarlo
        if not force_reindex and VECTOR_DB_DIR.exists():
            self.vectorstore = Chroma(
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embeddings,
                collection_name=collection,
            )
            logger.info("Almacén vectorial cargado desde %s", VECTOR_DB_DIR)
            return

        docs = self._load_documents()
        chunks = self._split_documents(docs)

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(VECTOR_DB_DIR),
            collection_name=collection,
        )
        if self.persist:
            self.vectorstore.persist()
        logger.info(
            "Índice vectorial creado con %d fragmentos en %s",
            len(chunks), VECTOR_DB_DIR,
        )

    # ------------------------------------------------------------------------
    # ETAPA 4: RECUPERAR FRAGMENTOS RELEVANTES
    # ------------------------------------------------------------------------
    def recuperar(self, consulta: str, k: int = None) -> List:
        """Recupera los fragmentos más relevantes para una consulta mediante
        búsqueda por similitud en el vector store."""
        if self.vectorstore is None:
            raise RuntimeError("Debes llamar a indexar() antes de recuperar.")
        k = k or RAG_K
        docs = self.vectorstore.similarity_search(consulta, k=k)
        logger.info("Recuperados %d fragmentos para la consulta", len(docs))
        return docs

    @staticmethod
    def context_to_text(docs: List) -> str:
        """Convierte los documentos recuperados en un bloque de texto de
        contexto para el prompt de síntesis."""
        bloques = []
        for i, d in enumerate(docs, 1):
            fuente = d.metadata.get("source", "desconocida")
            bloques.append(f"[Documento {i}] (fuente: {fuente})\n{d.page_content}")
        return "\n\n".join(bloques)
