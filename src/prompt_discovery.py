"""
Prompt Discovery Modul
Findet alle verfügbaren Prompts aus .md Dateien und LangFuse
"""

from pathlib import Path
from typing import Dict, List


class PromptDiscovery:
    """Entdeckt und listet alle verfügbaren Prompts"""
    
    def __init__(self, prompt_dir: Path, langfuse_client=None):
        self.prompt_dir = Path(prompt_dir)
        self.langfuse = langfuse_client
    
    def discover_file_prompts(self) -> List[Dict]:
        """Scannt nach .md Prompt-Dateien"""
        prompts = []
        if not self.prompt_dir.exists():
            return prompts
        
        for md_file in self.prompt_dir.glob("*.md"):
            prompts.append({
                "name": md_file.name,
                "display_name": md_file.stem,
                "source": "file",
                "versions": ["latest"]
            })
        return prompts
    
    def discover_langfuse_prompts(self) -> List[Dict]:
        """Fragt LangFuse nach ALLEN verfügbaren Prompts via REST API"""
        prompts = []
        if not self.langfuse:
            print("⚠️ Discovery: LangFuse Client nicht verfügbar")
            return prompts
        
        try:
            import os
            import requests
            
            # Hole API Keys aus Environment (wurden in config.py gesetzt)
            public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
            secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
            base_url = os.environ.get('LANGFUSE_BASE_URL', 'https://langfuse.ki.rndtech.de')
            
            if not public_key or not secret_key:
                print("⚠️ Discovery: LangFuse Credentials nicht gefunden")
                return prompts
            
            # REST API Endpoint
            url = f"{base_url}/api/public/v2/prompts"
            
            # HTTP Basic Auth mit public:secret
            response = requests.get(
                url,
                auth=(public_key, secret_key),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"⚠️ Discovery: LangFuse API Error {response.status_code}")
                return prompts
            
            data = response.json()
            prompt_dict = {}
            
            # Gruppiere Prompts nach Namen und sammle Versionen
            for prompt_data in data.get('data', []):
                name = prompt_data.get('name')
                if not name:
                    continue
                
                if name not in prompt_dict:
                    prompt_dict[name] = {
                        "name": name,
                        "display_name": name,
                        "source": "langfuse",
                        "versions": set()
                    }
                
                # Sammle Labels/Versionen
                labels = prompt_data.get('labels', [])
                if labels:
                    prompt_dict[name]["versions"].update(labels)
                
                # Füge Version-Nummer hinzu
                version = prompt_data.get('version')
                if version:
                    prompt_dict[name]["versions"].add(f"v{version}")
            
            # Konvertiere zu Liste
            for prompt_info in prompt_dict.values():
                prompt_info["versions"] = sorted(list(prompt_info["versions"]))
                
                # Sortiere: production zuerst, dann staging, dann rest
                priority_order = ["production", "staging"]
                sorted_versions = []
                for prio in priority_order:
                    if prio in prompt_info["versions"]:
                        sorted_versions.append(prio)
                        prompt_info["versions"].remove(prio)
                sorted_versions.extend(sorted(prompt_info["versions"]))
                prompt_info["versions"] = sorted_versions
                
                prompts.append(prompt_info)
                print(f"✅ Discovery: {prompt_info['name']} (Versionen: {len(prompt_info['versions'])})")
            
            print(f"ℹ️  Discovery: {len(prompts)} LangFuse Prompts gefunden")
            
        except ImportError:
            print("⚠️ Discovery: 'requests' Modul nicht verfügbar - installiere mit: pip install requests")
        except Exception as e:
            print(f"⚠️ Fehler beim Laden von LangFuse Prompts via REST API: {e}")
            import traceback
            print(traceback.format_exc())
        
        return prompts
    
    def list_available_prompts(self) -> Dict[str, List[Dict]]:
        """
        Listet alle verfügbaren Prompts, kategorisiert nach Phase
        Returns: {"extraction": [...], "draft": [...], "control": [...]}
        """
        file_prompts = self.discover_file_prompts()
        langfuse_prompts = self.discover_langfuse_prompts()
        all_prompts = file_prompts + langfuse_prompts
        
        categorized = {"extraction": [], "draft": [], "control": []}
        
        for prompt in all_prompts:
            name_lower = prompt["name"].lower()
            
            if "extract" in name_lower:
                categorized["extraction"].append(prompt)
            elif "draft" in name_lower or "generat" in name_lower:
                categorized["draft"].append(prompt)
            elif "check" in name_lower or "fact" in name_lower or "control" in name_lower:
                categorized["control"].append(prompt)
            else:
                # Fallback: zu allen hinzufügen
                for cat in categorized:
                    categorized[cat].append(prompt)
        
        return categorized
    
    def format_for_dropdown(self, prompts: List[Dict]) -> List[str]:
        """Formatiert für Gradio Dropdown"""
        formatted = []
        for prompt in prompts:
            source_display = "File" if prompt["source"] == "file" else "LangFuse"
            display = f"{prompt['display_name']} ({source_display})"
            formatted.append(display)
        return formatted
    
    def parse_dropdown_selection(self, selection: str) -> tuple:
        """Parsed Dropdown-String zu (name, source)"""
        if not selection or "(" not in selection:
            return None, None
        
        name = selection.split("(")[0].strip()
        source_part = selection.split("(")[1].split(")")[0].strip().lower()
        source = "file" if source_part == "file" else "langfuse"
        return name, source
    
    def get_prompt_versions(self, name: str, source: str) -> List[str]:
        """Holt verfügbare Versionen für einen Prompt"""
        if source == "file":
            prompts = self.discover_file_prompts()
        else:
            prompts = self.discover_langfuse_prompts()
        
        for prompt in prompts:
            if prompt["name"] == name or prompt["display_name"] == name:
                return prompt.get("versions", ["-"])
        
        return ["-"]
