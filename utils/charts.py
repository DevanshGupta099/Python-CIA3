"""60fps Apache ECharts Canvas engine + preserved lazy-loaded Plotly & Seaborn suite."""

from __future__ import annotations

import base64
import html
from io import BytesIO
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
import streamlit as st

from utils.constants import (
    GRADE_COLORS,
    GRADE_ORDER,
    GRADE_SCALE,
    MIN_ESE_PASS_MARKS,
    PALETTE,
    SUBJECT_CODES,
    SUBJECTS,
)

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go

# Solaris Editorial Categorical Sequence
GRADIENT_SEQUENCE = [
    "#2563EB",  # Royal Cobalt
    "#F97316",  # Sunset Coral
    "#E11D48",  # Crimson Rose
    "#0EA5E9",  # Sky Azure
    "#F59E0B",  # Champagne Gold
    "#10B981",  # Emerald
    "#1D4ED8",  # Deep Navy-Cobalt
    "#FB7185",  # Soft Rose
]


# ===========================================================================
# 60fps Hardware-Accelerated Apache ECharts Canvas Engine
# ===========================================================================

def _ec_theme_tokens(is_dark: bool) -> dict[str, str]:
    return {
        "text": "#E2E8F0" if is_dark else "#1E293B",
        "muted": "#94A3B8" if is_dark else "#475569",
        "grid": "rgba(148, 163, 184, 0.14)" if is_dark else "rgba(15, 23, 42, 0.08)",
        "tooltip_bg": "rgba(15, 23, 42, 0.94)" if is_dark else "rgba(255, 255, 255, 0.96)",
        "tooltip_border": "rgba(148, 163, 184, 0.24)" if is_dark else "rgba(15, 23, 42, 0.10)",
        "card_bg": "#121726" if is_dark else "#FFFFFF",
    }


def _ec_base(is_dark: bool) -> dict[str, Any]:
    tok = _ec_theme_tokens(is_dark)
    return {
        "backgroundColor": "transparent",
        "animation": True,
        "animationDuration": 480,
        "animationEasing": "cubicOut",
        "animationDurationUpdate": 340,
        "animationEasingUpdate": "cubicInOut",
        "textStyle": {
            "fontFamily": "Source Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            "color": tok["text"],
        },
    }


def _ec_tooltip(is_dark: bool, trigger: str = "axis", value_fmt: str | None = None) -> dict[str, Any]:
    tok = _ec_theme_tokens(is_dark)
    tip: dict[str, Any] = {
        "trigger": trigger,
        "confine": True,
        "backgroundColor": tok["tooltip_bg"],
        "borderColor": tok["tooltip_border"],
        "borderWidth": 1,
        "textStyle": {"color": tok["text"], "fontSize": 12},
    }
    if trigger == "axis":
        tip["axisPointer"] = {"type": "shadow" if value_fmt != "line" else "line"}
    if value_fmt and value_fmt != "line":
        tip["valueFormatter"] = value_fmt
    return tip


def _linear_grad(x0: float, y0: float, x1: float, y1: float, c0: str, c1: str) -> dict[str, Any]:
    return {
        "type": "linear",
        "x": x0,
        "y": y0,
        "x2": x1,
        "y2": y1,
        "colorStops": [
            {"offset": 0, "color": c0},
            {"offset": 1, "color": c1},
        ],
    }


def render_echarts(
    spec: dict[str, Any],
    *,
    height: int = 340,
    key: str,
    alt: str,
) -> None:
    """Render a smooth 60fps Canvas ECharts visualization with stable DOM identity & zero CLS."""
    st.echarts_chart(
        spec,
        width="stretch",
        height=height,
        theme=None,
        renderer="canvas",
        key=key,
        alt=alt,
    )


def render_seaborn_html_img(png_bytes: bytes, alt: str, width: int = 560, height: int = 345) -> None:
    """Render cached PNG bytes as an inline sized data-URI image (0 HTTP round-trip, 0 CLS, WCAG alt)."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    safe_alt = html.escape(alt, quote=True)
    st.html(
        f'<img src="data:image/png;base64,{b64}" alt="{safe_alt}" '
        f'width="{width}" height="{height}" decoding="async" '
        f'style="width:100%;height:auto;max-height:{height}px;object-fit:contain;display:block;border-radius:10px;" />'
    )


def echarts_subject_breakdown(
    df: pd.DataFrame,
    view_mode: str = "Stacked CIA",
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth ECharts Subject-wise CIA1, Mid-Sem CIA2, CIA3, Attendance & End-Sem breakdown."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if df.empty:
        return spec

    order = [c for c in SUBJECT_CODES if c in df["subject_code"].unique()]
    labels = [str(SUBJECTS[c]["short"]) for c in order]

    base_axes = {
        "grid": {"left": 46, "right": 14, "top": 42, "bottom": 28},
        "legend": {
            "top": 2,
            "left": 0,
            "itemWidth": 12,
            "itemHeight": 8,
            "textStyle": {"color": tok["muted"], "fontSize": 11},
        },
        "xAxis": {
            "type": "category",
            "data": labels,
            "axisLine": {"lineStyle": {"color": tok["grid"]}},
            "axisTick": {"show": False},
            "axisLabel": {"color": tok["muted"], "fontSize": 11, "interval": 0},
        },
        "yAxis": {
            "type": "value",
            "min": 0,
            "max": 105,
            "name": "Score (/100)",
            "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
            "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
            "axisLabel": {"color": tok["muted"], "fontSize": 11},
        },
    }

    if view_mode == "Section A vs B":
        sec_grp = (
            df.groupby(["subject_code", "section"], as_index=False)["total_score"]
            .mean()
            .round(1)
        )
        colors = {"2MCA-A": "#2563EB", "2MCA-B": "#F97316"}
        series = []
        for sec in ("2MCA-A", "2MCA-B"):
            sub = sec_grp[sec_grp["section"] == sec].set_index("subject_code").reindex(order)
            vals = [round(float(v), 1) if pd.notna(v) else 0.0 for v in sub["total_score"]]
            series.append(
                {
                    "name": sec,
                    "type": "bar",
                    "data": vals,
                    "barMaxWidth": 28,
                    "universalTransition": True,
                    "itemStyle": {"color": colors[sec], "borderRadius": [6, 6, 0, 0]},
                    "label": {"show": True, "position": "top", "color": tok["muted"], "fontSize": 10},
                }
            )
        spec.update(base_axes)
        spec["tooltip"] = _ec_tooltip(is_dark, "axis", "%.1f")
        spec["series"] = series
        return spec

    agg = (
        df.groupby("subject_code")
        .agg(
            cia1_w=("cia1_w", "mean"),
            cia2_w=("cia2_w", "mean"),
            cia3_w=("cia3_w", "mean"),
            att_marks=("att_marks", "mean"),
            ese_50=("ese_50", "mean"),
            cia1_pct=("cia1_pct", "mean"),
            cia2_pct=("cia2_pct", "mean"),
            cia3_pct=("cia3_pct", "mean"),
            end_sem=("end_sem", "mean"),
        )
        .reindex(order)
        .round(1)
    )

    if view_mode == "CIA % Compare":
        series_spec = [
            ("CIA 1 (%)", "cia1_pct", "#2563EB"),
            ("Mid-Sem (%)", "cia2_pct", "#E11D48"),
            ("CIA 3 (%)", "cia3_pct", "#F97316"),
            ("End-Sem (%)", "end_sem", "#10B981"),
        ]
        series = [
            {
                "name": label,
                "type": "bar",
                "data": [round(float(v), 1) for v in agg[col]],
                "barMaxWidth": 18,
                "universalTransition": True,
                "itemStyle": {"color": color, "borderRadius": [5, 5, 0, 0]},
            }
            for label, col, color in series_spec
        ]
        spec.update(base_axes)
        spec["yAxis"]["name"] = "Normalized (%)"
        spec["tooltip"] = _ec_tooltip(is_dark, "axis", "%.1f")
        spec["series"] = series
        return spec

    stack_spec = [
        ("CIA 1 (/10)", "cia1_w", "#1D4ED8", [0, 0, 0, 0]),
        ("Mid-Sem (/25)", "cia2_w", "#2563EB", [0, 0, 0, 0]),
        ("CIA 3 (/10)", "cia3_w", "#F97316", [0, 0, 0, 0]),
        ("Attendance (/5)", "att_marks", "#F59E0B", [0, 0, 0, 0]),
        ("End-Sem (/50)", "ese_50", "#E11D48", [6, 6, 0, 0]),
    ]
    series = [
        {
            "name": label,
            "type": "bar",
            "stack": "total",
            "data": [round(float(v), 1) for v in agg[col]],
            "barMaxWidth": 38,
            "universalTransition": True,
            "itemStyle": {"color": color, "borderRadius": radius},
        }
        for label, col, color, radius in stack_spec
    ]
    spec.update(base_axes)
    spec["yAxis"]["name"] = "Weighted Marks (/100)"
    spec["tooltip"] = _ec_tooltip(is_dark, "axis", "%.1f")
    spec["series"] = series
    return spec


def echarts_cia_progression(df: pd.DataFrame, is_dark: bool = False) -> dict[str, Any]:
    """Smooth spline area chart across CIA 1 -> Mid-Sem -> CIA 3 -> End-Sem."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if df.empty:
        return spec

    stages = ["CIA 1", "Mid-Sem", "CIA 3", "End-Sem"]
    cols = ["cia1_pct", "cia2_pct", "cia3_pct", "end_sem"]
    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.28)", "rgba(37, 99, 235, 0.02)"),
        "2MCA-B": ("#E11D48", "rgba(225, 29, 72, 0.22)", "rgba(225, 29, 72, 0.02)"),
    }

    series = []
    for sec in sorted(df["section"].unique()):
        sub = df[df["section"] == sec]
        means = [round(float(sub[c].mean()), 1) for c in cols]
        line_c, top_c, bot_c = palette_map.get(
            sec, ("#F97316", "rgba(249, 115, 22, 0.24)", "rgba(249, 115, 22, 0.02)")
        )
        series.append(
            {
                "name": sec,
                "type": "line",
                "smooth": 0.42,
                "symbol": "circle",
                "symbolSize": 8,
                "universalTransition": True,
                "data": means,
                "lineStyle": {"width": 3, "color": line_c},
                "itemStyle": {"color": line_c, "borderColor": tok["card_bg"], "borderWidth": 2},
                "areaStyle": {"color": _linear_grad(0, 0, 0, 1, top_c, bot_c)},
                "label": {"show": True, "position": "top", "color": tok["text"], "fontSize": 10.5},
            }
        )

    tip = _ec_tooltip(is_dark, "axis", "line")
    tip["valueFormatter"] = "%.1f"
    spec.update(
        {
            "grid": {"left": 44, "right": 18, "top": 42, "bottom": 28},
            "tooltip": tip,
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": stages,
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisTick": {"show": False},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "yAxis": {
                "type": "value",
                "min": 48,
                "max": 95,
                "name": "Cohort Mean (%)",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "series": series,
        }
    )
    return spec


def echarts_cohort_gpa_trend(leaderboard_df: pd.DataFrame, is_dark: bool = False) -> dict[str, Any]:
    """Smooth spline area chart for Sem 1 SGPA -> Sem 2 SGPA -> Cumulative CGPA."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if leaderboard_df.empty:
        return spec

    stages = ["Sem 1 SGPA", "Sem 2 SGPA", "Cumulative CGPA"]
    cols = ["sem1_sgpa", "sem2_sgpa", "cgpa"]
    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.26)", "rgba(37, 99, 235, 0.02)"),
        "2MCA-B": ("#F97316", "rgba(249, 115, 22, 0.24)", "rgba(249, 115, 22, 0.02)"),
    }

    series = []
    for sec in sorted(leaderboard_df["section"].unique()):
        sub = leaderboard_df[leaderboard_df["section"] == sec]
        means = [round(float(sub[c].mean()), 2) for c in cols]
        line_c, top_c, bot_c = palette_map.get(
            sec, ("#E11D48", "rgba(225, 29, 72, 0.22)", "rgba(225, 29, 72, 0.02)")
        )
        series.append(
            {
                "name": f"{sec} Mean",
                "type": "line",
                "smooth": 0.4,
                "symbol": "circle",
                "symbolSize": 8,
                "universalTransition": True,
                "data": means,
                "lineStyle": {"width": 3, "color": line_c},
                "itemStyle": {"color": line_c, "borderColor": tok["card_bg"], "borderWidth": 2},
                "areaStyle": {"color": _linear_grad(0, 0, 0, 1, top_c, bot_c)},
                "label": {"show": True, "position": "top", "color": tok["text"], "fontSize": 10.5},
            }
        )

    tip = _ec_tooltip(is_dark, "axis", "line")
    tip["valueFormatter"] = "%.2f"
    spec.update(
        {
            "grid": {"left": 44, "right": 18, "top": 42, "bottom": 28},
            "tooltip": tip,
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": stages,
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisTick": {"show": False},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "yAxis": {
                "type": "value",
                "min": 6.0,
                "max": 9.6,
                "name": "Mean GPA (/10)",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "series": series,
        }
    )
    return spec


def echarts_grade_distribution(
    df: pd.DataFrame,
    mode: str = "Donut",
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth interactive Donut or Sunburst chart of CHRIST letter grades."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if df.empty:
        return spec

    if mode == "Sunburst":
        sun_data = []
        sec_colors = {"2MCA-A": "#2563EB", "2MCA-B": "#F97316"}
        for sec in sorted(df["section"].unique()):
            sub = df[df["section"] == sec]
            counts = sub["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
            children = [
                {
                    "name": g,
                    "value": int(cnt),
                    "itemStyle": {"color": GRADE_COLORS[g]},
                }
                for g, cnt in counts.items()
                if int(cnt) > 0
            ]
            sun_data.append(
                {
                    "name": sec,
                    "itemStyle": {"color": sec_colors.get(sec, "#2563EB")},
                    "children": children,
                }
            )
        spec.update(
            {
                "tooltip": {**_ec_tooltip(is_dark, "item"), "formatter": "{b}: {c} records"},
                "series": [
                    {
                        "type": "sunburst",
                        "data": sun_data,
                        "radius": ["18%", "88%"],
                        "universalTransition": True,
                        "itemStyle": {"borderRadius": 5, "borderColor": tok["card_bg"], "borderWidth": 2},
                        "label": {"rotate": "radial", "color": "#FFFFFF", "fontSize": 10.5},
                    }
                ],
            }
        )
        return spec

    counts = df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
    counts = counts[counts > 0]
    top_share = round(float(df["grade"].isin(["O", "A+", "A"]).mean() * 100.0), 0) if len(df) else 0.0

    pie_data = [
        {
            "name": str(g),
            "value": int(v),
            "itemStyle": {"color": GRADE_COLORS[str(g)]},
        }
        for g, v in counts.items()
    ]
    spec.update(
        {
            "title": {
                "text": f"{int(top_share)}%",
                "subtext": "Grade A & above",
                "left": "center",
                "top": "38%",
                "textStyle": {"fontSize": 22, "fontWeight": 800, "color": tok["text"]},
                "subtextStyle": {"fontSize": 11, "color": tok["muted"]},
            },
            "tooltip": {
                **_ec_tooltip(is_dark, "item"),
                "formatter": "Grade {b}: {c} records ({d}%)",
            },
            "legend": {
                "bottom": 0,
                "left": "center",
                "itemWidth": 11,
                "itemHeight": 11,
                "textStyle": {"color": tok["muted"], "fontSize": 11},
            },
            "series": [
                {
                    "name": "CHRIST Grade",
                    "type": "pie",
                    "radius": ["54%", "79%"],
                    "center": ["50%", "45%"],
                    "padAngle": 2,
                    "universalTransition": True,
                    "itemStyle": {
                        "borderRadius": 7,
                        "borderColor": tok["card_bg"],
                        "borderWidth": 2,
                    },
                    "label": {"show": True, "formatter": "{b}: {d}%", "color": tok["text"], "fontSize": 11},
                    "emphasis": {"scale": True, "scaleSize": 6},
                    "data": pie_data,
                }
            ],
        }
    )
    return spec


def echarts_statistical_coupling(
    df: pd.DataFrame,
    mode: str = "Correlation Matrix",
    is_dark: bool = False,
) -> dict[str, Any]:
    """Interactive ECharts Pearson Correlation Matrix or Internal-vs-ESE Bivariate Scatter."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if df.empty or len(df) < 3:
        return spec

    if mode == "Correlation Matrix":
        corr_cols = [
            ("cia1_pct", "CIA 1"),
            ("cia2_pct", "Mid-Sem"),
            ("cia3_pct", "CIA 3"),
            ("attendance", "Att %"),
            ("internal_50", "Int /50"),
            ("end_sem", "ESE /100"),
            ("total_score", "Final"),
        ]
        keys = [k for k, _ in corr_cols]
        labels = [lbl for _, lbl in corr_cols]
        corr_mat = df[keys].corr().to_numpy()

        data = []
        n = len(labels)
        for yi in range(n):
            for xi in range(n):
                if xi <= yi:
                    data.append([xi, n - 1 - yi, round(float(corr_mat[yi, xi]), 2)])

        spec.update(
            {
                "grid": {"left": 62, "right": 16, "top": 14, "bottom": 34},
                "tooltip": {
                    **_ec_tooltip(is_dark, "item"),
                    "formatter": "r = {@[2]}",
                },
                "xAxis": {
                    "type": "category",
                    "data": labels,
                    "axisTick": {"show": False},
                    "axisLine": {"lineStyle": {"color": tok["grid"]}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5, "interval": 0},
                },
                "yAxis": {
                    "type": "category",
                    "data": list(reversed(labels)),
                    "axisTick": {"show": False},
                    "axisLine": {"lineStyle": {"color": tok["grid"]}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
                },
                "visualMap": {
                    "min": -0.2,
                    "max": 1.0,
                    "show": False,
                    "inRange": {
                        "color": (
                            ["#1E293B", "#1D4ED8", "#3B82F6", "#E11D48", "#FB923C"]
                            if is_dark
                            else ["#FFF7ED", "#DBEAFE", "#60A5FA", "#2563EB", "#E11D48"]
                        )
                    },
                },
                "series": [
                    {
                        "name": "Pearson r",
                        "type": "heatmap",
                        "data": data,
                        "universalTransition": True,
                        "itemStyle": {
                            "borderRadius": 5,
                            "borderColor": tok["card_bg"],
                            "borderWidth": 2,
                        },
                        "label": {"show": True, "fontSize": 10.5, "fontWeight": 700, "color": tok["text"]},
                    }
                ],
            }
        )
        return spec

    # Interactive Internal (/50) vs End-Sem (/100) Bivariate Coupling + OLS Fit
    sec_colors = {"2MCA-A": "#2563EB", "2MCA-B": "#F97316"}
    series = []
    for sec in sorted(df["section"].unique()):
        sub = df[df["section"] == sec]
        pts = [
            [round(float(r.internal_50), 2), round(float(r.end_sem), 1), str(r.name), str(r.subject_short)]
            for r in sub.itertuples(index=False)
        ]
        series.append(
            {
                "name": sec,
                "type": "scatter",
                "symbolSize": 8,
                "universalTransition": True,
                "itemStyle": {"color": sec_colors.get(sec, "#2563EB"), "opacity": 0.84},
                "data": pts,
            }
        )

    xv = df["internal_50"].to_numpy(dtype=float)
    yv = df["end_sem"].to_numpy(dtype=float)
    if len(xv) >= 2 and np.std(xv) > 0:
        slope, intercept = np.polyfit(xv, yv, 1)
        x0, x1 = round(float(xv.min()), 1), round(float(xv.max()), 1)
        series.append(
            {
                "name": f"OLS Fit (r={float(np.corrcoef(xv, yv)[0, 1]):.2f})",
                "type": "line",
                "showSymbol": False,
                "data": [[x0, round(float(slope * x0 + intercept), 1)], [x1, round(float(slope * x1 + intercept), 1)]],
                "lineStyle": {"color": "#E11D48", "width": 2.6, "type": "dashed"},
            }
        )

    spec.update(
        {
            "grid": {"left": 46, "right": 16, "top": 38, "bottom": 36},
            "tooltip": {
                **_ec_tooltip(is_dark, "item"),
                "formatter": "<b>{@[2]}</b> ({@[3]})<br/>Internal: {@[0]}/50 · ESE: {@[1]}/100",
            },
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "value",
                "name": "Internal (/50)",
                "nameLocation": "middle",
                "nameGap": 23,
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "min": 15,
                "max": 50,
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "yAxis": {
                "type": "value",
                "name": "End-Sem (/100)",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "min": 25,
                "max": 100,
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "series": series,
        }
    )
    return spec


def echarts_student_radar(
    student_df: pd.DataFrame,
    full_df: pd.DataFrame,
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth 6-axis Radar morphing Student vs Class Average vs Subject Topper."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if student_df.empty:
        return spec

    order = [c for c in SUBJECT_CODES if c in student_df["subject_code"].values]
    indicators = [{"name": str(SUBJECTS[c]["short"]), "min": 25, "max": 100} for c in order]

    stu_vals = [
        round(float(v), 1)
        for v in student_df.set_index("subject_code").reindex(order)["total_score"].tolist()
    ]
    avg_vals = [
        round(float(v), 1)
        for v in full_df.groupby("subject_code")["total_score"].mean().reindex(order).tolist()
    ]
    top_vals = [
        round(float(v), 1)
        for v in full_df.groupby("subject_code")["total_score"].max().reindex(order).tolist()
    ]

    spec.update(
        {
            "tooltip": _ec_tooltip(is_dark, "item"),
            "legend": {
                "bottom": 0,
                "left": "center",
                "itemWidth": 12,
                "itemHeight": 8,
                "textStyle": {"color": tok["muted"], "fontSize": 11},
            },
            "radar": {
                "indicator": indicators,
                "center": ["50%", "46%"],
                "radius": "63%",
                "splitNumber": 4,
                "axisName": {"color": tok["text"], "fontSize": 10.5, "fontWeight": 600},
                "splitLine": {"lineStyle": {"color": tok["grid"]}},
                "splitArea": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
            },
            "series": [
                {
                    "type": "radar",
                    "universalTransition": True,
                    "data": [
                        {
                            "name": "Subject Topper",
                            "value": top_vals,
                            "symbol": "none",
                            "lineStyle": {"color": "#F59E0B", "width": 1.8, "type": "dotted"},
                            "itemStyle": {"color": "#F59E0B"},
                        },
                        {
                            "name": "Class Average",
                            "value": avg_vals,
                            "symbol": "circle",
                            "symbolSize": 5,
                            "lineStyle": {"color": "#E11D48", "width": 2, "type": "dashed"},
                            "itemStyle": {"color": "#E11D48"},
                            "areaStyle": {"color": "rgba(225, 29, 72, 0.08)"},
                        },
                        {
                            "name": "Selected Student",
                            "value": stu_vals,
                            "symbol": "circle",
                            "symbolSize": 7,
                            "lineStyle": {"color": "#2563EB", "width": 3},
                            "itemStyle": {"color": "#2563EB"},
                            "areaStyle": {"color": "rgba(37, 99, 235, 0.25)"},
                        },
                    ],
                }
            ],
        }
    )
    return spec


def echarts_subject_quartiles(
    full_df: pd.DataFrame,
    student_df: pd.DataFrame,
    metric_col: str = "total_score",
    kind: str = "Box Plot",
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth Boxplot / Spread Bars with glowing Coral Diamond student overlay."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if full_df.empty:
        return spec

    order = [c for c in SUBJECT_CODES if c in full_df["subject_code"].unique()]
    labels = [str(SUBJECTS[c]["short"]) for c in order]

    box_data = []
    q1_vals, iqr_vals, mean_vals = [], [], []
    for code in order:
        arr = full_df.loc[full_df["subject_code"] == code, metric_col].to_numpy(dtype=float)
        q0, q25, q50, q75, q100 = np.percentile(arr, [0, 25, 50, 75, 100])
        box_data.append([round(float(x), 1) for x in (q0, q25, q50, q75, q100)])
        q1_vals.append(round(float(q25), 1))
        iqr_vals.append(round(float(q75 - q25), 1))
        mean_vals.append(round(float(np.mean(arr)), 1))

    series: list[dict[str, Any]] = []
    if kind == "Box Plot":
        series.append(
            {
                "name": "Cohort Quartiles",
                "type": "boxplot",
                "data": box_data,
                "universalTransition": True,
                "itemStyle": {
                    "color": "rgba(37, 99, 235, 0.20)",
                    "borderColor": "#2563EB",
                    "borderWidth": 2,
                },
            }
        )
    else:
        series.extend(
            [
                {
                    "name": "_base",
                    "type": "bar",
                    "stack": "iqr",
                    "silent": True,
                    "itemStyle": {"color": "transparent"},
                    "tooltip": {"show": False},
                    "data": q1_vals,
                },
                {
                    "name": "Interquartile Band (Q1–Q3)",
                    "type": "bar",
                    "stack": "iqr",
                    "barMaxWidth": 34,
                    "universalTransition": True,
                    "itemStyle": {
                        "color": "rgba(14, 165, 233, 0.34)",
                        "borderColor": "#0EA5E9",
                        "borderWidth": 1.5,
                        "borderRadius": 6,
                    },
                    "data": iqr_vals,
                },
                {
                    "name": "Class Mean",
                    "type": "line",
                    "smooth": 0.3,
                    "symbol": "circle",
                    "symbolSize": 6,
                    "lineStyle": {"color": "#64748B", "width": 2, "type": "dashed"},
                    "itemStyle": {"color": "#64748B"},
                    "data": mean_vals,
                },
            ]
        )

    if not student_df.empty:
        stu_ord = student_df.set_index("subject_code").reindex(order)
        stu_y = [
            round(float(v), 1) if pd.notna(v) else None
            for v in stu_ord[metric_col].tolist()
        ]
        series.append(
            {
                "name": "Selected Student",
                "type": "line",
                "data": stu_y,
                "symbol": "diamond",
                "symbolSize": 13,
                "universalTransition": True,
                "lineStyle": {"color": "#F97316", "width": 2.4, "type": "dotted"},
                "itemStyle": {"color": "#F97316", "borderColor": tok["card_bg"], "borderWidth": 2},
                "z": 5,
            }
        )

    y_max = 52 if metric_col == "internal_50" else 104
    y_min = 10 if metric_col == "internal_50" else 25
    y_label = "Internal (/50)" if metric_col == "internal_50" else "Composite (/100)"

    spec.update(
        {
            "grid": {"left": 46, "right": 14, "top": 40, "bottom": 28},
            "tooltip": _ec_tooltip(is_dark, "axis"),
            "legend": {
                "top": 2,
                "left": 0,
                "data": [s["name"] for s in series if not s["name"].startswith("_")],
                "textStyle": {"color": tok["muted"], "fontSize": 11},
            },
            "xAxis": {
                "type": "category",
                "data": labels,
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisTick": {"show": False},
                "axisLabel": {"color": tok["muted"], "fontSize": 11, "interval": 0},
            },
            "yAxis": {
                "type": "value",
                "min": y_min,
                "max": y_max,
                "name": y_label,
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "series": series,
        }
    )
    return spec


def echarts_semester_gpa_trend(
    sem1_sgpa: float,
    sem2_sgpa: float,
    projected_sem3: float,
    cohort_sem1_mean: float,
    cohort_sem2_mean: float,
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth SGPA & CGPA progression spline from Sem 1 -> Sem 2 -> Target Sem 3."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)

    sems = ["Sem 1", "Sem 2 (Current)", "Sem 3 (Goal)"]
    stu_sgpa = [round(float(sem1_sgpa), 2), round(float(sem2_sgpa), 2), round(float(projected_sem3), 2)]
    cgpa_curve = [
        round(float(sem1_sgpa), 2),
        round(float((sem1_sgpa + sem2_sgpa) / 2.0), 2),
        round(float((sem1_sgpa + sem2_sgpa + projected_sem3) / 3.0), 2),
    ]
    cohort_curve = [
        round(float(cohort_sem1_mean), 2),
        round(float(cohort_sem2_mean), 2),
        round(float((cohort_sem1_mean + cohort_sem2_mean) / 2.0 + 0.15), 2),
    ]

    tip = _ec_tooltip(is_dark, "axis", "line")
    tip["valueFormatter"] = "%.2f"

    spec.update(
        {
            "grid": {"left": 42, "right": 18, "top": 42, "bottom": 28},
            "tooltip": tip,
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": sems,
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisTick": {"show": False},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "yAxis": {
                "type": "value",
                "min": 4.5,
                "max": 10.2,
                "name": "GPA (/10)",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 11},
            },
            "series": [
                {
                    "name": "Cohort Mean",
                    "type": "line",
                    "data": cohort_curve,
                    "symbol": "circle",
                    "symbolSize": 6,
                    "lineStyle": {"color": "#64748B", "width": 2, "type": "dashed"},
                    "itemStyle": {"color": "#64748B"},
                },
                {
                    "name": "Cumulative CGPA",
                    "type": "line",
                    "smooth": 0.35,
                    "data": cgpa_curve,
                    "symbol": "circle",
                    "symbolSize": 7,
                    "lineStyle": {"color": "#E11D48", "width": 2.6},
                    "itemStyle": {"color": "#E11D48"},
                },
                {
                    "name": "Student SGPA",
                    "type": "line",
                    "smooth": 0.4,
                    "data": stu_sgpa,
                    "symbol": "circle",
                    "symbolSize": 9,
                    "lineStyle": {"color": "#2563EB", "width": 3.2},
                    "itemStyle": {"color": "#2563EB", "borderColor": tok["card_bg"], "borderWidth": 2},
                    "areaStyle": {
                        "color": _linear_grad(
                            0, 0, 0, 1, "rgba(37, 99, 235, 0.24)", "rgba(37, 99, 235, 0.01)"
                        )
                    },
                    "label": {"show": True, "position": "top", "color": tok["text"], "fontSize": 10.5},
                },
            ],
        }
    )
    return spec


def echarts_predictor_feasibility(
    internal_50: float,
    target_grade: str,
    ml_pred_ese: float,
    ml_lo: float,
    ml_hi: float,
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth 60fps End-Sem Feasibility Curve with grade bands, ML CI band & ripple pins."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)

    int_f = round(float(internal_50), 2)
    traj_pts = [[float(x), round(int_f + 0.5 * x, 2)] for x in range(0, 105, 5)]
    ml_final = round(int_f + 0.5 * float(ml_pred_ese), 1)

    cutoff = next(float(t["min_score"]) for t in GRADE_SCALE if t["grade"] == target_grade)
    req_ese = round(max(MIN_ESE_PASS_MARKS, (cutoff - int_f) / 0.5), 1)

    series: list[dict[str, Any]] = [
        {
            "name": "Final Score Trajectory",
            "type": "line",
            "showSymbol": False,
            "data": traj_pts,
            "lineStyle": {"color": "#2563EB", "width": 3.2},
            "markLine": {
                "silent": True,
                "symbol": "none",
                "lineStyle": {"color": "#E11D48", "type": "dotted", "width": 1.8},
                "label": {"formatter": "Min ESE (40)", "color": "#E11D48", "fontSize": 10},
                "data": [{"xAxis": float(MIN_ESE_PASS_MARKS)}],
            },
            "markArea": {
                "silent": True,
                "data": [
                    [
                        {"name": "O (90+)", "yAxis": 90, "itemStyle": {"color": "rgba(16, 185, 129, 0.09)"}, "label": {"position": "insideTopLeft", "color": tok["muted"], "fontSize": 10}},
                        {"yAxis": 100},
                    ],
                    [
                        {"name": "A+ (80–89)", "yAxis": 80, "itemStyle": {"color": "rgba(37, 99, 235, 0.08)"}, "label": {"position": "insideTopLeft", "color": tok["muted"], "fontSize": 10}},
                        {"yAxis": 90},
                    ],
                    [
                        {"name": "A (70–79)", "yAxis": 70, "itemStyle": {"color": "rgba(14, 165, 233, 0.06)"}, "label": {"position": "insideTopLeft", "color": tok["muted"], "fontSize": 10}},
                        {"yAxis": 80},
                    ],
                    [
                        {"name": "ML 90% CI", "xAxis": round(float(ml_lo), 1), "itemStyle": {"color": "rgba(225, 29, 72, 0.08)"}, "label": {"position": "insideBottom", "color": tok["muted"], "fontSize": 10}},
                        {"xAxis": round(float(ml_hi), 1)},
                    ],
                ],
            },
        },
        {
            "name": "ML Forecast",
            "type": "effectScatter",
            "symbolSize": 12,
            "rippleEffect": {"scale": 2.4, "brushType": "stroke"},
            "itemStyle": {"color": "#E11D48"},
            "label": {
                "show": True,
                "position": "bottom",
                "formatter": f"ML: {ml_pred_ese:.1f}",
                "color": tok["text"],
                "fontSize": 11,
                "fontWeight": 700,
            },
            "data": [[round(float(ml_pred_ese), 1), ml_final]],
        },
    ]

    if req_ese <= 100.0 and int_f >= 20.0:
        series.append(
            {
                "name": f"Target {target_grade}",
                "type": "effectScatter",
                "symbol": "diamond",
                "symbolSize": 14,
                "rippleEffect": {"scale": 2.2, "brushType": "stroke"},
                "itemStyle": {"color": "#F97316"},
                "label": {
                    "show": True,
                    "position": "top",
                    "formatter": f"{target_grade}: {req_ese:.1f}/100",
                    "color": tok["text"],
                    "fontSize": 11,
                    "fontWeight": 700,
                },
                "data": [[req_ese, round(int_f + 0.5 * req_ese, 1)]],
            }
        )

    spec.update(
        {
            "grid": {"left": 46, "right": 18, "top": 38, "bottom": 36},
            "tooltip": {
                **_ec_tooltip(is_dark, "axis", "line"),
                "valueFormatter": "%.1f",
            },
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "value",
                "min": 0,
                "max": 100,
                "name": "End-Semester Exam Marks (/100)",
                "nameLocation": "middle",
                "nameGap": 24,
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "yAxis": {
                "type": "value",
                "min": round(max(20.0, int_f - 5.0), 0),
                "max": 102,
                "name": "Final Score (/100)",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "series": series,
        }
    )
    return spec


def echarts_feature_importance(imp_df: pd.DataFrame, is_dark: bool = False) -> dict[str, Any]:
    """Horizontal Solaris gradient bar chart of scikit-learn feature importances."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    feats = [str(f) for f in imp_df["Feature"].tolist()]
    vals = [round(float(v), 1) for v in imp_df["Importance_Pct"].tolist()]
    x_max = round(max(max(vals) * 1.2, 25.0), 0) if vals else 30

    spec.update(
        {
            "grid": {"left": 148, "right": 42, "top": 12, "bottom": 28},
            "tooltip": _ec_tooltip(is_dark, "axis", "%.1f%%"),
            "xAxis": {
                "type": "value",
                "min": 0,
                "max": x_max,
                "name": "Relative Importance (%)",
                "nameLocation": "middle",
                "nameGap": 20,
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "yAxis": {
                "type": "category",
                "data": feats,
                "axisTick": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisLabel": {"color": tok["text"], "fontSize": 11},
            },
            "series": [
                {
                    "name": "Importance",
                    "type": "bar",
                    "barMaxWidth": 22,
                    "data": vals,
                    "itemStyle": {
                        "color": _linear_grad(0, 0, 1, 0, "#F97316", "#2563EB"),
                        "borderRadius": [0, 6, 6, 0],
                    },
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}%",
                        "color": tok["text"],
                        "fontSize": 11,
                        "fontWeight": 600,
                    },
                }
            ],
        }
    )
    return spec


def echarts_explorer_chart(
    df_in: pd.DataFrame,
    chart_kind: str,
    x_col: str,
    y_col: str,
    color_dim: str,
    metric_labels: dict[str, str],
    is_dark: bool = False,
) -> dict[str, Any]:
    """6-family dynamic 60fps ECharts Graph Explorer for Data Manipulation Studio."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if df_in.empty:
        return spec

    groups = sorted(df_in[color_dim].astype(str).unique().tolist())
    if color_dim == "grade":
        groups = [g for g in GRADE_ORDER if g in groups]

    def _grp_color(g: str, idx: int) -> str:
        if color_dim == "grade" and g in GRADE_COLORS:
            return GRADE_COLORS[g]
        return GRADIENT_SEQUENCE[idx % len(GRADIENT_SEQUENCE)]

    if chart_kind == "Scatter + OLS Regression Line":
        series: list[dict[str, Any]] = []
        for idx, grp in enumerate(groups):
            sub = df_in[df_in[color_dim].astype(str) == grp]
            pts = [
                [
                    round(float(getattr(r, x_col)), 2),
                    round(float(getattr(r, y_col)), 2),
                    str(r.name),
                    str(r.subject_short),
                ]
                for r in sub.itertuples(index=False)
            ]
            series.append(
                {
                    "name": grp,
                    "type": "scatter",
                    "symbolSize": 9,
                    "universalTransition": True,
                    "itemStyle": {"color": _grp_color(grp, idx), "opacity": 0.85},
                    "data": pts,
                }
            )
        if len(df_in) >= 2 and df_in[x_col].nunique() > 1:
            xv = df_in[x_col].to_numpy(dtype=float)
            yv = df_in[y_col].to_numpy(dtype=float)
            slope, intercept = np.polyfit(xv, yv, 1)
            x0, x1 = round(float(xv.min()), 2), round(float(xv.max()), 2)
            series.append(
                {
                    "name": f"OLS Fit (y = {slope:.2f}x + {intercept:.1f})",
                    "type": "line",
                    "showSymbol": False,
                    "data": [[x0, round(float(slope * x0 + intercept), 2)], [x1, round(float(slope * x1 + intercept), 2)]],
                    "lineStyle": {"color": "#E11D48", "width": 2.8, "type": "dashed"},
                }
            )
        spec.update(
            {
                "grid": {"left": 50, "right": 18, "top": 42, "bottom": 38},
                "tooltip": {
                    **_ec_tooltip(is_dark, "item"),
                    "formatter": "<b>{@[2]}</b> ({@[3]})<br/>X: {@[0]} · Y: {@[1]}",
                },
                "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
                "xAxis": {
                    "type": "value",
                    "scale": True,
                    "name": metric_labels.get(x_col, x_col),
                    "nameLocation": "middle",
                    "nameGap": 24,
                    "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                    "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
                },
                "yAxis": {
                    "type": "value",
                    "scale": True,
                    "name": metric_labels.get(y_col, y_col),
                    "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                    "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
                },
                "series": series,
            }
        )
        return spec

    if chart_kind in ("Box Quartile Comparison", "Violin Density Split"):
        subj_list = [str(SUBJECTS[c]["short"]) for c in SUBJECT_CODES if str(SUBJECTS[c]["short"]) in df_in["subject_short"].values]
        box_data, mean_data = [], []
        for s_short in subj_list:
            arr = df_in.loc[df_in["subject_short"] == s_short, y_col].to_numpy(dtype=float)
            q0, q25, q50, q75, q100 = np.percentile(arr, [0, 25, 50, 75, 100])
            box_data.append([round(float(v), 2) for v in (q0, q25, q50, q75, q100)])
            mean_data.append(round(float(np.mean(arr)), 2))

        series = [
            {
                "name": "Subject Quartiles",
                "type": "boxplot",
                "data": box_data,
                "universalTransition": True,
                "itemStyle": {
                    "color": "rgba(37, 99, 235, 0.20)" if chart_kind == "Box Quartile Comparison" else "rgba(225, 29, 72, 0.20)",
                    "borderColor": "#2563EB" if chart_kind == "Box Quartile Comparison" else "#E11D48",
                    "borderWidth": 2,
                },
            },
            {
                "name": "Subject Mean",
                "type": "line",
                "smooth": 0.35,
                "symbol": "diamond",
                "symbolSize": 9,
                "data": mean_data,
                "lineStyle": {"color": "#F97316", "width": 2.4, "type": "dotted"},
                "itemStyle": {"color": "#F97316"},
            },
        ]
        spec.update(
            {
                "grid": {"left": 50, "right": 18, "top": 42, "bottom": 30},
                "tooltip": _ec_tooltip(is_dark, "axis"),
                "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
                "xAxis": {
                    "type": "category",
                    "data": subj_list,
                    "axisTick": {"show": False},
                    "axisLine": {"lineStyle": {"color": tok["grid"]}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 11, "interval": 0},
                },
                "yAxis": {
                    "type": "value",
                    "scale": True,
                    "name": metric_labels.get(y_col, y_col),
                    "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                    "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
                },
                "series": series,
            }
        )
        return spec

    if chart_kind == "Distribution Histogram":
        vals = df_in[x_col].to_numpy(dtype=float)
        bins = np.linspace(float(vals.min()), float(vals.max()) + 1e-6, 15)
        bin_labels = [f"{bins[i]:.0f}–{bins[i + 1]:.0f}" for i in range(len(bins) - 1)]
        series = []
        for idx, grp in enumerate(groups):
            g_vals = df_in.loc[df_in[color_dim].astype(str) == grp, x_col].to_numpy(dtype=float)
            hist, _ = np.histogram(g_vals, bins=bins)
            series.append(
                {
                    "name": grp,
                    "type": "bar",
                    "stack": "hist",
                    "universalTransition": True,
                    "data": [int(c) for c in hist],
                    "itemStyle": {"color": _grp_color(grp, idx), "borderRadius": [3, 3, 0, 0]},
                }
            )
        spec.update(
            {
                "grid": {"left": 46, "right": 18, "top": 42, "bottom": 36},
                "tooltip": _ec_tooltip(is_dark, "axis"),
                "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
                "xAxis": {
                    "type": "category",
                    "data": bin_labels,
                    "axisTick": {"show": False},
                    "axisLine": {"lineStyle": {"color": tok["grid"]}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10},
                },
                "yAxis": {
                    "type": "value",
                    "name": "Assessments",
                    "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                    "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                    "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
                },
                "series": series,
            }
        )
        return spec

    if chart_kind == "Sunburst Hierarchy":
        tree = []
        for si, sec in enumerate(sorted(df_in["section"].unique())):
            s_df = df_in[df_in["section"] == sec]
            subj_nodes = []
            for subj_short in sorted(s_df["subject_short"].unique()):
                sb_df = s_df[s_df["subject_short"] == subj_short]
                g_counts = sb_df["grade"].value_counts()
                g_nodes = [
                    {"name": str(g), "value": int(cnt), "itemStyle": {"color": GRADE_COLORS.get(str(g), "#2563EB")}}
                    for g, cnt in g_counts.items()
                ]
                subj_nodes.append({"name": str(subj_short), "children": g_nodes})
            tree.append(
                {
                    "name": str(sec),
                    "itemStyle": {"color": GRADIENT_SEQUENCE[si % len(GRADIENT_SEQUENCE)]},
                    "children": subj_nodes,
                }
            )
        spec.update(
            {
                "tooltip": {**_ec_tooltip(is_dark, "item"), "formatter": "{b}: {c} records"},
                "series": [
                    {
                        "type": "sunburst",
                        "data": tree,
                        "radius": ["15%", "90%"],
                        "universalTransition": True,
                        "itemStyle": {"borderRadius": 4, "borderColor": tok["card_bg"], "borderWidth": 1.5},
                        "label": {"rotate": "radial", "fontSize": 10},
                    }
                ],
            }
        )
        return spec

    # Horizontal Subject Ranking
    ranked = (
        df_in.groupby("subject_short", as_index=False)[y_col]
        .mean()
        .sort_values(y_col, ascending=True)
        .round(2)
    )
    spec.update(
        {
            "grid": {"left": 120, "right": 44, "top": 20, "bottom": 32},
            "tooltip": _ec_tooltip(is_dark, "axis", "%.2f"),
            "xAxis": {
                "type": "value",
                "scale": True,
                "name": metric_labels.get(y_col, y_col),
                "nameLocation": "middle",
                "nameGap": 22,
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "yAxis": {
                "type": "category",
                "data": [str(s) for s in ranked["subject_short"].tolist()],
                "axisTick": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisLabel": {"color": tok["text"], "fontSize": 11},
            },
            "series": [
                {
                    "name": metric_labels.get(y_col, y_col),
                    "type": "bar",
                    "barMaxWidth": 26,
                    "universalTransition": True,
                    "data": [round(float(v), 2) for v in ranked[y_col].tolist()],
                    "itemStyle": {
                        "color": _linear_grad(0, 0, 1, 0, "#F97316", "#2563EB"),
                        "borderRadius": [0, 7, 7, 0],
                    },
                    "label": {"show": True, "position": "right", "color": tok["text"], "fontSize": 11},
                }
            ],
        }
    )
    return spec


def echarts_pivot_heatmap(piv_core: pd.DataFrame, is_dark: bool = False) -> dict[str, Any]:
    """Smooth interactive ECharts Heatmap for Pivot & Cross-Tab Builder."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    if piv_core.empty:
        return spec

    x_labels = [str(c) for c in piv_core.columns.tolist()]
    y_labels = [str(r) for r in piv_core.index.tolist()]
    vals = piv_core.to_numpy(dtype=float)

    data = []
    finite_vals = []
    for yi in range(len(y_labels)):
        for xi in range(len(x_labels)):
            v = vals[yi, xi]
            if not np.isnan(v):
                rv = round(float(v), 1)
                data.append([xi, yi, rv])
                finite_vals.append(rv)

    vmin = min(finite_vals) if finite_vals else 0.0
    vmax = max(finite_vals) if finite_vals else 100.0

    spec.update(
        {
            "grid": {"left": 86, "right": 14, "top": 12, "bottom": 30},
            "tooltip": {**_ec_tooltip(is_dark, "item"), "formatter": "{b}: {@[2]}"},
            "xAxis": {
                "type": "category",
                "data": x_labels,
                "axisTick": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5, "interval": 0},
            },
            "yAxis": {
                "type": "category",
                "data": y_labels,
                "axisTick": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "visualMap": {
                "min": vmin,
                "max": max(vmax, vmin + 1.0),
                "show": False,
                "inRange": {
                    "color": (
                        ["#172554", "#2563EB", "#E11D48"]
                        if is_dark
                        else ["#EFF6FF", "#60A5FA", "#2563EB", "#E11D48"]
                    )
                },
            },
            "series": [
                {
                    "type": "heatmap",
                    "data": data,
                    "universalTransition": True,
                    "itemStyle": {"borderRadius": 5, "borderColor": tok["card_bg"], "borderWidth": 2},
                    "label": {"show": True, "fontSize": 10.5, "fontWeight": 700, "color": tok["text"]},
                }
            ],
        }
    )
    return spec


def echarts_policy_sim(
    before_counts: pd.Series,
    after_counts: pd.Series,
    is_dark: bool = False,
) -> dict[str, Any]:
    """Smooth grouped bar chart comparing Baseline vs Policy Simulation grade counts."""
    tok = _ec_theme_tokens(is_dark)
    spec = _ec_base(is_dark)
    grades = [str(g) for g in GRADE_ORDER]

    spec.update(
        {
            "grid": {"left": 44, "right": 16, "top": 40, "bottom": 28},
            "tooltip": _ec_tooltip(is_dark, "axis"),
            "legend": {"top": 2, "left": 0, "textStyle": {"color": tok["muted"], "fontSize": 11}},
            "xAxis": {
                "type": "category",
                "data": grades,
                "axisTick": {"show": False},
                "axisLine": {"lineStyle": {"color": tok["grid"]}},
                "axisLabel": {"color": tok["text"], "fontSize": 11, "fontWeight": 600},
            },
            "yAxis": {
                "type": "value",
                "name": "Records",
                "nameTextStyle": {"color": tok["muted"], "fontSize": 11},
                "splitLine": {"lineStyle": {"color": tok["grid"], "type": "dashed"}},
                "axisLabel": {"color": tok["muted"], "fontSize": 10.5},
            },
            "series": [
                {
                    "name": "Baseline Cohort",
                    "type": "bar",
                    "barMaxWidth": 26,
                    "data": [int(v) for v in before_counts.reindex(GRADE_ORDER, fill_value=0).tolist()],
                    "itemStyle": {"color": "#64748B", "borderRadius": [6, 6, 0, 0]},
                },
                {
                    "name": "After Policy Simulation",
                    "type": "bar",
                    "barMaxWidth": 26,
                    "data": [int(v) for v in after_counts.reindex(GRADE_ORDER, fill_value=0).tolist()],
                    "itemStyle": {"color": "#2563EB", "borderRadius": [6, 6, 0, 0]},
                    "label": {"show": True, "position": "top", "color": tok["text"], "fontSize": 10.5},
                },
            ],
        }
    )
    return spec


# ===========================================================================
# Preserved Lazy-Loaded Plotly & Seaborn Suite (Academic Rubric & Test Suite)
# ===========================================================================

_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif", size=12),
    margin=dict(l=8, r=12, t=36, b=8),
    hoverlabel=dict(bordercolor="rgba(0,0,0,0)", font_size=12),
    transition=dict(duration=380, easing="cubic-in-out"),
)


def _apply_clean_axes(fig: go.Figure, y_title: str = "", x_title: str = "") -> go.Figure:
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_xaxes(title_text=x_title, showgrid=False, zeroline=False, tickfont=dict(size=11))
    fig.update_yaxes(
        title_text=y_title,
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.16)",
        griddash="dot",
        zeroline=False,
        tickfont=dict(size=11),
    )
    return fig


def subject_cia_breakdown_chart(df: pd.DataFrame, view_mode: str = "Stacked CIA") -> go.Figure:
    """Subject-wise CIA1, Mid-Sem CIA2, CIA3, Attendance & End-Sem breakdown (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    if df.empty:
        return _apply_clean_axes(fig)

    order = [c for c in SUBJECT_CODES if c in df["subject_code"].unique()]
    labels = [str(SUBJECTS[c]["short"]) for c in order]

    if view_mode == "Section A vs B":
        sec_grp = df.groupby(["subject_code", "section"], as_index=False)["total_score"].mean().round(1)
        colors = {"2MCA-A": PALETTE["cobalt"], "2MCA-B": PALETTE["coral"]}
        for sec in ("2MCA-A", "2MCA-B"):
            sub = sec_grp[sec_grp["section"] == sec].set_index("subject_code").reindex(order)
            fig.add_trace(
                go.Bar(
                    name=sec,
                    x=labels,
                    y=sub["total_score"],
                    marker=dict(color=colors[sec], cornerradius=7),
                    text=sub["total_score"].map(lambda v: f"{v:.1f}" if pd.notna(v) else ""),
                    textposition="outside",
                )
            )
        fig.update_layout(barmode="group", legend=dict(orientation="h", y=1.14, x=0), yaxis_range=[0, 106])
        return _apply_clean_axes(fig, y_title="Mean Composite Score (/100)")

    agg = (
        df.groupby("subject_code")
        .agg(
            cia1_w=("cia1_w", "mean"),
            cia2_w=("cia2_w", "mean"),
            cia3_w=("cia3_w", "mean"),
            att_marks=("att_marks", "mean"),
            ese_50=("ese_50", "mean"),
            cia1_pct=("cia1_pct", "mean"),
            cia2_pct=("cia2_pct", "mean"),
            cia3_pct=("cia3_pct", "mean"),
            end_sem=("end_sem", "mean"),
        )
        .reindex(order)
        .round(1)
    )

    if view_mode == "CIA % Compare":
        for label, col, color in [
            ("CIA 1 (%)", "cia1_pct", "#2563EB"),
            ("Mid-Sem CIA 2 (%)", "cia2_pct", "#E11D48"),
            ("CIA 3 Assignment (%)", "cia3_pct", "#F97316"),
            ("End-Sem (%)", "end_sem", "#10B981"),
        ]:
            fig.add_trace(go.Bar(name=label, x=labels, y=agg[col], marker=dict(color=color, cornerradius=6)))
        fig.update_layout(barmode="group", legend=dict(orientation="h", y=1.14, x=0), yaxis_range=[0, 106])
        return _apply_clean_axes(fig, y_title="Normalized Percentage (%)")

    for label, col, color in [
        ("CIA 1 (/10)", "cia1_w", "#1D4ED8"),
        ("Mid-Sem CIA 2 (/25)", "cia2_w", "#2563EB"),
        ("CIA 3 (/10)", "cia3_w", "#F97316"),
        ("Attendance (/5)", "att_marks", "#F59E0B"),
        ("End-Sem (/50)", "ese_50", "#E11D48"),
    ]:
        fig.add_trace(go.Bar(name=label, x=labels, y=agg[col], marker=dict(color=color, cornerradius=4)))
    fig.update_layout(barmode="stack", legend=dict(orientation="h", y=1.15, x=0), yaxis_range=[0, 103])
    return _apply_clean_axes(fig, y_title="Weighted Marks (/100)")


def cia_progression_area_chart(df: pd.DataFrame) -> go.Figure:
    """Smooth spline area chart across semester milestones (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    if df.empty:
        return _apply_clean_axes(fig)

    stages = ["CIA 1", "Mid-Sem (CIA 2)", "CIA 3 (Assign.)", "End-Sem Exam"]
    cols = ["cia1_pct", "cia2_pct", "cia3_pct", "end_sem"]
    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.20)"),
        "2MCA-B": ("#E11D48", "rgba(225, 29, 72, 0.14)"),
    }
    for sec in sorted(df["section"].unique()):
        sub = df[df["section"] == sec]
        means = [round(float(sub[c].mean()), 1) for c in cols]
        line_col, fill_col = palette_map.get(sec, ("#F97316", "rgba(249, 115, 22, 0.16)"))
        fig.add_trace(
            go.Scatter(
                name=sec,
                x=stages,
                y=means,
                mode="lines+markers+text",
                text=[f"{m:.1f}%" for m in means],
                textposition="top center",
                line=dict(color=line_col, width=3.2, shape="spline", smoothing=0.85),
                fill="tozeroy",
                fillcolor=fill_col,
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=1.14, x=0), yaxis_range=[48, 94])
    return _apply_clean_axes(fig, y_title="Cohort Mean (%)")


def cohort_gpa_trend_chart(leaderboard_df: pd.DataFrame) -> go.Figure:
    """Cohort-wide Sem 1 SGPA -> Sem 2 SGPA -> Cumulative CGPA trend (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    if leaderboard_df.empty:
        return _apply_clean_axes(fig)

    stages = ["Sem 1 SGPA", "Sem 2 SGPA (Current)", "Cumulative CGPA"]
    cols = ["sem1_sgpa", "sem2_sgpa", "cgpa"]
    palette_map = {
        "2MCA-A": ("#2563EB", "rgba(37, 99, 235, 0.18)"),
        "2MCA-B": ("#F97316", "rgba(249, 115, 22, 0.16)"),
    }
    for sec in sorted(leaderboard_df["section"].unique()):
        sub = leaderboard_df[leaderboard_df["section"] == sec]
        means = [round(float(sub[c].mean()), 2) for c in cols]
        line_col, fill_col = palette_map.get(sec, ("#E11D48", "rgba(225, 29, 72, 0.14)"))
        fig.add_trace(
            go.Scatter(
                name=f"{sec} Mean",
                x=stages,
                y=means,
                mode="lines+markers+text",
                text=[f"{m:.2f}" for m in means],
                textposition="top center",
                line=dict(color=line_col, width=3.2, shape="spline", smoothing=0.75),
                fill="tozeroy",
                fillcolor=fill_col,
            )
        )
    fig.update_layout(legend=dict(orientation="h", y=1.14, x=0), yaxis_range=[6.0, 9.6])
    return _apply_clean_axes(fig, y_title="Mean GPA (10-Point Scale)")


def grade_distribution_chart(df: pd.DataFrame, mode: str = "Donut") -> go.Figure:
    """Interactive Donut or Sunburst chart of CHRIST University letter grades (Plotly)."""
    import plotly.express as px
    import plotly.graph_objects as go

    if df.empty:
        return _apply_clean_axes(go.Figure())

    if mode == "Sunburst":
        sun_df = df.groupby(["section", "grade"], as_index=False).size().rename(columns={"size": "count"})
        fig = px.sunburst(
            sun_df,
            path=["section", "grade"],
            values="count",
            color="grade",
            color_discrete_map={**GRADE_COLORS, "(?)": "#2563EB"},
        )
        fig.update_layout(**_BASE_LAYOUT)
        return fig

    counts = df["grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
    counts = counts[counts > 0]
    fig = go.Figure(
        go.Pie(
            labels=counts.index.tolist(),
            values=counts.values.tolist(),
            hole=0.66,
            sort=False,
            marker=dict(colors=[GRADE_COLORS[g] for g in counts.index]),
        )
    )
    fig.update_layout(**_BASE_LAYOUT)
    return fig


def student_radar_chart(student_df: pd.DataFrame, full_df: pd.DataFrame) -> go.Figure:
    """Interactive 6-axis Radar comparing Student vs Class Average vs Subject Topper (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    if student_df.empty:
        return fig

    order = [c for c in SUBJECT_CODES if c in student_df["subject_code"].values]
    categories = [str(SUBJECTS[c]["short"]) for c in order]
    stu_vals = student_df.set_index("subject_code").reindex(order)["total_score"].tolist()
    avg_vals = full_df.groupby("subject_code")["total_score"].mean().reindex(order).round(1).tolist()
    top_vals = full_df.groupby("subject_code")["total_score"].max().reindex(order).round(1).tolist()

    cat_closed = categories + [categories[0]]
    fig.add_trace(go.Scatterpolar(r=top_vals + [top_vals[0]], theta=cat_closed, name="Subject Topper"))
    fig.add_trace(go.Scatterpolar(r=avg_vals + [avg_vals[0]], theta=cat_closed, name="Class Average", fill="toself"))
    fig.add_trace(go.Scatterpolar(r=stu_vals + [stu_vals[0]], theta=cat_closed, name="Selected Student", fill="toself"))
    fig.update_layout(**_BASE_LAYOUT)
    return fig


def subject_box_with_student_chart(
    full_df: pd.DataFrame,
    student_df: pd.DataFrame,
    metric_col: str = "total_score",
    kind: str = "Box Plot",
) -> go.Figure:
    """Class score distribution (Box or Violin) with diamond overlay markers (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure()
    if full_df.empty:
        return _apply_clean_axes(fig)

    order = [c for c in SUBJECT_CODES if c in full_df["subject_code"].unique()]
    for i, code in enumerate(order):
        sub = full_df[full_df["subject_code"] == code]
        short = str(SUBJECTS[code]["short"])
        color = GRADIENT_SEQUENCE[i % len(GRADIENT_SEQUENCE)]
        if kind == "Violin Plot":
            fig.add_trace(go.Violin(x=[short] * len(sub), y=sub[metric_col], name=short, line_color=color, showlegend=False))
        else:
            fig.add_trace(go.Box(x=[short] * len(sub), y=sub[metric_col], name=short, marker_color=color, showlegend=False))

    if not student_df.empty:
        stu_ord = student_df.set_index("subject_code").reindex(order).dropna(subset=[metric_col])
        fig.add_trace(
            go.Scatter(
                x=[str(SUBJECTS[c]["short"]) for c in stu_ord.index],
                y=stu_ord[metric_col],
                mode="markers+lines",
                name="Selected Student",
            )
        )
    return _apply_clean_axes(fig)


def semester_gpa_trend_chart(
    sem1_sgpa: float,
    sem2_sgpa: float,
    projected_sem3: float,
    cohort_sem1_mean: float,
    cohort_sem2_mean: float,
) -> go.Figure:
    """SGPA & CGPA progression chart from Sem 1 to Sem 2 and Projected Sem 3 (Plotly)."""
    import plotly.graph_objects as go

    sems = ["Sem 1 (Completed)", "Sem 2 (Current)", "Sem 3 (Target Plan)"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(name="Cohort Mean SGPA", x=sems, y=[cohort_sem1_mean, cohort_sem2_mean, (cohort_sem1_mean + cohort_sem2_mean) / 2.0 + 0.15]))
    fig.add_trace(go.Scatter(name="Student SGPA", x=sems, y=[sem1_sgpa, sem2_sgpa, projected_sem3]))
    return _apply_clean_axes(fig, y_title="GPA (10-Point Scale)")


def predictor_feasibility_curve(
    internal_50: float,
    target_grade: str,
    ml_pred_ese: float,
    ml_lo: float,
    ml_hi: float,
) -> go.Figure:
    """Plot Final Course Score vs End-Sem Exam Score (/100) with grade bands & ML prediction (Plotly)."""
    import plotly.graph_objects as go

    ese_grid = np.linspace(0, 100, 101)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ese_grid, y=internal_50 + 0.5 * ese_grid, mode="lines", name="Final Score Trajectory"))
    fig.add_trace(go.Scatter(x=[ml_pred_ese], y=[internal_50 + 0.5 * ml_pred_ese], mode="markers", name="ML Forecast"))
    cutoff = next(float(t["min_score"]) for t in GRADE_SCALE if t["grade"] == target_grade)
    req_ese = max(MIN_ESE_PASS_MARKS, (cutoff - internal_50) / 0.5)
    if req_ese <= 100.0 and internal_50 >= 20.0:
        fig.add_trace(go.Scatter(x=[req_ese], y=[internal_50 + 0.5 * req_ese], mode="markers", name=f"Required for {target_grade}"))
    return _apply_clean_axes(fig, y_title="Final Course Score (/100)", x_title="End-Semester Exam Marks (/100)")


def ml_feature_importance_chart(imp_df: pd.DataFrame) -> go.Figure:
    """Horizontal Solaris gradient bar chart of scikit-learn feature importances (Plotly)."""
    import plotly.graph_objects as go

    fig = go.Figure(go.Bar(x=imp_df["Importance_Pct"], y=imp_df["Feature"], orientation="h"))
    return _apply_clean_axes(fig, x_title="Relative Predictive Importance (%)")


def seaborn_statistical_figure(
    df: pd.DataFrame,
    mode: str = "Correlation Heatmap",
    is_dark: bool = False,
) -> plt.Figure:
    """Render a crisp, exact-sized Seaborn statistical plot in the Solaris palette."""
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.pyplot as plt
    import seaborn as sns

    text_col = "#E2E8F0" if is_dark else "#1E293B"
    muted_col = "#94A3B8" if is_dark else "#475569"

    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(5.6, 3.45), dpi=100)
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")

    cmap = LinearSegmentedColormap.from_list(
        "christgrade_solaris",
        ["#FDBA74", "#FFF7ED", "#93C5FD", "#2563EB", "#E11D48"]
        if not is_dark
        else ["#F97316", "#1E293B", "#2563EB", "#60A5FA", "#FB7185"],
    )

    if df.empty or len(df) < 3:
        ax.text(0.5, 0.5, "Not enough filtered records for statistical plot", ha="center", color=text_col)
        ax.axis("off")
        return fig

    if mode == "Correlation Heatmap":
        corr_cols = {
            "cia1_pct": "CIA 1 %",
            "cia2_pct": "Mid-Sem %",
            "cia3_pct": "CIA 3 %",
            "attendance": "Att %",
            "internal_50": "Int /50",
            "end_sem": "ESE /100",
            "total_score": "Final /100",
        }
        corr = df[list(corr_cols.keys())].rename(columns=corr_cols).corr()
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(
            corr,
            mask=mask,
            cmap=cmap,
            vmin=-0.2,
            vmax=1.0,
            annot=True,
            fmt=".2f",
            linewidths=1.0,
            cbar_kws={"shrink": 0.76},
            annot_kws={"size": 8, "weight": "bold"},
            ax=ax,
        )
        ax.tick_params(colors=text_col, labelsize=8)
        plt.xticks(rotation=22, ha="right")
        plt.yticks(rotation=0)
        cbar = ax.collections[0].colorbar
        if cbar is not None:
            cbar.ax.yaxis.set_tick_params(color=muted_col, labelcolor=muted_col, labelsize=7.5)
    else:
        sns.kdeplot(
            data=df,
            x="internal_50",
            y="end_sem",
            fill=True,
            cmap="rocket_r" if not is_dark else "mako",
            alpha=0.72,
            levels=7,
            thresh=0.05,
            ax=ax,
        )
        sns.scatterplot(
            data=df,
            x="internal_50",
            y="end_sem",
            hue="section",
            palette={"2MCA-A": "#2563EB", "2MCA-B": "#F97316"},
            s=24,
            alpha=0.85,
            edgecolor="white",
            linewidth=0.4,
            ax=ax,
        )
        ax.set_xlabel("Internal CIA Total (/50)", color=text_col, fontsize=9, fontweight="bold")
        ax.set_ylabel("End-Semester Score (/100)", color=text_col, fontsize=9, fontweight="bold")
        ax.tick_params(colors=muted_col, labelsize=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color(muted_col)
            ax.spines[spine].set_alpha(0.35)
        leg = ax.legend(title="Cohort", frameon=False, fontsize=7.5, title_fontsize=8)
        if leg:
            plt.setp(leg.get_texts(), color=text_col)
            plt.setp(leg.get_title(), color=text_col)

    fig.tight_layout()
    return fig


@st.cache_data(show_spinner=False, max_entries=24)
def render_seaborn_png_cached(
    plot_df: pd.DataFrame,
    mode: str,
    is_dark: bool,
) -> bytes:
    """Cache rasterized Seaborn statistical figure at exact viewport DPI for <1ms repeat renders."""
    import matplotlib.pyplot as plt

    fig = seaborn_statistical_figure(plot_df, mode=mode, is_dark=is_dark)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return buf.getvalue()
