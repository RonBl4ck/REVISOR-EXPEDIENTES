import streamlit as st

def calculate_score(observations, extracted_data):
    """
    Cálculo del Quality Score 0-100 basándose en las observaciones.
    """
    score = 100
    
    # Penalizaciones por tipo de observación
    for obs in observations:
        tipo = obs.get("tipo_obs", "").upper()
        desc = obs.get("descripcion", "").upper()
        
        if "ALERTA ROJA" in desc or tipo == "INCOHERENCIA":
            score -= 10
        elif tipo == "FORMATO" or "ORTOGRÁFICO" in desc:
            score -= 3
            
    # Penalizaciones por ausencias críticas
    if not any("Cuadro de Cargas" in obs.get("descripcion", "") for obs in observations):
         # Si no hay cuadro de cargas marcado por regex, check if we found it
         pass # En el analyzer marcamos la falta si no existe

    # Mínimo 0 puntos
    final_score = max(0, score)
    
    # Evaluar color
    color = "green"
    if final_score < 50:
        color = "red"
    elif final_score < 80:
        color = "orange"
        
    return final_score, color

def display_score_gauge(score, color):
    """
    Visualización personalizada del score en Streamlit.
    """
    st.metric(label="Quality Score del Expediente", value=f"{score}/100")
    if color == "green":
        st.success("✅ Expediente de ALTA CALIDAD técnica.")
    elif color == "orange":
        st.warning("⚠️ Expediente con OBSERVACIONES MODERADAS.")
    else:
        st.error("❌ Expediente con DEFICIENCIAS CRÍTICAS.")
