"""
Logging und Status-Tracking Modul
Sorgt für Transparenz im Workflow
"""

from datetime import datetime
from typing import List, Callable


class WorkflowLogger:
    """Logger für Workflow-Status und Debug-Infos"""
    
    def __init__(self):
        self.logs = []
        self.callbacks = []
    
    def log(self, message: str, level: str = "INFO"):
        """
        Loggt eine Nachricht mit Timestamp
        
        Args:
            message: Die Log-Nachricht
            level: Log-Level (INFO, DEBUG, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        
        # Callbacks für Live-Updates aufrufen
        for callback in self.callbacks:
            callback(log_entry)
        
        return log_entry
    
    def info(self, message: str):
        """Info-Level Log"""
        return self.log(message, "INFO")
    
    def debug(self, message: str):
        """Debug-Level Log"""
        return self.log(message, "DEBUG")
    
    def warning(self, message: str):
        """Warning-Level Log"""
        return self.log(message, "WARNING")
    
    def error(self, message: str):
        """Error-Level Log"""
        return self.log(message, "ERROR")
    
    def add_callback(self, callback: Callable):
        """Fügt einen Callback für Live-Updates hinzu"""
        self.callbacks.append(callback)
    
    def get_logs(self) -> List[str]:
        """Gibt alle Logs zurück"""
        return self.logs
    
    def get_logs_as_text(self) -> str:
        """Gibt alle Logs als Text zurück"""
        return "\n".join(self.logs)
    
    def clear(self):
        """Löscht alle Logs"""
        self.logs = []


class StatusTracker:
    """Tracked den Status der einzelnen Workflow-Schritte"""
    
    def __init__(self):
        self.steps = {
            "init": {"status": "pending", "details": None},
            "prompt_load": {"status": "pending", "details": None},
            "file_parse": {"status": "pending", "details": None},
            "extraction": {"status": "pending", "details": None},
            "draft": {"status": "pending", "details": None},
            "fact_check": {"status": "pending", "details": None},
            "save": {"status": "pending", "details": None}
        }
    
    def update_step(self, step: str, status: str, details: dict = None):
        """
        Updated einen Workflow-Schritt
        
        Args:
            step: Name des Schritts
            status: Status (pending, running, success, error)
            details: Zusätzliche Details
        """
        if step in self.steps:
            self.steps[step]["status"] = status
            self.steps[step]["details"] = details
    
    def get_status(self) -> dict:
        """Gibt den kompletten Status zurück"""
        return self.steps
    
    def get_progress_text(self) -> str:
        """Gibt Status als lesbaren Text zurück"""
        emoji_map = {
            "pending": "⏸️",
            "running": "🔄",
            "success": "✅",
            "error": "❌"
        }
        
        lines = []
        for step, data in self.steps.items():
            emoji = emoji_map.get(data["status"], "❓")
            lines.append(f"{emoji} {step.upper()}")
            if data["details"]:
                lines.append(f"   → {data['details']}")
        
        return "\n".join(lines)
