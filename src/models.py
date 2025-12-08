"""
models.py
Zentrale Verwaltung der verfügbaren KI-Modelle.
"""

# Deine gewünschte Liste
AVAILABLE_MODELS = [
    "gemini-2.0-flash-exp",      # Empfehlung: Aktuell bestes/schnellstes Modell
    "gemini-flash-latest",       # Alias
    "gemini-flash-lite-latest",  # Alias
    "gemini-3-pro-preview"       # Platzhalter/Zukunft
]

# Das Standard-Modell (wird genutzt, wenn nichts ausgewählt ist)
DEFAULT_MODEL = AVAILABLE_MODELS[1]
