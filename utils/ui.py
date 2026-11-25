"""Verdigris & Obsidian Design System: Floating Glass Navbar, Recessed Pill Controls & Zero-Overlap Typography."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import streamlit as st

from utils.constants import DEFINITIONS

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator

_META_DESCRIPTION = (
    "ChristGrade: Real-Time CHRIST University 2MCA CIA Academic Performance Analytics Dashboard, "
    "6-Axis Student Radar, SQLite3 CRUD Manager, and End-Semester Target Score Predictor."
)


def _build_editorial_css(is_dark: bool = False) -> str:
    """Build architectural Verdigris & Obsidian CSS with floating glass navbar and spring transitions."""
    bg_ambient = (
        "radial-gradient(ellipse 75% 260px at 50% -70px, rgba(20, 184, 166, 0.11), transparent 70%), "
        "radial-gradient(ellipse 45% 200px at 88% 0px, rgba(56, 189, 248, 0.06), transparent 65%)"
        if is_dark
        else "radial-gradient(ellipse 75% 240px at 50% -80px, rgba(13, 148, 136, 0.07), transparent 70%), "
        "radial-gradient(ellipse 45% 180px at 88% 0px, rgba(2, 132, 199, 0.045), transparent 65%)"
    )
    nav_bg = "rgba(18, 23, 29, 0.82)" if is_dark else "rgba(255, 255, 255, 0.86)"
    nav_border = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(15, 23, 42, 0.08)"
    nav_shadow = (
        "0 8px 30px -10px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.05)"
        if is_dark
        else "0 4px 20px -6px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.03)"
    )
    dock_bg = "rgba(8, 10, 13, 0.65)" if is_dark else "#EFF2F1"
    dock_border = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(15, 23, 42, 0.06)"
    nav_active_bg = (
        "linear-gradient(180deg, rgba(20, 184, 166, 0.20) 0%, rgba(13, 148, 136, 0.11) 100%)"
        if is_dark
        else "#FFFFFF"
    )
    nav_active_border = "rgba(45, 212, 191, 0.36)" if is_dark else "rgba(15, 118, 110, 0.22)"
    nav_active_text = "#5EEAD4" if is_dark else "#0F766E"
    nav_active_shadow = (
        "0 2px 10px -2px rgba(20, 184, 166, 0.22)"
        if is_dark
        else "0 1px 3px rgba(15, 23, 42, 0.08)"
    )
    nav_idle_text = "#9CA3AF" if is_dark else "#4B5563"
    nav_hover_bg = "rgba(255, 255, 255, 0.045)" if is_dark else "rgba(15, 23, 42, 0.04)"
    nav_hover_text = "#F3F4F6" if is_dark else "#111827"

    card_bg = (
        "linear-gradient(180deg, #141A21 0%, #11161C 100%)"
        if is_dark
        else "#FFFFFF"
    )
    card_border = "rgba(255, 255, 255, 0.075)" if is_dark else "rgba(17, 24, 39, 0.08)"
    card_shadow = (
        "0 6px 24px -8px rgba(0, 0, 0, 0.48), inset 0 1px 0 rgba(255, 255, 255, 0.045)"
        if is_dark
        else "0 1px 2px rgba(15, 23, 42, 0.03), 0 10px 28px -10px rgba(15, 23, 42, 0.055)"
    )
    hover_border = "rgba(45, 212, 191, 0.32)" if is_dark else "rgba(13, 148, 136, 0.28)"
    hover_shadow = (
        "0 12px 32px -8px rgba(0, 0, 0, 0.62), 0 0 0 1px rgba(45, 212, 191, 0.12)"
        if is_dark
        else "0 14px 32px -10px rgba(13, 148, 136, 0.11)"
    )

    seg_track_bg = "#0A0D10" if is_dark else "#EEF1F0"
    seg_track_border = "rgba(255, 255, 255, 0.07)" if is_dark else "rgba(15, 23, 42, 0.07)"
    seg_active_bg = "#18212A" if is_dark else "#FFFFFF"
    seg_active_fg = "#5EEAD4" if is_dark else "#0F766E"
    seg_active_border = "rgba(45, 212, 191, 0.35)" if is_dark else "rgba(15, 118, 110, 0.22)"
    seg_idle_fg = "#9CA3AF" if is_dark else "#4B5563"

    title_color = "#F9FAFB" if is_dark else "#111827"
    muted_text = "#9CA3AF" if is_dark else "#4B5563"
    subtle_line = "rgba(255, 255, 255, 0.07)" if is_dark else "rgba(15, 23, 42, 0.075)"
    stat_pill_bg = "rgba(255, 255, 255, 0.04)" if is_dark else "rgba(15, 23, 42, 0.035)"

    return f"""
    <style>
    @view-transition {{
        navigation: auto;
    }}

    @keyframes cgSmoothSettle {{
        from {{
            opacity: 0.96;
            transform: translate3d(0, 3px, 0);
        }}
        to {{
            opacity: 1;
            transform: translate3d(0, 0, 0);
        }}
    }}

    /* Hide utility style/SEO carrier containers so they add 0px height and 0px flex gap */
    div[data-testid="stElementContainer"]:has(.cg-hidden-util) {{
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Zero-flicker reruns: never dim existing DOM during fast fragment updates */
    [data-stale="true"],
    div[data-stale="true"] {{
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }}

    /* Ambient top spotlight & smooth page container breathing room */
    div[data-testid="stAppViewContainer"] {{
        background-image: {bg_ambient} !important;
        background-repeat: no-repeat !important;
    }}
    div[data-testid="stMainBlockContainer"] {{
        max-width: 1400px !important;
        padding-top: 2.1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        animation: cgSmoothSettle 0.22s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    @media (max-width: 768px) {{
        div[data-testid="stMainBlockContainer"] {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
    }}

    /* Make Streamlit's built-in outer chrome minimal & unobtrusive */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 2.1rem !important;
    }}
    header[data-testid="stHeader"]::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 2.5px;
        background: linear-gradient(90deg, #0F766E 0%, #14B8A6 38%, #38BDF8 72%, #F59E0B 100%);
        z-index: 999999;
        pointer-events: none;
    }}

    /* =====================================================================
       CUSTOM FLOATING GLASS NAVBAR (.st-key-cg_top_navbar)
       ===================================================================== */
    div.st-key-cg_top_navbar {{
        background: {nav_bg} !important;
        backdrop-filter: blur(16px) saturate(140%);
        -webkit-backdrop-filter: blur(16px) saturate(140%);
        border: 1px solid {nav_border} !important;
        border-radius: 16px !important;
        padding: 0.5rem 0.95rem !important;
        box-shadow: {nav_shadow} !important;
        margin-bottom: 0.65rem !important;
    }}

    /* Brand lockup inside Navbar */
    .cg-brand {{
        display: inline-flex;
        align-items: center;
        gap: 0.62rem;
        padding: 0.15rem 0.35rem 0.15rem 0.1rem;
        white-space: nowrap;
        user-select: none;
    }}
    .cg-brand-mark {{
        width: 30px;
        height: 30px;
        border-radius: 9px;
        background: linear-gradient(135deg, #0F766E 0%, #14B8A6 55%, #0284C7 100%);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 10px -2px rgba(20, 184, 166, 0.45);
        flex-shrink: 0;
    }}
    .cg-brand-name {{
        font-size: 1.02rem;
        font-weight: 750;
        letter-spacing: -0.025em;
        color: {title_color};
        line-height: 1.1;
    }}
    .cg-brand-tag {{
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: {muted_text};
        padding: 0.14rem 0.48rem;
        border-radius: 6px;
        background: {stat_pill_bg};
        border: 1px solid {subtle_line};
    }}

    /* Recessed Navigation Pill Dock (.st-key-cg_nav_dock) */
    div.st-key-cg_nav_dock {{
        background: {dock_bg} !important;
        border: 1px solid {dock_border} !important;
        border-radius: 12px !important;
        padding: 0.22rem 0.28rem !important;
        gap: 0.2rem !important;
    }}
    div.st-key-cg_nav_dock div[data-testid="stPageLink"] {{
        width: auto !important;
    }}
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"] {{
        border-radius: 9px !important;
        padding: 0.36rem 0.78rem !important;
        margin: 0 !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        transition:
            background-color 0.2s cubic-bezier(0.22, 1, 0.36, 1),
            border-color 0.2s ease,
            color 0.18s ease,
            transform 0.16s cubic-bezier(0.22, 1, 0.36, 1),
            box-shadow 0.2s ease !important;
    }}
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"] p,
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"] span {{
        font-size: 0.835rem !important;
        font-weight: 550 !important;
        color: {nav_idle_text} !important;
        letter-spacing: -0.008em;
        transition: color 0.18s ease !important;
    }}
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:hover {{
        background: {nav_hover_bg} !important;
        transform: translate3d(0, -0.5px, 0);
    }}
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:hover p,
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:hover span {{
        color: {nav_hover_text} !important;
    }}
    div.st-key-cg_nav_active_item a[data-testid="stPageLink-NavLink"],
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:has(strong) {{
        background: {nav_active_bg} !important;
        border-color: {nav_active_border} !important;
        box-shadow: {nav_active_shadow} !important;
    }}
    div.st-key-cg_nav_active_item a[data-testid="stPageLink-NavLink"] p,
    div.st-key-cg_nav_active_item a[data-testid="stPageLink-NavLink"] span,
    div.st-key-cg_nav_active_item a[data-testid="stPageLink-NavLink"] strong,
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:has(strong) strong,
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:has(strong) p,
    div.st-key-cg_nav_dock a[data-testid="stPageLink-NavLink"]:has(strong) span {{
        color: {nav_active_text} !important;
        font-weight: 650 !important;
    }}

    /* =====================================================================
       EDITORIAL PAGE HEADER & FILTER BAR (Clean, Non-AI, Generous Spacing)
       ===================================================================== */
    .cg-page-head {{
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.85rem;
        padding: 0.45rem 0.1rem 0.9rem 0.1rem;
        border-bottom: 1px solid {subtle_line};
        margin-bottom: 0.35rem;
    }}
    .cg-page-head h1 {{
        font-size: 1.52rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.028em !important;
        line-height: 1.22 !important;
        color: {title_color} !important;
        margin: 0 0 0.28rem 0 !important;
        padding: 0 !important;
    }}
    .cg-page-sub {{
        font-size: 0.88rem;
        line-height: 1.52;
        color: {muted_text};
        margin: 0;
        max-width: 780px;
    }}
    .cg-meta-summary {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.79rem;
        font-weight: 550;
        font-variant-numeric: tabular-nums;
        color: {muted_text};
        padding: 0.36rem 0.78rem;
        border-radius: 9px;
        background: {stat_pill_bg};
        border: 1px solid {subtle_line};
        white-space: nowrap;
    }}
    .cg-live-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
    }}

    /* =====================================================================
       RECESSED LINEAR / MACOS PILL SEGMENTED CONTROLS
       ===================================================================== */
    div[data-testid="stButtonGroup"] {{
        background: {seg_track_bg} !important;
        border: 1px solid {seg_track_border} !important;
        border-radius: 10px !important;
        padding: 3px !important;
        gap: 2px !important;
    }}
    button[data-variant="segmented_control"] {{
        border: 1px solid transparent !important;
        border-radius: 7px !important;
        background: transparent !important;
        padding: 0.24rem 0.72rem !important;
        min-height: 1.85rem !important;
        transition:
            background-color 0.2s cubic-bezier(0.22, 1, 0.36, 1),
            color 0.18s ease,
            border-color 0.2s ease,
            box-shadow 0.2s ease !important;
    }}
    button[data-variant="segmented_control"] p {{
        font-size: 0.8rem !important;
        font-weight: 550 !important;
        color: {seg_idle_fg} !important;
        white-space: nowrap !important;
    }}
    button[data-variant="segmented_control"]:hover:not([data-selected="true"]):not([aria-checked="true"]) {{
        background: {nav_hover_bg} !important;
    }}
    button[data-variant="segmented_control"][data-selected="true"],
    button[data-variant="segmented_control"][aria-checked="true"],
    button[data-testid="stBaseButton-pillsActive"] {{
        background: {seg_active_bg} !important;
        border-color: {seg_active_border} !important;
        color: {seg_active_fg} !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.18) !important;
    }}
    button[data-variant="segmented_control"][data-selected="true"] p,
    button[data-variant="segmented_control"][aria-checked="true"] p,
    button[data-testid="stBaseButton-pillsActive"] p {{
        color: {seg_active_fg} !important;
        font-weight: 650 !important;
    }}

    /* =====================================================================
       PRIMARY ACTION BUTTONS (WCAG AA >= 5.4:1 Verdigris Teal Gradient)
       ===================================================================== */
    button[data-testid="stBaseButton-primary"],
    .stDownloadButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%) !important;
        border: 1px solid rgba(45, 212, 191, 0.28) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 10px -2px rgba(13, 148, 136, 0.38) !important;
    }}
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primary"] span,
    .stDownloadButton > button[kind="primary"] p,
    .stDownloadButton > button[kind="primary"] span {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}
    button[data-testid="stBaseButton-primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #115E59 0%, #0F766E 100%) !important;
        box-shadow: 0 6px 18px -4px rgba(13, 148, 136, 0.52) !important;
    }}

    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 9px !important;
        transition:
            transform 0.16s cubic-bezier(0.22, 1, 0.36, 1),
            box-shadow 0.2s ease,
            background-color 0.18s ease,
            border-color 0.18s ease !important;
    }}
    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        transform: translate3d(0, -1px, 0);
    }}
    .stButton > button:active,
    .stDownloadButton > button:active {{
        transform: translate3d(0, 0.5px, 0) scale(0.985);
    }}

    /* =====================================================================
       ELEVATED BENTO CARDS & KPI METRICS (Generous Breathing Room)
       ===================================================================== */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"][style*="border"] {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.35rem !important;
        box-shadow: {card_shadow} !important;
        transition:
            transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
            border-color 0.22s ease,
            box-shadow 0.24s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover,
    div[data-testid="stVerticalBlock"][style*="border"]:hover {{
        border-color: {hover_border} !important;
        box-shadow: {hover_shadow} !important;
    }}

    div[data-testid="stMetric"] {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 16px !important;
        padding: 1.1rem 1.25rem !important;
        box-shadow: {card_shadow} !important;
        position: relative;
        overflow: hidden;
        font-variant-numeric: tabular-nums;
        transition:
            transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
            box-shadow 0.22s ease,
            border-color 0.2s ease;
    }}
    div[data-testid="stMetric"]::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #14B8A6 0%, rgba(56, 189, 248, 0.65) 55%, transparent 100%);
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translate3d(0, -2px, 0);
        border-color: {hover_border} !important;
        box-shadow: {hover_shadow} !important;
    }}

    /* Card Header Typography — crisp hierarchy, zero crowding */
    .cg-card-title {{
        font-size: 0.98rem;
        font-weight: 650;
        letter-spacing: -0.016em;
        color: {title_color};
        line-height: 1.32;
        margin: 0;
    }}
    .cg-card-sub {{
        font-size: 0.81rem;
        color: {muted_text};
        line-height: 1.45;
        margin: 0.18rem 0 0.35rem 0;
    }}

    /* Section Header H2 Spacing */
    div[data-testid="stHeading"] h2,
    div[data-testid="stHeading"] h3 {{
        letter-spacing: -0.02em !important;
    }}

    /* Reserved chart container heights for zero layout jump */
    .st-key-ov_breakdown_chart,
    .st-key-ov_traj_chart {{
        min-height: 350px;
    }}
    .st-key-ov_grade_chart,
    .st-key-ov_leaderboard_table {{
        min-height: 360px;
    }}
    .st-key-ov_coupling_chart {{
        min-height: 350px;
    }}
    .st-key-stu_radar_chart,
    .st-key-stu_quartile_chart {{
        min-height: 345px;
    }}
    .st-key-stu_gpa_trend_chart {{
        min-height: 325px;
    }}
    .st-key-pred_feasibility_chart {{
        min-height: 340px;
    }}
    .st-key-pred_feat_imp_chart {{
        min-height: 250px;
    }}
    .st-key-ds_explorer_chart {{
        min-height: 410px;
    }}

    /* Slim Refined Scrollbars */
    ::-webkit-scrollbar {{
        width: 7px;
        height: 7px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(148, 163, 184, 0.25);
        border-radius: 999px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(148, 163, 184, 0.42);
    }}

    /* Institutional Footer */
    .cg-footer {{
        margin-top: 2.2rem;
        padding-top: 1rem;
        border-top: 1px solid {subtle_line};
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.6rem;
        font-size: 0.78rem;
        color: {muted_text};
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }}
    }}
    </style>
    """


def inject_custom_css(is_dark: bool = False, page_title: str = "Overview") -> None:
    """Inject Verdigris & Obsidian CSS at top of render tree so navbar & cards paint with zero FOUC."""
    st.session_state["_cg_is_dark"] = is_dark
    st.session_state["_cg_page_title"] = page_title
    css_block = _build_editorial_css(is_dark=is_dark)
    st.html(f'<div class="cg-hidden-util" aria-hidden="true">{css_block}</div>')


def render_brand_lockup() -> None:
    """Render minimal geometric Verdigris mark + ChristGrade wordmark inside the floating navbar."""
    st.html(
        """<div class="cg-brand">
            <span class="cg-brand-mark" aria-hidden="true">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
                    <path d="M4 16.5L9.5 11L13.5 14L20 7" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="20" cy="7" r="2.2" fill="#FDE68A"/>
                </svg>
            </span>
            <span class="cg-brand-name">ChristGrade</span>
            <span class="cg-brand-tag">2MCA · Sem 2</span>
        </div>"""
    )


def render_page_header(
    title: str,
    subtitle: str,
    meta_summary: str | None = None,
) -> None:
    """Render a clean, authentic editorial H1 page header with understated live summary (no AI rainbow pills)."""
    meta_html = ""
    if meta_summary:
        meta_html = (
            f'<div class="cg-meta-summary">'
            f'<span class="cg-live-dot" aria-hidden="true"></span>'
            f'<span>{html.escape(meta_summary)}</span>'
            f"</div>"
        )
    st.html(
        f"""<header class="cg-page-head">
            <div>
                <h1>{html.escape(title)}</h1>
                <p class="cg-page-sub">{html.escape(subtitle)}</p>
            </div>
            {meta_html}
        </header>"""
    )


def render_hero_strip(
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[str] | None = None,
) -> None:
    """Backward-compatible wrapper routing legacy hero calls to the clean editorial page header."""
    _ = eyebrow
    summary = " · ".join(chips[:2]) if chips else None
    render_page_header(title=title, subtitle=subtitle, meta_summary=summary)


def build_sparkline_svg(
    values: list[float],
    *,
    color: str = "#14B8A6",
    kind: str = "area",
    uid: str = "sp",
) -> str:
    """Build a crisp inline SVG sparkline."""
    if not values or len(values) < 2:
        return ""

    w, h = 196.0, 32.0
    pad_x, pad_y = 4.0, 4.0
    vmin, vmax = min(values), max(values)
    span = (vmax - vmin) if vmax > vmin else 1.0
    n = len(values)

    if kind == "bar":
        gap = 4.0
        bar_w = max(6.0, (w - 2 * pad_x - gap * (n - 1)) / n)
        rects = []
        for i, v in enumerate(values):
            norm = 0.24 + 0.76 * ((v - vmin) / span)
            bh = round(norm * (h - 2 * pad_y), 1)
            bx = round(pad_x + i * (bar_w + gap), 1)
            by = round(h - pad_y - bh, 1)
            opacity = "0.92" if i == n - 1 else "0.55"
            rects.append(
                f'<rect x="{bx}" y="{by}" width="{bar_w:.1f}" '
                f'height="{bh}" rx="3" fill="{color}" fill-opacity="{opacity}"/>'
            )
        inner = "".join(rects)
    else:
        pts = [
            (
                round(pad_x + (i / (n - 1)) * (w - 2 * pad_x), 1),
                round(h - pad_y - ((v - vmin) / span) * (h - 2 * pad_y), 1),
            )
            for i, v in enumerate(values)
        ]
        d_line = "M " + " L ".join(f"{x},{y}" for x, y in pts)
        last_x, last_y = pts[-1]
        grad_id = f"cgSpGrad_{uid}"
        area_part = ""
        if kind == "area":
            d_area = f"{d_line} L {pts[-1][0]},{h} L {pts[0][0]},{h} Z"
            area_part = (
                f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0%" stop-color="{color}" stop-opacity="0.26"/>'
                f'<stop offset="100%" stop-color="{color}" stop-opacity="0.01"/>'
                f'</linearGradient></defs>'
                f'<path d="{d_area}" fill="url(#{grad_id})"/>'
            )
        inner = (
            f"{area_part}"
            f'<path d="{d_line}" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        )

    return (
        f'<svg viewBox="0 0 {int(w)} {int(h)}" width="196" height="32" '
        f'style="width:100%;height:32px;display:block;" preserveAspectRatio="none" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
    )


def render_footer() -> None:
    """Render institutional footer bar and sync document.head SEO metadata."""
    is_dark = bool(st.session_state.get("_cg_is_dark", False))
    page_title = str(st.session_state.get("_cg_page_title", "Overview"))
    safe_desc = html.escape(_META_DESCRIPTION, quote=True)
    safe_title = html.escape(f"ChristGrade · {page_title} · Academic Performance BI", quote=True)

    st.html(
        f"""<footer class="cg-footer">
            <span><b>ChristGrade</b> · CHRIST (Deemed to be University) · Department of Computer Science (2MCA-A &amp; B)</span>
            <span>MCA411-2 Component 3 · SQLite3 · Pandas · NumPy · ECharts · scikit-learn</span>
        </footer>
        <script>
        (function() {{
            try {{
                var d = document;
                if (!d || !d.head) return;
                function upsertMeta(attr, key, content) {{
                    var el = d.head.querySelector('meta[' + attr + '="' + key + '"]');
                    if (!el) {{
                        el = d.createElement('meta');
                        el.setAttribute(attr, key);
                        d.head.appendChild(el);
                    }}
                    if (el.getAttribute('content') !== content) {{
                        el.setAttribute('content', content);
                    }}
                }}
                upsertMeta('name', 'description', '{safe_desc}');
                upsertMeta('name', 'theme-color', '{("#0B0E11" if is_dark else "#0F766E")}');
                upsertMeta('property', 'og:title', '{safe_title}');
                upsertMeta('property', 'og:description', '{safe_desc}');
                upsertMeta('property', 'og:type', 'website');
            }} catch (_) {{}}
        }})();
        </script>""",
        unsafe_allow_javascript=True,
    )


def section_header(
    title: str,
    *,
    help_text: str | None = None,
    definition_key: str | None = None,
) -> DeltaGenerator:
    """Render a semantic H2 section heading (sequenced cleanly below H1 page title) with optional SQL popover."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.header(title, help=help_text, anchor=False)
        actions = st.container(
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
            width="content",
        )
    if definition_key and definition_key in DEFINITIONS:
        defn = DEFINITIONS[definition_key]
        with actions.popover("Formula & SQL", icon=":material/data_object:", type="tertiary"):
            st.markdown(f"**{defn.title}**")
            st.caption(f"Maintained by {defn.owner}")
            st.info(defn.formula, icon=":material/functions:")
            st.code(defn.sql, language="sql")
    return actions


def card_header(
    title: str,
    caption: str | None = None,
    *,
    verified: bool = False,
    help_text: str | None = None,
) -> DeltaGenerator:
    """Render a clean editorial card header without AI-cliché badges and return right-aligned controls."""
    _ = (verified, help_text)
    sub_html = f'<p class="cg-card-sub">{html.escape(caption)}</p>' if caption else ""
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.html(
            f'<div><div class="cg-card-title">{html.escape(title)}</div>{sub_html}</div>'
        )
        controls = st.container(
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
            width="content",
        )
    return controls
