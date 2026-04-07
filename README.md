# Asistente Revisor de Expedientes Técnicos (Streamlit)

Este sistema automatiza la revisión de expedientes eléctricos PDF utilizando RegEx para reglas rígidas y Google Gemini para análisis semántico.

## 🚀 Requisitos Previos

1.  **Google Cloud Console**:
    - Crea un proyecto.
    - Habilita las APIs: **Google Sheets API**, **Google Drive API** y **Generative Language API** (Gemini).
    - Crea una **Service Account**, genera una llave JSON y cámbiale el nombre a `credentials.json`. Colócala en la raíz del proyecto.
2.  **API de Gemini**:
    - Obtén tu API Key desde [Google AI Studio](https://aistudio.google.com/).
3.  **Configuración de Entorno**:
    - Crea un archivo `.env` en la raíz con:
        ```env
        GOOGLE_API_KEY=tu_api_key_aqui
        ```

## 🛠️ Instalación y Configuración

1.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Inicializar Base de Datos (Google Sheets)**:
    - Ejecuta el generador para crear el Spreadsheet y las pestañas necesarias:
    ```bash
    python sheet_generator.py
    ```
    - **MUY IMPORTANTE**: Abre el Spreadsheet creado y compártelo con el email de tu Service Account (está dentro del `credentials.json`) dándole permisos de Editor.

## 🖥️ Ejecutar Aplicación

Inicia el servidor de Streamlit:
```bash
streamlit run app/main.py
```

## 📂 Estructura del Proyecto

- `app/main.py`: Interfaz principal y coordinación.
- `app/modules/`: Lógica de PDF, Gemini, Sheets, Scoring y Reglas.
- `app/utils/`: Patrones RegEx y helpers de texto.
- `sheet_generator.py`: Script de utilidad para configurar la base de datos.
