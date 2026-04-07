from difflib import SequenceMatcher
import uuid
from datetime import datetime

class RulesEngine:
    def __init__(self, sheets_client):
        self.sheets_client = sheets_client

    def check_similarity(self, new_rule_text, threshold=0.70):
        """
        Compara la nueva regla con las pendientes existentes usando difflib.
        Si hay similitud, retorna el ID de la regla existente para incremento de frecuencia.
        """
        # Obtener todas las reglas pendientes
        ws = self.sheets_client.sh.worksheet("reglas_pendientes")
        data = ws.get_all_records()
        
        for row in data:
            similarity = SequenceMatcher(None, new_rule_text.lower(), str(row['texto_regla']).lower()).ratio()
            if similarity > threshold:
                return row['id'], row['frecuencia']
        
        return None, 0

    def process_new_rule(self, rule_text, ov, regex_pattern=""):
        """
        Procesa una nueva regla sugerida por el usuario o IA.
        Aplica lógica de similitud y frecuencia.
        """
        existing_id, freq = self.check_similarity(rule_text)
        
        if existing_id:
            # Incrementar frecuencia
            ws = self.sheets_client.sh.worksheet("reglas_pendientes")
            rows = ws.get_all_records()
            # Encontrar índice de fila (row 1 is header)
            for i, r in enumerate(rows):
                if r['id'] == existing_id:
                    new_freq = freq + 1
                    prioridad = 'ALTA' if new_freq >= 3 else r['prioridad']
                    ws.update_cell(i + 2, 7, new_freq) # Col 7: frecuencia
                    ws.update_cell(i + 2, 8, prioridad) # Col 8: prioridad
                    return f"Regla similar encontrada. Frecuencia actualizada a {new_freq}."
        
        # Si no existe, crear nueva
        rule_data = {
            "id": str(uuid.uuid4())[:8],
            "texto_regla": rule_text,
            "patron_regex": regex_pattern,
            "tipo": "APRENDIDA",
            "origen_ov": ov,
            "frecuencia": 1,
            "prioridad": "NORMAL"
        }
        self.sheets_client.add_pending_rule(rule_data)
        return "Nueva regla guardada para revisión del supervisor."
