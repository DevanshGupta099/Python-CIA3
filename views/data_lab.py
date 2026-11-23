"""Data Manipulation Studio: Fragment-Isolated Graph Explorer, GroupBy, Pivot, Outliers & Policy Sim."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.analytics import (
    build_groupby_summary,
    build_pivot_matrix,
    compute_normalized_and_outliers,
    enrich_assessments,
)
from utils.charts import GRADIENT_SEQUENCE
from utils.constants import GRADE_COLORS, GRADE_ORDER
from utils.ui import card_header, render_hero_strip

base_df: pd.DataFrame = st.session_state["filtered_df"]

render_hero_strip(
    eyebrow="Pandas & NumPy Data Engineering Playground",
    title="Interactive Data Manipulation, Graph Explorer & Faculty Moderation Simulator",
    subtitle=(
        "Filter assessment ranges dynamically to manipulate 6 Plotly chart families, build multi-level "
        "GroupBy summaries, reshape Pivot/Cross-Tab matrices, detect Z-score outliers, and simulate moderation policies."
    ),
    chips=[
        "6 Dynamic Chart Types",
        "Multi-Metric GroupBy & IQR",
        "Pivot & Cross-Tab Heatmaps",
        "Instant Fragment Studio",
    ],
)

if base_df.empty:
    st.warning("No records match the active global filters. Click **Reset** above.")
    st.stop()

with st.container(border=True):
    card_header(
        "Live Data Slicers (Manipulates All Charts & Aggregations Below)",
        "Combine these numeric range sliders with the top Cohort/Subject/Grade filter bar",
    )
    f1, f2, f3, f4 = st.columns([1.4, 1.4, 1.4, 1.4])
    int_range = f1.slider("Internal CIA Range (/50)", 0.0, 50.0, (15.0, 50.0), 1.0)
    ese_range = f2.slider("End-Sem Score Range (/100)", 0.0, 100.0, (25.0, 100.0), 1.0)
    att_range = f3.slider("Attendance % Range", 60.0, 100.0, (70.0, 100.0), 1.0)
    sort_metric = f4.selectbox(
        "Primary Sort Metric",
        ["total_score", "internal_50", "end_sem", "attendance", "cia_momentum", "z_score"],
        format_func=lambda c: {
            "total_score": "Final Score (/100)",
            "internal_50": "Internal CIA (/50)",
            "end_sem": "End-Semester (/100)",
            "attendance": "Attendance (%)",
            "cia_momentum": "CIA1->CIA3 Momentum",
            "z_score": "Subject Z-Score",
        }[c],
    )

sliced_df = base_df[
    (base_df["internal_50"].between(int_range[0], int_range[1]))
    & (base_df["end_sem"].between(ese_range[0], ese_range[1]))
    & (base_df["attendance"].between(att_range[0], att_range[1]))
].sort_values(sort_metric, ascending=False)

st.caption(
    f"Active slice retains **{len(sliced_df)}** of **{len(base_df)}** records "
    f"(**{sliced_df['reg_no'].nunique()}** unique students)."
)

if sliced_df.empty:
    st.info("Widen the numeric sliders above to include assessment records.", icon=":material/tune:")
    st.stop()

METRIC_OPTIONS = {
    "internal_50": "Internal CIA (/50)",
    "end_sem": "End-Semester (/100)",
    "total_score": "Composite Score (/100)",
    "cia1_pct": "CIA 1 (%)",
    "cia2_pct": "Mid-Sem CIA 2 (%)",
    "cia3_pct": "CIA 3 Assignment (%)",
    "attendance": "Attendance (%)",
    "cia_momentum": "CIA Momentum (CIA3% - CIA1%)",
}

COLOR_DIMS = {
    "section": "Cohort Section",
    "grade": "CHRIST Letter Grade",
    "risk_status": "Academic Standing",
    "subject_short": "MCA Subject",
}


@st.fragment
def _frag_graph_explorer(df_in: pd.DataFrame) -> None:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.6, 1.3, 1.3, 1.3])
        chart_kind = c1.selectbox(
            "Visualization Type",
            [
                "Scatter + OLS Regression Line",
                "Box Quartile Comparison",
                "Violin Density Split",
                "Distribution Histogram",
                "Sunburst Hierarchy",
                "Horizontal Subject Ranking",
            ],
        )
        x_col = c2.selectbox(
            "X-Axis Metric",
            list(METRIC_OPTIONS.keys()),
            index=0,
            format_func=lambda k: METRIC_OPTIONS[k],
        )
        y_col = c3.selectbox(
            "Y-Axis Metric",
            list(METRIC_OPTIONS.keys()),
            index=1,
            format_func=lambda k: METRIC_OPTIONS[k],
        )
        color_dim = c4.selectbox(
            "Color / Group By",
            list(COLOR_DIMS.keys()),
            index=0,
            format_func=lambda k: COLOR_DIMS[k],
        )

        cmap = GRADE_COLORS if color_dim == "grade" else None

        if chart_kind == "Scatter + OLS Regression Line":
            fig = px.scatter(
                df_in,
                x=x_col,
                y=y_col,
                color=color_dim,
                size="credits",
                hover_name="name",
                hover_data=["reg_no", "subject_code", "grade"],
                color_discrete_sequence=GRADIENT_SEQUENCE,
                color_discrete_map=cmap,
                labels={**METRIC_OPTIONS, **COLOR_DIMS},
                opacity=0.84,
            )
            if len(df_in) >= 2 and df_in[x_col].nunique() > 1:
                xv = df_in[x_col].to_numpy(dtype=float)
                yv = df_in[y_col].to_numpy(dtype=float)
                slope, intercept = np.polyfit(xv, yv, 1)
                xs = np.linspace(float(xv.min()), float(xv.max()), 50)
                fig.add_trace(
                    go.Scatter(
                        x=xs,
                        y=slope * xs + intercept,
                        mode="lines",
                        name=f"Linear Fit (y = {slope:.2f}x + {intercept:.1f})",
                        line=dict(color="#E11D48", width=2.8, dash="dash"),
                    )
                )
        elif chart_kind == "Box Quartile Comparison":
            fig = px.box(
                df_in,
                x="subject_short",
                y=y_col,
                color=color_dim,
                points="outliers",
                color_discrete_sequence=GRADIENT_SEQUENCE,
                color_discrete_map=cmap,
                labels={"subject_short": "Subject", **METRIC_OPTIONS, **COLOR_DIMS},
            )
        elif chart_kind == "Violin Density Split":
            fig = px.violin(
                df_in,
                x="subject_short",
                y=y_col,
                color=color_dim,
                box=True,
                color_discrete_sequence=GRADIENT_SEQUENCE,
                color_discrete_map=cmap,
                labels={"subject_short": "Subject", **METRIC_OPTIONS, **COLOR_DIMS},
            )
        elif chart_kind == "Distribution Histogram":
            fig = px.histogram(
                df_in,
                x=x_col,
                color=color_dim,
                nbins=22,
                barmode="overlay",
                marginal="box",
                opacity=0.78,
                color_discrete_sequence=GRADIENT_SEQUENCE,
                color_discrete_map=cmap,
                labels={**METRIC_OPTIONS, **COLOR_DIMS},
            )
        elif chart_kind == "Sunburst Hierarchy":
            fig = px.sunburst(
                df_in,
                path=["section", "subject_short", "grade"],
                values="total_score",
                color="total_score",
                color_continuous_scale=[[0, "#F97316"], [0.5, "#E11D48"], [1, "#2563EB"]],
            )
        else:
            ranked = (
                df_in.groupby("subject_short", as_index=False)[y_col]
                .mean()
                .sort_values(y_col, ascending=True)
                .round(2)
            )
            fig = px.bar(
                ranked,
                x=y_col,
                y="subject_short",
                orientation="h",
                text=y_col,
                color=y_col,
                color_continuous_scale=[[0, "#FDBA74"], [0.5, "#E11D48"], [1, "#2563EB"]],
                labels={"subject_short": "Subject", **METRIC_OPTIONS},
            )
            fig.update_traces(marker_cornerradius=7, textposition="outside")

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=12, t=28, b=8),
            height=410,
            transition=dict(duration=360, easing="cubic-in-out"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


@st.fragment
def _frag_groupby(df_in: pd.DataFrame) -> None:
    with st.container(border=True):
        card_header(
            "Pandas Multi-Column GroupBy & Dispersion Statistics",
            "Computes Count, Mean, Median, Std Dev, NumPy IQR, Min, Max & Pass %",
        )
        group_dims = st.multiselect(
            "Group By Dimensions",
            options=["section", "subject_code", "subject_short", "grade", "risk_status"],
            default=["section", "subject_short"],
        )
        if not group_dims:
            st.info("Select at least one grouping column.")
        else:
            grp_df = build_groupby_summary(df_in, group_dims)
            st.dataframe(grp_df, hide_index=True, width="stretch")
            st.download_button(
                "Download GroupBy Summary CSV",
                data=grp_df.to_csv(index=False).encode("utf-8"),
                file_name="christgrade_groupby_summary.csv",
                mime="text/csv",
                icon=":material/download:",
            )


@st.fragment
def _frag_pivot(df_in: pd.DataFrame) -> None:
    with st.container(border=True):
        card_header(
            "Dynamic Pivot Table & Cross-Tabulation Matrix",
            "Reshape multi-dimensional academic records and inspect cell intensity via heatmap",
        )
        p1, p2, p3, p4 = st.columns(4)
        idx_col = p1.selectbox("Row Index", ["subject_short", "section", "risk_status", "grade"], index=0)
        col_col = p2.selectbox("Column Header", ["section", "grade", "risk_status", "subject_short"], index=1)
        val_col = p3.selectbox(
            "Cell Value Metric",
            list(METRIC_OPTIONS.keys()),
            index=2,
            format_func=lambda k: METRIC_OPTIONS[k],
        )
        agg_fn = p4.selectbox(
            "Aggregation Function",
            ["Mean", "Median", "Max", "Min", "Std Dev", "Count (Cross-Tab)"],
            index=0,
        )

        if idx_col == col_col:
            st.warning("Choose distinct Row Index and Column Header fields to pivot.")
        else:
            piv_df = build_pivot_matrix(df_in, idx_col, col_col, val_col, agg_fn)
            pv_left, pv_right = st.columns([3, 2])
            with pv_left:
                st.dataframe(piv_df, width="stretch")
            with pv_right:
                core = piv_df.iloc[:-1, :-1] if len(piv_df) > 1 and piv_df.shape[1] > 1 else piv_df
                fig_hm = px.imshow(
                    core,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale=[[0, "#EFF6FF"], [0.55, "#3B82F6"], [1, "#E11D48"]],
                )
                fig_hm.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=4, r=4, t=16, b=4),
                    height=290,
                    coloraxis_showscale=False,
                    transition=dict(duration=340, easing="cubic-in-out"),
                )
                st.plotly_chart(fig_hm, width="stretch", config={"displayModeBar": False})


@st.fragment
def _frag_outliers(df_in: pd.DataFrame) -> None:
    with st.container(border=True):
        card_header(
            "Feature Scaling (Min-Max & Z-Score) and 1.5×IQR Outlier Slicer",
            "Standardizes raw marks onto [0, 1] and standard normal N(0, 1) scales",
        )
        nc1, nc2 = st.columns([1.6, 2.4])
        norm_metric = nc1.selectbox(
            "Target Metric to Normalize",
            list(METRIC_OPTIONS.keys()),
            index=2,
            format_func=lambda k: METRIC_OPTIONS[k],
        )
        slice_mode = nc2.segmented_control(
            "Record Slice",
            ["All Records", "IQR Outliers Only", "Top 10% Decile", "Bottom 10% Decile"],
            default="All Records",
            required=True,
        )

        norm_df = compute_normalized_and_outliers(df_in, norm_metric)
        if slice_mode == "IQR Outliers Only":
            norm_df = norm_df[norm_df["iqr_outlier"] != "Normal Range"]
        elif slice_mode == "Top 10% Decile":
            norm_df = norm_df[norm_df["percentile_rank"] >= 90.0]
        elif slice_mode == "Bottom 10% Decile":
            norm_df = norm_df[norm_df["percentile_rank"] <= 10.0]

        st.dataframe(
            norm_df,
            column_config={
                "reg_no": st.column_config.TextColumn("Reg. No."),
                "name": st.column_config.TextColumn("Student"),
                "section": st.column_config.TextColumn("Section"),
                "subject_code": st.column_config.TextColumn("Code"),
                "subject_short": st.column_config.TextColumn("Subject"),
                norm_metric: st.column_config.NumberColumn(METRIC_OPTIONS[norm_metric], format="%.2f"),
                "min_max_scaled": st.column_config.ProgressColumn(
                    "Min-Max [0–1]", min_value=0.0, max_value=1.0, format="%.3f"
                ),
                "z_score_global": st.column_config.NumberColumn("Z-Score (σ)", format="%+.2f"),
                "percentile_rank": st.column_config.NumberColumn("Percentile", format="%.1f%%"),
                "iqr_outlier": st.column_config.TextColumn("IQR Diagnostic"),
            },
            hide_index=True,
            height=340,
            width="stretch",
        )


@st.fragment
def _frag_policy_sim(df_in: pd.DataFrame) -> None:
    with st.container(border=True):
        card_header(
            "Faculty Moderation & Condonation What-If Policy Simulator",
            "Simulate cohort-wide CIA3 bonus marks, End-Sem moderation, or medical attendance condonation",
            verified=True,
        )
        s1, s2, s3 = st.columns(3)
        cia3_bonus = s1.slider("CIA 3 Moderation Bonus (+Marks /20)", 0.0, 5.0, 1.5, 0.5)
        ese_curve = s2.slider("End-Sem Scaling Curve (+Marks /100)", 0.0, 10.0, 3.0, 1.0)
        att_boost = s3.slider("Medical Attendance Condonation (+%)", 0.0, 8.0, 2.0, 0.5)

        raw_cols = [
            "assessment_id", "reg_no", "name", "section", "email", "sem1_sgpa",
            "subject_code", "semester", "cia1", "cia2", "cia3", "attendance",
            "end_sem", "updated_at", "subject_name", "subject_short", "credits", "faculty",
        ]
        sim_raw = df_in[raw_cols].copy()
        sim_raw["cia3"] = np.clip(sim_raw["cia3"] + cia3_bonus, 0.0, 20.0)
        sim_raw["end_sem"] = np.clip(sim_raw["end_sem"] + ese_curve, 0.0, 100.0)
        sim_raw["attendance"] = np.clip(sim_raw["attendance"] + att_boost, 0.0, 100.0)
        sim_df = enrich_assessments(sim_raw)

        m1, m2, m3, m4 = st.columns(4)
        base_mean, new_mean = float(df_in["total_score"].mean()), float(sim_df["total_score"].mean())
        base_pass, new_pass = float(df_in["is_pass"].mean() * 100), float(sim_df["is_pass"].mean() * 100)
        base_oa, new_oa = int(df_in["grade"].isin(["O", "A+"]).sum()), int(sim_df["grade"].isin(["O", "A+"]).sum())
        base_att, new_att = float(df_in["att_eligible"].mean() * 100), float(sim_df["att_eligible"].mean() * 100)

        m1.metric("Simulated Mean Score", f"{new_mean:.1f} / 100", f"{new_mean - base_mean:+.1f} pts", border=True)
        m2.metric("Simulated Pass Rate", f"{new_pass:.1f}%", f"{new_pass - base_pass:+.1f}%", border=True)
        m3.metric("O & A+ Grade Count", f"{new_oa} records", f"{new_oa - base_oa:+d} records", border=True)
        m4.metric("85%+ Attendance Eligible", f"{new_att:.1f}%", f"{new_att - base_att:+.1f}%", border=True)

        before_counts = df_in["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
        after_counts = sim_df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)

        fig_sim = go.Figure(
            data=[
                go.Bar(name="Baseline Cohort", x=list(GRADE_ORDER), y=before_counts.values, marker=dict(color="#64748B", cornerradius=6)),
                go.Bar(name="After Policy Simulation", x=list(GRADE_ORDER), y=after_counts.values, marker=dict(color="#2563EB", cornerradius=6)),
            ]
        )
        fig_sim.update_layout(
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=12, t=30, b=8),
            height=300,
            legend=dict(orientation="h", y=1.14, x=0),
            transition=dict(duration=360, easing="cubic-in-out"),
        )
        st.plotly_chart(fig_sim, width="stretch", config={"displayModeBar": False})


tab_viz, tab_group, tab_pivot, tab_norm, tab_sim = st.tabs(
    [
        ":material/bar_chart: Interactive Graph Explorer",
        ":material/functions: GroupBy & Aggregations",
        ":material/grid_on: Pivot & Cross-Tab Builder",
        ":material/analytics: Z-Scores & Outlier Detection",
        ":material/tune: Faculty Policy Simulator",
    ]
)

with tab_viz:
    _frag_graph_explorer(sliced_df)
with tab_group:
    _frag_groupby(sliced_df)
with tab_pivot:
    _frag_pivot(sliced_df)
with tab_norm:
    _frag_outliers(sliced_df)
with tab_sim:
    _frag_policy_sim(sliced_df)
