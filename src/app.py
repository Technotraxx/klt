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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #ff4b4b; }
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
def get_prompt_options(category):
    all_prompts = discovery.list_available_prompts()
    prompts = all_prompts.get(category, [])
    return [f"{p['display_name']} ({p['source']})" for p in prompts]

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

# --- Sidebar: Configuration ---
with st.sidebar:
    st.header("⚙️ Konfiguration")
    
    # API Keys (falls nicht in Secrets)
    if not config.api_key:
        st.warning("⚠️ Kein API Key gefunden")
        user_key = st.text_input("Google Gemini API Key", type="password")
        if user_key:
            config.api_key = user_key
            config.client = config.generate_content # Re-Init logic needed ideally
            st.rerun()
    
    st.divider()
    
    st.subheader("Prompts wählen")
    
    # Extraction Prompt
    p1_sel = st.selectbox("1. Extraktion", get_prompt_options("extraction"), index=0)
    p1_ver = st.selectbox("Version", get_versions(p1_sel), key="v1")
    
    # Draft Prompt
    p2_sel = st.selectbox("2. Entwurf", get_prompt_options("draft"), index=0)
    p2_ver = st.selectbox("Version", get_versions(p2_sel), key="v2")
    
    # Check Prompt
    p3_sel = st.selectbox("3. Kontrolle", get_prompt_options("control"), index=0)
    p3_ver = st.selectbox("Version", get_versions(p3_sel), key="v3")
    
    # LangFuse Status
    st.divider()
    if config.enable_langfuse:
        st.success(f"☁️ LangFuse Verbunden")
    else:
        st.info("☁️ LangFuse inaktiv")

# --- Main Content ---
st.title("📰 AI Editorial Assistant")
st.markdown("Automatisierte Verarbeitung von Pressemitteilungen und Leserbriefen.")

# Input Area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Input")
    meta_input = st.text_area("Metadaten (Absender, Datum)", height=100, placeholder="Max Mustermann, 12.10.2023...")
    text_input = st.text_area("Nachrichtentext", height=300, placeholder="Hier Email-Text einfügen...")

with col2:
    st.subheader("📎 Anhänge")
    uploaded_files = st.file_uploader("PDF, DOCX oder TXT", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    
    st.info("💡 Die Dateien werden nur temporär im Speicher verarbeitet.")
    
    # Start Button
    st.write("")
    st.write("")
    start_btn = st.button("🚀 Analyse starten", type="primary", use_container_width=True)

# --- Processing & Output ---
if "result" not in st.session_state:
    st.session_state.result = None

if start_btn:
    if not config.api_key:
        st.error("Bitte API Key konfigurieren!")
    elif not text_input and not uploaded_files:
        st.warning("Bitte Text eingeben oder Datei hochladen.")
    else:
        with st.spinner("Arbeite... (Dies kann ca. 30 Sekunden dauern)"):
            try:
                # Prompt Configs bauen
                n1, s1 = parse_selection(p1_sel)
                n2, s2 = parse_selection(p2_sel)
                n3, s3 = parse_selection(p3_sel)
                
                res = processor.process_workflow(
                    email_text=text_input,
                    sender_meta=meta_input,
                    uploaded_files=uploaded_files,
                    extraction_config={"name": n1, "source": s1, "version": p1_ver},
                    draft_config={"name": n2, "source": s2, "version": p2_ver},
                    control_config={"name": n3, "source": s3, "version": p3_ver}
                )
                st.session_state.result = res
                st.success("Verarbeitung abgeschlossen!")
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {str(e)}")

# Result Display
if st.session_state.result:
    res = st.session_state.result
    
    st.divider()
    tab1, tab2, tab3, tab4 = st.tabs(["📊 JSON Daten", "✍️ Entwurf", "✅ Fakten-Check", "📟 Logs"])
    
    with tab1:
        st.download_button("JSON Herunterladen", res["json"], "data.json", "application/json")
        st.code(res["json"], language="json")
        
    with tab2:
        st.download_button("Entwurf Herunterladen", res["draft"], "entwurf.txt", "text/plain")
        st.markdown(res["draft"])
        
    with tab3:
        st.markdown(res["check"])
        
    with tab4:
        for log in res["logs"]:
            st.text(log)
