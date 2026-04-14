"""
=====================================================
  ELEVATOR FACTORY SCHEDULING DASHBOARD
  Run with: streamlit run app.py
=====================================================

This is the main dashboard. It has 4 sections:
  1. Sidebar — Add new orders
  2. KPI Cards — Quick summary stats
  3. Gantt Chart — Visual timeline
  4. Schedule Table — Full details
"""

import streamlit as st
import pandas as pd
import time
from scheduler import run_scheduler, MACHINES, ORDERS
from naive_scheduler import run_naive_scheduler
from gantt import build_gantt, build_utilization_chart, build_comparison_chart
import copy

# ─────────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Elevator Factory Scheduler",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
#  Custom CSS Styling
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=JetBrains+Mono:wght@400;600&family=Lato:wght@300;400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
    }

    .main-title {
        font-family: 'IM Fell English', serif;
        font-size: 2.4rem;
        color: #ffffff;
        letter-spacing: -0.5px;
        border-bottom: 3px solid #4a6cf7;
        padding-bottom: 10px;
        margin-bottom: 4px;
    }

    .sub-title {
        color: #c9d1d9;
        font-size: 0.95rem;
        margin-bottom: 28px;
        font-weight: 300;
    }

    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border-left: 4px solid #4a6cf7;
    }

    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.2rem;
        font-weight: 600;
        color: #1a1f36;
        line-height: 1;
    }

    .kpi-label {
        color: #6b7280;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 6px;
    }

    .kpi-card-warn {
        border-left: 4px solid #f59e0b;
    }

    .kpi-card-success {
        border-left: 4px solid #10b981;
    }

    .kpi-card-danger {
        border-left: 4px solid #ef4444;
    }

    .kpi-card-before {
        background: #fff5f5;
        border-left: 4px solid #ef4444;
    }

    .kpi-card-after {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
    }

    .kpi-delta-positive {
        color: #10b981;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 4px;
    }

    .kpi-delta-negative {
        color: #ef4444;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 4px;
    }

    .section-header {
        font-family: 'IM Fell English', serif;
        font-size: 1.3rem;
        color: #ffffff;
        margin: 28px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .comparison-header {
        font-family: 'IM Fell English', serif;
        font-size: 1.5rem;
        color: #ffffff;
        margin: 36px 0 6px 0;
        border-bottom: 2px solid #4a6cf7;
        padding-bottom: 8px;
    }

    .comparison-subtext {
        color: #c9d1d9;
        font-size: 0.88rem;
        margin-bottom: 20px;
    }

    .before-label {
        background: #fee2e2;
        color: #991b1b;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 10px;
    }

    .after-label {
        background: #d1fae5;
        color: #065f46;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 10px;
    }

    .status-badge-ok {
        background: #d1fae5;
        color: #065f46;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .status-badge-late {
        background: #fee2e2;
        color: #991b1b;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .stButton > button {
        background: #4a6cf7;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
        width: 100%;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background: #3451d1;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74,108,247,0.3);
    }

    .sidebar-section {
        background: #f8f9ff;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 14px;
        border: 1px solid #e0e7ff;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
#  Session State
# ─────────────────────────────────────────────────
if "orders" not in st.session_state:
    st.session_state.orders = copy.deepcopy(ORDERS)

if "schedule_df" not in st.session_state:
    st.session_state.schedule_df = None
    st.session_state.total_time = 0

if "naive_df" not in st.session_state:
    st.session_state.naive_df = None
    st.session_state.naive_time = 0

# ─────────────────────────────────────────────────
#  Sidebar — Add New Orders
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 Factory Control")
    st.markdown("---")

    with st.expander("➕ Add New Order", expanded=False):
        with st.form("add_order_form"):
            order_name = st.text_input("Order Name", placeholder="e.g. Order F - Counterweight")
            deadline   = st.number_input("Deadline (hours)", min_value=1, max_value=100, value=12)
            priority   = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: {1:"🔴 High", 2:"🟡 Medium", 3:"🟢 Low"}[x])

            st.markdown("**Add Steps** (Machine → Duration)")
            step_rows = []
            for i in range(1, 5):
                c1, c2 = st.columns(2)
                machine_choice = c1.selectbox(f"Step {i} Machine", ["(none)"] + list(MACHINES.values()), key=f"m{i}")
                duration_val   = c2.number_input(f"Hrs", min_value=1, max_value=20, value=2, key=f"d{i}")
                if machine_choice != "(none)":
                    machine_id = [k for k, v in MACHINES.items() if v == machine_choice][0]
                    step_rows.append((machine_id, duration_val))

            submitted = st.form_submit_button("Add Order")
            if submitted:
                if order_name and step_rows:
                    st.session_state.orders[order_name] = {
                        "priority": priority,
                        "deadline": deadline,
                        "steps": step_rows,
                    }
                    st.success(f"✅ {order_name} added!")
                else:
                    st.error("Please enter a name and at least one step.")

    st.markdown("### 📋 Current Orders")
    for oname in list(st.session_state.orders.keys()):
        col1, col2 = st.columns([3, 1])
        priority_emoji = {1:"🔴", 2:"🟡", 3:"🟢"}.get(st.session_state.orders[oname]["priority"], "⚪")
        col1.markdown(f"{priority_emoji} {oname.split(' - ')[-1] if ' - ' in oname else oname}")
        if col2.button("🗑", key=f"del_{oname}", help=f"Remove {oname}"):
            del st.session_state.orders[oname]
            st.rerun()

    st.markdown("---")
    if st.button("🔄 Reset to Default Orders"):
        st.session_state.orders = copy.deepcopy(ORDERS)
        st.session_state.schedule_df = None
        st.session_state.naive_df = None
        st.rerun()


# ─────────────────────────────────────────────────
#  Main Area — Header
# ─────────────────────────────────────────────────
st.markdown('<div class="main-title">🏭 Elevator Factory — Smart Scheduler</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Powered by Google OR-Tools Constraint Programming · Real-time Gantt Visualization</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────
#  Run Scheduler Button
# ─────────────────────────────────────────────────
col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_clicked = st.button("⚙️ Run Scheduler")

with col_info:
    st.markdown(f"<br><span style='color:#c9d1d9;font-size:0.9rem'>📦 {len(st.session_state.orders)} orders loaded · {len(MACHINES)} machines available</span>", unsafe_allow_html=True)

if run_clicked:
    with st.spinner("🧠 OR-Tools is finding the optimal schedule..."):
        time.sleep(0.5)

        # Run naive scheduler first (before state)
        naive_df, naive_time = run_naive_scheduler(st.session_state.orders, MACHINES)
        st.session_state.naive_df   = naive_df
        st.session_state.naive_time = naive_time

        # Run optimized scheduler (after state)
        df, total_time, success = run_scheduler(st.session_state.orders, MACHINES)

    if success:
        st.session_state.schedule_df = df
        st.session_state.total_time  = total_time
        st.success(f"✅ Optimal schedule found in {int(total_time)} hours!")
    else:
        st.error("❌ Could not find a valid schedule. Check your order data.")

# ─────────────────────────────────────────────────
#  KPI Cards — Optimized Schedule
# ─────────────────────────────────────────────────
if st.session_state.schedule_df is not None:
    df         = st.session_state.schedule_df
    total_time = st.session_state.total_time
    naive_df   = st.session_state.naive_df
    naive_time = st.session_state.naive_time

    # ── Optimized metrics ──
    on_time_count       = df.groupby("Order")["On_Time"].first().sum()
    total_orders        = df["Order"].nunique()
    late_count          = total_orders - on_time_count
    busy_hours          = df["Duration"].sum()
    total_machine_hours = total_time * len(MACHINES)
    utilization         = round((busy_hours / total_machine_hours) * 100, 1)
    idle_machine_hours  = total_machine_hours - busy_hours

    # ── Naive metrics ──
    naive_on_time       = naive_df.groupby("Order")["On_Time"].first().sum()
    naive_late          = total_orders - naive_on_time
    naive_busy          = naive_df["Duration"].sum()
    naive_total_mh      = naive_time * len(MACHINES)
    naive_util          = round((naive_busy / naive_total_mh) * 100, 1)
    naive_idle          = naive_total_mh - naive_busy

    # ── Deltas ──
    delta_time    = int(naive_time) - int(total_time)
    delta_ontime  = int(on_time_count) - int(naive_on_time)
    delta_util    = round(utilization - naive_util, 1)
    delta_idle    = round(naive_idle - idle_machine_hours, 1)

    # ── Optimized KPI cards ──
    st.markdown('<div class="section-header">📊 Optimized Schedule — Results</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-value">{int(total_time)}h</div>
            <div class="kpi-label">Total Schedule Time</div>
            <div class="kpi-delta-positive">▼ {delta_time}h faster than manual</div>
        </div>""", unsafe_allow_html=True)

    with k2:
        st.markdown(f"""<div class="kpi-card kpi-card-success">
            <div class="kpi-value">{int(on_time_count)}</div>
            <div class="kpi-label">Orders On Time</div>
            <div class="kpi-delta-positive">▲ {delta_ontime} more than manual</div>
        </div>""", unsafe_allow_html=True)

    with k3:
        card_class = "kpi-card-danger" if late_count > 0 else "kpi-card"
        st.markdown(f"""<div class="kpi-card {card_class}">
            <div class="kpi-value">{int(late_count)}</div>
            <div class="kpi-label">Orders At Risk</div>
            <div class="kpi-delta-positive">▼ {int(naive_late - late_count)} fewer than manual</div>
        </div>""", unsafe_allow_html=True)

    with k4:
        util_class = "kpi-card-success" if utilization >= 70 else "kpi-card-warn"
        st.markdown(f"""<div class="kpi-card {util_class}">
            <div class="kpi-value">{utilization}%</div>
            <div class="kpi-label">Machine Utilization</div>
            <div class="kpi-delta-positive">▲ {delta_util}% better than manual</div>
        </div>""", unsafe_allow_html=True)

    with k5:
        st.markdown(f"""<div class="kpi-card kpi-card-warn">
            <div class="kpi-value">{int(idle_machine_hours)}h</div>
            <div class="kpi-label">Total Idle Machine-Hours</div>
            <div class="kpi-delta-positive">▼ {int(delta_idle)}h saved vs manual</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────
    #  Before vs After Comparison Section
    # ─────────────────────────────────────────────────
    st.markdown('<div class="comparison-header">⚖️ Before vs After Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="comparison-subtext">How much does the OR-Tools optimizer improve over manual Excel-style scheduling?</div>', unsafe_allow_html=True)

    # Before vs After KPI comparison row
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""<div class="kpi-card kpi-card-before">
            <div class="before-label">BEFORE (Manual)</div>
            <div class="kpi-value" style="color:#dc2626">{int(naive_time)}h</div>
            <div class="kpi-label">Total Time</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="kpi-card kpi-card-after">
            <div class="after-label">AFTER (Optimized)</div>
            <div class="kpi-value" style="color:#059669">{int(total_time)}h</div>
            <div class="kpi-label">Total Time</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""<div class="kpi-card kpi-card-before">
            <div class="before-label">BEFORE (Manual)</div>
            <div class="kpi-value" style="color:#dc2626">{naive_util}%</div>
            <div class="kpi-label">Machine Utilization</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="kpi-card kpi-card-after">
            <div class="after-label">AFTER (Optimized)</div>
            <div class="kpi-value" style="color:#059669">{utilization}%</div>
            <div class="kpi-label">Machine Utilization</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="kpi-card kpi-card-before">
            <div class="before-label">BEFORE (Manual)</div>
            <div class="kpi-value" style="color:#dc2626">{int(naive_idle)}h</div>
            <div class="kpi-label">Idle Machine-Hours</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="kpi-card kpi-card-after">
            <div class="after-label">AFTER (Optimized)</div>
            <div class="kpi-value" style="color:#059669">{int(idle_machine_hours)}h</div>
            <div class="kpi-label">Idle Machine-Hours</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""<div class="kpi-card kpi-card-before">
            <div class="before-label">BEFORE (Manual)</div>
            <div class="kpi-value" style="color:#dc2626">{int(naive_on_time)}</div>
            <div class="kpi-label">Orders On Time</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div class="kpi-card kpi-card-after">
            <div class="after-label">AFTER (Optimized)</div>
            <div class="kpi-value" style="color:#059669">{int(on_time_count)}</div>
            <div class="kpi-label">Orders On Time</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Before vs After utilization bar chart
    comparison_fig = build_comparison_chart(
        naive_df, naive_time,
        df, total_time,
        MACHINES
    )
    st.plotly_chart(comparison_fig, use_container_width=True)

    st.markdown("---")

    # ─────────────────────────────────────────────────
    #  Gantt Chart
    # ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Production Gantt Chart</div>', unsafe_allow_html=True)
    gantt_fig = build_gantt(df, total_time)
    st.plotly_chart(gantt_fig, use_container_width=True)

    # ─────────────────────────────────────────────────
    #  Utilization Chart + Order Status
    # ─────────────────────────────────────────────────
    col_util, col_table = st.columns([1, 1])

    with col_util:
        st.markdown('<div class="section-header">⚙️ Machine Utilization</div>', unsafe_allow_html=True)
        util_fig = build_utilization_chart(df, total_time)
        st.plotly_chart(util_fig, use_container_width=True)

    with col_table:
        st.markdown('<div class="section-header">📋 Order Status</div>', unsafe_allow_html=True)
        order_summary = df.groupby("Order").agg(
            Steps=("Step", "count"),
            Start=("Start_hr", "min"),
            Finish=("End_hr", "max"),
            Deadline=("Deadline", "first"),
            On_Time=("On_Time", "first"),
            Priority=("Priority", "first"),
        ).reset_index()

        order_summary["Status"]   = order_summary["On_Time"].map({True: "✅ On Time", False: "⚠️ At Risk"})
        order_summary["Priority"] = order_summary["Priority"].map({1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"})
        order_summary = order_summary.drop(columns=["On_Time"])
        order_summary.columns = ["Order", "Steps", "Start (hr)", "Finish (hr)", "Deadline (hr)", "Priority", "Status"]
        st.dataframe(order_summary, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────
    #  Full Schedule Table
    # ─────────────────────────────────────────────────
    with st.expander("🔍 View Full Schedule (All Steps)"):
        display_df = df[["Order", "Step", "Machine", "Start_hr", "End_hr", "Duration", "Priority", "On_Time"]].copy()
        display_df["Priority"] = display_df["Priority"].map({1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"})
        display_df["On_Time"]  = display_df["On_Time"].map({True: "✅", False: "⚠️"})
        display_df.columns     = ["Order", "Step", "Machine", "Start (hr)", "End (hr)", "Duration (hr)", "Priority", "On Time"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.markdown("""
    <div style='text-align:center; padding: 60px 20px; color: #9ca3af;'>
        <div style='font-size: 3rem;'>🏭</div>
        <div style='font-size: 1.2rem; margin-top: 12px; font-family: Georgia, serif;'>
            Click <b style='color:#4a6cf7'>⚙️ Run Scheduler</b> to generate the optimal production plan
        </div>
        <div style='font-size: 0.85rem; margin-top: 8px;'>
            OR-Tools will assign every job to a machine with zero conflicts
        </div>
    </div>
    """, unsafe_allow_html=True)
