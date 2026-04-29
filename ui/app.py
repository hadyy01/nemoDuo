"""
ui/app.py
NemoDuo Streamlit UI — streams the agent conversation live.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.orchestrator import Orchestrator
from core.metrics import MetricsLogger

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NemoDuo",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #76b900 0%, #00d4aa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.subtitle {
    color: #888;
    font-size: 0.9rem;
    font-family: 'Space Mono', monospace;
    margin-top: 0;
}

.agent-box {
    border-radius: 8px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.88rem;
    line-height: 1.6;
}

.planner-box {
    background: rgba(118, 185, 0, 0.08);
    border-left: 3px solid #76b900;
}

.executor-box {
    background: rgba(0, 212, 170, 0.08);
    border-left: 3px solid #00d4aa;
}

.status-box {
    background: rgba(255, 255, 255, 0.04);
    border-left: 3px solid #555;
    color: #aaa;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
}

.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
}

.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: #76b900;
}

.metric-label {
    font-size: 0.75rem;
    color: #888;
    margin-top: 2px;
}

.tag {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
}

.tag-planner { background: rgba(118,185,0,0.2); color: #76b900; }
.tag-executor { background: rgba(0,212,170,0.2); color: #00d4aa; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    reasoning_budget = st.select_slider(
        "Reasoning Budget (tokens)",
        options=[256, 512, 1024, 2048, 4096, 8192],
        value=2048,
        help="Higher = deeper reasoning by Super, slower response"
    )

    max_subtasks = st.slider("Max Subtasks", 1, 5, 3)

    st.markdown("---")
    st.markdown("### 🤖 Agents")
    st.markdown("""
    <div class="agent-box planner-box">
        <span class="tag tag-planner">PLANNER</span><br>
        <b>Nemotron 3 Super</b><br>
        <span style="color:#888;font-size:0.8rem">120B · NVIDIA NIM API<br>Strategic reasoning & synthesis</span>
    </div>
    <div class="agent-box executor-box">
        <span class="tag tag-executor">EXECUTOR</span><br>
        <b>Nemotron 3 Nano 4B</b><br>
        <span style="color:#888;font-size:0.8rem">4B · Ollama local<br>Fast task execution</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Recent Runs")
    try:
        logger = MetricsLogger()
        recent = logger.get_recent(5)
        if recent:
            for r in recent:
                st.markdown(
                    f"<small style='color:#666'>{r['query'][:40]}...<br>"
                    f"💰 ${r['estimated_cost_usd']:.5f} · {r['planner_tokens']+r['executor_tokens']} tok</small>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<small style='color:#555'>No runs yet</small>", unsafe_allow_html=True)
    except Exception:
        pass


# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">NemoDuo</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Nemotron 3 Super (Planner) + Nano 4B (Executor) · Multi-Agent Research System</p>',
    unsafe_allow_html=True
)

query = st.text_input(
    "",
    placeholder="Ask a research question — e.g. 'What are the latest breakthroughs in agentic AI in 2025?'",
    label_visibility="collapsed"
)

col1, col2 = st.columns([1, 5])
with col1:
    run_btn = st.button("▶ Run", use_container_width=True, type="primary")
with col2:
    mode = st.radio("", ["Duo Mode (Super + Nano)", "Solo Mode (Super only)"], horizontal=True, label_visibility="collapsed")

st.markdown("---")

if run_btn and query.strip():
    os.environ["REASONING_BUDGET"] = str(reasoning_budget)
    os.environ["MAX_SUBTASKS"] = str(max_subtasks)

    orchestrator = Orchestrator()

    # Live stream columns
    left, right = st.columns([3, 2])

    with left:
        st.markdown("### 💬 Agent Stream")
        stream_container = st.container()

    with right:
        st.markdown("### 📋 Plan")
        plan_container = st.container()

    answer_slot = st.empty()
    metrics_slot = st.empty()

    with stream_container:
        for event in orchestrator.run(query):
            etype = event["type"]
            data = event["data"]

            if etype == "status":
                st.markdown(
                    f'<div class="agent-box status-box">{data}</div>',
                    unsafe_allow_html=True
                )

            elif etype == "plan":
                with plan_container:
                    st.markdown(f"**Planner Reasoning:**")
                    st.markdown(
                        f'<div class="agent-box planner-box" style="font-size:0.82rem;color:#aaa">'
                        f'{data["reasoning"]}</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown("**Subtasks:**")
                    for s in data["subtasks"]:
                        st.markdown(
                            f'<div class="agent-box executor-box">'
                            f'<b>#{s["id"]}</b> <span style="color:#888">[{s["type"]}]</span><br>'
                            f'{s["instruction"]}</div>',
                            unsafe_allow_html=True
                        )

            elif etype == "subtask":
                st.markdown(
                    f'<div class="agent-box executor-box">'
                    f'<span class="tag tag-executor">NANO</span> '
                    f'<b>Subtask {data["subtask_id"]}</b> · {data["tokens"]} tok · {data["latency_ms"]:.0f}ms<br><br>'
                    f'{data["result"][:400]}{"..." if len(data["result"]) > 400 else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            elif etype == "answer":
                answer_slot.markdown("---")
                answer_slot.markdown("### ✅ Final Answer")
                answer_slot.markdown(data)

            elif etype == "metrics":
                m = data
                metrics_slot.markdown("---")
                metrics_slot.markdown("### 📊 Run Metrics")
                c1, c2, c3, c4, c5 = metrics_slot.columns(5)
                c1.markdown(
                    f'<div class="metric-card"><div class="metric-value">{m["planner_tokens"]}</div>'
                    f'<div class="metric-label">Planner Tokens</div></div>', unsafe_allow_html=True)
                c2.markdown(
                    f'<div class="metric-card"><div class="metric-value">{m["executor_tokens"]}</div>'
                    f'<div class="metric-label">Executor Tokens</div></div>', unsafe_allow_html=True)
                c3.markdown(
                    f'<div class="metric-card"><div class="metric-value">{m["reasoning_tokens"]}</div>'
                    f'<div class="metric-label">Reasoning Tokens</div></div>', unsafe_allow_html=True)
                c4.markdown(
                    f'<div class="metric-card"><div class="metric-value">{m["total_latency_ms"]}ms</div>'
                    f'<div class="metric-label">Total Latency</div></div>', unsafe_allow_html=True)
                c5.markdown(
                    f'<div class="metric-card"><div class="metric-value">${m["estimated_cost_usd"]:.5f}</div>'
                    f'<div class="metric-label">Est. Cost (USD)</div></div>', unsafe_allow_html=True)

elif run_btn and not query.strip():
    st.warning("Please enter a query.")
