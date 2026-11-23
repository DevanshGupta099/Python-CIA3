"""End-Semester Target Score & CGPA Predictor (Formula Engine + scikit-learn ML)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.analytics import (
    attendance_to_marks,
    build_student_leaderboard,
    calculate_target_ese_table,
    predict_ese_score,
    recommend_sgpa_plan,
    train_ml_ese_predictor,
)
from utils.charts import ml_feature_importance_chart, predictor_feasibility_curve
from utils.constants import (
    GRADE_BADGES,
    GRADE_ORDER,
    GRADE_SCALE,
    MIN_ATTENDANCE_ELIGIBILITY,
    MIN_ESE_PASS_MARKS,
    SUBJECT_CODES,
    SUBJECT_LABELS,
    SUBJECTS,
    TARGET_GRADES,
)
from utils.ui import card_header, render_hero_strip, section_header

full_df: pd.DataFrame = st.session_state["full_df"]
leaderboard = build_student_leaderboard(full_df)


@st.cache_resource(show_spinner=False)
def _get_trained_bundle(row_count: int, checksum: float):
    return train_ml_ese_predictor(st.session_state["full_df"])


ml_bundle = _get_trained_bundle(len(full_df), round(float(full_df["total_score"].sum()), 2))

render_hero_strip(
    eyebrow="Predictive Academic Calculator · CHRIST 10-Point Grading + scikit-learn",
    title="End-Semester Target Score & Semester CGPA Planner",
    subtitle=(
        "Compute the exact End-Semester Exam marks (/100) required for O, A+, A, or target SGPA/CGPA, "
        "paired with cross-validated Ridge & Random Forest regression forecasts."
    ),
    chips=[
        f"5-Fold CV R² = {ml_bundle.r2_cv:.2f}",
        f"MAE = ±{ml_bundle.mae_cv:.1f} pts",
        "Ridge + Random Forest Ensemble",
        "22-Credit SGPA Optimizer",
    ],
)

mode = st.segmented_control(
    "Predictor Mode",
    ["Subject Target Grade Predictor", "Semester SGPA & CGPA Planner"],
    default="Subject Target Grade Predictor",
    required=True,
    key="pred_main_mode",
    label_visibility="collapsed",
)

if mode == "Subject Target Grade Predictor":
    actions = section_header(
        "Subject End-Sem Score Calculator & ML Forecast",
        help_text="Syncs from an existing student record or custom live sliders.",
        definition_key="target_predictor",
    )
    actions.badge(
        f"CV R² = {ml_bundle.r2_cv:.2f} · MAE = ±{ml_bundle.mae_cv:.1f} pts",
        icon=":material/psychology:",
        color="blue",
    )

    with st.container(border=True):
        top_c1, top_c2, top_c3, top_c4 = st.columns([1.4, 2.3, 1.8, 1.5], vertical_alignment="bottom")
        input_source = top_c1.segmented_control(
            "Source",
            ["Student Record", "Custom Input"],
            default="Student Record",
            required=True,
            key="pred_input_src",
        )

        stu_labels = {
            r.reg_no: f"{r.reg_no} · {r.name} ({r.section})"
            for r in leaderboard.itertuples(index=False)
        }

        if input_source == "Student Record":
            sel_reg = top_c2.selectbox(
                "Student",
                options=leaderboard["reg_no"].tolist(),
                format_func=lambda r: stu_labels.get(r, r),
                key="pred_stu_reg",
            )
            sel_sub = top_c3.selectbox(
                "MCA Subject",
                options=list(SUBJECT_CODES),
                format_func=lambda c: SUBJECT_LABELS[c],
                key="pred_sub_code",
            )
            target_grade = top_c4.selectbox(
                "Target Grade",
                options=list(TARGET_GRADES),
                index=1,
                key="pred_target_grade",
            )

            rec = full_df[
                (full_df["reg_no"] == sel_reg) & (full_df["subject_code"] == sel_sub)
            ]
            if not rec.empty:
                r0 = rec.iloc[0]
                def_cia1, def_cia2, def_cia3 = float(r0["cia1"]), float(r0["cia2"]), float(r0["cia3"])
                def_att, def_sem1 = float(r0["attendance"]), float(r0["sem1_sgpa"])
            else:
                def_cia1, def_cia2, def_cia3, def_att, def_sem1 = 15.0, 36.0, 16.0, 90.0, 7.8
        else:
            sel_sub = top_c2.selectbox(
                "MCA Subject",
                options=list(SUBJECT_CODES),
                format_func=lambda c: SUBJECT_LABELS[c],
                key="pred_custom_sub",
            )
            target_grade = top_c3.selectbox(
                "Target Grade",
                options=list(TARGET_GRADES),
                index=0,
                key="pred_custom_grade",
            )
            def_sem1 = top_c4.number_input(
                "Sem 1 SGPA", min_value=4.0, max_value=10.0, value=8.0, step=0.1
            )
            def_cia1, def_cia2, def_cia3, def_att = 16.0, 38.0, 17.0, 91.0

        st.divider()
        s1, s2, s3, s4, s5 = st.columns([1, 1, 1, 1, 1.3])
        cia1_val = s1.slider("CIA 1 (/20)", 0.0, 20.0, float(def_cia1), 0.5)
        cia2_val = s2.slider("Mid-Sem CIA 2 (/50)", 0.0, 50.0, float(def_cia2), 0.5)
        cia3_val = s3.slider("CIA 3 Assign. (/20)", 0.0, 20.0, float(def_cia3), 0.5)
        att_val = s4.slider("Attendance (%)", 50.0, 100.0, float(def_att), 0.5)
        model_choice = s5.selectbox(
            "ML Estimator",
            [
                "Ensemble (Ridge + Random Forest)",
                "Ridge Linear Regression",
                "Random Forest Regressor",
            ],
            key="pred_ml_algo",
        )

    att_marks = float(attendance_to_marks(att_val))
    internal_50 = round(0.5 * cia1_val + 0.5 * cia2_val + 0.5 * cia3_val + att_marks, 2)
    credits = int(SUBJECTS[sel_sub]["credits"])

    cutoff = next(float(t["min_score"]) for t in GRADE_SCALE if t["grade"] == target_grade)
    raw_req_ese = (cutoff - internal_50) / 0.5
    req_ese = max(MIN_ESE_PASS_MARKS, raw_req_ese)
    is_possible = (internal_50 >= 20.0) and (req_ese <= 100.0)

    ml_pred, ml_lo, ml_hi = predict_ese_score(
        ml_bundle,
        cia1=cia1_val,
        cia2=cia2_val,
        cia3=cia3_val,
        attendance=att_val,
        sem1_sgpa=def_sem1,
        credits=credits,
        model_choice=model_choice,
    )
    ml_final = round(internal_50 + 0.5 * ml_pred, 1)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Current Internal Total",
        f"{internal_50:.2f} / 50",
        f"Att. Marks: {att_marks:.0f}/5 ({att_val:.1f}%)",
        delta_color="normal" if att_val >= MIN_ATTENDANCE_ELIGIBILITY else "inverse",
        icon=":material/fact_check:",
        border=True,
    )
    k2.metric(
        f"Required ESE for Grade {target_grade}",
        f"{req_ese:.1f} / 100" if is_possible else "Capped (>100)",
        f"Target >= {cutoff:.0f}/100 final" if is_possible else f"Max possible: {internal_50 + 50:.1f}/100",
        delta_color="normal" if is_possible else "inverse",
        icon=":material/ads_click:",
        border=True,
    )
    k3.metric(
        "ML Predicted End-Sem",
        f"{ml_pred:.1f} / 100",
        f"90% CI: [{ml_lo:.0f} – {ml_hi:.0f}]",
        icon=":material/auto_graph:",
        border=True,
    )
    gap = round(ml_pred - req_ese, 1)
    k4.metric(
        "Projected Final Score",
        f"{ml_final:.1f} / 100",
        f"{gap:+.1f} pts vs {target_grade} requirement" if is_possible else "Upgrade CIA to unlock tier",
        delta_color="normal" if (is_possible and gap >= 0) else "inverse",
        icon=":material/insights:",
        border=True,
    )

    if att_val < MIN_ATTENDANCE_ELIGIBILITY:
        st.warning(
            f"**Attendance Alert ({att_val:.1f}%):** CHRIST University mandates a minimum **85%** attendance "
            "for End-Semester Exam hall ticket eligibility (80–84.9% requires medical condonation).",
            icon=":material/warning:",
        )
    elif not is_possible:
        max_final = internal_50 + 50.0
        best_possible = next(
            (str(t["grade"]) for t in GRADE_SCALE if max_final >= float(t["min_score"]) and internal_50 >= 20),
            "F",
        )
        st.error(
            f"With **{internal_50:.2f}/50** internal marks, scoring 100/100 on End-Sem yields **{max_final:.1f}/100**. "
            f"Grade **{target_grade}** ({cutoff:.0f}+) is mathematically out of reach — highest achievable grade is **{best_possible}**.",
            icon=":material/block:",
        )

    c_curve, c_table = st.columns([3, 2])
    with c_curve.container(border=True, height="stretch"):
        card_header(
            "End-Sem Feasibility & Grade Band Curve",
            "Final score trajectory across ESE 0–100 with ML confidence band & target pin",
            verified=True,
        )
        st.plotly_chart(
            predictor_feasibility_curve(internal_50, target_grade, ml_pred, ml_lo, ml_hi),
            width="stretch",
            config={"displayModeBar": False},
        )

    with c_table.container(border=True, height="stretch"):
        card_header(
            "Exact Grade Cutoff Matrix",
            f"Required End-Sem marks (/100) for every CHRIST grade in {sel_sub}",
        )
        target_tbl = calculate_target_ese_table(internal_50, att_val)
        st.dataframe(
            target_tbl[
                [
                    "Target Grade",
                    "Grade Point",
                    "Min Final (/100)",
                    "Required End-Sem (/100)",
                    "Assessment",
                ]
            ],
            column_config={
                "Target Grade": st.column_config.TextColumn("Grade", width="small"),
                "Grade Point": st.column_config.NumberColumn("GP", format="%.1f", width="small"),
                "Min Final (/100)": st.column_config.NumberColumn("Cutoff", format="%.0f"),
                "Required End-Sem (/100)": st.column_config.ProgressColumn(
                    "Req. ESE (/100)", min_value=0, max_value=100, format="%.1f"
                ),
                "Assessment": st.column_config.TextColumn("Feasibility"),
            },
            hide_index=True,
            height=295,
            width="stretch",
        )

    with st.container(border=True):
        card_header(
            "scikit-learn Feature Importance Profile",
            "Relative contribution of CIA components, Attendance, and Sem 1 SGPA in predicting End-Sem scores",
        )
        st.plotly_chart(
            ml_feature_importance_chart(ml_bundle.feature_importance),
            width="stretch",
            config={"displayModeBar": False},
        )

else:
    actions = section_header(
        "Credit-Weighted Semester SGPA & CGPA Planner",
        help_text="Allocates optimal End-Sem target scores across all 6 subjects (22 credits).",
    )

    with st.container(border=True):
        p1, p2, p3 = st.columns([2.4, 1.5, 1.5], vertical_alignment="bottom")
        stu_labels = {
            r.reg_no: f"{r.reg_no} · {r.name} ({r.section} · Sem 1 SGPA: {r.sem1_sgpa:.2f})"
            for r in leaderboard.itertuples(index=False)
        }
        plan_reg = p1.selectbox(
            "Select Student",
            options=leaderboard["reg_no"].tolist(),
            format_func=lambda r: stu_labels.get(r, r),
            key="sgpa_plan_reg",
        )
        stu_info = leaderboard[leaderboard["reg_no"] == plan_reg].iloc[0]
        goal_type = p2.segmented_control(
            "Target Type",
            ["Target Sem 2 SGPA", "Target Cumulative CGPA"],
            default="Target Sem 2 SGPA",
            required=True,
            key="sgpa_goal_kind",
        )
        if goal_type == "Target Sem 2 SGPA":
            desired_sgpa = p3.slider("Desired Sem 2 SGPA", 5.5, 10.0, 8.5, 0.1)
        else:
            desired_cgpa = p3.slider("Desired Cumulative CGPA", 5.5, 9.8, 8.5, 0.1)
            desired_sgpa = float(min(10.0, max(5.0, 2.0 * desired_cgpa - float(stu_info["sem1_sgpa"]))))

    stu_df = full_df[full_df["reg_no"] == plan_reg].copy()
    roadmap = recommend_sgpa_plan(stu_df, desired_sgpa)
    achieved_sgpa = float(
        (roadmap["Target GP"] * roadmap["credits"]).sum() / roadmap["credits"].sum()
    )
    projected_cgpa = round((float(stu_info["sem1_sgpa"]) + achieved_sgpa) / 2.0, 2)

    actions.download_button(
        "Export Action Plan CSV",
        data=roadmap.to_csv(index=False).encode("utf-8"),
        file_name=f"ChristGrade_SGPA_Plan_{plan_reg}.csv",
        mime="text/csv",
        icon=":material/download:",
    )

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Sem 1 Baseline SGPA", f"{stu_info['sem1_sgpa']:.2f}", "Completed", icon=":material/history:", border=True)
    g2.metric(
        "Required Sem 2 SGPA",
        f"{desired_sgpa:.2f}",
        f"Plan delivers {achieved_sgpa:.2f} SGPA",
        delta_color="normal" if achieved_sgpa + 0.01 >= desired_sgpa else "inverse",
        icon=":material/flag:",
        border=True,
    )
    g3.metric(
        "Resulting Cumulative CGPA",
        f"{projected_cgpa:.2f} / 10",
        f"{projected_cgpa - float(stu_info['sem1_sgpa']):+.2f} vs Sem 1",
        icon=":material/workspace_premium:",
        border=True,
    )
    g4.metric(
        "Mean Required End-Sem",
        f"{roadmap['Required End-Sem (/100)'].mean():.1f} / 100",
        "Across 22 total credits",
        icon=":material/calculate:",
        border=True,
    )

    with st.container(border=True):
        card_header(
            "Recommended Subject-by-Subject End-Sem Action Plan",
            "Prioritizes higher-credit subjects with strong CIA internals to minimize exam strain",
            verified=True,
        )
        disp_plan = roadmap.copy()
        disp_plan["grade_badge"] = disp_plan["Recommended Grade"].map(lambda g: [g])
        st.dataframe(
            disp_plan[
                [
                    "subject_code",
                    "subject_name",
                    "credits",
                    "internal_50",
                    "attendance",
                    "grade_badge",
                    "Target GP",
                    "Required End-Sem (/100)",
                    "Effort Band",
                ]
            ],
            column_config={
                "subject_code": st.column_config.TextColumn("Code"),
                "subject_name": st.column_config.TextColumn("Subject Name"),
                "credits": st.column_config.NumberColumn("Credits", format="%d"),
                "internal_50": st.column_config.NumberColumn("Current Internal (/50)", format="%.2f"),
                "attendance": st.column_config.NumberColumn("Attendance %", format="%.1f%%"),
                "grade_badge": st.column_config.MultiselectColumn(
                    "Target Grade",
                    options=list(GRADE_ORDER),
                    color=[GRADE_BADGES[g] for g in GRADE_ORDER],
                ),
                "Target GP": st.column_config.NumberColumn("Grade Pt.", format="%.1f"),
                "Required End-Sem (/100)": st.column_config.ProgressColumn(
                    "Required End-Sem (/100)", min_value=0, max_value=100, format="%.1f"
                ),
                "Effort Band": st.column_config.TextColumn("Preparation Intensity"),
            },
            hide_index=True,
            width="stretch",
        )
