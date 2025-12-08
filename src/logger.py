"""
Logging Modul
Speichert Logs in einer Liste für die spätere Anzeige in der UI
"""

from datetime import datetime
from typing import List

class WorkflowLogger:
    """Logger für Workflow-Status und Debug-Infos"""
    
    def __init__(self):
        self.logs = []
    
    def log(self, message: str, level: str = "INFO"):
        """
        Loggt eine Nachricht mit Timestamp
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        # Print ist nützlich für Server-Logs (Streamlit Console)
        print(log_entry)
        self.logs.append(log_entry)
        return log_entry
    
    def info(self, message: str):
        return self.log(message, "INFO")
    
    def warning(self, message: str):
        return self.log(message, "WARNING")
    
    def error(self, message: str):
        return self.log(message, "ERROR")
    
    def get_logs(self) -> List[str]:
        """Gibt alle Logs zurück"""
        return self.logs
    
    def clear(self):
        """Löscht alle Logs"""
        self.logs = []


class StatusTracker:
    """Tracked den Status der einzelnen Workflow-Schritte"""
    
    def __init__(self):
        self.steps = {}
    
    def update_step(self, step: str, status: str, details: dict = None):
        self.steps[step] = {"status": status, "details": details}
