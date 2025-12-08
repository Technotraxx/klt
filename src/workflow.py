"""
Workflow Modul - Mit Deep Tracing für LangFuse
"""
import json
import langfuse
from langfuse.decorators import observe, langfuse_context

from document_parser import DocumentParser
from prompt_manager import PromptManager
from logger import WorkflowLogger, StatusTracker

class WorkflowProcessor:
    def __init__(self, config):
        self.config = config
        self.prompt_manager = PromptManager(
            config.PROMPT_DIR, 
            # Wir brauchen den Client hier nicht mehr zwingend explizit, 
            # da wir Decorators nutzen, aber für Prompts ist er gut.
            langfuse_client=langfuse.Langfuse() if config.enable_langfuse else None,
            use_langfuse=config.enable_langfuse
        )
        self.document_parser = DocumentParser()
        self.logger = WorkflowLogger()
        self.status_tracker = StatusTracker()

    # ----------------------------------------------------------------
    # STEPS (Als SPANS getrackt)
    # ----------------------------------------------------------------

    @observe() # Erstellt einen Span "step_parsing"
    def step_parsing(self, uploaded_files):
        self.logger.info(f"📎 Parse {len(uploaded_files) if uploaded_files else 0} Anhänge...")
        # Metadaten zum aktuellen Span hinzufügen
        langfuse_context.update_current_observation(
            metadata={"file_count": len(uploaded_files) if uploaded_files else 0}
        )
        return self.document_parser.parse_uploaded_files(uploaded_files)

    @observe() # Erstellt einen Span "step_extraction"
    def step_extraction(self, prompt_config, context, model_settings):
        self.logger.info("🤖 Phase 1: Daten-Extraktion...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        return self._api_call(prompt, context, json_mode=True, model_settings=model_settings, name="gemini-extraction")

    @observe() # Erstellt einen Span "step_draft"
    def step_draft(self, prompt_config, json_data, model_settings):
        self.logger.info("✍️ Phase 2: Entwurf...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2) if not isinstance(json_data, str) else json_data
        return self._api_call(prompt, json_str, json_mode=False, model_settings=model_settings, name="gemini-draft")

    @observe() # Erstellt einen Span "step_check"
    def step_check(self, prompt_config, json_data, draft_text, model_settings):
        self.logger.info("🔍 Phase 3: Faktenprüfung...")
        prompt = self.prompt_manager.load_prompt_by_config(prompt_config)
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2) if not isinstance(json_data, str) else json_data
        check_input = f"DATEN:\n{json_str}\n\nENTWURF:\n{draft_text}"
        return self._api_call(prompt, check_input, json_mode=False, model_settings=model_settings, name="gemini-check")

    # ----------------------------------------------------------------
    # CORE API CALL (Als GENERATION getrackt)
    # ----------------------------------------------------------------

    @observe(as_type="generation") # Wichtig: "generation" für Token-Tracking & Costs
    def _api_call(self, prompt, context, json_mode=False, model_settings=None, name="gemini-call"):
        try:
            settings = model_settings or {"model": None, "temp": 0.1}
            model_name = settings.get("model", "gemini-1.5-flash")
            
            # 1. Parameter an Langfuse übergeben (bevor der Call passiert)
            full_prompt = f"{prompt}\n\nINPUT:\n{context}"
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
            
            # 3. Antwort extrahieren
            text_response = response.text
            
            # 4. Token Usage aus Gemini Response extrahieren und an LangFuse senden
            # Gemini liefert usage_metadata
            usage = {}
            if response.usage_metadata:
                usage = {
                    "input": response.usage_metadata.prompt_token_count,
                    "output": response.usage_metadata.candidates_token_count,
                    "total": response.usage_metadata.total_token_count
                }
                # Update der Generation mit Output und Usage
                langfuse_context.update_current_observation(
                    output=text_response,
                    usage=usage
                )
            
            # JSON Handling
            if json_mode:
                clean_text = text_response.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            
            return text_response

        except Exception as e:
            self.logger.error(f"API Fehler: {e}")
            # Fehler explizit an LangFuse melden
            langfuse_context.update_current_observation(level="ERROR", status_message=str(e))
            raise e
            
    def flush_stats(self):
        """Erzwingt das Senden der Traces"""
        if self.config.enable_langfuse:
            langfuse.flush()
