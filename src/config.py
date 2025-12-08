"""
Konfigurationsmodul für Streamlit
Verwaltet API Keys, Pfade und Modell-Parameter
"""

import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

class Config:
    """Zentrale Konfigurationsklasse für Streamlit"""
    
    def __init__(self):
        # Basis-Pfade relativ zum Script (src/config.py -> parent -> root)
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(exist_ok=True)
        
        # Default Werte
        self.DEFAULT_MODEL = 'gemini-1.5-flash'
        
        # API Keys laden (Priorität: Streamlit Secrets > Env Vars)
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
        base_url = self._get_secret("LANGFUSE_BASE_URL") or self._get_secret("LANGFUSE_HOST")
        
        if public_key and secret_key and base_url:
            # Setze Env Vars für das Langfuse SDK
            os.environ["LANGFUSE_PUBLIC_KEY"] = public_key
            os.environ["LANGFUSE_SECRET_KEY"] = secret_key
            os.environ["LANGFUSE_HOST"] = base_url
            
            try:
                from langfuse import Langfuse
                self.langfuse = Langfuse()
                if self.langfuse.auth_check():
                    return True
            except Exception as e:
                print(f"LangFuse Init Error: {e}")
        
        return False

    def generate_content(self, prompt, model_name=None, temperature=0.1, json_mode=False):
        """
        Wrapper für Gemini API Call mit dynamischen Settings
        
        Args:
            prompt: Der Prompt String
            model_name: (Optional) Modellname, sonst Default
            temperature: (Optional) Kreativität 0.0 - 1.0
            json_mode: (Optional) Erzwingt JSON Output
        """
        if not self.client:
            raise ValueError("API Key fehlt! Bitte in der Sidebar eingeben.")

        # Nutze übergebenes Model oder Default
        target_model = model_name if model_name else self.DEFAULT_MODEL

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8192
        )
        
        if json_mode:
            config.response_mime_type = "application/json"
        
        try:
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=config
            )
            return response
        except Exception as e:
            # Hier könnten wir Fehler fangen (z.B. Model not found)
            raise e
