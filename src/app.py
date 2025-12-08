"""
Streamlit Main Application
"""

import streamlit as st
import json
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
    .json-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9em; }
    .json-table td, .json-table th { border: 1px solid #ddd; padding: 8px; }
    .json-table tr:nth-child(even){background-color: #f2f2f2;}
    .json-table th { padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #ff4b4b; color: white; }
    .key-col { font-weight: bold; width: 30%; color: #333; }
    .sub-header { background-color: #e0e0e0; font-weight: bold; }
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

# --- Helper Functions ---
def try_parse_json(content):
    """Versucht String-Inhalt (evtl. mit Markdown) in Dict zu wandeln"""
    if isinstance(content, dict):
        return content
    try:
        # Markdown Code-Blöcke entfernen
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return None

def render_json_html(data):
    """Konvertiert flaches JSON in eine schöne HTML Tabelle (für Entwurf)"""
    if not isinstance(data, dict):
        return f"<pre>{data}</pre>"
    
    html = '<table class="json-table"><thead><tr><th>Element</th><th>Inhalt</th></tr></thead><tbody>'
    
    for key, value in data.items():
        # Hauptkategorien (z.B. "headlines", "teaser")
        if isinstance(value, dict):
            html += f'<tr><td class="sub-header" colspan="2">{key.upper()}</td></tr>'
            for sub_k, sub_v in value.items():
                display_val = sub_v
                if isinstance(sub_v, list):
                    display_val = ", ".join([str(i) for i in sub_v])
                html += f'<tr><td class="key-col" style="padding-left:20px;">{sub_k}</td><td>{display_val}</td></tr>'
        
        # Listen (z.B. Keywords)
        elif isinstance(value, list):
            list_items = "".join([f"<li>{v}</li>" for v in value])
            html += f'<tr><td class="key-col">{key.upper()}</td><td><ul>{list_items}</ul></td></tr>'
        
        # Einfache Werte
        else:
            html += f'<tr><td class="key-col">{key.upper()}</td><td>{value}</td></tr>'
            
    html += '</tbody></table>'
    return html

def get_index_for_default(options, search_strings):
    if not isinstance(search_strings, list):
        search_strings = [search_strings]
    for search in search_strings:
        for i, option in enumerate(options):
            opt_name = option.split("(")[0].strip()
            if search.lower() == opt_name.lower():
                return i
            if search.lower() in option.lower():
                return i
    return 0

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
    
    if not config.api_key:
        st.warning("⚠️ API Key fehlt")
        config.api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    st.subheader("🤖 Modell Settings")
    available_models = [
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3-pro-preview"   
    ]
    model_choice = st.selectbox("Modell", available_models, index=0)
    temp_val = st.slider("Kreativität (Temp)", 0.0, 1.0, 0.2, 0.1)
    model_settings = {"model": model_choice, "temp": temp_val}
    
    st.divider()
    
    st.subheader("Prompts")
    available = discovery.list_available_prompts()
    
    opts_extract = [f"{p['display_name']} ({p['source']})" for p in available["extraction"]]
    opts_draft = [f"{p['display_name']} ({p['source']})" for p in available["draft"]]
    opts_check = [f"{p['display_name']} ({p['source']})" for p in available["control"]]
    
    idx_e = get_index_for_default(opts_extract, ["email-extract", "extract"])
    p1_sel = st.selectbox("1. Extraktion", opts_extract, index=idx_e)
    p1_ver = st.selectbox("Version", get_versions(p1_sel), key="v1")
    
    idx_d = get_index_for_default(opts_draft, ["email-draft", "draft"])
    p2_sel = st.selectbox("2. Entwurf", opts_draft, index=idx_d)
    p2_ver = st.selectbox("Version", get_versions(p2_sel), key="v2")
    
    idx_c = get_index_for_default(opts_check, ["fact-check", "check"])
    p3_sel = st.selectbox("3. Kontrolle", opts_check, index=idx_c)
    p3_ver = st.selectbox("Version", get_versions(p3_sel), key="v3")


# =========================================================
# MAIN CONTENT
# =========================================================
st.title("📰 AI Editorial Assistant")

if "workflow_data" not in st.session_state:
    st.session_state.workflow_data = {}

col1, col2 = st.columns([1, 1])
with col1:
    meta_input = st.text_area("Metadaten", height=100, placeholder="Absender, Datum...")
    text_input = st.text_area("Nachrichtentext", height=300, placeholder="Inhalt...")
with col2:
    uploaded_files = st.file_uploader("Anhänge", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    st.info(f"Modell: {model_choice}")
    start_btn = st.button("🚀 Analyse starten", type="primary", use_container_width=True)

st.divider()
status_container = st.status("Bereit...", expanded=False)
tab1, tab2, tab3 = st.tabs(["📊 Extraktion (JSON)", "✍️ Entwurf (Tabelle)", "✅ Check (Text)"])

if start_btn:
    st.session_state.workflow_data = {}
    processor.logger.clear()
    status_container.update(label="🚀 Workflow läuft...", state="running", expanded=True)
    
    try:
        # Configs
        n1, s1 = parse_selection(p1_sel)
        n2, s2 = parse_selection(p2_sel)
        n3, s3 = parse_selection(p3_sel)
        
        # 1. Parse
        status_container.write("📎 Parse Dokumente...")
        file_content = processor.step_parsing(uploaded_files)
        full_context = f"META: {meta_input}\nTEXT: {text_input}\nFILES: {file_content}"
        
        # 2. Extract
        status_container.write(f"🤖 Extraktion mit {n1}...")
        json_data = processor.step_extraction(
            {"name": n1, "source": s1, "version": p1_ver}, 
            full_context, model_settings
        )
        st.session_state.workflow_data["json"] = json_data
        
        # 3. Draft
        status_container.write(f"✍️ Entwurf mit {n2}...")
        draft_text = processor.step_draft(
            {"name": n2, "source": s2, "version": p2_ver}, 
            json_data, model_settings
        )
        st.session_state.workflow_data["draft"] = draft_text
        
        # 4. Check
        status_container.write(f"🔍 Check mit {n3}...")
        check_text = processor.step_check(
            {"name": n3, "source": s3, "version": p3_ver}, 
            json_data, draft_text, model_settings
        )
        st.session_state.workflow_data["check"] = check_text

        status_container.update(label="✅ Fertig!", state="complete", expanded=False)

    except Exception as e:
        status_container.update(label="❌ Fehler", state="error")
        st.error(f"Fehler: {str(e)}")

    finally:
        processor.flush_stats()

# --- ANZEIGE & DOWNLOAD LOGIK ---
if st.session_state.workflow_data:
    d = st.session_state.workflow_data
    
    # TAB 1: Extraktion (Raw JSON Viewer)
    with tab1:
        if "json" in d:
            st.json(d["json"], expanded=True)
        else:
            st.info("Keine Daten vorhanden.")

    # TAB 2: Entwurf (Tabelle oder Text)
    with tab2:
        if "draft" in d:
            # Versuch, den Draft als JSON zu interpretieren für die Tabelle
            draft_json = try_parse_json(d["draft"])
            if draft_json:
                st.markdown(render_json_html(draft_json), unsafe_allow_html=True)
            else:
                # Fallback, falls der Prompt Text statt JSON geliefert hat
                st.markdown(d["draft"])
        else:
            st.info("Kein Entwurf vorhanden.")

    # TAB 3: Check (Markdown)
    with tab3:
        if "check" in d:
            st.markdown(d["check"])
        else:
            st.info("Kein Check vorhanden.")

    # --- DOWNLOADS ---
    st.divider()
    with st.expander("💾 Ergebnisse herunterladen", expanded=True):
        dl_col1, dl_col2, dl_col3 = st.columns(3)
        
        # 1. JSON Download
        if "json" in d:
            json_str = json.dumps(d["json"], indent=2, ensure_ascii=False)
            dl_col1.download_button(
                label="📥 1. Extraktion (JSON)",
                data=json_str,
                file_name="extraction.json",
                mime="application/json"
            )
            
        # 2. Draft Download
        if "draft" in d:
            draft_content = d["draft"]
            # Falls Draft JSON-Objekt ist, stringifyen
            if isinstance(draft_content, dict):
                 draft_content = json.dumps(draft_content, indent=2, ensure_ascii=False)
            
            dl_col2.download_button(
                label="📥 2. Entwurf (Txt/JSON)",
                data=draft_content,
                file_name="draft_proposal.txt",
                mime="text/plain"
            )
            
        # 3. Check Download
        if "check" in d:
            dl_col3.download_button(
                label="📥 3. Fakten-Check (MD)",
                data=d["check"],
                file_name="fact_check.md",
                mime="text/markdown"
            )
