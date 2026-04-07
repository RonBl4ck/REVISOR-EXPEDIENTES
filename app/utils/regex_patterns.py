import re

# Centralización de patrones RegEx para el Asistente Revisor
PATTERNS = {
    # MODULO 1: EXTRACCIÓN DE DATOS CLAVE
    "titulo_tension": r"(?i)(\d+\s*kV).*(?:\(operación inicial en (\d+\s*kV)\))?",
    "potencia": r"(?i)(\d+(?:\.\d+)?)\s*(kVA|KVA)",
    "frecuencia": r"(?i)60\s*Hz",
    "grupo_conexion": r"(?i)dyn5",
    "profesionales": r"(?i)(Ingeniero\s+(?:Civil|Eléctrico|Electricista|Mecánico\s+Eléctrico))\s*,?\s*CIP\s*[:#]?\s*(\d+)?\s*,?\s*([A-ZáéíóúÁÉÍÓÚ\s]+)",
    "ubicacion_distrito": r"(?i)Distrito\s*[:\-\s]\s*([A-ZáéíóúÁÉÍÓÚ\s]+)",

    # MODULO 2: INVENTARIO SED
    "tipo_transformador": r"(?i)(aceite|seco)\s+.*?transformador",
    "ubicacion_sed_exterior": r"(?i)exterior",
    "trafomix": r"(?i)trafomix",
    "ubicacion_sed_interior": r"(?i)interior",
    "celda": r"(?i)celda\s+de\s+(llegada|protección|transformación|medición|remonte|salida)",
    "spt_comun": r"(?i)puesta\s+a\s+tierra\s+común",

    # MODULO 3: INCOHERENCIAS & TÉRMINOS PROHIBIDOS
    "termino_prohibido": r"(?i)subestación\s+compacta\s+tipo\s+trafomix",
    "alcance_nuevo": r"(?i)nuevo",
    "alcance_contradictorio": r"(?i)(continúa|existente|actual|mismo\s+cableado)",

    # MODULO 4: FORMATO Y ORTOGRAFÍA
    "error_kv": r"KV",  # Sugerir 'kV'
    "error_kva": r"\bKVA\b",  # Sugerir 'kVA'
    "error_kw": r"\bKW\b",  # Sugerir 'kW'
    "error_kwh": r"\bKWH\b",  # Sugerir 'kWh'
    "error_ohm": r"\bOHM\b",  # Sugerir 'ohm' o 'Ω'
    "error_peru": r"Peru\b",  # Sugerir 'Perú'
    "error_utilizacion": r"utilizacion\b",  # Sugerir 'utilización'
    "error_instalacion": r"instalacion\b",  # Sugerir 'instalación'
    
    # SECCIONES OBLIGATORIAS
    "cuadro_de_cargas": r"(?i)Cuadro\s+de\s+Cargas"
}

def find_matches(pattern_key, text):
    """
    Busca todas las coincidencias para una clave de patrón dada.
    """
    pattern = PATTERNS.get(pattern_key)
    if not pattern:
        return []
    return re.findall(pattern, text)
