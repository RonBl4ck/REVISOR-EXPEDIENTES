import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
from datetime import datetime

class SheetsClient:
    def __init__(self, spreadsheet_name="Asistente Revisor Expedientes"):
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds_path = 'credentials.json'
        self.spreadsheet_name = spreadsheet_name
        self.client = self._authenticate()
        self.sh = self.client.open(spreadsheet_name)

    def _authenticate(self):
        if not os.path.exists(self.creds_path):
            raise FileNotFoundError("Error: 'credentials.json' no encontrado.")
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_path, self.scope)
        return gspread.authorize(creds)

    def get_history(self, ov):
        """Obtiene el historial de revisiones para un OV específico."""
        ws = self.sh.worksheet("historial")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return df
        return df[df['OV'].astype(str) == str(ov)]

    def check_cache(self, hash_md5, expected_version=None):
        """Verifica si el hash ya fue analizado."""
        ws = self.sh.worksheet("cache_analisis")
        data = ws.get_all_records()
        for row in data:
            if row['hash_md5'] == hash_md5:
                # Retornar el resultado_json parseado
                import json
                result = json.loads(row['resultado_json'])
                if expected_version and result.get('analysis_version') != expected_version:
                    return None
                return result
        return None

    def save_cache(self, hash_md5, ov, result_json):
        """Guarda resultado en caché."""
        ws = self.sh.worksheet("cache_analisis")
        import json
        ws.append_row([hash_md5, ov, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps(result_json)])

    def save_observations(self, observations, ov, atc, revision):
        """Guarda múltiples observaciones en la hoja historial usando batch update."""
        ws = self.sh.worksheet("historial")
        rows = []
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for obs in observations:
            rows.append([
                ov, atc, revision, fecha,
                obs.get('tipo_obs', 'CHAT'),
                obs.get('descripcion', ''),
                obs.get('pagina', ''),
                obs.get('cita', ''),
                obs.get('estado', 'Pendiente'),
                obs.get('origen', 'AUTO')
            ])
        
        if rows:
            ws.append_rows(rows)

    def get_active_rules(self):
        """Obtiene las reglas activas para inyectar en el prompt."""
        ws = self.sh.worksheet("reglas_activas")
        data = ws.get_all_records()
        return [r['texto_regla'] for r in data]

    def add_pending_rule(self, rule_data):
        """Agrega una regla a la lista de pendientes (con lógica de similitud externa)."""
        ws = self.sh.worksheet("reglas_pendientes")
        # id | texto_regla | patron_regex | tipo | origen_ov | fecha_creacion | frecuencia | prioridad | estado_aprobacion
        ws.append_row([
            rule_data.get('id'),
            rule_data.get('texto_regla'),
            rule_data.get('patron_regex', ''),
            rule_data.get('tipo', 'APRENDIDA'),
            rule_data.get('origen_ov'),
            datetime.now().strftime("%Y-%m-%d"),
            rule_data.get('frecuencia', 1),
            rule_data.get('prioridad', 'NORMAL'),
            'En revision'
        ])
