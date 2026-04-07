import streamlit as st
import io
import pandas as pd
from modules.pdf_processor import get_pdf_hash, extract_text_from_pdf, create_suspicious_chunks
from modules.analyzer import Analyzer
from modules.gemini_client import GeminiClient
from modules.sheets_client import SheetsClient
from modules.scoring import calculate_score, display_score_gauge
from utils.text_helpers import build_chat_context

ANALYSIS_CACHE_VERSION = "2026-04-07-v1"

# Configuración de página
st.set_page_config(page_title="Asistente Revisor de Expedientes", layout="wide")

# Estilos personalizados (Premium)
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 20px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

# Inicializar cliente de Sheets (independiente de Gemini)
try:
    sheets = SheetsClient()
except Exception as e:
    st.error(f"Error de inicialización de Google Sheets: {e}")
    st.stop()

# --- SIDEBAR (Persistencia y Ajustes) ---
st.sidebar.title("🛠️ Configuración")

# Campo de API Key personal (tipo password para seguridad)
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 API de Gemini")
user_api_key = st.sidebar.text_input(
    "Tu API Key personal (opcional)",
    type="password",
    value=st.session_state.get('user_api_key', ''),
    help="Cada ingeniero puede usar su propia llave de Google AI Studio. Si lo dejas vacío, se usará la llave de la empresa."
)
if user_api_key:
    st.session_state['user_api_key'] = user_api_key

st.sidebar.markdown("---")
ov = st.sidebar.text_input("OV (Llave Primaria)", value=st.session_state.get('ov', ''), help="Obligatorio")
atc = st.sidebar.text_input("ATC", value=st.session_state.get('atc', ''), help="Cambia en cada revisión")
revision = st.sidebar.number_input("N° de Revisión", min_value=1, step=1, value=st.session_state.get('revision', 1))

if ov: st.session_state['ov'] = ov
if atc: st.session_state['atc'] = atc
st.session_state['revision'] = revision

# Inicializar cliente de Gemini (usa llave personal si existe, sino la de la empresa)
try:
    gemini = GeminiClient(api_key=st.session_state.get('user_api_key', ''))
    if gemini._using_personal_key:
        st.sidebar.success("✅ Usando tu llave personal")
    else:
        st.sidebar.info("ℹ️ Usando llave de la empresa")
except Exception as e:
    st.error(f"Error de inicialización de Gemini: {e}")
    st.stop()


# --- PANTALLA PRINCIPAL ---
st.title("⚡ Asistente Revisor de Expedientes Técnicos")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📂 Subida de Documento")
    uploaded_file = st.file_uploader("Cargar PDF del Expediente", type=["pdf"])

    if uploaded_file and ov and atc:
        if st.button("🚀 Iniciar Análisis"):
            with st.spinner("Procesando PDF..."):
                print("[DEBUG] Iniciando procesamiento...")
                # PASO 2 - Preprocesamiento
                pdf_bytes = uploaded_file.getvalue()
                pdf_hash = get_pdf_hash(pdf_bytes)
                print(f"[DEBUG] Hash calculado: {pdf_hash}")
                print("[DEBUG] Extrayendo texto del PDF...")
                pages_content = extract_text_from_pdf(io.BytesIO(pdf_bytes))
                print(f"[DEBUG] Texto extraído de {len(pages_content)} páginas")
                st.session_state['pages_content'] = pages_content
                st.session_state['current_pdf_hash'] = pdf_hash
                
                # Check Cache
                print("[DEBUG] Verificando caché en Sheets...")
                cached_result = sheets.check_cache(pdf_hash, ANALYSIS_CACHE_VERSION)
                print(f"[DEBUG] Caché encontrado: {bool(cached_result)}")
                if cached_result:
                    st.success("✅ Documento encontrado en caché. Cargando resultados...")
                    st.session_state['observations'] = cached_result['observations']
                    st.session_state['extracted_data'] = cached_result['extracted_data']
                    st.session_state['marked_pages'] = cached_result.get('marked_pages', [])
                else:
                    # Regex Analysis
                    analyzer = Analyzer(pages_content)
                    obs_regex, marked_pages = analyzer.analyze_all()
                    
                    # Gemini Analysis (Una sola petición consolidada para respetar Free Tier)
                    active_rules = sheets.get_active_rules()
                    chunks = create_suspicious_chunks(pages_content, marked_pages)
                    
                    # Consolidar TODOS los chunks en un solo texto grande
                    consolidated_text = "\n\n".join([chunk['text'] for chunk in chunks])
                    print(f"[DEBUG] Enviando {len(chunks)} chunks como 1 sola petición ({len(consolidated_text)} chars)...")
                    
                    obs_gemini = []
                    if consolidated_text.strip():
                        g_results = gemini.analyze_chunk(consolidated_text, active_rules)
                        for r in g_results:
                            obs_gemini.append({
                                "tipo_obs": r.get('tipo', 'INCOHERENCIA'),
                                "descripcion": r.get('descripcion', ''),
                                "pagina": r.get('pagina', ''),
                                "cita": r.get('cita', ''),
                                "estado": "Pendiente",
                                "origen": "AI"
                            })
                    
                    all_obs = obs_regex + obs_gemini
                    st.session_state['observations'] = all_obs
                    st.session_state['extracted_data'] = analyzer.extracted_data
                    st.session_state['marked_pages'] = marked_pages
                    
                    # Save Cache
                    sheets.save_cache(pdf_hash, ov, {
                        "analysis_version": ANALYSIS_CACHE_VERSION,
                        "observations": all_obs,
                        "extracted_data": analyzer.extracted_data,
                        "marked_pages": marked_pages
                    })

                # Check History
                hist = sheets.get_history(ov)
                if not hist.empty:
                    st.info(f"Se encontraron {len(hist)} observaciones previas para este OV.")
                    st.dataframe(hist[['N_revision', 'tipo_obs', 'descripcion', 'estado']].tail(5))

    # --- CHAT CON PDF ---
    if 'pages_content' in st.session_state:
        st.subheader("💬 Consulta Inteligente")
        with st.expander("Haz preguntas sobre el expediente", expanded=True):
            user_query = st.chat_input("¿De qué potencia es el transformador?")
            if user_query:
                # Reducimos tokens priorizando páginas introductorias, marcadas y semánticamente relevantes
                context, selected_pages = build_chat_context(
                    st.session_state['pages_content'],
                    user_query,
                    priority_pages=st.session_state.get('marked_pages', [])
                )
                response = gemini.chat_with_pdf(user_query, context)
                st.write(f"**Respuesta:** {response}")
                st.caption(f"Contexto enviado a Gemini: páginas {', '.join(map(str, selected_pages))}")
                
                # Persistencia del chat (Auditoría)
                sheets.save_observations([{
                    "tipo_obs": "CHAT",
                    "descripcion": f"Consulta: {user_query} | Respuesta: {response[:200]}...",
                    "pagina": ", ".join(map(str, selected_pages)) if selected_pages else "N/A",
                    "cita": response,
                    "origen": "AI_CHAT"
                }], ov, atc, revision)

with col2:
    st.subheader("📊 Resultados del Análisis")
    
    if 'observations' in st.session_state:
        # Score
        score, color = calculate_score(st.session_state['observations'], st.session_state['extracted_data'])
        display_score_gauge(score, color)
        
        tab_alerts, tab_data, tab_raw = st.tabs(["🔴 Alertas/Incoherencias", "🟢 Datos Extraídos", "📄 Lista Completa"])
        
        with tab_alerts:
            alerts = [o for o in st.session_state['observations'] if o['tipo_obs'] in ['INCOHERENCIA', 'ALERTA ROJA']]
            for i, a in enumerate(alerts):
                with st.expander(f"⚠️ {a['descripcion'][:60]}... (Pág. {a['pagina']})"):
                    st.write(f"**Detalle:** {a['descripcion']}")
                    st.write(f"**Cita:** `{a['cita']}`")
                    if st.button("📋 Copiar comentario", key=f"copy_btn_{i}_{a['pagina']}"):
                        st.info("Texto copiado al portapapeles (Simulado)")

        with tab_data:
            data = st.session_state['extracted_data']
            st.json(data)

        with tab_raw:
            df_obs = pd.DataFrame(st.session_state['observations'])
            st.dataframe(df_obs)
            
            if st.button("💾 Guardar Observaciones en Sheets"):
                # No guardar los de chat en la lista principal si queremos limpieza
                final_obs = [o for o in st.session_state['observations'] if o['tipo_obs'] != 'CHAT']
                sheets.save_observations(final_obs, ov, atc, revision)
                st.success("¡Observaciones guardadas exitosamente en la hoja historial!")

    else:
        st.info("Sube un PDF y presiona 'Iniciar Análisis' para ver los resultados.")
