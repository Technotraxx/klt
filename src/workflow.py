"""
Workflow Modul - Updated for 4-Step Process & Date Injection
"""
import json
import os
from datetime import datetime

# Langfuse Import Check
LANGFUSE_AVAILABLE = False
try:
    from langfuse import observe, Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    def observe(*args, **kwargs):
        def decorator(func): return func
        return decorator

from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
    def __init__(self, config):
        self.config = config
        lf_client = None
        if config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                lf_client = Langfuse()
            except Exception: pass

        self.prompt_manager = PromptManager(config.PROMPT_DIR, langfuse_client=lf_client, use_langfuse=config.enable_langfuse)
        self.document_parser = DocumentParser()
        self.logger = WorkflowLogger()

    def get_date_string(self):
        # Gibt das aktuelle Datum formatiert zurück (z.B. 08. Dezember 2025)
        return datetime.now().strftime("%d. %B %Y")

    # ----------------------------------------------------------------
    # STEPS
    # ----------------------------------------------------------------

    @observe() 
    def step_parsing(self, uploaded_files):
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        return self.document_parser.parse_uploaded_files(uploaded_files)

    @observe() 
    def step_extraction(self, prompt_config, context, model_settings):
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        # User Message ist der reine Kontext (Dateien + Text)
        return self._api_call(
            system_prompt=system_prompt,
            user_input=context,
            json_mode=True,
            model_settings=model_settings,
            name="gemini-extraction"
        )

    @observe() 
    def step_draft_concept(self, prompt_config, extraction_json, model_settings):
        self.logger.info("💡 Phase 2: Konzept/Entwurf (JSON)...")
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        # Input ist das JSON aus Phase 1
        json_str = json.dumps(extraction_json, ensure_ascii=False) if not isinstance(extraction_json, str) else extraction_json
        
        # WICHTIG: Step 2 muss JSON zurückgeben, damit Step 3 damit arbeiten kann
        return self._api_call(
            system_prompt=system_prompt,
            user_input=f"EXTRAHIERTE DATEN:\n{json_str}",
            json_mode=True, 
            model_settings=model_settings,
            name="gemini-draft-concept"
        )

    @observe() 
    def step_write_article(self, prompt_config, extraction_json, draft_json, model_settings):
        self.logger.info("✍️ Phase 3: Artikel schreiben...")
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        json1 = json.dumps(extraction_json, ensure_ascii=False)
        json2 = json.dumps(draft_json, ensure_ascii=False)
        
        user_msg = (
            f"1. Extrahierte Daten (JSON):\n{json1}\n\n"
            f"2. Redaktionsvorschläge (JSON):\n{json2}"
        )

        # Output ist hier Text (Markdown), kein JSON
        return self._api_call(
            system_prompt=system_prompt,
            user_input=user_msg,
            json_mode=False,
            model_settings=model_settings,
            name="gemini-write-article"
        )

    @observe() 
    def step_check(self, prompt_config, article_text, extraction_json, original_input, model_settings):
        self.logger.info("🔍 Phase 4: Faktenprüfung...")
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        
        json_str = json.dumps(extraction_json, ensure_ascii=False)
        
        user_msg = (
            f"ORIGINAL INPUT (Rohdaten):\n{original_input}\n\n"
            f"EXTRAHIERTE DATEN (Strukturiert):\n{json_str}\n\n"
            f"ZU PRÜFENDER ARTIKEL:\n{article_text}"
        )
        
        return self._api_call(
            system_prompt=system_prompt,
            user_input=user_msg,
            json_mode=False,
            model_settings=model_settings,
            name="gemini-final-check"
        )

    # ----------------------------------------------------------------
    # CORE API CALL
    # ----------------------------------------------------------------

    def _api_call(self, system_prompt, user_input, json_mode, model_settings, name):
        settings = model_settings or {"model": None, "temp": 0.1}
        model_name = settings.get("model", "gemini-1.5-flash")
        
        # Datum Injection in den System Prompt
        date_str = self.get_date_string()
        full_system_prompt = f"CURRENT DATE: {date_str}\n\n{system_prompt}"
        
        # Tracing Logic
        if self.config.enable_langfuse and LANGFUSE_AVAILABLE:
            langfuse = Langfuse()
            try:
                with langfuse.start_as_current_generation(
                    name=name,
                    model=model_name,
                    model_parameters={"temperature": settings.get("temp"), "json_mode": json_mode},
                    input=[{"role": "system", "content": full_system_prompt}, {"role": "user", "content": user_input}]
                ) as generation:
                    
                    response = self.config.generate_content(
                        user_content=user_input,
                        system_instruction=full_system_prompt,
                        model_name=model_name,
                        temperature=settings.get("temp", 0.1),
                        json_mode=json_mode
                    )
                    
                    text_response = response.text
                    
                    usage_dict = None
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        usage_dict = {
                            "input": response.usage_metadata.prompt_token_count,
                            "output": response.usage_metadata.candidates_token_count,
                            "total": response.usage_metadata.total_token_count
                        }

                    generation.update(output=text_response, usage=usage_dict)
                    
                    if json_mode:
                        clean = text_response.replace("```json", "").replace("```", "").strip()
                        return json.loads(clean)
                    return text_response

            except Exception as e:
                print(f"Tracking Error: {e}")
                # Fallback falls Langfuse failt
                return self._execute_gemini(full_system_prompt, user_input, model_name, settings.get("temp"), json_mode)
        else:
            return self._execute_gemini(full_system_prompt, user_input, model_name, settings.get("temp"), json_mode)

    def _execute_gemini(self, system_prompt, user_input, model, temp, json_mode):
        response = self.config.generate_content(
            user_content=user_input,
            system_instruction=system_prompt,
            model_name=model, 
            temperature=temp, 
            json_mode=json_mode
        )
        text = response.text
        if json_mode:
            clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        return text

    def flush_stats(self):
        if self.config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                from langfuse import flush
                flush()
            except Exception: pass
