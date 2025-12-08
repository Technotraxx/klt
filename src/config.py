"""
Konfigurationsmodul für Streamlit
"""

import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

class Config:
    """Zentrale Konfigurationsklasse"""
    
    def __init__(self):
        # Basis-Pfade (angepasst für Repo-Struktur)
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Modell Konfiguration
        self.MODEL_NAME = 'gemini-1.5-flash'
        
        # API Key Setup
        self.api_key = self._get_secret('GEMINI_API_KEY') or self._get_secret('GOOGLE_API_KEY')
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # LangFuse Setup - WICHTIG: Das Attribut muss existieren!
        self.langfuse = None 
        self.enable_langfuse = self._setup_langfuse()
    
    def _get_secret(self, key):
        """Holt Secrets aus Streamlit oder Environment"""
        if key in st.secrets:
            return st.secrets[key]
        return os.environ.get(key)
    
    def _setup_langfuse(self):
        """Setup LangFuse wie im Original"""
        try:
            from langfuse import Langfuse
            
            # Keys lesen
            pk = self._get_secret('LANGFUSE_PUBLIC_KEY')
            sk = self._get_secret('LANGFUSE_SECRET_KEY')
            host = self._get_secret('LANGFUSE_HOST') or self._get_secret('LANGFUSE_BASE_URL')
            
            if pk and sk and host:
                # Environment setzen (wichtig für SDK interne Calls)
                os.environ['LANGFUSE_PUBLIC_KEY'] = pk
                os.environ['LANGFUSE_SECRET_KEY'] = sk
                os.environ['LANGFUSE_HOST'] = host
                
                # Client instanziieren
                self.langfuse = Langfuse()
                
                # Test Connection
                if self.langfuse.auth_check():
                    print("✅ LangFuse: Verbindung erfolgreich")
                    return True
                else:
                    print("⚠️ LangFuse: Auth-Check fehlgeschlagen")
                    self.langfuse = None
                    return False
            return False
                
        except Exception as e:
            print(f"⚠️ LangFuse Setup fehlgeschlagen: {e}")
            self.langfuse = None
            return False
    
    def generate_content(self, prompt, model_name=None, temperature=0.1, json_mode=False):
        """Generiert Content (Original Wrapper)"""
        if not self.client:
            raise ValueError("API Key fehlt!")

        target_model = model_name if model_name else self.MODEL_NAME

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8192
        )
        
        if json_mode:
            config.response_mime_type = "application/json"
        
        response = self.client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config
        )
        
        return response
