"""
Prompt Discovery Modul
"""

import os
import requests
from pathlib import Path
from typing import Dict, List

class PromptDiscovery:
    def __init__(self, prompt_dir: Path, langfuse_client=None):
        self.prompt_dir = prompt_dir
        self.langfuse = langfuse_client
    
    def discover_file_prompts(self) -> List[Dict]:
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
        prompts = []
        
        # Keys aus Env (via Config gesetzt)
        public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
        secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
        base_url = os.environ.get('LANGFUSE_HOST') or os.environ.get('LANGFUSE_BASE_URL')
        
        if not (public_key and secret_key and base_url):
            return prompts
            
        try:
            # URL bereinigen (Slash am Ende entfernen falls vorhanden)
            base_url = base_url.rstrip('/')
            url = f"{base_url}/api/public/v2/prompts"
            
            response = requests.get(
                url,
                auth=(public_key, secret_key),
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"⚠️ LangFuse API Warning: {response.status_code} - {response.text}")
                return prompts
            
            data = response.json()
            prompt_dict = {}
            
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
                
                if 'labels' in prompt_data:
                    prompt_dict[name]["versions"].update(prompt_data['labels'])
                if 'version' in prompt_data:
                    prompt_dict[name]["versions"].add(f"v{prompt_data['version']}")
            
            # Sortieren
            for p in prompt_dict.values():
                vers = list(p["versions"])
                priority = ["production", "staging", "latest"]
                # Prio Sortierung
                sorted_vers = [v for v in priority if v in vers]
                # Restliche alphabetisch/numerisch
                rest = sorted([v for v in vers if v not in priority], reverse=True)
                
                p["versions"] = sorted_vers + rest if sorted_vers or rest else ["latest"]
                prompts.append(p)
                
        except Exception as e:
            print(f"⚠️ LangFuse Discovery Error: {e}")
        
        return prompts
    
    def list_available_prompts(self) -> Dict[str, List[Dict]]:
        file_prompts = self.discover_file_prompts()
        langfuse_prompts = self.discover_langfuse_prompts()
        
        # Fallback falls Langfuse leer: Zumindest File Prompts anzeigen
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
                # Fallback: zu allen hinzufügen, damit sie auffindbar sind
                categorized["extraction"].append(prompt)
                categorized["draft"].append(prompt)
                categorized["control"].append(prompt)
        
        return categorized
    
    def get_prompt_versions(self, name: str, source: str) -> List[str]:
        if source == "file": return ["latest"]
        # In Echtzeit suchen (einfach aber ineffizient, für Demo ok)
        for p in self.discover_langfuse_prompts():
            if p["name"] == name: return p["versions"]
        return ["latest"]
