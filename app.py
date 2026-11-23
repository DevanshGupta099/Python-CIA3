"""ChristGrade: Real-Time CIA Academic Performance Analytics & End-Semester Predictor.

2MCA-A & B · Python Programming (MCA411-2) · Component 3 Smart Dashboard Application.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.advisor import open_insights_drawer
from utils.analytics import GlobalFilters, apply_global_filters, enrich_assessments
from utils.constants import (
    GRADE_ORDER,
    RISK_LEVELS,
    SECTIONS,
    SUBJECT_CODES,
    SUBJECT_LABELS,
)
from utils.database import init_database, load_raw_assessments
from utils.ui import inject_custom_css, render_footer

st.set_page_config(
    page_title="ChristGrade · Academic Performance BI",
    page_icon=":material/insights:",
    layout="wide",
)

is_dark = getattr(st.context.theme, "type", "light") == "dark"
inject_custom_css(is_dark=is_dark)
init_database(force_reset=False)

STATIC_DIR = Path(__file__).resolve().parent / "static"
logo_file = STATIC_DIR / ("logo-dark.svg" if is_dark else "logo-light.svg")
icon_file = STATIC_DIR / "icon.svg"
if logo_file.exists():
    st.logo(str(logo_file), icon_image=str(icon_file), size="large")

page = st.navigation(
    [
        st.Page(
            "views/overview.py",
            title="Overview",
            icon=":material/insights:",
            default=True,
        ),
        st.Page(
            "views/student_analytics.py",
            title="Student Radar",
            icon=":material/person_search:",
        ),
        st.Page(
            "views/predictor.py",
            title="Score Predictor",
            icon=":material/ads_click:",
        ),
        st.Page(
            "views/data_lab.py",
            title="Data Studio",
            icon=":material/science:",
        ),
        st.Page(
            "views/crud_manager.py",
            title="Marks & CRUD",
            icon=":material/edit_note:",
        ),
    ],
    position="top",
)


def reset_global_filters() -> None:
    st.session_state["cohort_seg"] = "All"
    st.session_state["flt_subjects"] = []
    st.session_state["flt_grades"] = []
    st.session_state["flt_risk"] = []
    st.session_state["flt_att_short"] = False


raw_df = load_raw_assessments()
full_df = enrich_assessments(raw_df)
st.session_state["full_df"] = full_df

# Shared top header + Insights assistant + URL-bound global filter toolbar
with st.container(horizontal=True, vertical_alignment="center"):
    with st.container(gap=None):
        st.title(page.title, icon=page.icon, anchor=False)
        filter_summary_slot = st.empty()
    st.badge("CHRIST 2MCA · Sem 2", icon=":material/school:", color="blue")
    st.button(
        "Reset",
        icon=":material/restart_alt:",
        type="tertiary",
        on_click=reset_global_filters,
        help="Reset cohort, subject, grade, and attendance filters",
    )
    ask_clicked = st.button(
        "Academic Insights",
        icon=":material/auto_awesome:",
        type="primary",
        help="Open live data-grounded Academic Insights assistant",
    )

if page.title in {"Overview", "Data Studio"}:
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        cohort_choice = st.segmented_control(
            "Cohort",
            ["All", *SECTIONS],
            default="All",
            required=True,
            key="cohort_seg",
            bind="query-params",
            label_visibility="collapsed",
        )
        with st.popover("Filter Subjects & Grades", icon=":material/tune:"):
            sel_subjects = st.pills(
                "MCA Subjects",
                list(SUBJECT_CODES),
                format_func=lambda c: SUBJECT_LABELS[c],
                selection_mode="multi",
                key="flt_subjects",
                bind="query-params",
                help="Leave empty to include all 6 subjects.",
            )
            sel_grades = st.pills(
                "Letter Grades",
                list(GRADE_ORDER),
                selection_mode="multi",
                key="flt_grades",
                bind="query-params",
                help="Filter assessments by CHRIST University grade tier.",
            )
            sel_risk = st.pills(
                "Academic Standing",
                list(RISK_LEVELS),
                selection_mode="multi",
                key="flt_risk",
                bind="query-params",
            )
            st.caption("Filters bind directly to URL query parameters for shareable views.")

        att_short = st.toggle(
            "Attendance < 85% Only",
            value=False,
            key="flt_att_short",
            bind="query-params",
            help="Highlight assessments below CHRIST University's 85% attendance eligibility.",
        )

    active_sections = SECTIONS if cohort_choice == "All" else (cohort_choice,)
    filters = GlobalFilters(
        sections=active_sections,
        subjects=tuple(sel_subjects) if sel_subjects else SUBJECT_CODES,
        grades=tuple(sel_grades) if sel_grades else GRADE_ORDER,
        risk_levels=tuple(sel_risk) if sel_risk else RISK_LEVELS,
        att_only_shortage=bool(att_short),
    )
    filtered_df = apply_global_filters(full_df, filters)
    st.session_state["global_filters"] = filters
    st.session_state["filtered_df"] = filtered_df
    filter_summary_slot.caption(
        filters.describe(
            total_rows=len(filtered_df),
            total_students=int(filtered_df["reg_no"].nunique()) if not filtered_df.empty else 0,
        )
    )
else:
    st.session_state["filtered_df"] = full_df
    filter_summary_slot.caption(
        f"Live SQLite database synced · **{full_df['reg_no'].nunique()}** MCA students · "
        f"**{len(full_df)}** subject CIA assessments"
    )

if ask_clicked:
    open_insights_drawer(st.session_state["filtered_df"])

page.run()
render_footer()
