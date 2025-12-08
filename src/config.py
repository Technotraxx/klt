"""
Konfigurationsmodul für Streamlit
Verwaltet API Keys und Pfade
"""

import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

class Config:
    """Zentrale Konfigurationsklasse für Streamlit"""
    
    def __init__(self):
        # Basis-Pfade relativ zum Script
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(exist_ok=True)
        
        self.MODEL_NAME = 'gemini-flash-latest'
        
        # API Keys laden (Priorität: UI Input > Secrets > Env Vars)
        self.api_key = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # LangFuse Setup
        self.langfuse = None
        self.enable_langfuse = self._setup_langfuse()

    def _get_secret(self, key):
        """Holt Secrets aus Streamlit Secrets oder Environment"""
        if key in st.secrets:
            return st.secrets[key]
        return os.environ.get(key)

    def _setup_langfuse(self):
        """Initialisiert LangFuse wenn Keys vorhanden sind"""
        public_key = self._get_secret("LANGFUSE_PUBLIC_KEY")
        secret_key = self._get_secret("LANGFUSE_SECRET_KEY")
        base_url = self._get_secret("LANGFUSE_BASE_URL")
        
        if public_key and secret_key and base_url:
            os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
            os.environ["LANGFUSE_SECRET_KEY"] = secret_key
            os.environ["LANGFUSE_HOST"] = base_url # Langfuse SDK nutzt HOST oder BASE_URL
            
            try:
                from langfuse import Langfuse
                self.langfuse = Langfuse()
                if self.langfuse.auth_check():
                    return True
            except Exception as e:
                print(f"LangFuse Init Error: {e}")
        
        return False

    def generate_content(self, prompt, json_mode=False):
        """Wrapper für Gemini API Call"""
        if not self.client:
            raise ValueError("API Key fehlt! Bitte in der Sidebar eingeben.")

        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192
        )
        
        if json_mode:
            config.response_mime_type = "application/json"
        
        response = self.client.models.generate_content(
            model=self.MODEL_NAME,
            contents=prompt,
            config=config
        )
        
        return response
