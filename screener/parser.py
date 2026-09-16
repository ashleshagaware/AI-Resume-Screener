# Document Parser for TXT, PDF, and DOCX Resume Files

import os
import io
import re
from typing import Tuple, Optional
import pypdf
import docx

def extract_candidate_name(text: str, fallback_filename: str = "") -> str:
    """
    Infers the candidate name from the top lines of the resume text,
    avoiding header words like 'Resume', 'Curriculum Vitae', 'CV', etc.
    Falls back to cleaned filename if text header is ambiguous.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ignore_words = {'resume', 'curriculum vitae', 'cv', 'profile', 'contact', 'summary', 'about me', 'bio', 'personal'}
    
    for line in lines[:8]:
        # Remove phone numbers, emails, URLs, addresses
        clean_line = re.sub(r'[\w\.-]+@[\w\.-]+', '', line)
        clean_line = re.sub(r'(\+?\d[\d\s\-\(\)]{7,}\d)', '', clean_line)
        clean_line = re.sub(r'https?://\S+', '', clean_line)
        clean_line = re.sub(r'[^\w\s\.\'-]', '', clean_line).strip()
        
        words = clean_line.split()
        if 2 <= len(words) <= 4:
            if not any(w.lower() in ignore_words for w in words):
                # Ensure it looks like a person's name (letters only)
                if all(w.replace('.', '').replace('-', '').isalpha() for w in words):
                    return ' '.join(words).title()
    
    # Fallback to filename without extension
    if fallback_filename:
        name = os.path.splitext(fallback_filename)[0]
        name = re.sub(r'[_-]', ' ', name)
        name = re.sub(r'\bresume\b|\bcv\b|\bfinal\b|\bv\d+\b', '', name, flags=re.IGNORECASE).strip()
        if name:
            return name.title()
            
    return "Candidate"

def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extracts text from TXT file bytes with charset fallback."""
    for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode('utf-8', errors='ignore')

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts text from PDF file bytes using pypdf."""
    stream = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(stream)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from DOCX file bytes including paragraphs and tables."""
    stream = io.BytesIO(file_bytes)
    doc = docx.Document(stream)
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text.strip())
    for table in doc.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                text_parts.append(" | ".join(row_cells))
    return "\n".join(text_parts)

def parse_resume_file(filename: str, file_bytes: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parses a resume file and extracts text and candidate name.
    Returns: (candidate_name, extracted_text, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == '.txt':
            text = extract_text_from_txt(file_bytes)
        elif ext == '.pdf':
            text = extract_text_from_pdf(file_bytes)
        elif ext in ['.docx', '.doc']:
            text = extract_text_from_docx(file_bytes)
        else:
            return None, None, f"Unsupported file type: {ext}. Supported formats are .pdf, .docx, .txt"
        
        text = text.strip()
        if not text:
            return None, None, "File appears to be empty or contains no extractable text."
            
        candidate_name = extract_candidate_name(text, fallback_filename=filename)
        return candidate_name, text, None
        
    except Exception as e:
        return None, None, f"Failed to extract text from {filename}: {str(e)}"
