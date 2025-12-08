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
    .preview-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        background-color: white;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .online-header { border-top: 5px solid #ff4b4b; }
    .print-header { border-top: 5px solid #333; }
    
    .meta-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        font-size: 0.85em;
        margin-bottom: 15px;
        border-left: 3px solid #ff4b4b;
    }
    
    .print-font { font-family: "Times New Roman", Times, serif; }
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
    if isinstance(content, dict): return content
    try:
        clean = content.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except: return None

def render_json_html(data):
    # ... (Funktion wie zuvor, für Draft Tabelle)
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

# --- NEU: Visualisierung für Artikel Output ---
def render_article_dashboard(article_json):
    """Zeigt Online und Print Version nebeneinander an"""
    
    # Sicherstellen, dass die Keys existieren (Fehlertoleranz)
    online = article_json.get("online", {})
    print_ver = article_json.get("print", {})
    meta = article_json.get("confidence", {})
    
    # Metriken oben
    m1, m2, m3 = st.columns(3)
    m1.metric("Fakten-Check", f"{meta.get('fakten_vollstaendig', '?')}/3")
    m2.metric("Stil-Score", f"{meta.get('stil_konform', '?')}/3")
    m3.metric("Länge", f"{meta.get('laenge_eingehalten', '?')}/3")
    
    st.divider()

    col_online, col_print = st.columns(2)
    
    # --- ONLINE SPALTE ---
    with col_online:
        st.markdown("### 🌐 Online Version")
        with st.container(border=True):
            # Meta Description
            if "meta_description" in online:
                st.markdown(f"""
                <div class="meta-box">
                    <strong>SEO Description ({len(online.get('meta_description',''))} Zeichen):</strong><br>
                    {online.get('meta_description')}
                </div>
                """, unsafe_allow_html=True)
            
            # Content
            st.markdown(f"# {online.get('ueberschrift', '')}")
            st.markdown(f"*{online.get('teaser', '')}*")
            st.markdown("---")
            st.markdown(online.get('body', ''))
            
            st.caption(f"Zeichen (Body): {online.get('zeichen_body', 0)}")

    # --- PRINT SPALTE ---
    with col_print:
        st.markdown("### 📰 Print Version")
        with st.container(border=True):
            # Print Styling Simulation
            st.markdown(f"""
            <div class="print-font">
                <h4 style="margin-bottom:0; color:#555;">{print_ver.get('unterzeile', '')}</h4>
                <h2 style="margin-top:0; font-size: 2em;">{print_ver.get('ueberschrift', '')}</h2>
                <hr style="border-top: 2px solid black;">
                <p style="text-align: justify;">{print_ver.get('text', '').replace(chr(10), '<br>')}</p>
            </div>
            """, unsafe_allow_html=True)
             
            st.caption(f"Zeichen (Text): {print_ver.get('zeichen_text', 0)}")
            
    # --- FOOTER BEREICH ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**💬 Verwendete Zitate**")
        for q in article_json.get("verwendete_zitate", []):
            st.info(f"„{q.get('text')}“\n\n— *{q.get('sprecher')} ({q.get('funktion')})*")
            
    with c2:
        st.markdown("**🛠 Abweichungen vom Entwurf**")
        for diff in article_json.get("abweichungen_von_draft", []):
            st.warning(f"• {diff}")


# ... (Restliche Helper Funktionen: get_index_for_default, parse_selection, get_versions bleiben gleich)
# ... (Sidebar Code bleibt gleich)

# =========================================================
# MAIN CONTENT
# =========================================================
# ... (Setup Code bis zu den Tabs bleibt gleich)

# 4 Tabs für die 4 Phasen
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Daten (JSON)", 
    "💡 2. Konzept (Tabelle)", 
    "📰 3. Artikel (Preview)", # Umbenannt
    "✅ 4. Check (Report)"
])

# ... (Start Button Logik und Workflow Steps bleiben gleich)
# ... (step_write_article liefert jetzt JSON zurück)

# --- OUTPUT VIEW ---
if st.session_state.workflow_data:
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

    # 3. Artikel (NEU)
    with tab3:
        if "article" in d:
            # Versuchen, das JSON zu parsen (falls String)
            a_data = d["article"]
            if isinstance(a_data, str):
                a_data = try_parse_json(a_data)
            
            if isinstance(a_data, dict):
                # 1. Schöne Visualisierung
                render_article_dashboard(a_data)
                
                # 2. Raw JSON im Expander
                st.divider()
                with st.expander("🔍 Rohes JSON ansehen"):
                    st.json(a_data)
            else:
                # Fallback, falls doch Text kam
                st.warning("⚠️ Format ist kein valides JSON. Zeige Rohdaten:")
                st.markdown(d["article"])
        else: st.info("Warte auf Artikel...")

    # 4. Check
    with tab4:
        if "check" in d: st.markdown(d["check"])
        else: st.info("Warte auf Check...")

    # --- DOWNLOADS ---
    st.divider()
    with st.expander("💾 Alle Ergebnisse speichern", expanded=True):
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
