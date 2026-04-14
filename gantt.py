"""
=====================================================
  GANTT CHART GENERATOR
  Creates a visual timeline of the schedule
=====================================================

A Gantt Chart is just a bar chart where:
  - Y axis = Machines
  - X axis = Time (hours)
  - Each bar = One job step (colored by order)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from scheduler import run_scheduler, MACHINES, ORDERS


def build_gantt(df: pd.DataFrame, total_time: float) -> go.Figure:
    """
    Takes the schedule dataframe and draws a Gantt chart.
    Each order gets its own color.
    """

    # Assign a color to each unique order
    order_names = df["Order"].unique().tolist()
    colors = px.colors.qualitative.Bold
    color_map = {name: colors[i % len(colors)] for i, name in enumerate(order_names)}

    fig = go.Figure()

    # Draw one bar per step
    for _, row in df.iterrows():
        on_time_marker = "✅" if row["On_Time"] else "⚠️"
        fig.add_trace(go.Bar(
            name=row["Order"],
            x=[row["Duration"]],
            y=[row["Machine"]],
            base=row["Start_hr"],
            orientation="h",
            marker_color=color_map[row["Order"]],
            marker_line=dict(color="white", width=1.5),
            text=f"Step {row['Step']} ({row['Duration']}h)",
            textposition="inside",
            insidetextanchor="middle",
            hovertemplate=(
                f"<b>{row['Order']}</b><br>"
                f"Machine: {row['Machine']}<br>"
                f"Step: {row['Step']}<br>"
                f"Start: Hour {row['Start_hr']}<br>"
                f"End: Hour {row['End_hr']}<br>"
                f"Duration: {row['Duration']} hrs<br>"
                f"Deadline: Hour {row['Deadline']} {on_time_marker}<br>"
                "<extra></extra>"
            ),
            showlegend=row["Step"] == 1,
        ))

    # Add deadline markers as vertical dashed lines
    deadlines_drawn = set()
    for _, row in df.iterrows():
        order = row["Order"]
        if order not in deadlines_drawn:
            fig.add_vline(
                x=row["Deadline"],
                line_dash="dot",
                line_color=color_map[order],
                line_width=1.5,
                opacity=0.5,
            )
            deadlines_drawn.add(order)

    # Machine utilization calculation
    machine_util = {}
    for machine in df["Machine"].unique():
        mdf = df[df["Machine"] == machine]
        busy_hours = mdf["Duration"].sum()
        util_pct = round((busy_hours / total_time) * 100, 1)
        machine_util[machine] = util_pct

    fig.update_layout(
        title=dict(
            text=f"🏭 Elevator Factory — Optimal Production Schedule  |  Total Time: {int(total_time)} hrs",
            font=dict(size=18, family="Georgia, serif"),
            x=0.5,
        ),
        barmode="overlay",
        xaxis=dict(
            title="Time (Hours from Start of Shift)",
            tickmode="linear",
            tick0=0,
            dtick=1,
            gridcolor="#0b5d42",
            showgrid=True,
        ),
        yaxis=dict(
            title="Machine",
            autorange="reversed",
            tickfont=dict(size=12),
        ),
        legend=dict(
            title="Orders",
            orientation="v",
            x=1.02,
            y=1,
            font=dict(size=11),
        ),
        plot_bgcolor="#f8f9fb",
        paper_bgcolor="black",
        height=500,
        margin=dict(l=160, r=220, t=70, b=60),
        font=dict(family="Georgia, serif"),
    )

    annotation_text = "<b>Machine Utilization</b><br>" + "<br>".join(
        [f"{m}: {u}%" for m, u in machine_util.items()]
    )
    fig.add_annotation(
        x=1.18, y=0.5,
        xref="paper", yref="paper",
        text=annotation_text,
        showarrow=False,
        align="left",
        bgcolor="#064842",
        bordercolor="#4a6cf7",
        borderwidth=1,
        borderpad=8,
        font=dict(size=10, family="monospace"),
    )

    return fig


def build_utilization_chart(df: pd.DataFrame, total_time: float) -> go.Figure:
    """Bar chart showing how busy each machine is."""
    machine_data = []
    for machine in df["Machine"].unique():
        mdf = df[df["Machine"] == machine]
        busy = mdf["Duration"].sum()
        idle = total_time - busy
        machine_data.append({
            "Machine": machine,
            "Busy (hrs)": busy,
            "Idle (hrs)": idle,
            "Utilization %": round((busy / total_time) * 100, 1),
        })

    mdf = pd.DataFrame(machine_data).sort_values("Utilization %", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Busy",
        y=mdf["Machine"],
        x=mdf["Busy (hrs)"],
        orientation="h",
        marker_color="#4a6cf7",
        text=[f"{u}%" for u in mdf["Utilization %"]],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Idle",
        y=mdf["Machine"],
        x=mdf["Idle (hrs)"],
        orientation="h",
        marker_color="#e0e7ff",
    ))

    fig.update_layout(
        title=dict(
            text="Machine Utilization — Busy vs Idle Hours",
            font=dict(size=16, family="Georgia, serif"),
            x=0.5,
        ),
        barmode="stack",
        xaxis_title="Hours",
        yaxis_title="Machine",
        plot_bgcolor="#f8f9fb",
        paper_bgcolor="black",
        height=380,
        legend=dict(orientation="h", x=0.3, y=-0.2),
        font=dict(family="Georgia, serif"),
    )
    return fig


def build_comparison_chart(
    naive_df: pd.DataFrame, naive_time: float,
    optimized_df: pd.DataFrame, optimized_time: float,
    machines: dict
) -> go.Figure:
    """
    Side-by-side horizontal bar chart comparing
    machine utilization BEFORE (naive) vs AFTER (optimized).
    """

    all_machines = list(machines.values())
    naive_util = {}
    optimized_util = {}

    for machine in all_machines:
        # Naive utilization
        n_mdf = naive_df[naive_df["Machine"] == machine]
        naive_busy = n_mdf["Duration"].sum() if not n_mdf.empty else 0
        naive_util[machine] = round((naive_busy / naive_time) * 100, 1) if naive_time > 0 else 0

        # Optimized utilization
        o_mdf = optimized_df[optimized_df["Machine"] == machine]
        opt_busy = o_mdf["Duration"].sum() if not o_mdf.empty else 0
        optimized_util[machine] = round((opt_busy / optimized_time) * 100, 1) if optimized_time > 0 else 0

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Before (Manual)",
        y=all_machines,
        x=[naive_util[m] for m in all_machines],
        orientation="h",
        marker_color="#f87171",
        text=[f"{naive_util[m]}%" for m in all_machines],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Manual: %{x}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="After (Optimized)",
        y=all_machines,
        x=[optimized_util[m] for m in all_machines],
        orientation="h",
        marker_color="#4a6cf7",
        text=[f"{optimized_util[m]}%" for m in all_machines],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Optimized: %{x}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Machine Utilization — Before vs After Optimization",
            font=dict(size=16, family="Georgia, serif"),
            x=0.5,
        ),
        barmode="group",
        xaxis=dict(
            title="Utilization (%)",
            range=[0, 120],
        ),
        yaxis_title="Machine",
        plot_bgcolor="#f8f9fb",
        paper_bgcolor="black",
        height=420,
        legend=dict(orientation="h", x=0.2, y=-0.2),
        font=dict(family="Georgia, serif"),
        margin=dict(l=160, r=40, t=60, b=80),
    )

    return fig


if __name__ == "__main__":
    df, total_time, success = run_scheduler()
    if success:
        fig = build_gantt(df, total_time)
        fig.write_html("gantt_chart.html")
        print("✅ Gantt chart saved to gantt_chart.html — open it in your browser!")
