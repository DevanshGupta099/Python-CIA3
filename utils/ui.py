"""Solaris Editorial UI Design System: Zero-CLS reserved geometry, WCAG AA contrast, SEO head & SVG sparklines."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import streamlit as st

from utils.constants import DEFINITIONS

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator

VERIFIED_BADGE = ":blue-badge[:material/verified:]"

_META_DESCRIPTION = (
    "ChristGrade: Real-Time CHRIST University 2MCA CIA Academic Performance Analytics Dashboard, "
    "6-Axis Student Radar, SQLite3 CRUD Manager, and End-Semester Target Score Predictor."
)


def _build_solaris_css(is_dark: bool = False) -> str:
    """Return theme-aware Solaris Editorial CSS with zero-CLS chart slot reservations and WCAG AA contrast."""
    card_bg = "#121726" if is_dark else "#FFFFFF"
    card_border = "rgba(148, 163, 184, 0.18)" if is_dark else "rgba(15, 23, 42, 0.085)"
    card_shadow = (
        "0 4px 18px -4px rgba(0, 0, 0, 0.42)"
        if is_dark
        else "0 1px 2px rgba(15, 23, 42, 0.035), 0 8px 22px -8px rgba(15, 23, 42, 0.06)"
    )
    hover_border = "rgba(96, 165, 250, 0.45)" if is_dark else "rgba(29, 78, 216, 0.34)"
    hover_shadow = (
        "0 10px 26px -6px rgba(37, 99, 235, 0.24)"
        if is_dark
        else "0 12px 26px -8px rgba(29, 78, 216, 0.13)"
    )
    hero_bg = (
        "radial-gradient(circle at 8% 15%, rgba(59, 130, 246, 0.22), transparent 45%), "
        "radial-gradient(circle at 88% 20%, rgba(244, 63, 94, 0.18), transparent 42%), "
        "radial-gradient(circle at 75% 90%, rgba(249, 115, 22, 0.15), transparent 45%), "
        "linear-gradient(135deg, #101626 0%, #161D31 100%)"
        if is_dark
        else "radial-gradient(circle at 6% 15%, rgba(29, 78, 216, 0.10), transparent 42%), "
        "radial-gradient(circle at 90% 18%, rgba(225, 29, 72, 0.08), transparent 40%), "
        "radial-gradient(circle at 76% 92%, rgba(249, 115, 22, 0.08), transparent 45%), "
        "linear-gradient(135deg, #FFFFFF 0%, #FBFBFD 100%)"
    )
    hero_border = "rgba(251, 113, 133, 0.26)" if is_dark else "rgba(29, 78, 216, 0.16)"
    eyebrow_color = "#93C5FD" if is_dark else "#1D4ED8"
    title_color = "#F8FAFC" if is_dark else "#0F172A"
    pill_bg = "rgba(255, 255, 255, 0.075)" if is_dark else "rgba(15, 23, 42, 0.045)"
    pill_text = "#F1F5F9" if is_dark else "#1E293B"
    muted_text = "#CBD5E1" if is_dark else "#475569"
    seg_active_fg = "#93C5FD" if is_dark else "#1D4ED8"
    seg_active_bg = "rgba(59, 130, 246, 0.18)" if is_dark else "rgba(29, 78, 216, 0.10)"
    seg_active_border = "rgba(96, 165, 250, 0.55)" if is_dark else "rgba(29, 78, 216, 0.42)"

    return f"""
    <style>
    @keyframes cgSparkDraw {{
        from {{ stroke-dashoffset: 240; }}
        to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes cgBarGrow {{
        from {{ transform: scaleY(0.18); }}
        to   {{ transform: scaleY(1); }}
    }}

    /* Zero-flicker reruns: never dim existing DOM during fast fragment updates */
    [data-stale="true"],
    div[data-stale="true"] {{
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }}

    /* Explicit header logo geometry to prevent CLS on load */
    img[data-testid="stHeaderLogo"],
    img.stLogo {{
        height: 28px !important;
        width: auto !important;
    }}

    /* Zero-CLS Reserved Heights for Async Chart & Grid Containers */
    .st-key-ov_breakdown_chart,
    .st-key-ov_traj_chart {{
        min-height: 335px;
    }}
    .st-key-ov_grade_chart,
    .st-key-ov_leaderboard_table {{
        min-height: 355px;
    }}
    .st-key-ov_coupling_chart {{
        min-height: 345px;
    }}
    .st-key-stu_radar_chart,
    .st-key-stu_quartile_chart {{
        min-height: 330px;
    }}
    .st-key-stu_gpa_trend_chart {{
        min-height: 315px;
    }}
    .st-key-pred_feasibility_chart {{
        min-height: 310px;
    }}
    .st-key-pred_feat_imp_chart {{
        min-height: 240px;
    }}
    .st-key-ds_explorer_chart {{
        min-height: 405px;
    }}

    /* Top Solaris accent ribbon */
    header[data-testid="stHeader"]::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(
            90deg,
            #1D4ED8 0%,
            #2563EB 28%,
            #E11D48 56%,
            #F97316 80%,
            #F59E0B 100%
        );
        z-index: 999999;
        pointer-events: none;
    }}

    /* WCAG AA >= 6.7:1 Primary Action Button Contrast (#FFFFFF on #1D4ED8) */
    button[data-testid="stBaseButton-primary"],
    .stDownloadButton > button[kind="primary"] {{
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
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
        background-color: #1E40AF !important;
        border-color: #1E40AF !important;
        box-shadow: 0 6px 18px -4px rgba(29, 78, 216, 0.42) !important;
    }}

    /* WCAG AA >= 6.5:1 Selected Segmented Control & Active Pill Contrast in Light & Dark */
    button[data-variant="segmented_control"][data-selected="true"],
    button[data-variant="segmented_control"][aria-checked="true"],
    button[data-testid="stBaseButton-pillsActive"] {{
        background-color: {seg_active_bg} !important;
        border-color: {seg_active_border} !important;
        color: {seg_active_fg} !important;
        font-weight: 700 !important;
    }}
    button[data-variant="segmented_control"][data-selected="true"] p,
    button[data-variant="segmented_control"][aria-checked="true"] p,
    button[data-testid="stBaseButton-pillsActive"] p {{
        color: {seg_active_fg} !important;
        font-weight: 700 !important;
    }}

    /* Elevated Bento Card Surfaces */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"][style*="border"] {{
        background: {card_bg};
        border: 1px solid {card_border} !important;
        border-radius: 16px !important;
        box-shadow: {card_shadow};
        transition:
            transform 0.18s cubic-bezier(0.22, 1, 0.36, 1),
            border-color 0.18s ease,
            box-shadow 0.2s ease;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"]:hover,
    div[data-testid="stVerticalBlock"][style*="border"]:hover {{
        border-color: {hover_border} !important;
        box-shadow: {hover_shadow};
    }}

    /* Elevated KPI Metric Cards */
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid {card_border} !important;
        border-radius: 16px !important;
        box-shadow: {card_shadow};
        position: relative;
        overflow: hidden;
        font-variant-numeric: tabular-nums;
        transition:
            transform 0.18s cubic-bezier(0.22, 1, 0.36, 1),
            box-shadow 0.2s ease,
            border-color 0.18s ease;
    }}
    div[data-testid="stMetric"]::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #1D4ED8 0%, #E11D48 55%, #F97316 100%);
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translate3d(0, -2px, 0);
        border-color: {hover_border} !important;
        box-shadow: {hover_shadow};
    }}

    .cg-kpi-spark-wrap {{
        height: 32px;
        margin-top: -0.35rem;
        padding: 0 0.15rem;
        overflow: hidden;
    }}
    .cg-spark-line {{
        stroke-dasharray: 240;
        stroke-dashoffset: 0;
        animation: cgSparkDraw 0.52s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    .cg-spark-bar {{
        transform-origin: bottom;
        animation: cgBarGrow 0.4s cubic-bezier(0.22, 1, 0.36, 1);
    }}

    /* Tactile Button Micro-Interactions */
    .stButton > button,
    .stDownloadButton > button {{
        transition:
            transform 0.14s cubic-bezier(0.22, 1, 0.36, 1),
            box-shadow 0.16s ease,
            background-color 0.16s ease,
            border-color 0.16s ease !important;
    }}
    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        transform: translate3d(0, -1px, 0);
    }}
    .stButton > button:active,
    .stDownloadButton > button:active {{
        transform: translate3d(0, 0.5px, 0) scale(0.985);
    }}

    /* Editorial Sunrise Mesh Hero Card (targets preloaded native container for 0-CLS & instant LCP) */
    div[class*="st-key-cg_hero_"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[class*="st-key-cg_hero_"][data-testid="stVerticalBlockBorderWrapper"],
    .cg-solaris-hero {{
        position: relative;
        border-radius: 18px !important;
        border: 1px solid {hero_border} !important;
        background: {hero_bg} !important;
        box-shadow: {card_shadow} !important;
    }}
    div[class*="st-key-cg_hero_"] h2 {{
        font-size: 1.28rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.022em !important;
        line-height: 1.28 !important;
        color: {title_color} !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    /* Subtle Institutional Footer */
    .cg-footer {{
        margin-top: 1.8rem;
        padding-top: 0.85rem;
        border-top: 1px solid {card_border};
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.5rem;
        font-size: 0.78rem;
        color: {muted_text};
    }}

    div[data-testid="stElementContainer"]:has(.cg-seo-sync) {{
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
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
    """Record theme state for inline hero CSS & footer SEO sync (avoids extra above-the-fold DOM containers)."""
    st.session_state["_cg_is_dark"] = is_dark
    st.session_state["_cg_page_title"] = page_title


def build_sparkline_svg(
    values: list[float],
    *,
    color: str = "#2563EB",
    kind: str = "area",
    uid: str = "sp",
) -> str:
    """Build a crisp, zero-JS, GPU-animated inline SVG sparkline with zero accessibility noise."""
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
        rects: list[str] = []
        for i, v in enumerate(values):
            norm = 0.24 + 0.76 * ((v - vmin) / span)
            bh = round(norm * (h - 2 * pad_y), 1)
            bx = round(pad_x + i * (bar_w + gap), 1)
            by = round(h - pad_y - bh, 1)
            opacity = "0.92" if i == n - 1 else "0.58"
            rects.append(
                f'<rect class="cg-spark-bar" x="{bx}" y="{by}" width="{bar_w:.1f}" '
                f'height="{bh}" rx="3" fill="{color}" fill-opacity="{opacity}"/>'
            )
        inner = "".join(rects)
    else:
        pts: list[tuple[float, float]] = []
        for i, v in enumerate(values):
            px_x = round(pad_x + (i / (n - 1)) * (w - 2 * pad_x), 1)
            px_y = round(h - pad_y - ((v - vmin) / span) * (h - 2 * pad_y), 1)
            pts.append((px_x, px_y))

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
            f'<path class="cg-spark-line" d="{d_line}" fill="none" stroke="{color}" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        )

    return (
        f'<div class="cg-kpi-spark-wrap" aria-hidden="true">'
        f'<svg viewBox="0 0 {int(w)} {int(h)}" width="196" height="32" '
        f'style="width:100%;height:32px;display:block;" preserveAspectRatio="none" '
        f'aria-hidden="true" focusable="false">{inner}</svg>'
        f"</div>"
    )


def render_hero_strip(
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[str] | None = None,
) -> None:
    """Render elevated Solaris hero card using preloaded native components (instant LCP, 0 CLS, H2 heading)."""
    slug = "".join(ch if ch.isalnum() else "_" for ch in title[:18].lower()).strip("_") or "main"
    with st.container(border=True, gap="small", key=f"cg_hero_{slug}"):
        st.caption(f"**{eyebrow.upper()}**")
        st.header(title, anchor=False)
        st.caption(subtitle)
        if chips:
            with st.container(horizontal=True, gap="small"):
                for idx, c in enumerate(chips):
                    badge_col = ("blue", "orange", "green", "violet")[idx % 4]
                    st.badge(str(c), color=badge_col)


def render_footer() -> None:
    """Render Solaris CSS, institutional footer bar, and document.head SEO metadata below the fold."""
    is_dark = bool(st.session_state.get("_cg_is_dark", False))
    page_title = str(st.session_state.get("_cg_page_title", "Overview"))
    css_block = _build_solaris_css(is_dark=is_dark)
    safe_desc = html.escape(_META_DESCRIPTION, quote=True)
    safe_title = html.escape(f"ChristGrade · {page_title} · Academic Performance BI", quote=True)

    st.html(
        f"""{css_block}<footer class="cg-footer">
            <span><b>ChristGrade BI</b> · CHRIST (Deemed to be University) · 2MCA-A &amp; B (MCA411-2 Component 3)</span>
            <span>Powered by Streamlit · Pandas · NumPy · ECharts · Plotly · Seaborn · SQLite3 · scikit-learn</span>
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
                upsertMeta('name', 'theme-color', '{("#0A0D16" if is_dark else "#1D4ED8")}');
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
    """Render a semantic H3 section title with optional SQL/Formula popover and right-aligned actions."""
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
