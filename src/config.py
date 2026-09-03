# ============================================================================
# CONFIGURACIÓN - Asistente Virtual Municipal (VirtualMuni)
# ============================================================================
# Este módulo centraliza la configuración del sistema: credenciales,
# selección de modelos y rutas. Permite usar proveedores de pago (OpenAI)
# o alternativas gratuitas y locales sin modificar el resto del código.
# ============================================================================

import os
from pathlib import Path

# Ruta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta de los documentos internos (fuente del RAG)
DOCS_DIR = BASE_DIR / "data" / "documentos"

# Ruta donde se persistirá el almacén vectorial (ChromaDB)
VECTOR_DB_DIR = BASE_DIR / "data" / "chroma_db"

# Directorio de pruebas / evidencia
PRUEBAS_DIR = BASE_DIR / "pruebas"


def get_api_key():
    """Obtiene la clave de API OpenAI desde variables de entorno.

    Se lee desde la variable de entorno OPENAI_API_KEY. El usuario debe
    configurar esta variable (o un archivo .env) antes de ejecutar el sistema.
    """
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        # Intenta leer un archivo .env sencillo (formato CLAVE=valor)
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("OPENAI_API_KEY=") and not line.startswith("#"):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


# Configuración del modelo de embeddings
EMBEDDING_MODEL = "text-embedding-3-small"   # OpenAI

# Configuración del LLM generador
LLM_MODEL = "gpt-4o-mini"                     # OpenAI
LLM_TEMPERATURE = 0.2                         # Baja para respuestas precisas
MAX_TOKENS = 700

# Configuración de recuperación RAG
RAG_K = 4                                     # Número de documentos a recuperar

# Número de documentos a dividir (chunking)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
