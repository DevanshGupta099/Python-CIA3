"""Solaris Editorial UI Design System: 60fps spring animations, Bento cards, mesh banners & headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from utils.constants import DEFINITIONS

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator

VERIFIED_BADGE = ":blue-badge[:material/verified:]"


def inject_custom_css(is_dark: bool = False) -> None:
    """Inject theme-aware Solaris Editorial CSS with GPU-accelerated transitions & anti-flicker."""
    card_bg = "#121726" if is_dark else "#FFFFFF"
    card_border = "rgba(148, 163, 184, 0.16)" if is_dark else "rgba(15, 23, 42, 0.08)"
    card_shadow = (
        "0 4px 20px -4px rgba(0, 0, 0, 0.45)"
        if is_dark
        else "0 1px 3px rgba(15, 23, 42, 0.04), 0 8px 24px -8px rgba(15, 23, 42, 0.06)"
    )
    hover_border = "rgba(59, 130, 246, 0.48)" if is_dark else "rgba(37, 99, 235, 0.36)"
    hover_shadow = (
        "0 12px 30px -6px rgba(37, 99, 235, 0.25)"
        if is_dark
        else "0 14px 30px -8px rgba(37, 99, 235, 0.14)"
    )
    hero_bg = (
        "radial-gradient(circle at 8% 15%, rgba(59, 130, 246, 0.24), transparent 45%), "
        "radial-gradient(circle at 88% 20%, rgba(244, 63, 94, 0.20), transparent 42%), "
        "radial-gradient(circle at 75% 90%, rgba(249, 115, 22, 0.17), transparent 45%), "
        "linear-gradient(135deg, #101626 0%, #161D31 100%)"
        if is_dark
        else "radial-gradient(circle at 6% 15%, rgba(37, 99, 235, 0.12), transparent 42%), "
        "radial-gradient(circle at 90% 18%, rgba(225, 29, 72, 0.10), transparent 40%), "
        "radial-gradient(circle at 76% 92%, rgba(249, 115, 22, 0.10), transparent 45%), "
        "linear-gradient(135deg, #FFFFFF 0%, #FBFBFD 100%)"
    )
    hero_border = "rgba(251, 113, 133, 0.26)" if is_dark else "rgba(37, 99, 235, 0.16)"
    pill_bg = "rgba(255, 255, 255, 0.07)" if is_dark else "rgba(15, 23, 42, 0.045)"
    pill_text = "#E2E8F0" if is_dark else "#334155"
    muted_text = "#94A3B8" if is_dark else "#475569"

    st.markdown(
        f"""
        <style>
        /* Keyframes: Flowing Solaris Ribbon & Smooth Spring Reveal */
        @keyframes cgAuroraShift {{
            0%   {{ background-position: 0% 50%; }}
            50%  {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        @keyframes cgRevealUp {{
            from {{
                opacity: 0;
                transform: translate3d(0, 10px, 0);
            }}
            to {{
                opacity: 1;
                transform: translate3d(0, 0, 0);
            }}
        }}

        @keyframes cgPulseDot {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50%      {{ transform: scale(1.35); opacity: 0.72; }}
        }}

        /* Eliminate harsh Streamlit grey-out dim during Cloud network reruns */
        [data-stale="true"] {{
            opacity: 0.90 !important;
            transition: opacity 0.18s cubic-bezier(0.22, 1, 0.36, 1) !important;
        }}

        /* Animated Solaris top gradient ribbon */
        header[data-testid="stHeader"]::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3.5px;
            background: linear-gradient(
                90deg,
                #1D4ED8 0%,
                #2563EB 25%,
                #E11D48 52%,
                #F97316 76%,
                #F59E0B 90%,
                #2563EB 100%
            );
            background-size: 220% 100%;
            animation: cgAuroraShift 9s ease-in-out infinite;
            z-index: 999999;
        }}

        /* Elevated Bento Card Surfaces (supports all Streamlit 1.40 - 1.67 DOM wrappers) */
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlock"][style*="border"] {{
            background: {card_bg};
            border: 1px solid {card_border} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow};
            animation: cgRevealUp 0.34s cubic-bezier(0.16, 1, 0.3, 1) both;
            will-change: transform, box-shadow;
            transition:
                transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
                border-color 0.22s ease,
                box-shadow 0.22s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover,
        div[data-testid="stVerticalBlock"][style*="border"]:hover {{
            border-color: {hover_border} !important;
            box-shadow: {hover_shadow};
        }}

        /* Elevated KPI Metric Cards with staggered entrance & spring hover */
        div[data-testid="stMetric"] {{
            background: {card_bg};
            border: 1px solid {card_border} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow};
            position: relative;
            overflow: hidden;
            font-variant-numeric: tabular-nums;
            animation: cgRevealUp 0.36s cubic-bezier(0.16, 1, 0.3, 1) both;
            will-change: transform, box-shadow;
            transition:
                transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.22s ease,
                border-color 0.22s ease;
        }}
        div[data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #2563EB 0%, #E11D48 55%, #F97316 100%);
        }}
        div[data-testid="stMetric"]:hover {{
            transform: translate3d(0, -3px, 0);
            border-color: {hover_border} !important;
            box-shadow: {hover_shadow};
        }}

        /* Smooth Chart & Dataframe Fade-In */
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"] {{
            animation: cgRevealUp 0.32s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}

        /* Tactile Button & Pill Micro-Interactions */
        .stButton > button,
        .stDownloadButton > button {{
            transition:
                transform 0.15s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.18s ease,
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

        /* Editorial Sunrise Mesh Hero Card */
        .cg-solaris-hero {{
            position: relative;
            padding: 1.2rem 1.45rem;
            border-radius: 18px;
            border: 1px solid {hero_border};
            background: {hero_bg};
            box-shadow: {card_shadow};
            margin-bottom: 0.85rem;
            overflow: hidden;
            animation: cgRevealUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) both;
        }}
        .cg-solaris-eyebrow {{
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            background: linear-gradient(90deg, #2563EB 0%, #E11D48 60%, #F97316 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }}
        .cg-solaris-title {{
            font-size: 1.3rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            line-height: 1.28;
            margin: 0 0 0.28rem 0;
        }}
        .cg-solaris-sub {{
            font-size: 0.865rem;
            color: {muted_text};
            margin: 0;
            max-width: 920px;
            line-height: 1.48;
        }}
        .cg-chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.72rem;
        }}
        .cg-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.68rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 600;
            background: {pill_bg};
            color: {pill_text};
            border: 1px solid {card_border};
            transition: transform 0.16s ease, border-color 0.16s ease;
        }}
        .cg-chip:hover {{
            transform: translateY(-1px);
            border-color: {hover_border};
        }}
        .cg-chip-dot {{
            width: 6.5px;
            height: 6.5px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2563EB, #E11D48);
            animation: cgPulseDot 2.8s ease-in-out infinite;
        }}

        /* Modernized Tabs */
        button[data-baseweb="tab"] {{
            font-weight: 600 !important;
            padding-top: 0.55rem !important;
            padding-bottom: 0.55rem !important;
            transition: color 0.18s ease, background-color 0.18s ease !important;
        }}

        /* Subtle Footer */
        .cg-footer {{
            margin-top: 2rem;
            padding-top: 0.85rem;
            border-top: 1px solid {card_border};
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem;
            font-size: 0.77rem;
            color: {muted_text};
        }}

        /* Accessibility: respect reduced-motion OS setting */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_strip(
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[str] | None = None,
) -> None:
    """Render an elevated Solaris mesh hero card with live animated status chips."""
    chips_html = ""
    if chips:
        items = "".join(
            f'<span class="cg-chip"><span class="cg-chip-dot"></span>{c}</span>'
            for c in chips
        )
        chips_html = f'<div class="cg-chip-row">{items}</div>'

    st.markdown(
        f"""
        <div class="cg-solaris-hero">
            <div class="cg-solaris-eyebrow">{eyebrow}</div>
            <div class="cg-solaris-title">{title}</div>
            <p class="cg-solaris-sub">{subtitle}</p>
            {chips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render a subtle institutional footer bar."""
    st.markdown(
        """
        <div class="cg-footer">
            <span><b>ChristGrade BI</b> · CHRIST (Deemed to be University) · 2MCA-A &amp; B (MCA411-2 Component 3)</span>
            <span>Powered by Streamlit · Pandas · NumPy · Plotly · Seaborn · SQLite3 · scikit-learn</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(
    title: str,
    *,
    help_text: str | None = None,
    definition_key: str | None = None,
) -> DeltaGenerator:
    """Render a clean section title with optional SQL/Formula popover and right-aligned actions."""
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader(title, help=help_text, anchor=False)
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
    """Render a card title row and return a right-aligned controls container."""
    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        with st.container(gap=None):
            heading = f"**{title}** {VERIFIED_BADGE}" if verified else f"**{title}**"
            st.markdown(heading, help=help_text)
            if caption:
                st.caption(caption)
        controls = st.container(
            horizontal=True,
            horizontal_alignment="right",
            vertical_alignment="center",
            width="content",
        )
    return controls
