"""Solaris Editorial UI Design System: elevated Bento cards, mesh banners, drawers & headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from utils.constants import DEFINITIONS

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator

VERIFIED_BADGE = ":blue-badge[:material/verified:]"


def inject_custom_css(is_dark: bool = False) -> None:
    """Inject theme-aware Solaris Editorial CSS (Royal Cobalt x Sunset Coral x Gold)."""
    card_bg = "#121726" if is_dark else "#FFFFFF"
    card_border = "rgba(148, 163, 184, 0.16)" if is_dark else "rgba(15, 23, 42, 0.08)"
    card_shadow = (
        "0 4px 20px -4px rgba(0, 0, 0, 0.45)"
        if is_dark
        else "0 1px 3px rgba(15, 23, 42, 0.04), 0 8px 24px -8px rgba(15, 23, 42, 0.06)"
    )
    hover_border = "rgba(59, 130, 246, 0.45)" if is_dark else "rgba(37, 99, 235, 0.34)"
    hover_shadow = (
        "0 10px 28px -6px rgba(37, 99, 235, 0.22)"
        if is_dark
        else "0 12px 28px -8px rgba(37, 99, 235, 0.13)"
    )
    hero_bg = (
        "radial-gradient(circle at 8% 15%, rgba(59, 130, 246, 0.22), transparent 45%), "
        "radial-gradient(circle at 88% 20%, rgba(244, 63, 94, 0.19), transparent 42%), "
        "radial-gradient(circle at 75% 90%, rgba(249, 115, 22, 0.16), transparent 45%), "
        "linear-gradient(135deg, #101626 0%, #161D31 100%)"
        if is_dark
        else "radial-gradient(circle at 6% 15%, rgba(37, 99, 235, 0.11), transparent 42%), "
        "radial-gradient(circle at 90% 18%, rgba(225, 29, 72, 0.09), transparent 40%), "
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
        /* Signature Solaris top gradient ribbon */
        header[data-testid="stHeader"]::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3.5px;
            background: linear-gradient(90deg, #1D4ED8 0%, #2563EB 30%, #E11D48 68%, #F97316 88%, #F59E0B 100%);
            z-index: 999999;
        }}

        /* Elevated Bento Card Surfaces */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {card_bg};
            border: 1px solid {card_border} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow};
            transition: transform 0.18s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: {hover_border} !important;
            box-shadow: {hover_shadow};
        }}

        /* Elevated KPI Metric Cards with top Solaris gradient accent */
        div[data-testid="stMetric"] {{
            background: {card_bg};
            border: 1px solid {card_border} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow};
            position: relative;
            overflow: hidden;
            font-variant-numeric: tabular-nums;
            transition: transform 0.18s ease, box-shadow 0.2s ease;
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
            transform: translateY(-2px);
            box-shadow: {hover_shadow};
        }}

        /* Editorial Sunrise Mesh Hero Card */
        .cg-solaris-hero {{
            position: relative;
            padding: 1.25rem 1.5rem;
            border-radius: 18px;
            border: 1px solid {hero_border};
            background: {hero_bg};
            box-shadow: {card_shadow};
            margin-bottom: 0.9rem;
            overflow: hidden;
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
            margin-bottom: 0.28rem;
        }}
        .cg-solaris-title {{
            font-size: 1.32rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            line-height: 1.28;
            margin: 0 0 0.3rem 0;
        }}
        .cg-solaris-sub {{
            font-size: 0.87rem;
            color: {muted_text};
            margin: 0;
            max-width: 920px;
            line-height: 1.48;
        }}
        .cg-chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.75rem;
        }}
        .cg-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.32rem;
            padding: 0.22rem 0.68rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 600;
            background: {pill_bg};
            color: {pill_text};
            border: 1px solid {card_border};
        }}
        .cg-chip-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2563EB, #E11D48);
        }}

        /* Modernized Tabs */
        button[data-baseweb="tab"] {{
            font-weight: 600 !important;
            padding-top: 0.55rem !important;
            padding-bottom: 0.55rem !important;
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
    """Render an elevated Solaris mesh hero card with optional live status chips."""
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
