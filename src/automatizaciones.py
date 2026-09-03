# ============================================================================
# AUTOMATIZACIONES - Municipalidad de Puente Alto (VirtualMuni)
# ============================================================================
# Módulo de HERRAMIENTAS ACCIONABLES que permiten al agente no solo responder
# consultas, sino EJECUTAR TAREAS reales:
#
#   1. agendar_cita        : reserva una hora de atención para un trámite.
#   2. consultar_estado    : consulta el estado de un trámite por folio.
#   3. generar_solicitud   : rellena una plantilla de solicitud y la guarda.
#
# Estas herramientas simulan la integración con sistemas internos municipales
# (agenda de citas y sistema de gestión de trámites) almacenando los datos en
# archivos JSON locales, lo que permite demostrar el flujo de principio a fin.
# ============================================================================

import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Archivos que simulan las "bases de datos" internas de la municipalidad
CITAS_FILE = DATA_DIR / "citas.json"
TRAMITES_FILE = DATA_DIR / "tramites.json"
SOLICITUDES_DIR = DATA_DIR / "solicitudes_generadas"


def _leer_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def _escribir_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _seed_tramites():
    """Crea un registro inicial de trámites si no existe (datos simulados)."""
    if not TRAMITES_FILE.exists():
        inicial = {
            "trámites": [
                {
                    "folio": "PA-2025-0001",
                    "tipo": "Certificado de Nacimiento",
                    "solicitante": "Ana Pérez",
                    "estado": "En revisión",
                    "oficina": "Registro Civil",
                    "fecha": "2025-05-12",
                },
                {
                    "folio": "PA-2025-0002",
                    "tipo": "Permiso de Circulación",
                    "solicitante": "Luis Gómez",
                    "estado": "Aprobado",
                    "oficina": "Tesorería",
                    "fecha": "2025-04-02",
                },
                {
                    "folio": "PA-2025-0003",
                    "tipo": "Patente Comercial",
                    "solicitante": "María Torres",
                    "estado": "Pendiente de documentación",
                    "oficina": "Unidad de Patentes",
                    "fecha": "2025-03-20",
                },
            ]
        }
        _escribir_json(TRAMITES_FILE, inicial)


_seed_tramites()


# ----------------------------------------------------------------------------
# HERRAMIENTA 1: AGENDAR CITA
# ----------------------------------------------------------------------------
def agendar_cita(nombre: str, tramite: str, fecha: str, hora: str) -> str:
    """Registra una cita de atención municipal. Devuelve el folio de la cita."""
    citas = _leer_json(CITAS_FILE, {"citas": []})
    folio = f"CITA-{len(citas['citas']) + 1:04d}"
    cita = {
        "folio": folio,
        "nombre": nombre,
        "trámite": tramite,
        "fecha": fecha,
        "hora": hora,
        "creada": datetime.now().isoformat(timespec="minutes"),
    }
    citas["citas"].append(cita)
    _escribir_json(CITAS_FILE, citas)
    return (
        f"Cita agendada correctamente. Folio: {folio}. "
        f"Trámite: {tramite} para {nombre} el {fecha} a las {hora}."
    )


# ----------------------------------------------------------------------------
# HERRAMIENTA 2: CONSULTAR ESTADO DE TRÁMITE
# ----------------------------------------------------------------------------
def consultar_estado(folio: str) -> str:
    """Consulta el estado de un trámite por su folio interno."""
    datos = _leer_json(TRAMITES_FILE, {"trámites": []})
    for t in datos["trámites"]:
        if t["folio"].lower() == folio.strip().lower():
            return (
                f"Trámite {t['folio']} ({t['tipo']}) del solicitante "
                f"{t['solicitante']}: estado actual = {t['estado']}. "
                f"Oficina responsable: {t['oficina']}."
            )
    return (
        f"No se encontró un trámite con el folio '{folio}'. "
        "Verifica el folio o contacta a la mesa de ayuda municipal."
    )


# ----------------------------------------------------------------------------
# HERRAMIENTA 3: GENERAR SOLICITUD (formulario descargable)
# ----------------------------------------------------------------------------
def generar_solicitud(tipo_tramite: str, nombre: str, rut: str, detalle: str = "") -> str:
    """Genera una plantilla de solicitud rellenada con los datos del usuario
    y la guarda como archivo de texto descargable."""
    SOLICITUDES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"solicitud_{tipo_tramite.replace(' ', '_')}_{timestamp}.txt"
    filepath = SOLICITUDES_DIR / filename

    contenido = (
        "SOLICITUD DE TRÁMITE - MUNICIPALIDAD DE PUENTE ALTO\n"
        "=" * 45 + "\n\n"
        f"Tipo de trámite : {tipo_tramite}\n"
        f"Solicitante     : {nombre}\n"
        f"RUT             : {rut}\n"
        f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    )
    if detalle:
        contenido += f"Detalle         : {detalle}\n"
    contenido += (
        "\nDeclaro que la información entregada es verídica.\n\n"
        "______________________________\nFirma del solicitante\n"
    )

    filepath.write_text(contenido, encoding="utf-8")
    return (
        f"Solicitud generada correctamente y guardada en "
        f"{filepath.relative_to(BASE_DIR)}. Puedes descargarla desde este "
        f"archivo y presentarla en la oficina municipal."
    )
