"""Executive Cohort Overview: Fragment-isolated cards, KPI sparklines, row modal & cached Seaborn."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.advisor import open_student_drawer
from utils.analytics import build_student_leaderboard
from utils.charts import (
    cia_progression_area_chart,
    cohort_gpa_trend_chart,
    grade_distribution_chart,
    render_seaborn_png_cached,
    subject_cia_breakdown_chart,
)
from utils.constants import RISK_BADGES, RISK_LEVELS, SUBJECT_CODES
from utils.ui import card_header, render_hero_strip, section_header

full_df: pd.DataFrame = st.session_state["full_df"]
df: pd.DataFrame = st.session_state["filtered_df"]

render_hero_strip(
    eyebrow="CHRIST (Deemed to be University) · Department of Computer Science",
    title="ChristGrade: Real-Time 2MCA Academic Performance & CIA Intelligence",
    subtitle=(
        "Monitor CIA 1, Mid-Sem (CIA 2), CIA 3 Assignment, 85% Attendance compliance, and End-Semester "
        "trajectories across 2MCA-A & 2MCA-B with sub-50ms fragment updates."
    ),
    chips=[
        f"{df['reg_no'].nunique() if not df.empty else 0} Active Scholars",
        f"{len(df)} CIA Records",
        "22 Semester Credits",
        "Instant Fragment Rendering",
    ],
)

if df.empty:
    st.warning(
        "No assessment records match the active filter combination. Click **Reset** in the top bar.",
        icon=":material/filter_alt_off:",
    )
    st.stop()

actions = section_header(
    "Cohort Performance Snapshot",
    help_text="Certified real-time aggregates computed from the active filter selection.",
    definition_key="final_grade",
)
actions.badge("Live SQLite", icon=":material/database:", color="green")
actions.download_button(
    "Export CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="christgrade_filtered_assessments.csv",
    mime="text/csv",
    icon=":material/download:",
)

# ---------------------------------------------------------------------------
# Row 1: 4 Elevated Bento KPI Cards with Native Sparklines
# ---------------------------------------------------------------------------
subj_order = [c for c in SUBJECT_CODES if c in df["subject_code"].unique()]
subj_means = df.groupby("subject_code")["total_score"].mean().reindex(subj_order).fillna(0).tolist()
subj_int_means = df.groupby("subject_code")["internal_50"].mean().reindex(subj_order).fillna(0).tolist()
subj_pass_rates = (df.groupby("subject_code")["is_pass"].mean().reindex(subj_order).fillna(0) * 100).tolist()
subj_att_rates = (df.groupby("subject_code")["att_eligible"].mean().reindex(subj_order).fillna(0) * 100).tolist()

mean_score = float(df["total_score"].mean())
overall_mean = float(full_df["total_score"].mean())
mean_internal = float(df["internal_50"].mean())
pass_rate = float(df["is_pass"].mean() * 100.0)
top_grade_share = float(df["grade"].isin(["O", "A+"]).mean() * 100.0)
att_compliance = float(df["att_eligible"].mean() * 100.0)
shortage_cnt = int((~df["att_eligible"]).sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Mean Composite Score :blue[:material/verified:]",
    f"{mean_score:.1f} / 100",
    f"{mean_score - overall_mean:+.1f} pts vs cohort",
    chart_data=subj_means if len(subj_means) > 1 else None,
    chart_type="area",
    icon=":material/leaderboard:",
    border=True,
)
k2.metric(
    "Mean CIA Internal :blue[:material/verified:]",
    f"{mean_internal:.2f} / 50",
    f"{(mean_internal / 50.0) * 100:.1f}% internal avg",
    chart_data=subj_int_means if len(subj_int_means) > 1 else None,
    chart_type="bar",
    icon=":material/assignment_turned_in:",
    border=True,
)
k3.metric(
    "Course Pass Rate",
    f"{pass_rate:.1f}%",
    f"{top_grade_share:.1f}% in O / A+ tier",
    chart_data=subj_pass_rates if len(subj_pass_rates) > 1 else None,
    chart_type="line",
    icon=":material/workspace_premium:",
    border=True,
)
k4.metric(
    "85%+ Attendance Eligibility",
    f"{att_compliance:.1f}%",
    f"{shortage_cnt} shortage flags",
    delta_color="normal" if shortage_cnt == 0 else "inverse",
    chart_data=subj_att_rates if len(subj_att_rates) > 1 else None,
    chart_type="bar",
    icon=":material/event_available:",
    border=True,
)


# ---------------------------------------------------------------------------
# Row 2: Fragment-Isolated Subject Breakdown & Milestone Progression
# ---------------------------------------------------------------------------
@st.fragment
def _render_breakdown_section(active_df: pd.DataFrame) -> None:
    col_left, col_right = st.columns([3, 2])

    with col_left.container(border=True, height="stretch"):
        ctrl = card_header(
            "Subject-Wise Assessment Architecture",
            "Contribution of CIA 1, Mid-Sem CIA 2, CIA 3, Attendance & End-Sem",
            verified=True,
        )
        breakdown_view = ctrl.segmented_control(
            "Breakdown Mode",
            ["Stacked CIA", "CIA % Compare", "Section A vs B"],
            default="Stacked CIA",
            required=True,
            key="ov_breakdown_mode",
            label_visibility="collapsed",
        )
        st.plotly_chart(
            subject_cia_breakdown_chart(active_df, view_mode=breakdown_view),
            width="stretch",
            config={"displayModeBar": False},
        )

    with col_right.container(border=True, height="stretch"):
        r_ctrl = card_header(
            "Semester Trajectory & GPA Trend",
            "Switch between CIA milestone momentum and Sem 1 → Sem 2 GPA trend",
            verified=True,
        )
        traj_mode = r_ctrl.segmented_control(
            "Trajectory View",
            ["CIA Momentum", "Sem 1→2 GPA"],
            default="CIA Momentum",
            required=True,
            key="ov_traj_mode",
            label_visibility="collapsed",
        )
        if traj_mode == "CIA Momentum":
            st.plotly_chart(
                cia_progression_area_chart(active_df),
                width="stretch",
                config={"displayModeBar": False},
            )
        else:
            lb_sub = build_student_leaderboard(active_df)
            st.plotly_chart(
                cohort_gpa_trend_chart(lb_sub),
                width="stretch",
                config={"displayModeBar": False},
            )


_render_breakdown_section(df)

# ---------------------------------------------------------------------------
# Row 3: Fragment-Isolated Grade Mix & Leaderboard (with Sticky-Modal Fix!)
# ---------------------------------------------------------------------------
section_header(
    "Grade Distribution & Interactive Scholar Leaderboard",
    help_text="Select any student row in the table to open their profile modal & printable marksheet.",
    definition_key="cia_internal",
)


@st.fragment
def _render_leaderboard_section(active_df: pd.DataFrame, all_df: pd.DataFrame) -> None:
    g_col, t_col = st.columns([2, 3])

    with g_col.container(border=True, height="stretch"):
        g_ctrl = card_header(
            "CHRIST Grade Mix",
            "Distribution across O, A+, A, B+, B, C, P, and F tiers",
            verified=True,
        )
        chart_style = g_ctrl.segmented_control(
            "Grade Chart Style",
            ["Donut", "Sunburst"],
            default="Donut",
            required=True,
            key="ov_grade_style",
            label_visibility="collapsed",
        )
        st.plotly_chart(
            grade_distribution_chart(active_df, mode=chart_style),
            width="stretch",
            config={"displayModeBar": False},
        )

    with t_col.container(border=True, height="stretch"):
        l_ctrl = card_header(
            "Scholar SGPA Leaderboard (Select Row to Inspect)",
            "Click any row checkbox to launch Student Radar, Deep-Links & HTML Marksheet",
        )
        top_n = l_ctrl.segmented_control(
            "Rows",
            ["Top 15", "All"],
            default="Top 15",
            required=True,
            key="ov_top_n",
            label_visibility="collapsed",
        )

        leaderboard = build_student_leaderboard(active_df)
        if top_n == "Top 15":
            leaderboard = leaderboard.head(15)

        display_lb = leaderboard.copy()
        display_lb["standing_badge"] = display_lb["standing"].map(lambda s: [s])

        sel_event = st.dataframe(
            display_lb[
                [
                    "rank",
                    "reg_no",
                    "name",
                    "section",
                    "sem2_sgpa",
                    "cgpa",
                    "avg_internal_50",
                    "avg_attendance",
                    "trajectory",
                    "standing_badge",
                ]
            ],
            column_config={
                "rank": st.column_config.NumberColumn("#", format="%d", width="small"),
                "reg_no": st.column_config.TextColumn("Reg. No."),
                "name": st.column_config.TextColumn("Student Name"),
                "section": st.column_config.TextColumn("Cohort"),
                "sem2_sgpa": st.column_config.NumberColumn("Sem 2 SGPA", format="%.2f"),
                "cgpa": st.column_config.NumberColumn("CGPA", format="%.2f"),
                "avg_internal_50": st.column_config.ProgressColumn(
                    "Avg Internal (/50)",
                    min_value=0,
                    max_value=50,
                    format="%.1f",
                ),
                "avg_attendance": st.column_config.NumberColumn("Att. %", format="%.1f%%"),
                "trajectory": st.column_config.AreaChartColumn(
                    "CIA1→ESE Trend",
                    y_min=30,
                    y_max=100,
                    width="small",
                ),
                "standing_badge": st.column_config.MultiselectColumn(
                    "Standing",
                    options=list(RISK_LEVELS),
                    color=[RISK_BADGES[r] for r in RISK_LEVELS],
                ),
            },
            hide_index=True,
            height=355,
            width="stretch",
            on_select="rerun",
            selection_mode="single-row",
            key="ov_leaderboard_table",
        )

        rows_selected = (
            list(sel_event.selection.rows)
            if (sel_event and sel_event.selection and sel_event.selection.rows)
            else []
        )
        if rows_selected:
            clicked_idx = int(rows_selected[0])
            if 0 <= clicked_idx < len(display_lb):
                clicked_reg = str(display_lb.iloc[clicked_idx]["reg_no"])
                sig = (len(display_lb), clicked_idx, clicked_reg)
                # Open modal ONLY when the user freshly selects a row (prevents sticky re-open on unrelated clicks)
                if st.session_state.get("_last_lb_modal_sig") != sig:
                    st.session_state["_last_lb_modal_sig"] = sig
                    open_student_drawer(clicked_reg, all_df)
        else:
            st.session_state.pop("_last_lb_modal_sig", None)


_render_leaderboard_section(df, full_df)


# ---------------------------------------------------------------------------
# Row 4: Fragment-Isolated Cached Seaborn Plot & Subject Pass Audit
# ---------------------------------------------------------------------------
@st.fragment
def _render_statistical_section(active_df: pd.DataFrame) -> None:
    s_col1, s_col2 = st.columns([5, 5])

    with s_col1.container(border=True, height="stretch"):
        sb_ctrl = card_header(
            "Statistical Assessment Coupling (Seaborn)",
            "Pearson correlation matrix & bivariate kernel density of CIA vs End-Sem",
            verified=True,
        )
        sb_mode = sb_ctrl.segmented_control(
            "Seaborn Plot",
            ["Correlation Heatmap", "Internal vs ESE KDE"],
            default="Correlation Heatmap",
            required=True,
            key="ov_seaborn_mode",
            label_visibility="collapsed",
        )
        is_dark = getattr(st.context.theme, "type", "light") == "dark"
        sb_cols = [
            "section",
            "cia1_pct",
            "cia2_pct",
            "cia3_pct",
            "attendance",
            "internal_50",
            "end_sem",
            "total_score",
        ]
        png_bytes = render_seaborn_png_cached(active_df[sb_cols], sb_mode, is_dark)
        st.image(png_bytes, width="stretch")

    with s_col2.container(border=True, height="stretch"):
        card_header(
            "Subject Benchmark & Pass Audit",
            "Faculty lead, credit weight, internal mean, ESE mean, and 85% attendance compliance",
        )
        subj_audit = (
            active_df.groupby(["subject_code", "subject_short", "credits", "faculty"], as_index=False)
            .agg(
                avg_int=("internal_50", "mean"),
                avg_ese=("end_sem", "mean"),
                avg_tot=("total_score", "mean"),
                pass_pct=("is_pass", lambda s: float(s.mean() * 100.0)),
                att_ok_pct=("att_eligible", lambda s: float(s.mean() * 100.0)),
            )
            .round(1)
        )
        st.dataframe(
            subj_audit,
            column_config={
                "subject_code": st.column_config.TextColumn("Code"),
                "subject_short": st.column_config.TextColumn("Subject"),
                "credits": st.column_config.NumberColumn("Cr.", format="%d", width="small"),
                "faculty": st.column_config.TextColumn("Faculty"),
                "avg_int": st.column_config.NumberColumn("Int. (/50)", format="%.1f"),
                "avg_ese": st.column_config.NumberColumn("ESE (/100)", format="%.1f"),
                "avg_tot": st.column_config.ProgressColumn(
                    "Total (/100)", min_value=0, max_value=100, format="%.1f"
                ),
                "pass_pct": st.column_config.NumberColumn("Pass %", format="%.0f%%"),
                "att_ok_pct": st.column_config.NumberColumn("Att >=85%", format="%.0f%%"),
            },
            hide_index=True,
            height=350,
            width="stretch",
        )


_render_statistical_section(df)
