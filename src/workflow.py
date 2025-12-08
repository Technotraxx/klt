"""
Workflow Modul
Enthält die Hauptverarbeitungslogik
Basierend auf Original-Code
"""

import json
import datetime
import os

# Absolute Imports für Streamlit
from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
    """Verarbeitet den kompletten Workflow von Input bis Output"""
    
    def __init__(self, config):
        self.config = config
        self.prompt_manager = PromptManager(
            config.PROMPT_DIR,
            langfuse_client=config.langfuse,
            use_langfuse=config.enable_langfuse
        )
        self.document_parser = DocumentParser()
        self.logger = WorkflowLogger()
        self.status_tracker = StatusTracker()
        
    # --- Public Steps für App.py (damit wir Zwischenschritte sehen) ---
    
    def step_parsing(self, uploaded_files):
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        return self.document_parser.parse_uploaded_files(uploaded_files)

    def step_extraction(self, prompt_config, context, model_settings):
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        return self._do_extraction(prompt, context, model_settings)

    def step_draft(self, prompt_config, json_data, model_settings):
        self.logger.info("✍️ Phase 2: Entwurf...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False) if not isinstance(json_data, str) else json_data
        return self._do_draft(prompt, json_str, model_settings)

    def step_check(self, prompt_config, json_data, draft_text, model_settings):
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False) if not isinstance(json_data, str) else json_data
        return self._do_fact_check(prompt, json_str, draft_text, model_settings)

    # --- Interne Logik mit Original Tracing ---

    def _do_extraction(self, prompt, context, model_settings):
        # Tracing nur wenn aktiv
        if self.config.enable_langfuse:
            from langfuse.decorators import observe
            @observe(name="extract_data")
            def _trace():
                return self._api_call(prompt, context, True, model_settings)
            return _trace()
        return self._api_call(prompt, context, True, model_settings)

    def _do_draft(self, prompt, json_str, model_settings):
        if self.config.enable_langfuse:
            from langfuse.decorators import observe
            @observe(name="generate_draft")
            def _trace():
                return self._api_call(prompt, json_str, False, model_settings)
            return _trace()
        return self._api_call(prompt, json_str, False, model_settings)

    def _do_fact_check(self, prompt, json_str, draft_text, model_settings):
        check_input = f"ORIGINAL DATEN (JSON):\n{json_str}\n\nGENERIERTER ENTWURF:\n{draft_text}"
        if self.config.enable_langfuse:
            from langfuse.decorators import observe
            @observe(name="fact_check")
            def _trace():
                return self._api_call(prompt, check_input, False, model_settings)
            return _trace()
        return self._api_call(prompt, check_input, False, model_settings)

    def _api_call(self, prompt, input_data, json_mode, model_settings):
        # Settings bauen
        settings = model_settings or {"model": None, "temp": 0.1}
        
        full_prompt = f"{prompt}\n\nINPUT:\n{input_data}"
        
        response = self.config.generate_content(
            full_prompt,
            model_name=settings.get("model"),
            temperature=settings.get("temp", 0.1),
            json_mode=json_mode
        )
        
        text = response.text
        if json_mode:
             clean_text = text.replace("```json", "").replace("```", "").strip()
             return json.loads(clean_text)
        return text

    def flush_stats(self):
        if self.config.enable_langfuse and self.config.langfuse:
            self.config.langfuse.flush()
