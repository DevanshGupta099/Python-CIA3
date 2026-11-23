"""Interactive Plotly & statistical Seaborn visualizations in the Solaris palette."""

from __future__ import annotations

from io import BytesIO
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

from utils.constants import (
    GRADE_COLORS,
    GRADE_ORDER,
    GRADE_SCALE,
    MIN_ESE_PASS_MARKS,
    PALETTE,
    SUBJECT_CODES,
    SUBJECTS,
)

# Solaris Editorial Categorical Sequence
GRADIENT_SEQUENCE = [
    "#2563EB",  # Royal Cobalt
    "#F97316",  # Sunset Coral
    "#E11D48",  # Crimson Rose
    "#0EA5E9",  # Sky Azure
    "#F59E0B",  # Champagne Gold
    "#10B981",  # Emerald
    "#1D4ED8",  # Deep Navy-Cobalt
    "#FB7185",  # Soft Rose
]

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", size=12),
    margin=dict(l=8, r=12, t=36, b=8),
    hoverlabel=dict(bordercolor="rgba(0,0,0,0)", font_size=12),
    transition=dict(duration=380, easing="cubic-in-out"),
)


def _apply_clean_axes(fig: go.Figure, y_title: str = "", x_title: str = "") -> go.Figure:
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_xaxes(
        title_text=x_title,
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title_text=y_title,
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.16)",
        griddash="dot",
        zeroline=False,
        tickfont=dict(size=11),
    )
    return fig


def subject_cia_breakdown_chart(df: pd.DataFrame, view_mode: str = "Stacked CIA") -> go.Figure:
    """Subject-wise CIA1, Mid-Sem CIA2, CIA3, Attendance & End-Sem breakdown."""
    fig = go.Figure()
    if df.empty:
        return _apply_clean_axes(fig)

    order = [c for c in SUBJECT_CODES if c in df["subject_code"].unique()]
    labels = [str(SUBJECTS[c]["short"]) for c in order]

    if view_mode == "Section A vs B":
        sec_grp = (
            df.groupby(["subject_code", "section"], as_index=False)["total_score"]
            .mean()
            .round(1)
        )
        colors = {"2MCA-A": PALETTE["cobalt"], "2MCA-B": PALETTE["coral"]}
        for sec in ("2MCA-A", "2MCA-B"):
            sub = sec_grp[sec_grp["section"] == sec].set_index("subject_code").reindex(order)
            fig.add_trace(
                go.Bar(
                    name=sec,
                    x=labels,
                    y=sub["total_score"],
                    marker=dict(color=colors[sec], cornerradius=7),
                    text=sub["total_score"].map(lambda v: f"{v:.1f}" if pd.notna(v) else ""),
                    textposition="outside",
                )
            )
        fig.update_layout(
            barmode="group",
            legend=dict(orientation="h", y=1.14, x=0),
            yaxis_range=[0, 106],
        )
        return _apply_clean_axes(fig, y_title="Mean Composite Score (/100)")

    agg = (
        df.groupby("subject_code")
        .agg(
            cia1_w=("cia1_w", "mean"),
            cia2_w=("cia2_w", "mean"),
            cia3_w=("cia3_w", "mean"),
            att_marks=("att_marks", "mean"),
            ese_50=("ese_50", "mean"),
            cia1_pct=("cia1_pct", "mean"),
            cia2_pct=("cia2_pct", "mean"),
            cia3_pct=("cia3_pct", "mean"),
            end_sem=("end_sem", "mean"),
        )
        .reindex(order)
        .round(1)
    )

    if view_mode == "CIA % Compare":
        series_spec = [
            ("CIA 1 (%)", "cia1_pct", "#2563EB"),
            ("Mid-Sem CIA 2 (%)", "cia2_pct", "#E11D48"),
            ("CIA 3 Assignment (%)", "cia3_pct", "#F97316"),
            ("End-Sem (%)", "end_sem", "#10B981"),
        ]
        for label, col, color in series_spec:
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=labels,
                    y=agg[col],
                    marker=dict(color=color, cornerradius=6),
                )
            )
        fig.update_layout(
            barmode="group",
            legend=dict(orientation="h", y=1.14, x=0),
            yaxis_range=[0, 106],
        )
        return _apply_clean_axes(fig, y_title="Normalized Percentage (%)")

    # Default: Stacked weighted contribution adding up to 100
    stack_spec = [
        ("CIA 1 (/10)", "cia1_w", "#1D4ED8"),
        ("Mid-Sem CIA 2 (/25)", "cia2_w", "#2563EB"),
        ("CIA 3 (/10)", "cia3_w", "#F97316"),
        ("Attendance (/5)", "att_marks", "#F59E0B"),
        ("End-Sem (/50)", "ese_50", "#E11D48"),
    ]
    for label, col, color in stack_spec:
        fig.add_trace(
            go.Bar(
                name=label,
                x=labels,
                y=agg[col],
                marker=dict(color=color, cornerradius=4),
                hovertemplate=f"<b>%{{x}}</b><br>{label}: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="stack",
        legend=dict(orientation="h", y=1.15, x=0),
        yaxis_range=[0, 103],
    )
    return _apply_clean_axes(fig, y_title="Weighted Marks (/100)")


def cia_progression_area_chart(df: pd.DataFrame) -> go.Figure:
    """Smooth spline area chart with Solaris gradient fills across semester milestones."""
    fig = go.Figure()
    if df.empty:
        return _apply_clean_axes(fig)

    stages = ["CIA 1", "Mid-Sem (CIA 2)", "CIA 3 (Assign.)", "End-Sem Exam"]
    cols = ["cia1_pct", "cia2_pct", "cia3_pct", "end_sem"]

    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.20)"),
        "2MCA-B": ("#E11D48", "rgba(225, 29, 72, 0.14)"),
    }

    for sec in sorted(df["section"].unique()):
        sub = df[df["section"] == sec]
        means = [round(float(sub[c].mean()), 1) for c in cols]
        line_col, fill_col = palette_map.get(sec, ("#F97316", "rgba(249, 115, 22, 0.16)"))
        fig.add_trace(
            go.Scatter(
                name=sec,
                x=stages,
                y=means,
                mode="lines+markers+text",
                text=[f"{m:.1f}%" for m in means],
                textposition="top center",
                line=dict(color=line_col, width=3.2, shape="spline", smoothing=0.85),
                marker=dict(size=9, color=line_col, line=dict(width=2, color="#FFFFFF")),
                fill="tozeroy",
                fillcolor=fill_col,
                hovertemplate=f"<b>{sec}</b> · %{{x}}: %{{y:.1f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        legend=dict(orientation="h", y=1.14, x=0),
        yaxis_range=[48, 94],
    )
    return _apply_clean_axes(fig, y_title="Cohort Mean (%)")


def cohort_gpa_trend_chart(leaderboard_df: pd.DataFrame) -> go.Figure:
    """Cohort-wide Sem 1 SGPA -> Sem 2 SGPA -> Cumulative CGPA trend across 2MCA sections."""
    fig = go.Figure()
    if leaderboard_df.empty:
        return _apply_clean_axes(fig)

    stages = ["Sem 1 SGPA", "Sem 2 SGPA (Current)", "Cumulative CGPA"]
    cols = ["sem1_sgpa", "sem2_sgpa", "cgpa"]
    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.18)"),
        "2MCA-B": ("#F97316", "rgba(249, 115, 22, 0.16)"),
    }

    for sec in sorted(leaderboard_df["section"].unique()):
        sub = leaderboard_df[leaderboard_df["section"] == sec]
        means = [round(float(sub[c].mean()), 2) for c in cols]
        line_col, fill_col = palette_map.get(sec, ("#E11D48", "rgba(225, 29, 72, 0.14)"))
        fig.add_trace(
            go.Scatter(
                name=f"{sec} Mean",
                x=stages,
                y=means,
                mode="lines+markers+text",
                text=[f"{m:.2f}" for m in means],
                textposition="top center",
                line=dict(color=line_col, width=3.2, shape="spline", smoothing=0.75),
                marker=dict(size=9, color=line_col, line=dict(width=2, color="#FFFFFF")),
                fill="tozeroy",
                fillcolor=fill_col,
                hovertemplate=f"<b>{sec}</b> · %{{x}}: %{{y:.2f}} / 10<extra></extra>",
            )
        )

    fig.update_layout(
        legend=dict(orientation="h", y=1.14, x=0),
        yaxis_range=[6.0, 9.6],
    )
    return _apply_clean_axes(fig, y_title="Mean GPA (10-Point Scale)")


def grade_distribution_chart(df: pd.DataFrame, mode: str = "Donut") -> go.Figure:
    """Interactive Donut or Sunburst chart of CHRIST University letter grades."""
    if df.empty:
        return _apply_clean_axes(go.Figure())

    if mode == "Sunburst":
        sun_df = (
            df.groupby(["section", "grade"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        fig = px.sunburst(
            sun_df,
            path=["section", "grade"],
            values="count",
            color="grade",
            color_discrete_map={**GRADE_COLORS, "(?)": "#2563EB"},
        )
        fig.update_layout(**_BASE_LAYOUT)
        fig.update_traces(textinfo="label+percent parent")
        return fig

    counts = df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
    counts = counts[counts > 0]
    top_share = df["grade"].isin(["O", "A+", "A"]).mean() * 100.0 if len(df) else 0.0

    fig = go.Figure(
        go.Pie(
            labels=counts.index.tolist(),
            values=counts.values.tolist(),
            hole=0.66,
            sort=False,
            pull=[0.03 if g in ("O", "A+") else 0.0 for g in counts.index],
            marker=dict(
                colors=[GRADE_COLORS[g] for g in counts.index],
                line=dict(color="rgba(255,255,255,0.75)", width=2),
            ),
            textinfo="label+percent",
            hovertemplate="<b>Grade %{label}</b><br>%{value} records (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(
        **_BASE_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
        annotations=[
            dict(
                text=f"<b>{top_share:.0f}%</b><br><span style='font-size:11px'>Grade A & above</span>",
                x=0.5,
                y=0.5,
                font_size=16,
                showarrow=False,
            )
        ],
    )
    return fig


def student_radar_chart(student_df: pd.DataFrame, full_df: pd.DataFrame) -> go.Figure:
    """Interactive 6-axis Radar comparing Student vs Class Average vs Subject Topper."""
    fig = go.Figure()
    if student_df.empty:
        return fig

    order = [c for c in SUBJECT_CODES if c in student_df["subject_code"].values]
    categories = [str(SUBJECTS[c]["short"]) for c in order]

    stu_vals = student_df.set_index("subject_code").reindex(order)["total_score"].tolist()
    avg_vals = (
        full_df.groupby("subject_code")["total_score"]
        .mean()
        .reindex(order)
        .round(1)
        .tolist()
    )
    top_vals = (
        full_df.groupby("subject_code")["total_score"]
        .max()
        .reindex(order)
        .round(1)
        .tolist()
    )

    cat_closed = categories + [categories[0]]
    stu_closed = stu_vals + [stu_vals[0]]
    avg_closed = avg_vals + [avg_vals[0]]
    top_closed = top_vals + [top_vals[0]]

    fig.add_trace(
        go.Scatterpolar(
            r=top_closed,
            theta=cat_closed,
            name="Subject Topper",
            line=dict(color="#F59E0B", width=1.8, dash="dot"),
            fill="none",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=avg_closed,
            theta=cat_closed,
            name="Class Average",
            line=dict(color="#E11D48", width=2, dash="dash"),
            fill="toself",
            fillcolor="rgba(225, 29, 72, 0.08)",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=stu_closed,
            theta=cat_closed,
            name="Selected Student",
            line=dict(color="#2563EB", width=3.2),
            marker=dict(size=7, color="#2563EB"),
            fill="toself",
            fillcolor="rgba(37, 99, 235, 0.24)",
        )
    )

    fig.update_layout(
        **_BASE_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[25, 100],
                gridcolor="rgba(148, 163, 184, 0.22)",
                tickfont=dict(size=10),
            ),
            angularaxis=dict(gridcolor="rgba(148, 163, 184, 0.22)"),
        ),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    )
    return fig


def subject_box_with_student_chart(
    full_df: pd.DataFrame,
    student_df: pd.DataFrame,
    metric_col: str = "total_score",
    kind: str = "Box Plot",
) -> go.Figure:
    """Class score distribution (Box or Violin) with Coral-Gold diamond overlay markers."""
    fig = go.Figure()
    if full_df.empty:
        return _apply_clean_axes(fig)

    order = [c for c in SUBJECT_CODES if c in full_df["subject_code"].unique()]
    for i, code in enumerate(order):
        sub = full_df[full_df["subject_code"] == code]
        short = str(SUBJECTS[code]["short"])
        color = GRADIENT_SEQUENCE[i % len(GRADIENT_SEQUENCE)]
        if kind == "Violin Plot":
            fig.add_trace(
                go.Violin(
                    x=[short] * len(sub),
                    y=sub[metric_col],
                    name=short,
                    box_visible=True,
                    meanline_visible=True,
                    line_color=color,
                    fillcolor=color,
                    opacity=0.52,
                    showlegend=False,
                )
            )
        else:
            fig.add_trace(
                go.Box(
                    x=[short] * len(sub),
                    y=sub[metric_col],
                    name=short,
                    boxmean=True,
                    marker_color=color,
                    line=dict(width=1.8),
                    showlegend=False,
                )
            )

    if not student_df.empty:
        stu_ord = student_df.set_index("subject_code").reindex(order).dropna(subset=[metric_col])
        fig.add_trace(
            go.Scatter(
                x=[str(SUBJECTS[c]["short"]) for c in stu_ord.index],
                y=stu_ord[metric_col],
                mode="markers+lines",
                name="Selected Student",
                marker=dict(
                    symbol="diamond",
                    size=13,
                    color="#F97316",
                    line=dict(width=2.2, color="#FFFFFF"),
                ),
                line=dict(color="rgba(249, 115, 22, 0.65)", width=2, dash="dot"),
                hovertemplate="<b>%{x}</b><br>Student Score: %{y:.1f}<extra></extra>",
            )
        )

    y_label = "Internal Score (/50)" if metric_col == "internal_50" else "Composite Score (/100)"
    fig.update_layout(legend=dict(orientation="h", y=1.13, x=0))
    return _apply_clean_axes(fig, y_title=y_label)


def semester_gpa_trend_chart(
    sem1_sgpa: float,
    sem2_sgpa: float,
    projected_sem3: float,
    cohort_sem1_mean: float,
    cohort_sem2_mean: float,
) -> go.Figure:
    """SGPA & CGPA progression chart from Sem 1 to Sem 2 and Projected Sem 3."""
    sems = ["Sem 1 (Completed)", "Sem 2 (Current)", "Sem 3 (Target Plan)"]
    stu_sgpa = [sem1_sgpa, sem2_sgpa, projected_sem3]
    cgpa_curve = [
        sem1_sgpa,
        round((sem1_sgpa + sem2_sgpa) / 2.0, 2),
        round((sem1_sgpa + sem2_sgpa + projected_sem3) / 3.0, 2),
    ]
    cohort_curve = [
        round(cohort_sem1_mean, 2),
        round(cohort_sem2_mean, 2),
        round((cohort_sem1_mean + cohort_sem2_mean) / 2.0 + 0.15, 2),
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            name="Cohort Mean SGPA",
            x=sems,
            y=cohort_curve,
            mode="lines+markers",
            line=dict(color="#64748B", width=2, dash="dash"),
            marker=dict(size=6),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Cumulative CGPA",
            x=sems,
            y=cgpa_curve,
            mode="lines+markers",
            line=dict(color="#E11D48", width=2.6),
            marker=dict(size=8),
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Student SGPA",
            x=sems,
            y=stu_sgpa,
            mode="lines+markers+text",
            text=[f"{v:.2f}" for v in stu_sgpa],
            textposition="top center",
            line=dict(color="#2563EB", width=3.4, shape="spline"),
            marker=dict(size=10, color="#2563EB", line=dict(width=2, color="#FFFFFF")),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.14)",
        )
    )
    fig.update_layout(
        legend=dict(orientation="h", y=1.15, x=0),
        yaxis_range=[4.5, 10.3],
    )
    return _apply_clean_axes(fig, y_title="GPA (10-Point Scale)")


def predictor_feasibility_curve(
    internal_50: float,
    target_grade: str,
    ml_pred_ese: float,
    ml_lo: float,
    ml_hi: float,
) -> go.Figure:
    """Plot Final Course Score vs End-Sem Exam Score (/100) with grade bands & ML prediction."""
    ese_grid = np.linspace(0, 100, 101)
    final_scores = internal_50 + 0.5 * ese_grid

    fig = go.Figure()

    band_specs = [
        (90, 100, "O (90+)", "rgba(16, 185, 129, 0.11)"),
        (80, 90, "A+ (80-89)", "rgba(37, 99, 235, 0.10)"),
        (70, 80, "A (70-79)", "rgba(14, 165, 233, 0.08)"),
        (60, 70, "B+ (60-69)", "rgba(249, 115, 22, 0.08)"),
    ]
    for y0, y1, label, color in band_specs:
        fig.add_hrect(
            y0=y0,
            y1=y1,
            fillcolor=color,
            line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation_font_size=10,
        )

    fig.add_vrect(
        x0=ml_lo,
        x1=ml_hi,
        fillcolor="rgba(37, 99, 235, 0.11)",
        line_width=0,
        annotation_text="ML 90% Range",
        annotation_position="bottom right",
        annotation_font_size=10,
    )

    fig.add_vline(
        x=MIN_ESE_PASS_MARKS,
        line_dash="dot",
        line_color="#E11D48",
        annotation_text="Min Pass ESE (40)",
        annotation_position="bottom left",
        annotation_font_size=10,
    )

    fig.add_trace(
        go.Scatter(
            x=ese_grid,
            y=final_scores,
            mode="lines",
            name="Final Score Trajectory",
            line=dict(color="#2563EB", width=3.2),
            hovertemplate="End-Sem: %{x:.0f}/100<br>Final Total: %{y:.1f}/100<extra></extra>",
        )
    )

    ml_final = internal_50 + 0.5 * ml_pred_ese
    fig.add_trace(
        go.Scatter(
            x=[ml_pred_ese],
            y=[ml_final],
            mode="markers+text",
            name=f"ML Forecast ({ml_pred_ese:.1f})",
            text=[f"ML: {ml_pred_ese:.1f}"],
            textposition="bottom center",
            marker=dict(size=12, symbol="circle", color="#E11D48", line=dict(width=2, color="#FFFFFF")),
        )
    )

    cutoff = next(float(t["min_score"]) for t in GRADE_SCALE if t["grade"] == target_grade)
    req_ese = max(MIN_ESE_PASS_MARKS, (cutoff - internal_50) / 0.5)
    if req_ese <= 100.0 and internal_50 >= 20.0:
        fig.add_trace(
            go.Scatter(
                x=[req_ese],
                y=[internal_50 + 0.5 * req_ese],
                mode="markers+text",
                name=f"Required for {target_grade} ({req_ese:.1f})",
                text=[f"Target {target_grade}: {req_ese:.1f}/100"],
                textposition="top center",
                marker=dict(
                    size=14,
                    symbol="diamond",
                    color="#F97316",
                    line=dict(width=2, color="#FFFFFF"),
                ),
            )
        )

    fig.update_layout(
        legend=dict(orientation="h", y=1.14, x=0),
        yaxis_range=[max(20, internal_50 - 5), 103],
        xaxis_range=[0, 103],
    )
    return _apply_clean_axes(
        fig,
        y_title="Final Course Score (/100)",
        x_title="End-Semester Exam Marks (/100)",
    )


def ml_feature_importance_chart(imp_df: pd.DataFrame) -> go.Figure:
    """Horizontal Solaris gradient bar chart of scikit-learn feature importances."""
    fig = go.Figure(
        go.Bar(
            x=imp_df["Importance_Pct"],
            y=imp_df["Feature"],
            orientation="h",
            marker=dict(
                color=imp_df["Importance_Pct"],
                colorscale=[[0, "#FDBA74"], [0.45, "#F97316"], [0.78, "#E11D48"], [1.0, "#2563EB"]],
                cornerradius=7,
            ),
            text=imp_df["Importance_Pct"].map(lambda v: f"{v:.1f}%"),
            textposition="outside",
        )
    )
    fig.update_layout(xaxis_range=[0, max(float(imp_df["Importance_Pct"].max()) * 1.22, 25)])
    return _apply_clean_axes(fig, x_title="Relative Predictive Importance (%)")


def seaborn_statistical_figure(
    df: pd.DataFrame,
    mode: str = "Correlation Heatmap",
    is_dark: bool = False,
) -> plt.Figure:
    """Render a crisp, theme-aware Seaborn statistical plot in the Solaris palette."""
    text_col = "#E2E8F0" if is_dark else "#1E293B"
    muted_col = "#94A3B8" if is_dark else "#64748B"

    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(6.8, 4.1), dpi=150)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    cmap = LinearSegmentedColormap.from_list(
        "christgrade_solaris",
        ["#FDBA74", "#FFF7ED", "#93C5FD", "#2563EB", "#E11D48"]
        if not is_dark
        else ["#F97316", "#1E293B", "#2563EB", "#60A5FA", "#FB7185"],
    )

    if df.empty or len(df) < 3:
        ax.text(0.5, 0.5, "Not enough filtered records for statistical plot", ha="center", color=text_col)
        ax.axis("off")
        return fig

    if mode == "Correlation Heatmap":
        corr_cols = {
            "cia1_pct": "CIA 1 %",
            "cia2_pct": "Mid-Sem %",
            "cia3_pct": "CIA 3 %",
            "attendance": "Attendance %",
            "internal_50": "Internal /50",
            "end_sem": "End-Sem /100",
            "total_score": "Final /100",
        }
        corr = df[list(corr_cols.keys())].rename(columns=corr_cols).corr()
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(
            corr,
            mask=mask,
            cmap=cmap,
            vmin=-0.2,
            vmax=1.0,
            annot=True,
            fmt=".2f",
            linewidths=1.2,
            cbar_kws={"shrink": 0.78},
            annot_kws={"size": 8.5, "weight": "bold"},
            ax=ax,
        )
        ax.tick_params(colors=text_col, labelsize=8.5)
        plt.xticks(rotation=25, ha="right")
        plt.yticks(rotation=0)
        cbar = ax.collections[0].colorbar
        if cbar is not None:
            cbar.ax.yaxis.set_tick_params(color=muted_col, labelcolor=muted_col, labelsize=8)
    else:
        sns.kdeplot(
            data=df,
            x="internal_50",
            y="end_sem",
            fill=True,
            cmap="rocket_r" if not is_dark else "mako",
            alpha=0.72,
            levels=8,
            thresh=0.05,
            ax=ax,
        )
        sns.scatterplot(
            data=df,
            x="internal_50",
            y="end_sem",
            hue="section",
            palette={"2MCA-A": "#2563EB", "2MCA-B": "#F97316"},
            s=28,
            alpha=0.85,
            edgecolor="white",
            linewidth=0.45,
            ax=ax,
        )
        ax.set_xlabel("Internal CIA Total (/50)", color=text_col, fontsize=9.5, fontweight="bold")
        ax.set_ylabel("End-Semester Score (/100)", color=text_col, fontsize=9.5, fontweight="bold")
        ax.tick_params(colors=muted_col, labelsize=8.5)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(muted_col)
            ax.spines[spine].set_alpha(0.35)
        leg = ax.legend(title="Cohort", frameon=False, fontsize=8, title_fontsize=8.5)
        if leg:
            plt.setp(leg.get_texts(), color=text_col)
            plt.setp(leg.get_title(), color=text_col)

    fig.tight_layout()
    return fig


@st.cache_data(show_spinner=False, max_entries=24)
def render_seaborn_png_cached(
    plot_df: pd.DataFrame,
    mode: str,
    is_dark: bool,
) -> bytes:
    """Cache rasterized Seaborn statistical figure as crisp PNG bytes for <1ms repeat renders."""
    fig = seaborn_statistical_figure(plot_df, mode=mode, is_dark=is_dark)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=145, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return buf.getvalue()
