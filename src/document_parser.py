"""
Dokumenten-Parser Modul für Streamlit
Verarbeitet UploadedFile Objekte (Streams)
"""

import fitz  # PyMuPDF
import docx

class DocumentParser:
    """Parser für Streamlit Uploads"""
    
    @staticmethod
    def parse_pdf(file_stream):
        """Liest PDF aus Memory Stream"""
        text = ""
        try:
            # fitz.open kann direkt mit Bytes arbeiten
            with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        except Exception as e:
            text = f"[Fehler beim Lesen der PDF: {e}]"
        return text
    
    @staticmethod
    def parse_docx(file_stream):
        """Liest DOCX aus Memory Stream"""
        text = ""
        try:
            doc = docx.Document(file_stream)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            text = f"[Fehler beim Lesen der DOCX: {e}]"
        return text
    
    @staticmethod
    def parse_text_file(file_stream):
        """Liest Textdatei aus Memory Stream"""
        try:
            return file_stream.getvalue().decode("utf-8")
        except Exception as e:
            return f"[Fehler beim Lesen der Datei: {e}]"
    
    @classmethod
    def parse_uploaded_files(cls, uploaded_files):
        """
        Router für Streamlit UploadedFile Objekte
        
        Args:
            uploaded_files: Liste von Streamlit UploadedFile Objekten
            
        Returns:
            str: Kombinierter Inhalt
        """
        combined_content = ""
        if not uploaded_files:
            return ""
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            content = ""
            
            # Cursor auf Anfang setzen (wichtig bei Streamlit)
            uploaded_file.seek(0)
            
            if filename.lower().endswith('.pdf'):
                content = cls.parse_pdf(uploaded_file)
            elif filename.lower().endswith('.docx'):
                content = cls.parse_docx(uploaded_file)
            else:
                content = cls.parse_text_file(uploaded_file)
            
            combined_content += f"\n--- ANHANG: {filename} ---\n{content}\n"
        
        return combined_content
