import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st
from utils.text_helpers import estimate_tokens

# Load env
load_dotenv()

class GeminiClient:
    def __init__(self, api_key=None):
        # Primero busca en st.secrets (Nube), luego en env (Local)
        self.api_key = api_key or st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("Error: GOOGLE_API_KEY no encontrada en .env ni en st.secrets")
        genai.configure(api_key=self.api_key)
        
        # Configuraciones de modelos (Actualizados a 2.5 Flash)
        self.flash_model = genai.GenerativeModel('gemini-2.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_chunk(self, chunk_text, active_rules=None):
        """
        Analiza un chunk de texto (máx 3 págs) usando gemini-1.5-flash.
        Devuelve una lista de observaciones en formato JSON.
        """
        rules_text = "\n".join([f"- {r}" for r in active_rules]) if active_rules else "No hay reglas adicionales."
        
        system_prompt = f"""
        Eres un experto revisor de expedientes técnicos eléctricos en Perú.
        Tu tarea es analizar el siguiente fragmento de un PDF y detectar:
        1. Incoherencias técnicas (ej. contradicciones de potencia, materiales no permitidos).
        2. Omisiones de normativa eléctrica peruana.
        3. Términos prohibidos o ambiguos.
        
        REGLAS ACTIVAS APLICAR:
        {rules_text}
        
        IMPORTANTE: Devuelve la respuesta ÚNICAMENTE como una lista de objetos JSON con esta estructura exacta:
        [
            {{
                "tipo": "INCOHERENCIA",
                "descripcion": "Descripción clara del error",
                "pagina": "Número de página",
                "cita": "Fragmento exacto del texto donde está el error",
                "sugerencia_comentario": "Texto formal para el reporte"
            }}
        ]
        Si no encuentras nada, devuelve una lista vacía [].
        """
        
        # Log de tokens estimado
        tokens = estimate_tokens(chunk_text)
        print(f"[Gemini Log] Analizando chunk (~{tokens} tokens)...")
        
        try:
            response = self.flash_model.generate_content(
                f"{system_prompt}\n\nTEXTO DEL EXPEDIENTE:\n{chunk_text}",
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[Gemini Error]: {e}")
            return []

    def chat_with_pdf(self, user_query, context_text):
        """
        Responde a una consulta libre del usuario usando gemini-1.5-pro.
        Context_text debe ser el conjunto de páginas relevantes.
        """
        chat_prompt = f"""
        Actúa como un asistente técnico experto. Responde de forma CONCISA a la consulta del usuario basándote EN EL SIGUIENTE CONTEXTO.
        REGLA ESTRICTA: Debes citar obligatoriamente el Número de Página y el Fragmento Exacto del que extraes la información.
        
        CONTEXTO DEL EXPEDIENTE:
        {context_text}
        
        CONSULTA DEL USUARIO:
        {user_query}
        """
        
        try:
            response = self.pro_model.generate_content(chat_prompt)
            return response.text
        except Exception as e:
            return f"Error en el chat: {e}"
