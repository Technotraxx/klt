"""
Workflow Modul - LangFuse V3 Compliant
"""
import json
import os

# --- Imports & V3 Safety Check ---
LANGFUSE_AVAILABLE = False
try:
    # ✅ RICHTIG für V3: Import direkt aus langfuse
    from langfuse import observe, Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    print("⚠️ Langfuse SDK nicht gefunden oder zu alt.")
    # Dummy Decorator
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
    def __init__(self, config):
        self.config = config
        
        # Client für Prompt Management (V3 Style)
        lf_client = None
        if config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                # V3: Initialisierung ohne Args (holt aus Env)
                lf_client = Langfuse()
            except Exception as e:
                print(f"⚠️ Langfuse Init: {e}")

        self.prompt_manager = PromptManager(
            config.PROMPT_DIR, 
            langfuse_client=lf_client,
            use_langfuse=config.enable_langfuse and LANGFUSE_AVAILABLE
        )
        self.document_parser = DocumentParser()
        self.logger = WorkflowLogger()
        self.status_tracker = StatusTracker()

    # ----------------------------------------------------------------
    # STEPS - V3 Pattern 4: Verschachtelte Spans (automatisch)
    # ----------------------------------------------------------------

    @observe() 
    def step_parsing(self, uploaded_files):
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        return self.document_parser.parse_uploaded_files(uploaded_files)

    @observe() 
    def step_extraction(self, prompt_config, context, model_settings):
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        return self._api_call(prompt, context, True, model_settings, "gemini-extraction")

    @observe() 
    def step_draft(self, prompt_config, json_data, model_settings):
        self.logger.info("✍️ Phase 2: Entwurf...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False) if not isinstance(json_data, str) else json_data
        return self._api_call(prompt, json_str, False, model_settings, "gemini-draft")

    @observe() 
    def step_check(self, prompt_config, json_data, draft_text, model_settings):
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False) if not isinstance(json_data, str) else json_data
        check_input = f"DATEN:\n{json_str}\n\nENTWURF:\n{draft_text}"
        return self._api_call(prompt, check_input, False, model_settings, "gemini-check")

    # ----------------------------------------------------------------
    # CORE API CALL - V3 Pattern: Generation mit Context Manager
    # ----------------------------------------------------------------

    def _api_call(self, prompt, context, json_mode, model_settings, name):
        """
        Führt den API Call aus und trackt ihn manuell als Generation.
        """
        settings = model_settings or {"model": None, "temp": 0.1}
        model_name = settings.get("model", "gemini-1.5-flash")
        full_prompt = f"{prompt}\n\nINPUT:\n{context}"
        
        # Logik ohne Tracing (Fallback)
        if not (self.config.enable_langfuse and LANGFUSE_AVAILABLE):
            return self._execute_gemini(full_prompt, model_name, settings.get("temp"), json_mode)

        # Logik MIT V3 Tracing (Context Manager Pattern)
        langfuse = Langfuse()
        
        try:
            # KORREKTUR HIER: model_parameters statt modelParameters
            with langfuse.start_as_current_generation(
                name=name,
                model=model_name,
                model_parameters={"temperature": settings.get("temp"), "json_mode": json_mode},
                input=full_prompt
            ) as generation:
                
                # Der eigentliche Call
                response = self.config.generate_content(
                    full_prompt,
                    model_name=model_name,
                    temperature=settings.get("temp", 0.1),
                    json_mode=json_mode
                )
                
                text_response = response.text
                
                # Usage extrahieren
                usage_dict = None
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage_dict = {
                        "input": response.usage_metadata.prompt_token_count,
                        "output": response.usage_metadata.candidates_token_count,
                        "total": response.usage_metadata.total_token_count
                    }

                # V3: Generation updaten
                generation.update(
                    output=text_response,
                    usage=usage_dict
                )
                
                # Output verarbeiten
                if json_mode:
                    clean_text = text_response.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_text)
                return text_response

        except Exception as e:
            # Da wir im "try" des "with" blocks sind, müssen wir den Fehler fangen
            # Wenn Langfuse selbst crashed, wollen wir trotzdem weitermachen?
            # Besser: Fehler loggen und Fallback versuchen oder Fehler werfen
            print(f"Tracking Error: {e}")
            # Fallback Call ohne Tracking, falls es am Tracking lag
            return self._execute_gemini(full_prompt, model_name, settings.get("temp"), json_mode)

    def _execute_gemini(self, prompt, model, temp, json_mode):
        """Helper für Ausführung ohne Tracing"""
        response = self.config.generate_content(
            prompt, model_name=model, temperature=temp, json_mode=json_mode
        )
        text = response.text
        if json_mode:
            clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        return text

    def flush_stats(self):
        """V3 Pattern 5: Flush am Ende"""
        if self.config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                from langfuse import flush
                flush()
            except Exception:
                pass
