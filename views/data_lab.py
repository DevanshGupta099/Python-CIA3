"""Data Manipulation Studio: Editorial Layout, Lazy Single-Module Execution & 60fps Explorer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.analytics import (
    build_groupby_summary,
    build_pivot_matrix,
    compute_normalized_and_outliers,
    enrich_assessments,
)
from utils.charts import (
    echarts_explorer_chart,
    echarts_pivot_heatmap,
    echarts_policy_sim,
    render_echarts,
)
from utils.constants import GRADE_ORDER
from utils.ui import card_header, render_page_header

base_df: pd.DataFrame = st.session_state["filtered_df"]
is_dark = getattr(st.context.theme, "type", "light") == "dark"

render_page_header(
    title="Data Studio & Policy Simulator",
    subtitle="Slice numeric ranges, explore multi-dimensional GroupBy and Pivot matrices, inspect Z-score outliers, and model moderation curves.",
    meta_summary=f"{len(base_df)} Filtered Assessments",
)

_toolbar_fn = st.session_state.get("_render_global_filter_toolbar")
if callable(_toolbar_fn):
    _toolbar_fn()

if base_df.empty:
    st.warning("No records match the active global filters. Click **Reset** in the top bar.")
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

STUDIO_MODULES = [
    "Graph Explorer",
    "GroupBy & Dispersion",
    "Pivot & Cross-Tab",
    "Z-Scores & Outliers",
    "Policy Simulator",
]


@st.fragment
def _render_data_studio(df_source: pd.DataFrame, dark_mode: bool) -> None:
    with st.container(border=True):
        card_header(
            "Numeric Range Slicers",
            "Filter internal, End-Semester, and attendance intervals dynamically across all studio modules",
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

    sliced_df = df_source[
        (df_source["internal_50"].between(int_range[0], int_range[1]))
        & (df_source["end_sem"].between(ese_range[0], ese_range[1]))
        & (df_source["attendance"].between(att_range[0], att_range[1]))
    ].sort_values(sort_metric, ascending=False)

    if sliced_df.empty:
        st.info("Widen the numeric sliders above to include assessment records.", icon=":material/tune:")
        return

    with st.container(horizontal=True, vertical_alignment="center"):
        active_mod = st.segmented_control(
            "Studio Module",
            STUDIO_MODULES,
            default="Graph Explorer",
            required=True,
            key="ds_active_module",
            label_visibility="collapsed",
        )
        st.caption(
            f"Retaining **{len(sliced_df)}** of **{len(df_source)}** assessments "
            f"(**{sliced_df['reg_no'].nunique()}** students)"
        )

    if active_mod == "Graph Explorer":
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
                key="ds_chart_kind",
            )
            x_col = c2.selectbox(
                "X-Axis Metric",
                list(METRIC_OPTIONS.keys()),
                index=0,
                format_func=lambda k: METRIC_OPTIONS[k],
                key="ds_x_col",
            )
            y_col = c3.selectbox(
                "Y-Axis Metric",
                list(METRIC_OPTIONS.keys()),
                index=1,
                format_func=lambda k: METRIC_OPTIONS[k],
                key="ds_y_col",
            )
            color_dim = c4.selectbox(
                "Color / Group By",
                list(COLOR_DIMS.keys()),
                index=0,
                format_func=lambda k: COLOR_DIMS[k],
                key="ds_color_dim",
            )

            render_echarts(
                echarts_explorer_chart(
                    sliced_df,
                    chart_kind=chart_kind,
                    x_col=x_col,
                    y_col=y_col,
                    color_dim=color_dim,
                    metric_labels=METRIC_OPTIONS,
                    is_dark=dark_mode,
                ),
                height=410,
                key="ds_explorer_chart",
                alt=f"Data Studio {chart_kind} chart",
            )

    elif active_mod == "GroupBy & Dispersion":
        with st.container(border=True):
            card_header(
                "Multi-Column GroupBy & Dispersion Summary",
                "Count, Mean, Median, Std Dev, NumPy IQR, Min, Max & Pass Rate",
            )
            group_dims = st.multiselect(
                "Group By Dimensions",
                options=["section", "subject_code", "subject_short", "grade", "risk_status"],
                default=["section", "subject_short"],
                key="ds_group_dims",
            )
            if not group_dims:
                st.info("Select at least one grouping column.")
            else:
                grp_df = build_groupby_summary(sliced_df, group_dims)
                st.dataframe(grp_df, hide_index=True, width="stretch")
                st.download_button(
                    "Export GroupBy CSV",
                    data=grp_df.to_csv(index=False).encode("utf-8"),
                    file_name="christgrade_groupby_summary.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )

    elif active_mod == "Pivot & Cross-Tab":
        with st.container(border=True):
            card_header(
                "Dynamic Pivot & Cross-Tabulation Matrix",
                "Reshape multi-dimensional academic records with synchronized cell intensity heatmap",
            )
            p1, p2, p3, p4 = st.columns(4)
            idx_col = p1.selectbox("Row Index", ["subject_short", "section", "risk_status", "grade"], index=0, key="ds_piv_idx")
            col_col = p2.selectbox("Column Header", ["section", "grade", "risk_status", "subject_short"], index=1, key="ds_piv_col")
            val_col = p3.selectbox(
                "Cell Value Metric",
                list(METRIC_OPTIONS.keys()),
                index=2,
                format_func=lambda k: METRIC_OPTIONS[k],
                key="ds_piv_val",
            )
            agg_fn = p4.selectbox(
                "Aggregation Function",
                ["Mean", "Median", "Max", "Min", "Std Dev", "Count (Cross-Tab)"],
                index=0,
                key="ds_piv_agg",
            )

            if idx_col == col_col:
                st.warning("Choose distinct Row Index and Column Header fields to pivot.")
            else:
                piv_df = build_pivot_matrix(sliced_df, idx_col, col_col, val_col, agg_fn)
                pv_left, pv_right = st.columns([3, 2])
                with pv_left:
                    st.dataframe(piv_df, width="stretch")
                with pv_right:
                    core = piv_df.iloc[:-1, :-1] if len(piv_df) > 1 and piv_df.shape[1] > 1 else piv_df
                    render_echarts(
                        echarts_pivot_heatmap(core, is_dark=dark_mode),
                        height=300,
                        key="ds_pivot_heatmap",
                        alt=f"Pivot heatmap of {val_col} by {idx_col} and {col_col}",
                    )

    elif active_mod == "Z-Scores & Outliers":
        with st.container(border=True):
            card_header(
                "Feature Scaling & 1.5×IQR Outlier Slicer",
                "Min-Max [0, 1] normalization, Z-score standardization, and interquartile outlier detection",
            )
            nc1, nc2 = st.columns([1.6, 2.4])
            norm_metric = nc1.selectbox(
                "Target Metric to Normalize",
                list(METRIC_OPTIONS.keys()),
                index=2,
                format_func=lambda k: METRIC_OPTIONS[k],
                key="ds_norm_metric",
            )
            slice_mode = nc2.segmented_control(
                "Record Slice",
                ["All Records", "IQR Outliers Only", "Top 10% Decile", "Bottom 10% Decile"],
                default="All Records",
                required=True,
                key="ds_norm_slice",
            )

            norm_df = compute_normalized_and_outliers(sliced_df, norm_metric)
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
                height=345,
                width="stretch",
            )

    else:
        with st.container(border=True):
            card_header(
                "Faculty Moderation & Condonation Simulator",
                "Model cohort-wide CIA 3 bonus marks, End-Sem curve adjustments, and medical attendance condonation",
            )
            s1, s2, s3 = st.columns(3)
            cia3_bonus = s1.slider("CIA 3 Moderation Bonus (+Marks /20)", 0.0, 5.0, 1.5, 0.5, key="ds_sim_c3")
            ese_curve = s2.slider("End-Sem Scaling Curve (+Marks /100)", 0.0, 10.0, 3.0, 1.0, key="ds_sim_ese")
            att_boost = s3.slider("Medical Attendance Condonation (+%)", 0.0, 8.0, 2.0, 0.5, key="ds_sim_att")

            raw_cols = [
                "assessment_id", "reg_no", "name", "section", "email", "sem1_sgpa",
                "subject_code", "semester", "cia1", "cia2", "cia3", "attendance",
                "end_sem", "updated_at", "subject_name", "subject_short", "credits", "faculty",
            ]
            sim_raw = sliced_df[raw_cols].copy()
            sim_raw["cia3"] = np.clip(sim_raw["cia3"] + cia3_bonus, 0.0, 20.0)
            sim_raw["end_sem"] = np.clip(sim_raw["end_sem"] + ese_curve, 0.0, 100.0)
            sim_raw["attendance"] = np.clip(sim_raw["attendance"] + att_boost, 0.0, 100.0)
            sim_df = enrich_assessments(sim_raw)

            m1, m2, m3, m4 = st.columns(4)
            base_mean, new_mean = float(sliced_df["total_score"].mean()), float(sim_df["total_score"].mean())
            base_pass, new_pass = float(sliced_df["is_pass"].mean() * 100), float(sim_df["is_pass"].mean() * 100)
            base_oa, new_oa = int(sliced_df["grade"].isin(["O", "A+"]).sum()), int(sim_df["grade"].isin(["O", "A+"]).sum())
            base_att, new_att = float(sliced_df["att_eligible"].mean() * 100), float(sim_df["att_eligible"].mean() * 100)

            m1.metric("Simulated Mean Score", f"{new_mean:.1f} / 100", f"{new_mean - base_mean:+.1f} pts", border=True)
            m2.metric("Simulated Pass Rate", f"{new_pass:.1f}%", f"{new_pass - base_pass:+.1f}%", border=True)
            m3.metric("O & A+ Grade Count", f"{new_oa} records", f"{new_oa - base_oa:+d} records", border=True)
            m4.metric("85%+ Attendance Eligible", f"{new_att:.1f}%", f"{new_att - base_att:+.1f}%", border=True)

            before_counts = sliced_df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
            after_counts = sim_df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)

            render_echarts(
                echarts_policy_sim(before_counts, after_counts, is_dark=dark_mode),
                height=310,
                key="ds_policy_sim_chart",
                alt="Grade distribution before and after policy moderation simulation",
            )


_render_data_studio(base_df, is_dark)
