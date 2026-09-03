# ============================================================================
# MAIN - Asistente Virtual Municipal (VirtualMuni)
# ============================================================================
# Punto de entrada del sistema. Ofrece:
#   - Modo interactivo (chat en terminal).
#   - Modo demo (responde una lista de preguntas de prueba y guarda evidencia).
#
# USO:
#   python main.py --demo          -> ejecuta la demo con preguntas de prueba
#   python main.py                 -> chat interactivo en la terminal
# ============================================================================

import argparse
import os
import sys

# Asegura que los módulos del proyecto sean importables
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_api_key            # noqa: E402
from rag_pipeline import RAGPipeline      # noqa: E402
from agente import AgenteMunicipal        # noqa: E402
from automatizaciones import agendar_cita, consultar_estado, generar_solicitud  # noqa: E402


def inicializar_sistema():
    """Configura la API key e inicializa el pipeline RAG y el agente."""
    if not get_api_key():
        print("=" * 60)
        print("FALTA LA CLAVE OPENAI_API_KEY.")
        print("Configúrala como variable de entorno o crea un archivo .env")
        print("junto al proyecto con el contenido:")
        print("    OPENAI_API_KEY=tu_clave_aqui")
        print("=" * 60)
        sys.exit(1)

    print("Inicializando almacén vectorial (RAG)...")
    rag = RAGPipeline()
    rag.indexar()
    print("Índice vectorial listo.\n")
    return AgenteMunicipal(rag)


def modo_demo(agente):
    """Responde un conjunto de preguntas de prueba y guarda la evidencia."""
    preguntas = [
        "¿Qué necesito para obtener un certificado de nacimiento?",
        "¿Cuál es el horario de atención de la municipalidad?",
        "¿Cuánto cuesta el permiso de circulación y cuándo debo pagarlo?",
        "¿Cuánto se demora el trámite de patente comercial?",
    ]
    linea = "=" * 70
    salida = [linea, "EVIDENCIA DE PRUEBAS - Asistente Virtual Municipal", linea]

    for p in preguntas:
        print(f"\n>> Pregunta: {p}")
        try:
            resp = agente.responder(p)
        except Exception as e:  # noqa: BLE001
            resp = f"[ERROR] {e}"
        print(f">> Respuesta: {resp}\n")
        salida.append(f"PREGUNTA: {p}\nRESPUESTA: {resp}\n")

    # Guardar evidencia en pruebas/
    os.makedirs("pruebas", exist_ok=True)
    with open("pruebas/evidencia_demo.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(salida))
    print(f"\nEvidencia guardada en pruebas/evidencia_demo.txt")


def modo_demo_automatizaciones():
    """Demuestra el funcionamiento de las herramientas de automatización y
    guarda evidencia de pruebas."""
    resultados = []
    casos = [
        ("AGENDAR CITA",
         agendar_cita("Ana Pérez", "Certificado de Nacimiento", "2025-06-10", "10:30")),
        ("CONSULTAR ESTADO",
         consultar_estado("PA-2025-0002")),
        ("CONSULTAR ESTADO (folio inexistente)",
         consultar_estado("PA-0000")),
        ("GENERAR SOLICITUD",
         generar_solicitud("Permiso de Circulación", "Luis Gómez", "12.345.678-9",
                            "Vehículo patente ABC123")),
    ]
    linea = "=" * 70
    salida = [linea, "EVIDENCIA DE PRUEBAS - HERRAMIENTAS DE AUTOMATIZACIÓN",
              "Municipalidad de Puente Alto", linea]

    for nombre, resultado in casos:
        print(f"\n[{nombre}]")
        print(resultado)
        salida.append(f"[{nombre}]\n{resultado}\n")

    os.makedirs("pruebas", exist_ok=True)
    with open("pruebas/evidencia_automatizaciones.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(salida))
    print(f"\nEvidencia guardada en pruebas/evidencia_automatizaciones.txt")


def modo_chat(agente):
    """Chat interactivo en la terminal."""
    print("VirtualMuni: ¡Hola! Soy tu asistente municipal. Escribe tu consulta "
          "o 'salir' para terminar.\n")
    while True:
        try:
            pregunta = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break
        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("VirtualMuni: Hasta luego. ¡No dudes en volver!")
            break
        try:
            respuesta = agente.responder(pregunta)
        except Exception as e:  # noqa: BLE001
            respuesta = f"[ERROR] {e}"
        print(f"VirtualMuni: {respuesta}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VirtualMuni - Agente municipal IA")
    parser.add_argument(
        "--demo", action="store_true",
        help="Ejecuta la demo con preguntas de prueba y guarda evidencia.",
    )
    parser.add_argument(
        "--reindex", action="store_true",
        help="Fuerza la reconstrucción del índice vectorial.",
    )
    parser.add_argument(
        "--automatizar", action="store_true",
        help="Ejecuta la demo de las herramientas de automatización.",
    )
    args = parser.parse_args()

    # Modo automatizaciones no requiere API key (solo herramientas locales)
    if args.automatizar:
        modo_demo_automatizaciones()
        sys.exit(0)

    agente = inicializar_sistema()
    if args.reindex:
        agente.rag.indexar(force_reindex=True)

    if args.demo:
        modo_demo(agente)
    else:
        modo_chat(agente)
