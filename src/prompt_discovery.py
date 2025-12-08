"""
Prompt Discovery Modul
Findet alle verfügbaren Prompts aus .md Dateien und LangFuse API
"""

import os
import requests
from pathlib import Path
from typing import Dict, List

class PromptDiscovery:
    """Entdeckt und listet alle verfügbaren Prompts"""
    
    def __init__(self, prompt_dir: Path, langfuse_client=None):
        self.prompt_dir = prompt_dir
        self.langfuse = langfuse_client
    
    def discover_file_prompts(self) -> List[Dict]:
        """Scannt nach lokalen .md Prompt-Dateien"""
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
        
        # Keys aus Environment lesen (wurden in config.py gesetzt)
        public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
        secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
        # Versuche verschiedene Varianten für den Host
        base_url = os.environ.get('LANGFUSE_HOST') or os.environ.get('LANGFUSE_BASE_URL')
        
        if not (public_key and secret_key and base_url):
            return prompts
            
        try:
            # REST API Endpoint um Liste aller Prompts zu holen
            # (Das SDK hat oft keine einfache "List All" Funktion für Dropdowns)
            url = f"{base_url}/api/public/v2/prompts"
            
            response = requests.get(
                url,
                auth=(public_key, secret_key),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Discovery Error: {response.status_code}")
                return prompts
            
            data = response.json()
            prompt_dict = {}
            
            # Gruppiere Prompts nach Namen und sammle Versionen
            for prompt_data in data.get('data', []):
                name = prompt_data.get('name')
                if not name: continue
                
                if name not in prompt_dict:
                    prompt_dict[name] = {
                        "name": name,
                        "display_name": name,
                        "source": "langfuse",
                        "versions": set()
                    }
                
                # Labels als Versionen
                labels = prompt_data.get('labels', [])
                if labels:
                    prompt_dict[name]["versions"].update(labels)
                
                # Versionsnummer
                v_num = prompt_data.get('version')
                if v_num:
                    prompt_dict[name]["versions"].add(f"v{v_num}")
            
            # Formatieren
            for prompt_info in prompt_dict.values():
                # Sortierung: production, staging, dann Rest
                vers = list(prompt_info["versions"])
                priority = ["production", "staging", "latest"]
                sorted_vers = [v for v in priority if v in vers]
                sorted_vers += sorted([v for v in vers if v not in priority])
                
                prompt_info["versions"] = sorted_vers if sorted_vers else ["latest"]
                prompts.append(prompt_info)
                
        except Exception as e:
            print(f"LangFuse Discovery Failed: {e}")
        
        return prompts
    
    def list_available_prompts(self) -> Dict[str, List[Dict]]:
        """
        Listet alle verfügbaren Prompts, kategorisiert nach Phase
        """
        file_prompts = self.discover_file_prompts()
        langfuse_prompts = self.discover_langfuse_prompts()
        all_prompts = file_prompts + langfuse_prompts
        
        categorized = {"extraction": [], "draft": [], "control": []}
        
        for prompt in all_prompts:
            name_lower = prompt["name"].lower()
            
            # Simple Keyword Matching für Kategorien
            if "extract" in name_lower:
                categorized["extraction"].append(prompt)
            elif "draft" in name_lower or "generat" in name_lower:
                categorized["draft"].append(prompt)
            elif "check" in name_lower or "fact" in name_lower or "control" in name_lower:
                categorized["control"].append(prompt)
            else:
                # Unbekannte Prompts überall anzeigen
                for cat in categorized:
                    categorized[cat].append(prompt)
        
        return categorized
    
    def get_prompt_versions(self, name: str, source: str) -> List[str]:
        """Holt verfügbare Versionen für einen Prompt"""
        if source == "file":
            return ["latest"]
        
        # Um API Calls zu sparen, hier eine vereinfachte Logik:
        # In einer echten App würde man cachen. Hier rufen wir neu ab.
        prompts = self.discover_langfuse_prompts()
        for p in prompts:
            if p["name"] == name:
                return p["versions"]
        return ["latest"]
