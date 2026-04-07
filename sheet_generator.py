import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def initialize_sheets(spreadsheet_name="Asistente Revisor Expedientes"):
    """
    Creates or initializes a Google Spreadsheet with required tabs and headers.
    """
    # Scope for Google Sheets and Drive
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Path to credentials
    creds_path = 'credentials.json'
    
    if not os.path.exists(creds_path):
        print(f"Error: No se encontró '{creds_path}'. Por favor, colócalo en el directorio raíz.")
        return

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        
        # Try to open, if not create
        print("\nOpciones:")
        print("1. Presiona ENTER para buscar por nombre.")
        print("2. Pega la URL completa del Spreadsheet.")
        user_input = input("> ").strip()

        if user_input.startswith("http"):
            sh = client.open_by_url(user_input)
            print(f"Abriendo spreadsheet por URL.")
        else:
            try:
                sh = client.open(spreadsheet_name)
                print(f"Abriendo spreadsheet existente: {spreadsheet_name}")
            except gspread.exceptions.SpreadsheetNotFound:
                print(f"No se encontró '{spreadsheet_name}'. Intentando crear uno nuevo...")
                sh = client.create(spreadsheet_name)
                print(f"Creado nuevo spreadsheet: {sh.title}")
                print(f"URL: {sh.url}")

        # Define tabs and headers
        tabs_config = {
            "historial": ["OV", "ATC", "N_revision", "fecha", "tipo_obs", "descripcion", "pagina", "cita", "estado", "origen"],
            "reglas_pendientes": ["id", "texto_regla", "patron_regex", "tipo", "origen_ov", "fecha_creacion", "frecuencia", "prioridad", "estado_aprobacion"],
            "reglas_activas": ["id", "texto_regla", "patron_regex", "tipo", "fecha_aprobacion", "aprobado_por"],
            "cache_analisis": ["hash_md5", "ov", "fecha", "resultado_json"]
        }

        for tab_name, headers in tabs_config.items():
            try:
                worksheet = sh.worksheet(tab_name)
                print(f"Pestaña '{tab_name}' ya existe.")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sh.add_worksheet(title=tab_name, rows="100", cols=len(headers) + 2)
                print(f"Creada pestaña '{tab_name}'.")
            
            # Set headers
            worksheet.update('A1', [headers])
            print(f"Headers actualizados para '{tab_name}'.")

        # Remove the default 'Sheet1' if it exists and we have others
        try:
            sheet1 = sh.worksheet("Hoja 1") or sh.worksheet("Sheet1")
            if len(sh.worksheets()) > 1:
                sh.del_worksheet(sheet1)
                print("Eliminada 'Sheet1' por defecto.")
        except:
            pass

        print("\n¡Inicialización completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la inicialización: {e}")

if __name__ == "__main__":
    name = input("Ingresa el nombre del Spreadsheet a crear/usar [Asistente Revisor Expedientes]: ") or "Asistente Revisor Expedientes"
    initialize_sheets(name)
