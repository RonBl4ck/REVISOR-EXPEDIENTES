import hashlib
import pdfplumber
import fitz # PyMuPDF
from utils.text_helpers import clean_text, detect_scanned_page

def get_pdf_hash(pdf_bytes):
    """
    Calcula el hash MD5 de los bytes del PDF.
    """
    return hashlib.md5(pdf_bytes).hexdigest()

def extract_text_from_pdf(pdf_file, min_chars=50):
    """
    Extrae texto de cada página del PDF utilizando pdfplumber como principal
    y fitz como fallback.
    Retorna una lista de diccionarios: [{'page_num': 1, 'text': '...', 'is_scanned': False}, ...]
    """
    pages_content = []
    
    # Abrir con pdfplumber
    with pdfplumber.open(pdf_file) as pdf:
        doc = fitz.open(stream=pdf_file.getvalue(), filetype="pdf")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            # Intentar fallback si falla la extracción o es muy corta
            if not text or len(text) < min_chars:
                # Usar PyMuPDF (fitz) para esta página específica
                fitz_page = doc[i]
                text = fitz_page.get_text()
            
            text = clean_text(text)
            is_scanned = detect_scanned_page(text, min_chars)
            
            pages_content.append({
                "page_num": i + 1,
                "text": text,
                "is_scanned": is_scanned
            })
        doc.close()
            
    return pages_content

def create_suspicious_chunks(pages_content, marked_page_nums, max_chunk_size=3):
    """
    Agrupa páginas marcadas como sospechosas en bloques de máximo 3 consecutivas.
    marked_page_nums: Lista de números de página (1-indexed) donde se encontró algo relevante por regex.
    """
    if not marked_page_nums:
        return []

    chunks = []
    current_chunk = []
    
    # Sort and remove duplicates
    marked_page_nums = sorted(list(set(marked_page_nums)))
    
    for i, p_num in enumerate(marked_page_nums):
        # Si la página actual no es consecutiva a la anterior o el chunk está lleno, cerramos el anterior
        if current_chunk and (p_num != current_chunk[-1] + 1 or len(current_chunk) >= max_chunk_size):
            # Guardamos el chunk actual con su contenido consolidado y trazabilidad de página
            texts = [
                f"--- PÁGINA {p['page_num']} ---\n{p['text']}"
                for p in pages_content if p['page_num'] in current_chunk
            ]
            chunks.append({
                "pages": current_chunk,
                "text": "\n".join(texts)
            })
            current_chunk = []
            
        current_chunk.append(p_num)
        
    # Añadir el último chunk
    if current_chunk:
        texts = [
            f"--- PÁGINA {p['page_num']} ---\n{p['text']}"
            for p in pages_content if p['page_num'] in current_chunk
        ]
        chunks.append({
            "pages": current_chunk,
            "text": "\n".join(texts)
        })
        
    return chunks
