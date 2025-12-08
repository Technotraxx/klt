"""
Konfigurationsmodul
"""
import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

# --- NEU: Import ---
from models import DEFAULT_MODEL 

class Config:
    def __init__(self):
        self.langfuse = None 
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        
        # --- NEU: Nutzung der Konstante ---
        self.MODEL_NAME = DEFAULT_MODEL
        
        # API Keys
        self.api_key = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        self.enable_langfuse = self._setup_langfuse()

    # ... (Rest der Datei bleibt exakt gleich: _get_secret, _setup_langfuse, generate_content)
    def _get_secret(self, key):
        if key in st.secrets:
            return st.secrets[key]
        return os.environ.get(key)

    def _setup_langfuse(self):
        try:
            pk = self._get_secret("LANGFUSE_PUBLIC_KEY")
            sk = self._get_secret("LANGFUSE_SECRET_KEY")
            host = self._get_secret("LANGFUSE_HOST") or self._get_secret("LANGFUSE_BASE_URL")
            
            if pk and sk and host:
                os.environ["LANGFUSE_PUBLIC_KEY"] = pk
                os.environ["LANGFUSE_SECRET_KEY"] = sk
                os.environ["LANGFUSE_HOST"] = host
                from langfuse import Langfuse
                self.langfuse = Langfuse()
                if self.langfuse.auth_check():
                    return True
                else:
                    self.langfuse = None
                    return False
            return False
        except Exception:
            self.langfuse = None
            return False

    def generate_content(self, user_content, system_instruction=None, model_name=None, temperature=0.1, json_mode=False):
        if not self.client:
            raise ValueError("API Key fehlt!")
            
        # Fallback auf Default aus models.py
        target_model = model_name if model_name else self.MODEL_NAME
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8192,
            system_instruction=system_instruction
        )
        if json_mode:
            config.response_mime_type = "application/json"
            
        return self.client.models.generate_content(
            model=target_model,
            contents=user_content,
            config=config
        )
