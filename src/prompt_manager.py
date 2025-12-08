from pathlib import Path

class PromptManager:
    def __init__(self, prompt_dir, langfuse_client=None, use_langfuse=False):
        self.prompt_dir = Path(prompt_dir)
        self.langfuse = langfuse_client
        self.use_langfuse = use_langfuse and langfuse_client is not None
    
    def load_prompt_by_config(self, config: dict) -> str:
        name = config.get("name")
        source = config.get("source", "file")
        version = config.get("version", "production")
        
        if source == "langfuse" and self.use_langfuse:
            try:
                # Bei Langfuse "latest" entspricht keinem Label -> hole aktuelle Version
                label = version if version != "latest" else None
                prompt_obj = self.langfuse.get_prompt(name, label=label)
                return prompt_obj.prompt
            except Exception as e:
                print(f"Fallback zu File wegen Fehler: {e}")
        
        # File Source Fallback
        filename = name if name.endswith('.md') else f"{name}.md"
        path = self.prompt_dir / filename
        if path.exists():
            return path.read_text(encoding='utf-8')
        return f"Error: Prompt {filename} nicht gefunden."
