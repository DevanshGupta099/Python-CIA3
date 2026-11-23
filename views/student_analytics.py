"""Student Deep-Dive: Fragment-accelerated Radar, Box/Violin Standing, Printable Marksheet & GPA Trend."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.advisor import generate_student_html_report
from utils.analytics import build_student_leaderboard, enrich_assessments
from utils.charts import (
    semester_gpa_trend_chart,
    student_radar_chart,
    subject_box_with_student_chart,
)
from utils.constants import GRADE_BADGES, GRADE_ORDER, RISK_BADGES, SECTIONS
from utils.ui import card_header, render_hero_strip

full_df: pd.DataFrame = st.session_state["full_df"]
leaderboard: pd.DataFrame = st.session_state["full_leaderboard"]

# Handle incoming deep-link from Overview's Student Modal
jumped_reg = st.session_state.pop("_jump_stu_reg", None)
if jumped_reg:
    st.session_state["stu_sec_pick"] = "All"
    st.session_state["stu_selected_reg"] = jumped_reg

render_hero_strip(
    eyebrow="Individual Academic Diagnostics & Live What-If Sandbox",
    title="Student Standing vs. Class Average · Radar, Box Plots & Printable Marksheet",
    subtitle=(
        "Inspect any 2MCA scholar's 6-subject polygon against cohort benchmarks, toggle Live What-If "
        "marks in session memory, jump straight to Target Score Predictor, or export an HTML Progress Card."
    ),
    chips=[
        "6-Axis Radar Comparison",
        "Instant Fragment Quartiles",
        "Live Session-State Sandbox",
        "Printable HTML Marksheet",
    ],
)

with st.container(border=True):
    c_sec, c_stu, c_sandbox = st.columns([1.3, 3.2, 1.5], vertical_alignment="bottom")
    sec_filter = c_sec.segmented_control(
        "Section",
        ["All", *SECTIONS],
        default="All",
        required=True,
        key="stu_sec_pick",
    )
    stu_pool = (
        leaderboard
        if sec_filter == "All"
        else leaderboard[leaderboard["section"] == sec_filter]
    )
    stu_options = stu_pool["reg_no"].tolist()
    if st.session_state.get("stu_selected_reg") not in stu_options and stu_options:
        st.session_state["stu_selected_reg"] = stu_options[0]

    stu_labels = {
        r.reg_no: f"{r.reg_no} · {r.name} ({r.section} · SGPA {r.sem2_sgpa:.2f})"
        for r in stu_pool.itertuples(index=False)
    }

    selected_reg = c_stu.selectbox(
        "Search Student by Register Number or Name",
        options=stu_options,
        format_func=lambda r: stu_labels.get(r, r),
        key="stu_selected_reg",
    )
    sandbox_mode = c_sandbox.toggle(
        "Live What-If Marks",
        value=False,
        key="stu_whatif_toggle",
        help="Temporarily tweak this student's CIA scores in st.session_state without overwriting SQLite.",
    )

student_rows = full_df[full_df["reg_no"] == selected_reg].copy()
stu_meta = leaderboard[leaderboard["reg_no"] == selected_reg].iloc[0]

if sandbox_mode:
    with st.container(border=True):
        card_header(
            "Real-Time Session Sandbox (What-If CIA Simulator)",
            "Adjust CIA 1, Mid-Sem CIA 2, CIA 3, Attendance, or End-Sem below — charts update instantaneously!",
        )
        editable_cols = ["subject_code", "subject_short", "cia1", "cia2", "cia3", "attendance", "end_sem"]
        sandbox_edit = st.data_editor(
            student_rows[editable_cols],
            column_config={
                "subject_code": st.column_config.TextColumn("Code", disabled=True),
                "subject_short": st.column_config.TextColumn("Subject", disabled=True),
                "cia1": st.column_config.NumberColumn("CIA 1 (/20)", min_value=0.0, max_value=20.0, step=0.5),
                "cia2": st.column_config.NumberColumn("Mid-Sem (/50)", min_value=0.0, max_value=50.0, step=0.5),
                "cia3": st.column_config.NumberColumn("CIA 3 (/20)", min_value=0.0, max_value=20.0, step=0.5),
                "attendance": st.column_config.NumberColumn("Attendance %", min_value=0.0, max_value=100.0, step=0.5),
                "end_sem": st.column_config.NumberColumn("End-Sem (/100)", min_value=0.0, max_value=100.0, step=1.0),
            },
            hide_index=True,
            width="stretch",
            key=f"sandbox_editor_{selected_reg}",
        )
        for col in ("cia1", "cia2", "cia3", "attendance", "end_sem"):
            student_rows[col] = sandbox_edit[col].to_numpy()

        raw_cols = [
            "assessment_id", "reg_no", "name", "section", "email", "sem1_sgpa",
            "subject_code", "semester", "cia1", "cia2", "cia3", "attendance",
            "end_sem", "updated_at", "subject_name", "subject_short", "credits", "faculty",
        ]
        merged_raw = pd.concat(
            [full_df.loc[full_df["reg_no"] != selected_reg, raw_cols], student_rows[raw_cols]],
            ignore_index=True,
        )
        re_enriched = enrich_assessments(merged_raw)
        student_rows = re_enriched[re_enriched["reg_no"] == selected_reg].copy()
        stu_meta = build_student_leaderboard(re_enriched).query("reg_no == @selected_reg").iloc[0]

# ---------------------------------------------------------------------------
# Student Header Badges, Deep-Link to Predictor & Printable Marksheet
# ---------------------------------------------------------------------------
with st.container(horizontal=True, vertical_alignment="center"):
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.subheader(f"{stu_meta['name']} ({selected_reg})", anchor=False)
        st.badge(str(stu_meta["section"]), icon=":material/groups:", color="blue")
        st.badge(
            str(stu_meta["standing"]),
            icon=":material/verified_user:",
            color=RISK_BADGES.get(str(stu_meta["standing"]), "blue"),
        )
        st.badge(f"Cohort Rank #{int(stu_meta['rank'])} of {len(leaderboard)}", icon=":material/emoji_events:", color="orange")
        if sandbox_mode:
            st.badge("Sandbox Mode Active", icon=":material/science:", color="red")

    with st.container(horizontal=True, horizontal_alignment="right", width="content"):
        if st.button("Predict End-Sem Targets", icon=":material/ads_click:"):
            st.session_state["_jump_pred_reg"] = selected_reg
            st.switch_page("views/predictor.py")
        st.download_button(
            "Download HTML Marksheet",
            data=generate_student_html_report(student_rows, stu_meta),
            file_name=f"ChristGrade_Marksheet_{selected_reg}.html",
            mime="text/html",
            type="primary",
            icon=":material/download:",
        )

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Sem 2 SGPA",
    f"{stu_meta['sem2_sgpa']:.2f}",
    f"{stu_meta['sgpa_delta']:+.2f} vs Sem 1 ({stu_meta['sem1_sgpa']:.2f})",
    icon=":material/school:",
    border=True,
)
m2.metric(
    "Cumulative CGPA",
    f"{stu_meta['cgpa']:.2f} / 10",
    f"Avg Score: {stu_meta['avg_total_100']:.1f}/100",
    icon=":material/workspace_premium:",
    border=True,
)
m3.metric(
    "Mean Internal CIA",
    f"{stu_meta['avg_internal_50']:.2f} / 50",
    f"{(stu_meta['avg_internal_50'] / 50.0) * 100:.1f}% internal",
    icon=":material/assignment:",
    border=True,
)
m4.metric(
    "Mean Attendance",
    f"{stu_meta['avg_attendance']:.1f}%",
    "Eligible (>=85%)" if int(stu_meta["shortage_subjects"]) == 0 else f"{int(stu_meta['shortage_subjects'])} subject(s) <85%",
    delta_color="normal" if int(stu_meta["shortage_subjects"]) == 0 else "inverse",
    icon=":material/event_available:",
    border=True,
)

weak_subjects = student_rows[
    (student_rows["score_vs_avg"] < -3.0)
    | (student_rows["internal_50"] < 30.0)
    | (~student_rows["att_eligible"])
]
strong_subjects = student_rows[student_rows["score_vs_avg"] >= 5.0]

if not weak_subjects.empty:
    items = []
    for r in weak_subjects.itertuples(index=False):
        reasons = []
        if r.score_vs_avg < -3.0:
            reasons.append(f"{r.score_vs_avg:+.1f} pts below class avg")
        if r.internal_50 < 30.0:
            reasons.append(f"Internal {r.internal_50:.1f}/50")
        if not r.att_eligible:
            reasons.append(f"Attendance {r.attendance:.1f}% (<85%)")
        items.append(f"**{r.subject_code} ({r.subject_short})**: {', '.join(reasons)}")
    st.warning(
        "**Priority Focus Subjects Identified:** " + "  ·  ".join(items),
        icon=":material/troubleshoot:",
    )
else:
    st.success(
        f"**All 6 subjects are on or above cohort benchmark!** Strongest lead in "
        f"{', '.join(strong_subjects['subject_short'].tolist()) or 'consistent performance across subjects'}.",
        icon=":material/check_circle:",
    )


# ---------------------------------------------------------------------------
# Fragment-Isolated Radar + Box/Violin Standing Plot
# ---------------------------------------------------------------------------
@st.fragment
def _render_radar_and_quartiles(stu_df: pd.DataFrame, cohort_df: pd.DataFrame) -> None:
    r_col, b_col = st.columns([2, 3])

    with r_col.container(border=True, height="stretch"):
        card_header(
            "Multi-Subject Radar Profile",
            "Selected student polygon vs. Class Average & Subject Topper",
            verified=True,
        )
        st.plotly_chart(
            student_radar_chart(stu_df, cohort_df),
            width="stretch",
            config={"displayModeBar": False},
        )

    with b_col.container(border=True, height="stretch"):
        b_ctrl = card_header(
            "Standing Across Cohort Quartiles",
            "Coral diamonds pinpoint the student inside each subject's distribution",
            verified=True,
        )
        dist_metric = b_ctrl.segmented_control(
            "Metric",
            ["Total (/100)", "Internal (/50)"],
            default="Total (/100)",
            required=True,
            key="stu_dist_metric",
            label_visibility="collapsed",
        )
        dist_kind = b_ctrl.segmented_control(
            "Plot",
            ["Box Plot", "Violin Plot"],
            default="Box Plot",
            required=True,
            key="stu_dist_kind",
            label_visibility="collapsed",
        )
        st.plotly_chart(
            subject_box_with_student_chart(
                cohort_df,
                stu_df,
                metric_col="internal_50" if dist_metric == "Internal (/50)" else "total_score",
                kind=dist_kind,
            ),
            width="stretch",
            config={"displayModeBar": False},
        )


_render_radar_and_quartiles(student_rows, full_df)


# ---------------------------------------------------------------------------
# Fragment-Isolated Semester GPA Trajectory + Subject Transcript
# ---------------------------------------------------------------------------
@st.fragment
def _render_gpa_and_transcript(
    stu_df: pd.DataFrame,
    meta: pd.Series,
    c_sem1_mean: float,
    c_sem2_mean: float,
) -> None:
    t_col1, t_col2 = st.columns([2, 3])

    with t_col1.container(border=True, height="stretch"):
        t_ctrl = card_header(
            "Semester SGPA & CGPA Trajectory",
            "Historical Sem 1 -> Current Sem 2 -> Target Sem 3 projection",
        )
        target_sem3 = t_ctrl.slider(
            "Sem 3 Goal",
            min_value=6.0,
            max_value=10.0,
            value=min(10.0, round(float(meta["sem2_sgpa"]) + 0.4, 1)),
            step=0.1,
            key=f"stu_sem3_goal_{meta['reg_no']}",
            label_visibility="collapsed",
        )
        st.plotly_chart(
            semester_gpa_trend_chart(
                sem1_sgpa=float(meta["sem1_sgpa"]),
                sem2_sgpa=float(meta["sem2_sgpa"]),
                projected_sem3=float(target_sem3),
                cohort_sem1_mean=c_sem1_mean,
                cohort_sem2_mean=c_sem2_mean,
            ),
            width="stretch",
            config={"displayModeBar": False},
        )

    with t_col2.container(border=True, height="stretch"):
        card_header(
            "Subject-by-Subject CIA Transcript",
            "Detailed breakdown with class delta, Z-score, and percentile standing",
        )
        transcript = stu_df.copy()
        transcript["grade_badge"] = transcript["grade"].map(lambda g: [g])
        st.dataframe(
            transcript[
                [
                    "subject_code",
                    "subject_short",
                    "credits",
                    "cia1",
                    "cia2",
                    "cia3",
                    "attendance",
                    "internal_50",
                    "end_sem",
                    "total_score",
                    "score_vs_avg",
                    "percentile",
                    "grade_badge",
                ]
            ],
            column_config={
                "subject_code": st.column_config.TextColumn("Code"),
                "subject_short": st.column_config.TextColumn("Subject"),
                "credits": st.column_config.NumberColumn("Cr.", format="%d", width="small"),
                "cia1": st.column_config.NumberColumn("CIA 1 (/20)", format="%.1f"),
                "cia2": st.column_config.NumberColumn("CIA 2 (/50)", format="%.1f"),
                "cia3": st.column_config.NumberColumn("CIA 3 (/20)", format="%.1f"),
                "attendance": st.column_config.NumberColumn("Att. %", format="%.1f%%"),
                "internal_50": st.column_config.NumberColumn("Int. (/50)", format="%.2f"),
                "end_sem": st.column_config.NumberColumn("ESE (/100)", format="%.1f"),
                "total_score": st.column_config.ProgressColumn(
                    "Final (/100)", min_value=0, max_value=100, format="%.1f"
                ),
                "score_vs_avg": st.column_config.NumberColumn("vs Avg", format="%+.1f"),
                "percentile": st.column_config.NumberColumn("Pct. Rank", format="%.0f%%"),
                "grade_badge": st.column_config.MultiselectColumn(
                    "Grade",
                    options=list(GRADE_ORDER),
                    color=[GRADE_BADGES[g] for g in GRADE_ORDER],
                ),
            },
            hide_index=True,
            height=315,
            width="stretch",
        )


_render_gpa_and_transcript(
    student_rows,
    stu_meta,
    float(leaderboard["sem1_sgpa"].mean()),
    float(leaderboard["sem2_sgpa"].mean()),
)
