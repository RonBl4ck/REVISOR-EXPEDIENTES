import re

def clean_text(text):
    """
    Limpia y normaliza el texto extraído del PDF.
    """
    if not text:
        return ""
    # Normalizar espacios en blanco y saltos de línea
    text = re.sub(r'\s+', ' ', text)
    # Eliminar caracteres no imprimibles básicos
    text = "".join(char for char in text if char.isprintable() or char == "\n")
    return text.strip()

def detect_scanned_page(text, min_chars=50):
    """
    Detecta si una página es un escaneo o un plano basándose en la cantidad de texto extraído.
    """
    if not text:
        return True
    return len(text) < min_chars

def estimate_tokens(text):
    """
    Estimación rápida de tokens (aprox. 1 token cada 4 caracteres).
    """
    if not text:
        return 0
    return len(text) // 4

def build_chat_context(pages_content, user_query, priority_pages=None, max_pages=6, max_chars=12000):
    """
    Construye un contexto compacto para chat priorizando:
    1. primeras páginas,
    2. páginas marcadas por el análisis,
    3. páginas cuyo texto coincide con términos de la consulta.
    """
    if not pages_content:
        return "", []

    priority_pages = set(priority_pages or [])
    query_terms = {
        term.lower()
        for term in re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]{3,}\b", user_query or "")
        if term.lower() not in {
            "que", "qué", "cual", "cuál", "como", "cómo", "donde", "dónde",
            "para", "sobre", "tiene", "esta", "este", "expediente", "pdf"
        }
    }

    ranked_pages = []
    for idx, page in enumerate(pages_content):
        page_num = page["page_num"]
        text_lower = page["text"].lower()
        score = 0

        if idx < 2:
            score += 5
        if page_num in priority_pages:
            score += 4
        if page.get("is_scanned"):
            score -= 2

        term_hits = sum(1 for term in query_terms if term in text_lower)
        score += min(term_hits, 5) * 3

        if score > 0:
            ranked_pages.append((score, page_num, page["text"]))

    if not ranked_pages:
        ranked_pages = [(1 if idx < 3 else 0, page["page_num"], page["text"]) for idx, page in enumerate(pages_content[:3])]

    ranked_pages.sort(key=lambda item: (-item[0], item[1]))

    selected_blocks = []
    selected_pages = []
    total_chars = 0

    for _, page_num, text in ranked_pages:
        block = f"--- PÁGINA {page_num} ---\n{text}"
        if selected_pages and (len(selected_pages) >= max_pages or total_chars + len(block) > max_chars):
            continue
        if not selected_pages and len(block) > max_chars:
            block = block[:max_chars]
        selected_blocks.append(block)
        selected_pages.append(page_num)
        total_chars += len(block)
        if len(selected_pages) >= max_pages or total_chars >= max_chars:
            break

    return "\n\n".join(selected_blocks), selected_pages
