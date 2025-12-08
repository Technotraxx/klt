"""
Workflow Modul
Hauptverarbeitungslogik ohne Colab-Abhängigkeiten
"""

import json
import datetime

# Absolute Imports (wichtig für Streamlit Execution Context)
from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
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
        
    def process_workflow(self, email_text, sender_meta, uploaded_files, 
                         extraction_config, draft_config, control_config, 
                         model_settings=None, user_id="streamlit_user"):
        """
        Führt den gesamten Workflow am Stück aus (Legacy / Batch Mode).
        Nutzt LangFuse Tracing für den Gesamtprozess.
        """
        if self.config.enable_langfuse:
            try:
                from langfuse.decorators import observe, langfuse_context
                
                @observe(name="streamlit_workflow_full")
                def traced_workflow():
                    langfuse_context.update_current_trace(
                        user_id=user_id,
                        tags=["streamlit", "full_run"],
                        metadata={
                            "file_count": len(uploaded_files) if uploaded_files else 0,
                            "model": model_settings.get("model") if model_settings else "default"
                        }
                    )
                    return self._execute_full_workflow(email_text, sender_meta, uploaded_files,
                                                      extraction_config, draft_config, control_config,
                                                      model_settings)
                
                return traced_workflow()
            except ImportError:
                return self._execute_full_workflow(email_text, sender_meta, uploaded_files,
                                                  extraction_config, draft_config, control_config,
                                                  model_settings)
        else:
            return self._execute_full_workflow(email_text, sender_meta, uploaded_files,
                                              extraction_config, draft_config, control_config,
                                              model_settings)

    def _execute_full_workflow(self, email_text, sender_meta, uploaded_files,
                              extraction_config, draft_config, control_config, model_settings):
        """Interne Helper-Methode für den Gesamtprozess"""
        self.logger.clear()
        self.logger.info("🚀 Full Workflow gestartet")
        
        # 1. Parsing
        file_content = self.step_parsing(uploaded_files)
        full_context = f"META: {sender_meta}\nTEXT: {email_text}\nFILES: {file_content}"
        
        # 2. Extraktion
        json_data = self.step_extraction(extraction_config, full_context, model_settings)
        
        # 3. Draft
        draft_text = self.step_draft(draft_config, json_data, model_settings)
        
        # 4. Check
        check_text = self.step_check(control_config, json_data, draft_text, model_settings)
        
        self.logger.info("✅ Full Workflow beendet")
        
        return {
            "json": json.dumps(json_data, ensure_ascii=False, indent=2),
            "draft": draft_text,
            "check": check_text,
            "logs": self.logger.get_logs()
        }

    # =========================================================================
    # Einzelne Schritte (Public API für App.py)
    # =========================================================================

    def step_parsing(self, uploaded_files):
        """Schritt 1: Dateien parsen"""
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        return self.document_parser.parse_uploaded_files(uploaded_files)

    def step_extraction(self, prompt_config, context, model_settings):
        """Schritt 2: Extraktion (JSON)"""
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        return self._api_call(
            prompt, 
            context, 
            json_mode=True, 
            model_settings=model_settings
        )

    def step_draft(self, prompt_config, json_data, model_settings):
        """Schritt 3: Entwurf schreiben"""
        self.logger.info("✍️ Phase 2: Entwurf...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        # JSON wieder zu String für den Prompt
        if isinstance(json_data, str):
            json_str = json_data
        else:
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        return self._api_call(
            prompt, 
            json_str, 
            json_mode=False, 
            model_settings=model_settings
        )

    def step_check(self, prompt_config, json_data, draft_text, model_settings):
        """Schritt 4: Faktenprüfung"""
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        if isinstance(json_data, str):
            json_str = json_data
        else:
            json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
            
        check_input = f"DATEN:\n{json_str}\n\nENTWURF:\n{draft_text}"
        
        return self._api_call(
            prompt, 
            check_input, 
            json_mode=False, 
            model_settings=model_settings
        )

    def _api_call(self, prompt, context, json_mode=False, model_settings=None):
        """Zentraler API Aufruf mit Error Handling und Settings"""
        try:
            # Default Settings falls None
            settings = model_settings or {"model": None, "temp": 0.1}
            model_name = settings.get("model")
            temp = settings.get("temp", 0.1)
            
            response = self.config.generate_content(
                f"{prompt}\n\nINPUT:\n{context}",
                model_name=model_name,
                temperature=temp,
                json_mode=json_mode
            )
            
            text = response.text
            if json_mode:
                # Manchmal liefert das Modell Markdown Code-Blöcke trotz JSON Mode
                clean_text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            return text
            
        except Exception as e:
            self.logger.error(f"API Fehler: {e}")
            raise e
