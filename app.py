import streamlit as st
import pandas as pd
import os
import re
import json
from datetime import datetime
from agent.retrieve import retrieve_phase
from agent.plan import plan_phase
from cleaner.auto_clean import auto_clean
from explain.eda_plan import gemini_generate_eda_plan
from agent.analyze import analyze_phase
from agent.respond import respond_phase

st.set_page_config(
    page_title="Data Analysis Agent",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
.stApp { background: #ffffff; }
.block-container { padding: 3rem 5rem; max-width: 1200px; }

h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: 1.8rem !important; font-weight: 600 !important;
    color: #111 !important; letter-spacing: -0.02em;
    margin-bottom: 1.5rem !important;
}

.stButton > button {
    font-family: 'Inter', sans-serif; font-size: 0.9rem; font-weight: 500;
    border: 1px solid #e2e8f0; border-radius: 6px;
    background: #ffffff; color: #1e293b; padding: 0.5rem 1.25rem;
    transition: all 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.stButton > button:hover { border-color: #3b82f6; color: #3b82f6; background: #f8faff; }

.stButton > button[kind="primary"] { 
    background: #2563eb; color: #ffffff; border: 1px solid #2563eb; 
}
.stButton > button[kind="primary"]:hover { 
    background: #1d4ed8; border-color: #1d4ed8; color: #ffffff; 
}

.stFileUploader { border: 2px dashed #e2e8f0; border-radius: 12px; padding: 2rem; background: #f8fafc; }
.stMetric { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; }

.thinking-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 1.25rem; margin: 0.75rem 0;
}
.thinking-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; text-transform: uppercase; color: #64748b;
    letter-spacing: 0.05em; margin-bottom: 0.5rem; display: block;
}
.thinking-text { font-size: 0.9rem; color: #334155; line-height: 1.6; }

.step-indicator {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #3b82f6; font-weight: 600;
    margin-bottom: -10px;
}

.download-section {
    background: #f8fafc; border: 1px solid #e2e8f0;
    padding: 1.5rem; border-radius: 10px; margin: 1rem 0 2rem;
}
</style>
""", unsafe_allow_html=True)

def render_thinking(step_num, total_steps, label, reasoning):
    st.markdown(f'<div class="step-indicator">STEP {step_num}/{total_steps}</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="thinking-card">
        <span class="thinking-header">{label} Phase reasoning</span>
        <div class="thinking-text">{reasoning}</div>
    </div>
    """, unsafe_allow_html=True)

def clean_report_markdown(report_md):
    if not report_md: return ""
    report_md = re.sub(r'NOTE: All charts are generated and saved.*?\.', '', report_md, flags=re.DOTALL)
    return report_md.strip()

def render_report_with_charts(report_md, chart_dir):
    clean = clean_report_markdown(report_md)
    parts = re.split(r'(!\[.*?\]\(.*?\))', clean)
    for part in parts:
        img_match = re.search(r'!\[(.*?)\]\((.*?)\)', part)
        if img_match:
            fname = os.path.basename(img_match.group(2))
            path = os.path.join(chart_dir, fname)
            if os.path.exists(path):
                st.image(path, caption=img_match.group(1), use_container_width=True)
        elif part.strip():
            st.markdown(part)

st.title("Data Analysis Agent")

if 'sample_mode' not in st.session_state: st.session_state.sample_mode = False
if 'final_report' not in st.session_state: st.session_state.final_report = None
if 'analysis_logs' not in st.session_state: st.session_state.analysis_logs = None
if 'out_path' not in st.session_state: st.session_state.out_path = None

top_col1, top_col2 = st.columns([2, 1])

with top_col1:
    st.markdown("#### 1. Input Data")
    uploaded_file = st.file_uploader("Drop CSV here", type="csv", label_visibility="collapsed")

with top_col2:
    st.markdown("#### 2. Quick Actions")
    if st.button("Use Netflix Sample", use_container_width=True):
        st.session_state.sample_mode = True
        st.session_state.final_report = None
    if st.button("Clear All", use_container_width=True):
        st.cache_data.clear()
        for key in ['final_report', 'analysis_logs', 'out_path', 'sample_mode']:
            st.session_state[key] = None
        st.rerun()

target_path = None
out_path = None

if uploaded_file:
    st.session_state.sample_mode = False
    run_id = datetime.now().strftime('%M%S')
    out_path = os.path.join("sample_outputs", f"upload_{run_id}")
    os.makedirs(os.path.join(out_path, "charts"), exist_ok=True)
    os.makedirs(os.path.join(out_path, "eda_outputs"), exist_ok=True)
    target_path = os.path.join(out_path, "input.csv")
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
elif st.session_state.sample_mode:
    sample = "sample_inputs/netflix.csv"
    if os.path.exists(sample):
        target_path = sample
        out_path = os.path.join("sample_outputs", f"sample_{datetime.now().strftime('%M%S')}")
        os.makedirs(os.path.join(out_path, "charts"), exist_ok=True)
        os.makedirs(os.path.join(out_path, "eda_outputs"), exist_ok=True)

if target_path:
    st.markdown("---")
    if st.button("Run Full Analysis", type="primary", use_container_width=True):
        with st.status("Agent is analyzing data...", expanded=True) as status:
            df_orig, r_r, r_c = retrieve_phase(target_path, out_path)
            render_thinking(1, 4, "Retrieve", r_r)
            
            plan, p_r, p_c = plan_phase(df_orig)
            render_thinking(2, 4, "Plan", p_r)
            
            cleaned_df = auto_clean(df_orig.copy(), plan)
            
            eda_plan, _ = gemini_generate_eda_plan(cleaned_df)
            res, a_r, a_c = analyze_phase(cleaned_df, eda_plan, out_path)
            render_thinking(3, 4, "Analyze", a_r)
            
            report, res_r, res_c = respond_phase(plan, eda_plan, res, out_path)
            render_thinking(4, 4, "Respond", res_r)
            
            st.session_state.final_report = report
            st.session_state.out_path = out_path
            st.session_state.analysis_logs = {"Retrieve": r_c, "Plan": p_c, "Analyze": a_c, "Respond": res_c}
            status.update(label="Analysis Finished", state="complete", expanded=False)

if st.session_state.final_report:
    m_cols = st.columns(4)
    for i, (k, v) in enumerate(st.session_state.analysis_logs.items()):
        val = int(v * 100) if isinstance(v, float) else v
        m_cols[i].metric(k, f"{val}%")

    st.markdown("---")
    
    st.markdown('<div class="download-section">', unsafe_allow_html=True)
    col_text, col_dl = st.columns([3, 1])
    with col_text:
        st.markdown("#### Export Results")
        st.markdown("Download the current analysis report as a Markdown file.")
    with col_dl:
        st.download_button(
            label="Download Report (.md)",
            data=clean_report_markdown(st.session_state.final_report),
            file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_report_btn"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Executive Report")
    render_report_with_charts(st.session_state.final_report, os.path.join(st.session_state.out_path, "charts"))