"""ChristGrade: Real-Time CIA Academic Performance Analytics & End-Semester Predictor.

2MCA-A & B · Python Programming (MCA411-2) · Component 3 Smart Dashboard Application.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
import time

import streamlit as st

# Throttled hot-reload check (runs at most once every 3s so clicks pay 0 filesystem syscalls)
_APP_ROOT = Path(__file__).resolve().parent
_NOW_MONO = time.monotonic()
if _NOW_MONO - float(getattr(sys, "_cg_last_mtime_check", 0.0)) > 3.0:
    setattr(sys, "_cg_last_mtime_check", _NOW_MONO)
    _SAVED_MTIMES: dict[str, float] = getattr(sys, "_cg_module_mtimes", {})
    _UTILS_ORDER = (
        "utils.constants",
        "utils.validators",
        "utils.database",
        "utils.analytics",
        "utils.ui",
        "utils.charts",
        "utils.advisor",
    )
    _reload_needed = False
    for _mname in _UTILS_ORDER:
        _mpath = _APP_ROOT / (_mname.replace(".", "/") + ".py")
        if _mpath.exists():
            _mt = _mpath.stat().st_mtime
            if _SAVED_MTIMES.get(_mname) != _mt:
                _SAVED_MTIMES[_mname] = _mt
                _reload_needed = True
    if _reload_needed:
        for _mname in _UTILS_ORDER:
            if _mname in sys.modules:
                importlib.reload(sys.modules[_mname])
        setattr(sys, "_cg_module_mtimes", _SAVED_MTIMES)

from utils.advisor import open_insights_drawer
from utils.analytics import GlobalFilters, get_filtered_bundle_cached, load_enriched_cached
from utils.constants import (
    GRADE_ORDER,
    RISK_LEVELS,
    SECTIONS,
    SUBJECT_CODES,
    SUBJECT_LABELS,
)
from utils.database import get_db_version, init_database
from utils.ui import inject_custom_css, render_brand_lockup, render_footer

STATIC_DIR = _APP_ROOT / "static"
icon_file = STATIC_DIR / "icon.svg"

st.set_page_config(
    page_title="ChristGrade · Academic Performance BI",
    page_icon=str(icon_file) if icon_file.exists() else ":material/insights:",
    layout="wide",
)

if not st.session_state.get("_db_initialized"):
    init_database(force_reset=False)
    st.session_state["_db_initialized"] = True

is_dark = getattr(st.context.theme, "type", "light") == "dark"

PAGES = [
    st.Page(
        "views/overview.py",
        title="Overview",
        icon=":material/space_dashboard:",
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
        icon=":material/track_changes:",
    ),
    st.Page(
        "views/data_lab.py",
        title="Data Studio",
        icon=":material/tune:",
    ),
    st.Page(
        "views/crud_manager.py",
        title="Marks & CRUD",
        icon=":material/edit_note:",
    ),
]

page = st.navigation(PAGES, position="hidden")
inject_custom_css(is_dark=is_dark, page_title=page.title)

pending_jump = st.session_state.pop("_pending_page_jump", None)
if pending_jump:
    st.switch_page(pending_jump)


def _hydrate_filters_from_url_once() -> None:
    """Hydrate initial session filter memory from URL query parameters on first load."""
    if st.session_state.get("_url_hydrated"):
        return
    st.session_state["_url_hydrated"] = True
    qp = st.query_params

    q_cohort = qp.get("cohort", "All")
    st.session_state["_saved_cohort"] = q_cohort if q_cohort in ("All", *SECTIONS) else "All"

    raw_subs = [s for s in qp.get_all("sub") if s in SUBJECT_CODES]
    st.session_state["_saved_subjects"] = raw_subs

    raw_grades = [g for g in qp.get_all("grade") if g in GRADE_ORDER]
    st.session_state["_saved_grades"] = raw_grades

    raw_risk = [r for r in qp.get_all("risk") if r in RISK_LEVELS]
    st.session_state["_saved_risk"] = raw_risk

    st.session_state["_saved_att_short"] = qp.get("att_short", "0") in ("1", "true", "True")


_hydrate_filters_from_url_once()


def _write_query_params_from_saved() -> None:
    """Mirror saved filter state into shareable URL query parameters."""
    cohort = st.session_state.get("_saved_cohort", "All")
    subs = list(st.session_state.get("_saved_subjects", []))
    grades = list(st.session_state.get("_saved_grades", []))
    risks = list(st.session_state.get("_saved_risk", []))
    att_short = bool(st.session_state.get("_saved_att_short", False))

    new_params: dict[str, str | list[str]] = {}
    if cohort != "All":
        new_params["cohort"] = cohort
    if subs:
        new_params["sub"] = subs
    if grades:
        new_params["grade"] = grades
    if risks:
        new_params["risk"] = risks
    if att_short:
        new_params["att_short"] = "1"

    st.query_params.clear()
    for k, v in new_params.items():
        st.query_params[k] = v


def _sync_saved_filters() -> None:
    st.session_state["_saved_cohort"] = st.session_state.get("cohort_seg", "All")
    st.session_state["_saved_subjects"] = list(st.session_state.get("flt_subjects", []))
    st.session_state["_saved_grades"] = list(st.session_state.get("flt_grades", []))
    st.session_state["_saved_risk"] = list(st.session_state.get("flt_risk", []))
    st.session_state["_saved_att_short"] = bool(st.session_state.get("flt_att_short", False))
    _write_query_params_from_saved()


def reset_global_filters() -> None:
    st.session_state["cohort_seg"] = "All"
    st.session_state["flt_subjects"] = []
    st.session_state["flt_grades"] = []
    st.session_state["flt_risk"] = []
    st.session_state["flt_att_short"] = False
    st.session_state["_saved_cohort"] = "All"
    st.session_state["_saved_subjects"] = []
    st.session_state["_saved_grades"] = []
    st.session_state["_saved_risk"] = []
    st.session_state["_saved_att_short"] = False
    st.query_params.clear()


db_ver = get_db_version()
full_df, full_leaderboard = load_enriched_cached(db_ver)
st.session_state["full_df"] = full_df
st.session_state["full_leaderboard"] = full_leaderboard

is_filterable_page = page.title in {"Overview", "Data Studio"}
has_custom_filters = False
if is_filterable_page:
    if "cohort_seg" not in st.session_state:
        st.session_state["cohort_seg"] = st.session_state["_saved_cohort"]
    if "flt_subjects" not in st.session_state:
        st.session_state["flt_subjects"] = list(st.session_state["_saved_subjects"])
    if "flt_grades" not in st.session_state:
        st.session_state["flt_grades"] = list(st.session_state["_saved_grades"])
    if "flt_risk" not in st.session_state:
        st.session_state["flt_risk"] = list(st.session_state["_saved_risk"])
    if "flt_att_short" not in st.session_state:
        st.session_state["flt_att_short"] = bool(st.session_state["_saved_att_short"])

    cur_cohort = st.session_state["cohort_seg"]
    cur_subs = list(st.session_state["flt_subjects"])
    cur_grades = list(st.session_state["flt_grades"])
    cur_risks = list(st.session_state["flt_risk"])
    cur_att_short = bool(st.session_state["flt_att_short"])
    has_custom_filters = bool(
        cur_cohort != "All" or cur_subs or cur_grades or cur_risks or cur_att_short
    )

    active_sections = SECTIONS if cur_cohort == "All" else (cur_cohort,)
    filters = GlobalFilters(
        sections=active_sections,
        subjects=tuple(cur_subs) if cur_subs else SUBJECT_CODES,
        grades=tuple(cur_grades) if cur_grades else GRADE_ORDER,
        risk_levels=tuple(cur_risks) if cur_risks else RISK_LEVELS,
        att_only_shortage=cur_att_short,
    )
    filtered_df, filtered_lb, filtered_csv = get_filtered_bundle_cached(db_ver, filters)
    st.session_state["global_filters"] = filters
    st.session_state["filtered_df"] = filtered_df
    st.session_state["filtered_leaderboard"] = filtered_lb
    st.session_state["filtered_csv"] = filtered_csv
else:
    st.session_state["filtered_df"] = full_df
    st.session_state["filtered_leaderboard"] = full_leaderboard

# ---------------------------------------------------------------------------
# Custom Floating Glass Command Navbar (Brand · Pill Nav Dock · Actions)
# ---------------------------------------------------------------------------
with st.container(horizontal=True, vertical_alignment="center", gap="medium", key="cg_top_navbar"):
    with st.container(width="content"):
        render_brand_lockup()

    with st.container(horizontal=True, horizontal_alignment="center", vertical_alignment="center"):
        with st.container(horizontal=True, vertical_alignment="center", width="content", key="cg_nav_dock"):
            for nav_page in PAGES:
                if nav_page.title == page.title:
                    with st.container(width="content", key="cg_nav_active_item"):
                        st.page_link(nav_page, label=nav_page.title, icon=nav_page.icon, width="content")
                else:
                    st.page_link(nav_page, label=nav_page.title, icon=nav_page.icon, width="content")

    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="small", width="content"):
        if has_custom_filters:
            st.button(
                "Reset",
                icon=":material/restart_alt:",
                type="tertiary",
                on_click=reset_global_filters,
                help="Clear active cohort, subject, and grade filters",
            )
        ask_clicked = st.button(
            "Insights",
            icon=":material/auto_awesome:",
            type="primary",
            help="Open live Academic Insights assistant",
        )


def render_global_filter_toolbar() -> None:
    """Render shared Cohort/Subject/Grade/Attendance filter toolbar below the page header."""
    if not is_filterable_page:
        return
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.segmented_control(
            "Cohort",
            ["All", *SECTIONS],
            required=True,
            key="cohort_seg",
            on_change=_sync_saved_filters,
            label_visibility="collapsed",
        )
        with st.popover("Subjects & Grades", icon=":material/tune:"):
            st.pills(
                "MCA Subjects",
                list(SUBJECT_CODES),
                format_func=lambda c: SUBJECT_LABELS[c],
                selection_mode="multi",
                key="flt_subjects",
                on_change=_sync_saved_filters,
                help="Leave empty to include all 6 subjects.",
            )
            st.pills(
                "Letter Grades",
                list(GRADE_ORDER),
                selection_mode="multi",
                key="flt_grades",
                on_change=_sync_saved_filters,
                help="Filter assessments by CHRIST University grade tier.",
            )
            st.pills(
                "Academic Standing",
                list(RISK_LEVELS),
                selection_mode="multi",
                key="flt_risk",
                on_change=_sync_saved_filters,
            )
            st.caption("Filters sync to URL query parameters and persist across views.")

        st.toggle(
            "Attendance < 85% Only",
            key="flt_att_short",
            on_change=_sync_saved_filters,
            help="Highlight assessments below CHRIST University's 85% attendance eligibility.",
        )


st.session_state["_render_global_filter_toolbar"] = render_global_filter_toolbar

if ask_clicked:
    open_insights_drawer(st.session_state["filtered_df"])

page.run()
render_footer()
