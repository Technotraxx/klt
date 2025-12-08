"""
Streamlit Main Application - V2 mit Live-Updates
"""

import streamlit as st
import json
import pandas as pd
from config import Config
from workflow import WorkflowProcessor
from prompt_discovery import PromptDiscovery

# Page Config
st.set_page_config(
    page_title="AI Editorial Workflow",
    page_icon="📰",
    layout="wide"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .reportview-container { margin-top: -2em; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; }
    /* Schöne JSON Tabelle */
    .json-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9em; }
    .json-table td, .json-table th { border: 1px solid #ddd; padding: 8px; }
    .json-table tr:nth-child(even){background-color: #f2f2f2;}
    .json-table th { padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #ff4b4b; color: white; }
    .key-col { font-weight: bold; width: 30%; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- Initialisierung (Cached) ---
@st.cache_resource
def get_core_components():
    config = Config()
    processor = WorkflowProcessor(config)
    discovery = PromptDiscovery(config.PROMPT_DIR, config.langfuse)
    return config, processor, discovery

config, processor, discovery = get_core_components()

# --- Helper: JSON to HTML ---
def render_json_html(data):
    """Konvertiert flaches JSON in eine schöne HTML Tabelle"""
    if not isinstance(data, dict):
        return f"<pre>{json.dumps(data, indent=2)}</pre>"
    
    html = '<table class="json-table"><thead><tr><th>Feld</th><th>Wert</th></tr></thead><tbody>'
    
    def flatten(x, prefix=''):
        items = []
        if isinstance(x, dict):
            for k, v in x.items():
                new_key = f"{prefix}.{k}" if prefix else k
                items.extend(flatten(v, new_key))
        elif isinstance(x, list):
             # Listen schön formatieren
             list_html = "<ul>" + "".join([f"<li>{str(i)}</li>" for i in x]) + "</ul>"
             items.append((prefix, list_html))
        else:
            items.append((prefix, str(x)))
        return items

    # Rekursiv oder einfach Top-Level iteration?
    # Für Übersichtlichkeit iterieren wir hier nur Top-Level und 2nd Level
    for key, value in data.items():
        if isinstance(value, dict):
            html += f'<tr><td class="key-col" colspan="2" style="background-color:#e0e0e0;"><strong>{key.upper()}</strong></td></tr>'
            for sub_k, sub_v in value.items():
                display_val = sub_v
                if isinstance(sub_v, list):
                    display_val = ", ".join([str(i) for i in sub_v])
                html += f'<tr><td class="key-col" style="padding-left:20px;">{sub_k}</td><td>{display_val}</td></tr>'
        elif isinstance(value, list):
            list_items = "".join([f"<li>{v}</li>" for v in value])
            html += f'<tr><td class="key-col">{key}</td><td><ul>{list_items}</ul></td></tr>'
        else:
            html += f'<tr><td class="key-col">{key}</td><td>{value}</td></tr>'
            
    html += '</tbody></table>'
    return html

# --- Helper: Defaults finden ---
def get_index_for_default(options, search_string):
    """Sucht den Index einer Option, die den search_string enthält"""
    for i, option in enumerate(options):
        if search_string.lower() in option.lower():
            return i
    return 0

# --- Helper: Parse Selection ---
def parse_selection(selection):
    if not selection or "(" not in selection:
        return None, "file"
    name = selection.split("(")[0].strip()
    source = "file" if "(file)" in selection.lower() else "langfuse"
    return name, source

def get_versions(selection):
    name, source = parse_selection(selection)
    if not name: return ["latest"]
    return discovery.get_prompt_versions(name, source)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("⚙️ Konfiguration")
    
    # 1. API Keys
    if not config.api_key:
        st.warning("⚠️ API Key fehlt")
        config.api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    # 2. Modell Einstellungen (NEU!)
    st.subheader("🤖 Modell Settings")
    model_choice = st.selectbox(
        "Modell", 
        ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0
    )
    temp_val = st.slider("Kreativität (Temp)", 0.0, 1.0, 0.1, 0.1)
    
    model_settings = {"model": model_choice, "temp": temp_val}
    
    st.divider()
    
    # 3. Prompt Auswahl mit DEFAULTS (NEU!)
    st.subheader("Prompts")
    
    # Optionen laden
    opts_extract = [f"{p['display_name']} ({p['source']})" for p in discovery.list_available_prompts()["extraction"]]
    opts_draft = [f"{p['display_name']} ({p['source']})" for p in discovery.list_available_prompts()["draft"]]
    opts_check = [f"{p['display_name']} ({p['source']})" for p in discovery.list_available_prompts()["control"]]
    
    # Extraktion (Default: 'extract')
    idx_e = get_index_for_default(opts_extract, "extract")
    p1_sel = st.selectbox("1. Extraktion", opts_extract, index=idx_e)
    p1_ver = st.selectbox("Version", get_versions(p1_sel), key="v1")
    
    # Draft (Default: 'draft')
    idx_d = get_index_for_default(opts_draft, "draft")
    p2_sel = st.selectbox("2. Entwurf", opts_draft, index=idx_d)
    p2_ver = st.selectbox("Version", get_versions(p2_sel), key="v2")
    
    # Check (Default: 'check' oder 'fact')
    idx_c = get_index_for_default(opts_check, "fact")
    p3_sel = st.selectbox("3. Kontrolle", opts_check, index=idx_c)
    p3_ver = st.selectbox("Version", get_versions(p3_sel), key="v3")


# =========================================================
# MAIN CONTENT
# =========================================================
st.title("📰 AI Editorial Assistant")

# Session State für Ergebnisse
if "workflow_data" not in st.session_state:
    st.session_state.workflow_data = {}

# Input Area
col1, col2 = st.columns([1, 1])
with col1:
    meta_input = st.text_area("Metadaten", height=100, placeholder="Absender, Datum...")
    text_input = st.text_area("Nachrichtentext", height=300, placeholder="Inhalt...")
with col2:
    uploaded_files = st.file_uploader("Anhänge", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    st.info(f"Modell: {model_choice} | Temp: {temp_val}")
    start_btn = st.button("🚀 Analyse starten", type="primary", use_container_width=True)

# Output Area (Platzhalter)
st.divider()
status_container = st.status("Warte auf Start...", expanded=False)
tab1, tab2, tab3 = st.tabs(["📊 Daten (Live)", "✍️ Entwurf", "✅ Check"])

# =========================================================
# WORKFLOW LOGIK (Schrittweise)
# =========================================================
if start_btn:
    # Reset
    st.session_state.workflow_data = {}
    processor.logger.clear()
    
    status_container.update(label="🚀 Workflow gestartet...", state="running", expanded=True)
    
    try:
        # Configs vorbereiten
        n1, s1 = parse_selection(p1_sel)
        n2, s2 = parse_selection(p2_sel)
        n3, s3 = parse_selection(p3_sel)
        
        cfg_extract = {"name": n1, "source": s1, "version": p1_ver}
        cfg_draft = {"name": n2, "source": s2, "version": p2_ver}
        cfg_check = {"name": n3, "source": s3, "version": p3_ver}

        # --- SCHRITT 1: Parsing ---
        status_container.write("📎 Parse Dokumente...")
        file_content = processor.step_parsing(uploaded_files)
        full_context = f"META: {meta_input}\nTEXT: {text_input}\nFILES: {file_content}"
        
        # --- SCHRITT 2: Extraktion ---
        status_container.write("🤖 Extrahiere Daten (LLM)...")
        json_data = processor.step_extraction(cfg_extract, full_context, model_settings)
        st.session_state.workflow_data["json"] = json_data
        
        # LIVE UPDATE TAB 1
        with tab1:
            st.success("Extraktion fertig!")
            # HTML Render
            html_table = render_json_html(json_data)
            st.markdown(html_table, unsafe_allow_html=True)
            # Raw JSON Expander
            with st.expander("Rohes JSON ansehen"):
                st.json(json_data)

        # --- SCHRITT 3: Draft ---
        status_container.write("✍️ Schreibe Entwurf...")
        draft_text = processor.step_draft(cfg_draft, json_data, model_settings)
        st.session_state.workflow_data["draft"] = draft_text
        
        # LIVE UPDATE TAB 2
        with tab2:
            st.markdown(draft_text)
            st.download_button("Download .txt", draft_text, "entwurf.txt")

        # --- SCHRITT 4: Check ---
        status_container.write("🔍 Prüfe Fakten...")
        check_text = processor.step_check(cfg_check, json_data, draft_text, model_settings)
        st.session_state.workflow_data["check"] = check_text
        
        # LIVE UPDATE TAB 3
        with tab3:
            st.markdown(check_text)

        status_container.update(label="✅ Fertig!", state="complete", expanded=False)

    except Exception as e:
        status_container.update(label="❌ Fehler aufgetreten", state="error")
        st.error(f"Fehler: {str(e)}")

# Anzeige persistenter Daten (falls man Tabs wechselt nach dem Run)
elif st.session_state.workflow_data:
    data = st.session_state.workflow_data
    
    with tab1:
        if "json" in data:
            st.markdown(render_json_html(data["json"]), unsafe_allow_html=True)
            with st.expander("Rohes JSON"):
                st.json(data["json"])
                
    with tab2:
        if "draft" in data:
            st.markdown(data["draft"])
            st.download_button("Download .txt", data["draft"], "entwurf.txt")
            
    with tab3:
        if "check" in data:
            st.markdown(data["check"])
