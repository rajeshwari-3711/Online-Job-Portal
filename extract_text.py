# extract_text.py

from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)
