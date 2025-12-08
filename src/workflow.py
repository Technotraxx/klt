"""
Workflow Modul
Hauptverarbeitungslogik ohne Colab-Abhängigkeiten
"""

import json
import datetime
from .document_parser import DocumentParser
from .prompt_manager import PromptManager
from .logger import WorkflowLogger, StatusTracker

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
                         extraction_config, draft_config, control_config, user_id="streamlit_user"):
        """
        Hauptworkflow für Streamlit
        Returns: Dictionary mit Ergebnissen statt Dateipfad
        """
        if self.config.enable_langfuse:
            try:
                from langfuse.decorators import observe, langfuse_context
                
                @observe(name="streamlit_workflow")
                def traced_workflow():
                    langfuse_context.update_current_trace(
                        user_id=user_id,
                        tags=["streamlit", "v1.0"],
                        metadata={"file_count": len(uploaded_files) if uploaded_files else 0}
                    )
                    return self._execute_workflow(email_text, sender_meta, uploaded_files,
                                                 extraction_config, draft_config, control_config)
                
                return traced_workflow()
            except ImportError:
                return self._execute_workflow(email_text, sender_meta, uploaded_files,
                                             extraction_config, draft_config, control_config)
        else:
            return self._execute_workflow(email_text, sender_meta, uploaded_files,
                                         extraction_config, draft_config, control_config)

    def _execute_workflow(self, email_text, sender_meta, uploaded_files,
                         extraction_config, draft_config, control_config):
        
        self.logger.clear()
        self.logger.info("🚀 Workflow gestartet")
        
        # 1. Prompts laden
        prompt_extract = self.prompt_manager.load_prompt_by_config(extraction_config)
        prompt_draft = self.prompt_manager.load_prompt_by_config(draft_config)
        prompt_check = self.prompt_manager.load_prompt_by_config(control_config)
        
        # 2. Files Parsen
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        file_content = self.document_parser.parse_uploaded_files(uploaded_files)
        
        full_context = (
            f"METADATEN:\n{sender_meta}\n\n"
            f"NACHRICHT:\n{email_text}\n\n"
            f"ANHÄNGE:{file_content}"
        )
        
        # 3. Extraktion
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        extracted_data = self._api_call(prompt_extract, full_context, json_mode=True)
        extracted_json_str = json.dumps(extracted_data, ensure_ascii=False, indent=2)
        
        # 4. Draft
        self.logger.info("✍️ Phase 2: Entwurf...")
        draft_text = self._api_call(prompt_draft, extracted_json_str)
        
        # 5. Check
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        check_input = f"DATEN:\n{extracted_json_str}\n\nENTWURF:\n{draft_text}"
        fact_check_text = self._api_call(prompt_check, check_input)
        
        self.logger.info("✅ Fertig!")
        
        return {
            "json": extracted_json_str,
            "draft": draft_text,
            "check": fact_check_text,
            "logs": self.logger.get_logs()
        }

    def _api_call(self, prompt, context, json_mode=False):
        """Hilfsmethode für API Calls mit Error Handling"""
        try:
            response = self.config.generate_content(
                f"{prompt}\n\nINPUT:\n{context}",
                json_mode=json_mode
            )
            text = response.text
            if json_mode:
                return json.loads(text)
            return text
        except Exception as e:
            self.logger.error(f"API Fehler: {e}")
            raise e
