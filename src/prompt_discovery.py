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
        pk = os.environ.get('LANGFUSE_PUBLIC_KEY')
        sk = os.environ.get('LANGFUSE_SECRET_KEY')
        base_url = os.environ.get('LANGFUSE_HOST')
        
        if not (pk and sk and base_url):
            return prompts
            
        try:
            base_url = base_url.rstrip('/')
            url = f"{base_url}/api/public/v2/prompts"
            response = requests.get(url, auth=(pk, sk), headers={'Content-Type': 'application/json'}, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                prompt_dict = {}
                for prompt_data in data.get('data', []):
                    name = prompt_data.get('name')
                    if not name: continue
                    if name not in prompt_dict:
                        prompt_dict[name] = {"name": name, "display_name": name, "source": "langfuse", "versions": set()}
                    if 'labels' in prompt_data: prompt_dict[name]["versions"].update(prompt_data['labels'])
                    if 'version' in prompt_data: prompt_dict[name]["versions"].add(f"v{prompt_data['version']}")
                
                for p in prompt_dict.values():
                    vers = list(p["versions"])
                    p["versions"] = sorted(vers, reverse=True) if vers else ["latest"]
                    prompts.append(p)
        except Exception as e:
            print(f"LangFuse Discovery Error: {e}")
        
        return prompts
    
    def list_available_prompts(self) -> Dict[str, List[Dict]]:
        all_prompts = self.discover_file_prompts() + self.discover_langfuse_prompts()
        
        # Neue Kategorie: write
        categorized = {"extraction": [], "draft": [], "write": [], "control": []}
        
        for prompt in all_prompts:
            n = prompt["name"].lower()
            
            if "extract" in n:
                categorized["extraction"].append(prompt)
            # Wichtig: Unterscheidung Draft (Konzept) vs Write (Artikel)
            elif "write" in n or "artikel" in n or "article" in n:
                categorized["write"].append(prompt)
            elif "draft" in n or "concept" in n or "entwurf" in n:
                categorized["draft"].append(prompt)
            elif "check" in n or "fact" in n or "control" in n:
                categorized["control"].append(prompt)
            else:
                # Fallback
                categorized["draft"].append(prompt)
        
        return categorized
    
    def get_prompt_versions(self, name: str, source: str) -> List[str]:
        if source == "file": return ["latest"]
        for p in self.discover_langfuse_prompts():
            if p["name"] == name: return p["versions"]
        return ["latest"]
