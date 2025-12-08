"""
Dokumenten-Parser Modul
Angepasst für Streamlit UploadedFile Objekte
"""

import fitz  # PyMuPDF
import docx

class DocumentParser:
    
    @staticmethod
    def parse_pdf(file_stream):
        text = ""
        try:
            with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        except Exception as e:
            text = f"[Fehler PDF: {e}]"
        return text
    
    @staticmethod
    def parse_docx(file_stream):
        text = ""
        try:
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"[Fehler DOCX: {e}]"
        return text
    
    @staticmethod
    def parse_text_file(file_stream):
        try:
            return file_stream.getvalue().decode("utf-8")
        except Exception as e:
            return f"[Fehler TXT: {e}]"
    
    @classmethod
    def parse_uploaded_files(cls, uploaded_files):
        """Erwartet Streamlit UploadedFile Liste"""
        combined_content = ""
        if not uploaded_files:
            return ""
        
        for file_obj in uploaded_files:
            filename = file_obj.name
            file_obj.seek(0) # Reset pointer
            
            content = ""
            if filename.lower().endswith('.pdf'):
                content = cls.parse_pdf(file_obj)
            elif filename.lower().endswith('.docx'):
                content = cls.parse_docx(file_obj)
            else:
                content = cls.parse_text_file(file_obj)
            
            combined_content += f"\n--- ANHANG: {filename} ---\n{content}\n"
        
        return combined_content
