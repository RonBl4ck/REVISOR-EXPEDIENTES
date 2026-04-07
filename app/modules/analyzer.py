import re
from utils.regex_patterns import find_matches, PATTERNS

class Analyzer:
    def __init__(self, pages_content):
        self.pages_content = pages_content
        self.extracted_data = {}  # Datos extraídos para comparación cruzada
        self.observations = []
        self.marked_pages = set() # Páginas donde regex encontró algo

    def add_observation(self, tipo, descripcion, pagina, cita, origen="AUTO"):
        """
        Agrega una observación al sistema.
        """
        self.observations.append({
            "tipo_obs": tipo,
            "descripcion": descripcion,
            "pagina": pagina,
            "cita": cita,
            "estado": "Pendiente",
            "origen": origen
        })
        self.marked_pages.add(pagina)

    def analyze_all(self):
        """
        Ejecuta los 4 módulos de análisis.
        """
        # Módulo 1 - Extracción de Datos Clave
        self.module_1_extraction()
        # Módulo 2 - Inventario SED
        self.module_2_inventory()
        # Módulo 3 - Detección de Incoherencias
        self.module_3_inconsistencies()
        # Módulo 4 - Formato y Ortografía
        self.module_4_formatting()

        return self.observations, list(self.marked_pages)

    def module_1_extraction(self):
        """
        Busca datos clave en las primeras páginas y guarda en `extracted_data`.
        """
        # Buscar en las primeras 5 páginas prioritariamente
        for page in self.pages_content[:10]: # Mayor alcance para mayor seguridad
            text = page['text']
            p_num = page['page_num']

            # Título/Tensión
            t_matches = re.search(PATTERNS["titulo_tension"], text)
            if t_matches:
                self.extracted_data["tension"] = t_matches.group(1)
                self.add_observation("EXTRACCION", f"Tensión detectada: {t_matches.group(1)}", p_num, t_matches.group(0))

            # Potencia
            p_matches = re.finditer(PATTERNS["potencia"], text)
            for m in p_matches:
                val = m.group(1)
                if "potencias" not in self.extracted_data:
                    self.extracted_data["potencias"] = []
                self.extracted_data["potencias"].append({"val": val, "p_num": p_num, "text": m.group(0)})
                self.add_observation("EXTRACCION", f"Potencia detectada: {m.group(0)}", p_num, m.group(0))

            # Frecuencia
            if re.search(PATTERNS["frecuencia"], text):
                self.extracted_data["frecuencia"] = "60Hz"
            elif re.search(r"\d+\s*Hz", text) and "60" not in text:
                self.add_observation("INCOHERENCIA", "Frecuencia diferente a 60Hz detectada", p_num, "Frecuencia no estándar")

            # Grupo de Conexión
            if re.search(PATTERNS["grupo_conexion"], text):
                self.extracted_data["grupo_conexion"] = "dyn5"

            # Profesionales
            prof_matches = re.finditer(PATTERNS["profesionales"], text)
            for m in prof_matches:
                self.add_observation("EXTRACCION", f"Profesional detectado: {m.group(1)} - {m.group(3)} (CIP {m.group(2)})", p_num, m.group(0))

    def module_2_inventory(self):
        """Módulo 2 - Inventario SED."""
        sed_count = 0
        for page in self.pages_content:
            text = page['text']
            p_num = page['page_num']

            # Tipo Transformador (Cerca de Transformador)
            if re.search(PATTERNS["tipo_transformador"], text):
                self.add_observation("INVENTARIO", "Tipo de transformador detectado", p_num, "Ver sección de equipos")

            # SED Exterior vs Trafomix
            if re.search(PATTERNS["ubicacion_sed_exterior"], text):
                if not re.search(PATTERNS["trafomix"], text):
                    self.add_observation("INCOHERENCIA", "SED Exterior mencionada pero no se detectó Trafomix", p_num, "Exterior sin Trafomix")
            
            # SED Interior vs Celda
            if re.search(PATTERNS["ubicacion_sed_interior"], text):
                if not re.search(PATTERNS["celda"], text):
                    self.add_observation("INCOHERENCIA", "SED Interior mencionada pero no se detectó Celda", p_num, "Interior sin Celdas")

            # Celdas Count
            celda_matches = re.findall(PATTERNS["celda"], text)
            if celda_matches:
                sed_count += len(celda_matches)

        self.extracted_data["total_celdas"] = sed_count

    def module_3_inconsistencies(self):
        """Módulo 3 - Detección de Incoherencias y términos prohibidos."""
        # Verificar Potencia (Global)
        pots = self.extracted_data.get("potencias", [])
        if pots:
            unique_pots = set([p['val'] for p in pots])
            if len(unique_pots) > 1:
                # Alerta Roja: Diferentes potencias
                desc = f"¡ALERTA ROJA! Se encontraron múltiples valores de potencia en el documento: {', '.join(unique_pots)}"
                all_pages = [p['p_num'] for p in pots]
                self.add_observation("INCOHERENCIA", desc, all_pages[0], "Conflicto entre páginas " + str(all_pages))

        for page in self.pages_content:
            text = page['text']
            p_num = page['page_num']

            # Término Prohibido
            if re.search(PATTERNS["termino_prohibido"], text):
                self.add_observation("INCOHERENCIA", "Término prohibido: 'subestación compacta tipo trafomix' no permitido en terminología técnico-legal actual", p_num, "Término prohibido")

            # Contradicción de alcance
            if re.search(PATTERNS["alcance_nuevo"], text) and re.search(PATTERNS["alcance_contradictorio"], text):
                self.add_observation("INCOHERENCIA", "¡ALERTA ROJA! Contradicción de alcance (dice 'nuevo' pero refiere a 'existente/actual')", p_num, "Contradicción Nuevo/Existente")

        # Verificar Cuadro de Cargas
        full_text = " ".join([p['text'] for p in self.pages_content])
        if not re.search(PATTERNS["cuadro_de_cargas"], full_text[:10000]): # Buscar en los primeros chars
             self.add_observation("INCOHERENCIA", "No se detectó sección 'Cuadro de Cargas' explícitamente", 1, "Falta Cuadro de Cargas")

    def module_4_formatting(self):
        """Módulo 4 - Formato y Ortografía."""
        for page in self.pages_content:
            text = page['text']
            p_num = page['page_num']

            # KV vs kV
            if re.search(PATTERNS["error_kv"], text):
                self.add_observation("FORMATO", "Uso de 'KV'. La norma técnica exige 'kV' (v minúscula).", p_num, "KV")
            
            # Acentos
            if re.search(PATTERNS["error_peru"], text): self.add_observation("FORMATO", "Error ortográfico: 'Peru' debe ser 'Perú'.", p_num, "Peru")
            if re.search(PATTERNS["error_utilizacion"], text): self.add_observation("FORMATO", "Error ortográfico: 'utilizacion' debe ser 'utilización'.", p_num, "utilizacion")
            if re.search(PATTERNS["error_instalacion"], text): self.add_observation("FORMATO", "Error ortográfico: 'instalacion' debe ser 'instalación'.", p_num, "instalacion")
            if re.search(PATTERNS["error_kva"], text): self.add_observation("FORMATO", "Uso de 'KVA'. La nomenclatura correcta es 'kVA'.", p_num, "KVA")
            if re.search(PATTERNS["error_kw"], text): self.add_observation("FORMATO", "Uso de 'KW'. La nomenclatura correcta es 'kW'.", p_num, "KW")
            if re.search(PATTERNS["error_kwh"], text): self.add_observation("FORMATO", "Uso de 'KWH'. La nomenclatura correcta es 'kWh'.", p_num, "KWH")
            if re.search(PATTERNS["error_ohm"], text): self.add_observation("FORMATO", "Uso de 'OHM'. La nomenclatura recomendada es 'ohm' o el símbolo 'Ω'.", p_num, "OHM")
