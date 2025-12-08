"""
Konfigurationsmodul
"""
import os
import streamlit as st
from pathlib import Path
from google import genai
from google.genai import types

class Config:
    def __init__(self):
        # 1. Definitive Initialisierung der Variable (Verhindert AttributeError)
        self.langfuse = None 
        
        # 2. Pfade setup
        self.BASE_DIR = Path(__file__).parent.parent
        self.PROMPT_DIR = self.BASE_DIR / "prompts"
        self.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 3. Model Defaults
        self.MODEL_NAME = 'gemini-flash-lastest'
        
        # 4. API Keys
        self.api_key = self._get_secret("GEMINI_API_KEY") or self._get_secret("GOOGLE_API_KEY")
        
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # 5. Langfuse Setup (Versucht self.langfuse zu befüllen)
        self.enable_langfuse = self._setup_langfuse()

    def _get_secret(self, key):
        if key in st.secrets:
            return st.secrets[key]
        return os.environ.get(key)

    def _setup_langfuse(self):
        try:
            # Versuche Keys zu laden
            pk = self._get_secret("LANGFUSE_PUBLIC_KEY")
            sk = self._get_secret("LANGFUSE_SECRET_KEY")
            host = self._get_secret("LANGFUSE_HOST") or self._get_secret("LANGFUSE_BASE_URL")
            
            if pk and sk and host:
                # Wichtig: Env Vars setzen für die Library (V3 braucht das)
                os.environ["LANGFUSE_PUBLIC_KEY"] = pk
                os.environ["LANGFUSE_SECRET_KEY"] = sk
                os.environ["LANGFUSE_HOST"] = host
                
                # Import und Init
                from langfuse import Langfuse
                self.langfuse = Langfuse()
                
                # Kurzer Auth Check
                if self.langfuse.auth_check():
                    print("✅ Langfuse verbunden")
                    return True
                else:
                    print("⚠️ Langfuse Auth fehlgeschlagen")
                    self.langfuse = None
                    return False
            
            return False
        except Exception as e:
            print(f"⚠️ Langfuse Fehler: {e}")
            self.langfuse = None
            return False

    def generate_content(self, prompt, model_name=None, temperature=0.1, json_mode=False):
        if not self.client:
            raise ValueError("API Key fehlt!")
            
        target_model = model_name if model_name else self.MODEL_NAME
        
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
