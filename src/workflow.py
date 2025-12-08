"""
Workflow Modul
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
        return datetime.now().strftime("%d. %B %Y")

    # ----------------------------------------------------------------
    # MASTER WORKFLOW (Parent Trace)
    # ----------------------------------------------------------------
    
    @observe(name="editorial_workflow") # <--- Das hier erzeugt den EINEN Trace
    def run_workflow(self, uploaded_files, meta_input, text_input, prompt_configs, model_settings, status_callback=None):
        """
        Führt alle Schritte innerhalb eines einzigen Traces aus.
        status_callback: Funktion, um Updates an die UI zu senden (z.B. container.write)
        """
        results = {}
        
        # Helper für Status-Updates
        def update_ui(msg):
            if status_callback: status_callback(msg)
            self.logger.info(msg)

        # 0. Parsing
        update_ui("📎 Parse Dokumente...")
        file_content = self.step_parsing(uploaded_files) # Wird automatisch Child-Span
        full_raw_input = f"META: {meta_input}\nTEXT: {text_input}\nFILES: {file_content}"
        results["raw"] = full_raw_input
        
        # 1. Extraction
        update_ui(f"🤖 Extraktion mit {prompt_configs['extract']['name']}...")
        json_data = self.step_extraction(prompt_configs['extract'], full_raw_input, model_settings)
        results["json"] = json_data
        
        # 2. Draft
        update_ui(f"💡 Konzept mit {prompt_configs['draft']['name']}...")
        concept_json = self.step_draft_concept(prompt_configs['draft'], json_data, model_settings)
        results["concept"] = concept_json
        
        # 3. Write
        update_ui(f"✍️ Artikel schreiben mit {prompt_configs['write']['name']}...")
        article_data = self.step_write_article(prompt_configs['write'], json_data, concept_json, model_settings)
        results["article"] = article_data
        
        # 4. Check
        update_ui(f"🔍 Check mit {prompt_configs['check']['name']}...")
        
        # Check Input vorbereiten
        article_text_for_check = json.dumps(article_data, ensure_ascii=False) if isinstance(article_data, dict) else str(article_data)
        check_text = self.step_check(prompt_configs['check'], article_text_for_check, json_data, full_raw_input, model_settings)
        results["check"] = check_text
        
        return results

    # ----------------------------------------------------------------
    # SUB-STEPS (Werden automatisch zu Spans im Trace)
    # ----------------------------------------------------------------

    @observe() 
    def step_parsing(self, uploaded_files):
        return self.document_parser.parse_uploaded_files(uploaded_files)

    @observe() 
    def step_extraction(self, prompt_config, context, model_settings):
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        return self._api_call(system_prompt, context, True, model_settings, "gemini-extraction")

    @observe() 
    def step_draft_concept(self, prompt_config, extraction_json, model_settings):
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(extraction_json, ensure_ascii=False) if not isinstance(extraction_json, str) else extraction_json
        return self._api_call(system_prompt, f"EXTRAHIERTE DATEN:\n{json_str}", True, model_settings, "gemini-draft-concept")

    @observe() 
    def step_write_article(self, prompt_config, extraction_json, draft_json, model_settings):
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json1 = json.dumps(extraction_json, ensure_ascii=False)
        json2 = json.dumps(draft_json, ensure_ascii=False)
        user_msg = f"1. Extrahierte Daten (JSON):\n{json1}\n\n2. Redaktionsvorschläge (JSON):\n{json2}"
        return self._api_call(system_prompt, user_msg, True, model_settings, "gemini-write-article")

    @observe() 
    def step_check(self, prompt_config, article_text, extraction_json, original_input, model_settings):
        system_prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(extraction_json, ensure_ascii=False)
        user_msg = f"ORIGINAL INPUT (Rohdaten):\n{original_input}\n\nEXTRAHIERTE DATEN:\n{json_str}\n\nZU PRÜFENDER ARTIKEL:\n{article_text}"
        return self._api_call(system_prompt, user_msg, False, model_settings, "gemini-final-check")

    # ----------------------------------------------------------------
    # API CALL (Generation)
    # ----------------------------------------------------------------

    def _api_call(self, system_prompt, user_input, json_mode, model_settings, name):
        """
        Führt den Call aus. Durch @observe auf den Parent-Methoden
        können wir hier den Context Manager nutzen, um Generation-Details hinzuzufügen.
        """
        settings = model_settings or {"model": None, "temp": 0.1}
        model_name = settings.get("model", "gemini-1.5-flash")
        
        date_str = self.get_date_string()
        full_system_prompt = f"CURRENT DATE: {date_str}\n\n{system_prompt}"
        
        # Fallback ohne Langfuse
        if not (self.config.enable_langfuse and LANGFUSE_AVAILABLE):
            return self._execute_gemini(full_system_prompt, user_input, model_name, settings.get("temp"), json_mode)

        # MIT Langfuse V3 Context Manager
        try:
            langfuse = Langfuse() # Holt Kontext automatisch, wenn wir im Trace sind
            
            # Hier nutzen wir start_as_current_generation. 
            # Weil diese Methode von einer @observe Methode aufgerufen wird,
            # wird diese Generation automatisch untergeordnet.
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
                
                # Usage Tracking
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
            return self._execute_gemini(full_system_prompt, user_input, model_name, settings.get("temp"), json_mode)

    def _execute_gemini(self, system_prompt, user_input, model, temp, json_mode):
        # ... (bleibt gleich wie vorher)
        response = self.config.generate_content(user_content=user_input, system_instruction=system_prompt, model_name=model, temperature=temp, json_mode=json_mode)
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
