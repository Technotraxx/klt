"""
Workflow Modul - V3 Ready (Dezember 2025)
"""
import json
import os

# --- Imports & Safety Checks ---
try:
    # Der Standard-Weg in Langfuse V2/V3
    import langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    # Fallback, falls Library fehlt oder zu alt ist
    print("⚠️ WARNUNG: Langfuse SDK zu alt oder nicht installiert. Tracing deaktiviert.")
    LANGFUSE_AVAILABLE = False
    
    # Dummy-Decorator, damit der Code nicht crasht
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    # Dummy-Context
    class DummyContext:
        def update_current_observation(self, **kwargs): pass
        def update_current_trace(self, **kwargs): pass
    langfuse_context = DummyContext()

from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
    def __init__(self, config):
        self.config = config
        
        # Langfuse Client Initialisierung (V3 Style)
        # Wir initialisieren den Client nur für Prompt-Management explizit.
        # Das Tracing läuft über die Env-Vars und den Decorator.
        lf_client = None
        if config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                # In V3 instanziert man Langfuse() oft ohne Argumente, 
                # da es sich alles aus os.environ holt.
                lf_client = langfuse.Langfuse()
            except Exception as e:
                print(f"⚠️ Langfuse Init Fehler: {e}")
        
        self.prompt_manager = PromptManager(
            config.PROMPT_DIR, 
            langfuse_client=lf_client,
            use_langfuse=config.enable_langfuse and LANGFUSE_AVAILABLE
        )
        self.document_parser = DocumentParser()
        self.logger = WorkflowLogger()
        self.status_tracker = StatusTracker()

    # ----------------------------------------------------------------
    # STEPS (Als SPANS getrackt)
    # ----------------------------------------------------------------

    @observe() 
    def step_parsing(self, uploaded_files):
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        if LANGFUSE_AVAILABLE:
            langfuse_context.update_current_observation(
                metadata={"file_count": len(uploaded_files) if uploaded_files else 0}
            )
        return self.document_parser.parse_uploaded_files(uploaded_files)

    @observe() 
    def step_extraction(self, prompt_config, context, model_settings):
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        return self._api_call(prompt, context, json_mode=True, model_settings=model_settings, name="gemini-extraction")

    @observe() 
    def step_draft(self, prompt_config, json_data, model_settings):
        self.logger.info("✍️ Phase 2: Entwurf...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2) if not isinstance(json_data, str) else json_data
        return self._api_call(prompt, json_str, json_mode=False, model_settings=model_settings, name="gemini-draft")

    @observe() 
    def step_check(self, prompt_config, json_data, draft_text, model_settings):
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2) if not isinstance(json_data, str) else json_data
        check_input = f"DATEN:\n{json_str}\n\nENTWURF:\n{draft_text}"
        return self._api_call(prompt, check_input, json_mode=False, model_settings=model_settings, name="gemini-check")

    # ----------------------------------------------------------------
    # CORE API CALL (Als GENERATION getrackt)
    # ----------------------------------------------------------------

    @observe(as_type="generation")
    def _api_call(self, prompt, context, json_mode=False, model_settings=None, name="gemini-call"):
        try:
            settings = model_settings or {"model": None, "temp": 0.1}
            model_name = settings.get("model", "gemini-1.5-flash")
            
            full_prompt = f"{prompt}\n\nINPUT:\n{context}"
            
            # 1. Parameter an Langfuse (V3 Context Update)
            if LANGFUSE_AVAILABLE:
                langfuse_context.update_current_observation(
                    name=name,
                    model=model_name,
                    model_parameters={"temperature": settings.get("temp"), "json_mode": json_mode},
                    input=full_prompt
                )

            # 2. Der eigentliche Call
            response = self.config.generate_content(
                full_prompt,
                model_name=model_name,
                temperature=settings.get("temp", 0.1),
                json_mode=json_mode
            )
            
            text_response = response.text
            
            # 3. Token Usage & Output an Langfuse senden
            if LANGFUSE_AVAILABLE:
                usage = {}
                # Gemini liefert usage_metadata objekt
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = {
                        "input": response.usage_metadata.prompt_token_count,
                        "output": response.usage_metadata.candidates_token_count,
                        "total": response.usage_metadata.total_token_count
                    }
                
                langfuse_context.update_current_observation(
                    output=text_response,
                    usage=usage
                )
            
            if json_mode:
                clean_text = text_response.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            
            return text_response

        except Exception as e:
            self.logger.error(f"API Fehler: {e}")
            if LANGFUSE_AVAILABLE:
                langfuse_context.update_current_observation(level="ERROR", status_message=str(e))
            raise e
            
    def flush_stats(self):
        """Erzwingt das Senden der Traces"""
        if self.config.enable_langfuse and LANGFUSE_AVAILABLE:
            try:
                # In V3 ist flush() eine Methode auf der langfuse library selbst, 
                # oder auf dem globalen client
                langfuse.flush()
            except Exception:
                pass
