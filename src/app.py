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
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 50px; }
    
    /* JSON Tables */
    .json-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.95em; }
    .json-table td, .json-table th { border: 1px solid #ddd; padding: 10px; vertical-align: top; }
    .json-table tr:nth-child(even){background-color: #f9f9f9;}
    .json-table th { padding-top: 12px; padding-bottom: 12px; text-align: left; background-color: #ff4b4b; color: white; }
    .key-col { font-weight: bold; width: 25%; color: #333; background-color: #f0f2f6; }
    .sub-header { background-color: #31333F; color: white; font-weight: bold; padding: 8px; text-align: center; }

    /* Article Preview Cards */
    .meta-box {
        background-color: #eef2f6;
        padding: 12px;
        border-radius: 6px;
        font-size: 0.9em;
        margin-bottom: 20px;
        border-left: 4px solid #ff4b4b;
        color: #444;
    }
    
    .print-font { 
        font-family: "Georgia", "Times New Roman", serif; 
        padding: 20px;
        background-color: white;
        border: 1px solid #eee;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    .online-card {
        padding: 20px;
        background-color: white;
        border: 1px solid #eee;
        border-top: 4px solid #4285F4;
        border-radius: 4px;
    }
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

# --- WICHTIG: Session State Initialisierung ---
# Dies muss VOR jeglicher Verwendung von st.session_state.workflow_data stehen!
if "workflow_data" not in st.session_state:
    st.session_state.workflow_data = {}

# --- Helper Functions ---
def try_parse_json(content):
    if isinstance(content, dict): return content
    try:
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except: return None

def render_json_html(data):
    if not isinstance(data, dict): return f"<div>{data}</div>"
    html = '<table class="json-table"><thead><tr><th>Feld</th><th>Inhalt</th></tr></thead><tbody>'
    for key, value in data.items():
        if isinstance(value, dict):
            html += f'<tr><td class="sub-header" colspan="2">{key.upper()}</td></tr>'
            for sub_k, sub_v in value.items():
                display_val = sub_v
                if isinstance(sub_v, list): display_val = ", ".join([str(i) for i in sub_v])
                html += f'<tr><td class="key-col" style="padding-left:20px;">{sub_k}</td><td>{display_val}</td></tr>'
        elif isinstance(value, list):
            list_items = "".join([f"<li>{v}</li>" for v in value])
            html += f'<tr><td class="key-col">{key.upper()}</td><td><ul>{list_items}</ul></td></tr>'
        else:
            html += f'<tr><td class="key-col">{key.upper()}</td><td>{value}</td></tr>'
    html += '</tbody></table>'
    return html

def render_article_dashboard(article_json):
    """Zeigt Online und Print Version nebeneinander an"""
    
    # Safely get nested dicts
    online = article_json.get("online", {})
    print_ver = article_json.get("print", {})
    meta = article_json.get("confidence", {})
    
    # Top Metriken
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Fakten-Check", f"{meta.get('fakten_vollstaendig', '?')}/3")
        c2.metric("Stil-Score", f"{meta.get('stil_konform', '?')}/3")
        c3.metric("Länge", f"{meta.get('laenge_eingehalten', '?')}/3")

    col_online, col_print = st.columns(2)
    
    # --- ONLINE SPALTE ---
    with col_online:
        st.subheader("🌐 Online")
        with st.container():
            st.markdown('<div class="online-card">', unsafe_allow_html=True)
            
            # SEO Box
            if "meta_description" in online:
                st.markdown(f"""
                <div class="meta-box">
                    <strong>🔍 SEO Description ({len(str(online.get('meta_description','')))} Zeichen):</strong><br>
                    {online.get('meta_description')}
                </div>
                """, unsafe_allow_html=True)
            
            # Content
            st.markdown(f"## {online.get('ueberschrift', 'Keine Überschrift')}")
            st.markdown(f"**{online.get('teaser', '')}**")
            st.markdown("---")
            # Body rendern
            st.markdown(online.get('body', ''))
            
            st.caption(f"📏 Zeichen (Body): {online.get('zeichen_body', 0)}")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PRINT SPALTE ---
    with col_print:
        st.subheader("📰 Print")
        with st.container():
            # Print Styling Simulation
            st.markdown(f"""
            <div class="print-font">
                <h4 style="margin-bottom:5px; color:#666; text-transform:uppercase; font-size:0.8em;">{print_ver.get('unterzeile', '')}</h4>
                <h2 style="margin-top:0; font-size: 1.8em; line-height:1.1;">{print_ver.get('ueberschrift', '')}</h2>
                <hr style="border-top: 2px solid black; margin: 15px 0;">
                <p style="text-align: justify; line-height: 1.4;">{str(print_ver.get('text', '')).replace(chr(10), '<br>')}</p>
            </div>
            """, unsafe_allow_html=True)
             
            st.caption(f"📏 Zeichen (Text): {print_ver.get('zeichen_text', 0)}")
            
    # --- FOOTER BEREICH ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 💬 Zitate")
        zitate = article_json.get("verwendete_zitate", [])
        if zitate:
            for q in zitate:
                st.info(f"„{q.get('text')}“\n\n— *{q.get('sprecher')} ({q.get('funktion')})*")
        else:
            st.caption("Keine Zitate verwendet.")
            
    with c2:
        st.markdown("#### 🛠 KI-Anpassungen")
        diffs = article_json.get("abweichungen_von_draft", [])
        if diffs:
            for diff in diffs:
                st.warning(f"• {diff}")
        else:
            st.caption("Keine Abweichungen.")

def get_index_for_default(options, search_strings):
    if not isinstance(search_strings, list): search_strings = [search_strings]
    for search in search_strings:
        for i, option in enumerate(options):
            if search.lower() in option.lower(): return i
    return 0

def parse_selection(selection):
    if not selection or "(" not in selection: return None, "file"
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
    available_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
    model_choice = st.selectbox("Modell", available_models, index=0)
    temp_val = st.slider("Kreativität (Temp)", 0.0, 1.0, 0.2, 0.1)
    model_settings = {"model": model_choice, "temp": temp_val}
    
    st.divider()
    
    st.subheader("Prompts")
    available = discovery.list_available_prompts()
    
    opts_extract = [f"{p['display_name']} ({p['source']})" for p in available["extraction"]]
    opts_draft = [f"{p['display_name']} ({p['source']})" for p in available["draft"]]
    opts_write = [f"{p['display_name']} ({p['source']})" for p in available["write"]]
    opts_check = [f"{p['display_name']} ({p['source']})" for p in available["control"]]
    
    # 1. Extraction
    idx_e = get_index_for_default(opts_extract, "extract")
    p1_sel = st.selectbox("1. Daten-Extraktion", opts_extract, index=idx_e)
    p1_ver = st.selectbox("Version", get_versions(p1_sel), key="v1")
    
    # 2. Draft (Concept)
    idx_d = get_index_for_default(opts_draft, ["draft", "concept"])
    p2_sel = st.selectbox("2. Konzept/Planung", opts_draft, index=idx_d)
    p2_ver = st.selectbox("Version", get_versions(p2_sel), key="v2")

    # 3. Write (Article)
    idx_w = get_index_for_default(opts_write, ["write", "artikel", "article"])
    p3_sel = st.selectbox("3. Artikel Schreiben", opts_write, index=idx_w)
    p3_ver = st.selectbox("Version", get_versions(p3_sel), key="v3")
    
    # 4. Check
    idx_c = get_index_for_default(opts_check, ["check", "control"])
    p4_sel = st.selectbox("4. Fakten-Check", opts_check, index=idx_c)
    p4_ver = st.selectbox("Version", get_versions(p4_sel), key="v4")


# =========================================================
# MAIN CONTENT
# =========================================================
st.title("📰 AI Editorial Assistant")

col1, col2 = st.columns([1, 1])
with col1:
    meta_input = st.text_area("Metadaten", height=100, placeholder="Absender, Datum...")
    text_input = st.text_area("Nachrichtentext", height=300, placeholder="Inhalt...")
with col2:
    uploaded_files = st.file_uploader("Anhänge", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    st.info(f"Modell: {model_choice} | Datum: {processor.get_date_string()}")
    start_btn = st.button("🚀 Workflow starten", type="primary", use_container_width=True)

st.divider()
status_container = st.status("Bereit...", expanded=False)

# 4 Tabs für die 4 Phasen
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Daten (JSON)", 
    "💡 2. Konzept (Tabelle)", 
    "📰 3. Artikel (Preview)", 
    "✅ 4. Check (Report)"
])

if start_btn:
    # Reset workflow data
    st.session_state.workflow_data = {}
    processor.logger.clear()
    status_container.update(label="🚀 Workflow läuft...", state="running", expanded=True)
    
    try:
        # Prompt Configs
        c1 = {"name": parse_selection(p1_sel)[0], "source": parse_selection(p1_sel)[1], "version": p1_ver}
        c2 = {"name": parse_selection(p2_sel)[0], "source": parse_selection(p2_sel)[1], "version": p2_ver}
        c3 = {"name": parse_selection(p3_sel)[0], "source": parse_selection(p3_sel)[1], "version": p3_ver}
        c4 = {"name": parse_selection(p4_sel)[0], "source": parse_selection(p4_sel)[1], "version": p4_ver}
        
        # 0. Parse Input
        status_container.write("📎 Parse Dokumente...")
        file_content = processor.step_parsing(uploaded_files)
        full_raw_input = f"META: {meta_input}\nTEXT: {text_input}\nFILES: {file_content}"
        st.session_state.workflow_data["raw"] = full_raw_input
        
        # 1. Extract
        status_container.write(f"🤖 Extraktion mit {c1['name']}...")
        json_data = processor.step_extraction(c1, full_raw_input, model_settings)
        st.session_state.workflow_data["json"] = json_data
        
        # 2. Draft (Concept)
        status_container.write(f"💡 Konzept mit {c2['name']}...")
        concept_json = processor.step_draft_concept(c2, json_data, model_settings)
        st.session_state.workflow_data["concept"] = concept_json
        
        # 3. Write (Article)
        status_container.write(f"✍️ Artikel schreiben mit {c3['name']}...")
        article_data = processor.step_write_article(c3, json_data, concept_json, model_settings)
        st.session_state.workflow_data["article"] = article_data

        # 4. Check (Hier müssen wir evtl. den Article in String wandeln für den Check-Input)
        status_container.write(f"🔍 Check mit {c4['name']}...")
        
        # Article kann JSON oder String sein, Check braucht String
        article_text_for_check = json.dumps(article_data, ensure_ascii=False) if isinstance(article_data, dict) else str(article_data)
        
        check_text = processor.step_check(c4, article_text_for_check, json_data, full_raw_input, model_settings)
        st.session_state.workflow_data["check"] = check_text

        status_container.update(label="✅ Fertig!", state="complete", expanded=False)

    except Exception as e:
        status_container.update(label="❌ Fehler", state="error")
        st.error(f"Fehler im Ablauf: {str(e)}")
        # Debugging: Stacktrace anzeigen
        import traceback
        st.code(traceback.format_exc())

    finally:
        processor.flush_stats()

# --- OUTPUT VIEW ---
# Hier greifen wir sicher auf session_state zu
if "workflow_data" in st.session_state and st.session_state.workflow_data:
    d = st.session_state.workflow_data
    
    # 1. Daten
    with tab1:
        if "json" in d: st.json(d["json"], expanded=True)
        else: st.info("Warte auf Daten...")

    # 2. Konzept
    with tab2:
        if "concept" in d:
            c_json = try_parse_json(d["concept"])
            if c_json: st.markdown(render_json_html(c_json), unsafe_allow_html=True)
            else: st.markdown(d["concept"])
        else: st.info("Warte auf Konzept...")

    # 3. Artikel (NEU - Dashboard)
    with tab3:
        if "article" in d:
            # Versuchen zu parsen
            a_data = d["article"]
            if isinstance(a_data, str):
                a_data = try_parse_json(a_data)
            
            if isinstance(a_data, dict):
                # 1. Dashboard Visualisierung
                render_article_dashboard(a_data)
                
                # 2. Expander für Raw Data
                st.divider()
                with st.expander("🔍 Rohes JSON ansehen"):
                    st.json(a_data)
            else:
                # Fallback
                st.warning("⚠️ Konnte Artikel-Format nicht parsen (kein JSON). Zeige Text:")
                st.markdown(d["article"])
        else: st.info("Warte auf Artikel...")

    # 4. Check
    with tab4:
        if "check" in d: st.markdown(d["check"])
        else: st.info("Warte auf Check...")

    # --- DOWNLOADS ---
    st.divider()
    with st.expander("💾 Ergebnisse herunterladen", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        
        if "json" in d:
            c1.download_button("📥 1. Daten (JSON)", json.dumps(d["json"], indent=2, ensure_ascii=False), "data.json", "application/json")
        
        if "concept" in d:
            c_content = d["concept"]
            if isinstance(c_content, dict): c_content = json.dumps(c_content, indent=2, ensure_ascii=False)
            c2.download_button("📥 2. Konzept (JSON)", c_content, "concept.json", "application/json")
            
        if "article" in d:
            # Download als JSON
            a_content = d["article"]
            if isinstance(a_content, dict): a_content = json.dumps(a_content, indent=2, ensure_ascii=False)
            c3.download_button("📥 3. Artikel (JSON)", a_content, "article.json", "application/json")
            
        if "check" in d:
            c4.download_button("📥 4. Check (MD)", d["check"], "check_report.md", "text/markdown")
