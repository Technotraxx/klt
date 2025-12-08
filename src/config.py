"""
Konfigurationsmodul - V3 Compliant
"""
import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

class Config:
    def __init__(self):
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(exist_ok=True)
        self.DEFAULT_MODEL = 'gemini-1.5-flash'
        
        # API Keys
        self.api_key = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
        
        # LangFuse V3 Setup
        # Wir setzen nur die Env Vars, die Instanziierung übernimmt der Workflow bei Bedarf
        self.enable_langfuse = self._setup_langfuse_env()

    def _get_secret(self, key):
        if key in st.secrets:
            return st.secrets[key]
        return os.environ.get(key)

    def _setup_langfuse_env(self):
        pk = self._get_secret("LANGFUSE_PUBLIC_KEY")
        sk = self._get_secret("LANGFUSE_SECRET_KEY")
        host = self._get_secret("LANGFUSE_HOST") or self._get_secret("LANGFUSE_BASE_URL")
        
        if pk and sk and host:
            os.environ["LANGFUSE_PUBLIC_KEY"] = pk
            os.environ["LANGFUSE_SECRET_KEY"] = sk
            os.environ["LANGFUSE_HOST"] = host
            return True
        return False

    def generate_content(self, prompt, model_name=None, temperature=0.1, json_mode=False):
        """Reiner Wrapper für Gemini"""
        if not self.client:
            raise ValueError("API Key fehlt!")

        target_model = model_name if model_name else self.DEFAULT_MODEL
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=8192
        )
        if json_mode:
            config.response_mime_type = "application/json"
            
        return self.client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=config
        )
