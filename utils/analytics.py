"""Pandas/NumPy academic analytics, data manipulation helpers, and scikit-learn predictor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import streamlit as st

from utils.constants import (
    GRADE_POINTS,
    GRADE_SCALE,
    MIN_ATTENDANCE_ELIGIBILITY,
    MIN_ESE_PASS_MARKS,
    MIN_INTERNAL_PASS_MARKS,
    MIN_TOTAL_PASS_MARKS,
    RISK_LEVELS,
    SECTIONS,
    SUBJECT_CODES,
    TARGET_GRADES,
)
from utils.database import load_raw_assessments


@dataclass(frozen=True)
class GlobalFilters:
    sections: tuple[str, ...]
    subjects: tuple[str, ...]
    grades: tuple[str, ...]
    risk_levels: tuple[str, ...]
    att_only_shortage: bool = False

    def describe(self, total_rows: int, total_students: int) -> str:
        sec_txt = (
            "All sections (2MCA-A & B)"
            if len(self.sections) == len(SECTIONS)
            else ", ".join(self.sections)
        )
        sub_txt = (
            f"all {len(SUBJECT_CODES)} MCA subjects"
            if len(self.subjects) == len(SUBJECT_CODES)
            else f"{len(self.subjects)} selected subject(s)"
        )
        extra: list[str] = []
        if self.grades and len(self.grades) < len(GRADE_SCALE):
            extra.append(f"Grades: {', '.join(self.grades)}")
        if self.risk_levels and len(self.risk_levels) < len(RISK_LEVELS):
            extra.append(f"Standing: {', '.join(self.risk_levels)}")
        if self.att_only_shortage:
            extra.append("Attendance < 85% only")
        suffix = f" · {' · '.join(extra)}" if extra else ""
        return f"Showing **{total_students}** students (**{total_rows}** assessments) across **{sec_txt}** · {sub_txt}{suffix}"


def attendance_to_marks(attendance: np.ndarray | pd.Series | float) -> np.ndarray | float:
    """CHRIST University attendance rubric out of 5 internal marks."""
    arr = np.asarray(attendance, dtype=float)
    marks = np.select(
        [arr >= 95.0, arr >= 90.0, arr >= 85.0, arr >= 80.0],
        [5.0, 4.0, 3.0, 2.0],
        default=0.0,
    )
    return float(marks) if np.ndim(attendance) == 0 else marks


def assign_grade_and_gp(
    total_score: np.ndarray,
    internal_50: np.ndarray,
    end_sem_100: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized CHRIST University 10-point grading with internal & ESE pass rules."""
    passed = (
        (internal_50 >= MIN_INTERNAL_PASS_MARKS)
        & (end_sem_100 >= MIN_ESE_PASS_MARKS)
        & (total_score >= MIN_TOTAL_PASS_MARKS)
    )

    grades = np.full(len(total_score), "F", dtype=object)
    gps = np.zeros(len(total_score), dtype=float)

    # Iterate ascending from P to O so higher thresholds overwrite cleanly
    for tier in reversed(GRADE_SCALE[:-1]):
        mask = passed & (total_score >= float(tier["min_score"]))
        grades[mask] = str(tier["grade"])
        gps[mask] = float(tier["gp"])

    return grades, gps, passed


def enrich_assessments(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Compute all weighted CIA totals, grades, z-scores, percentiles, and risk flags."""
    if raw_df.empty:
        return raw_df.copy()

    df = raw_df.copy()
    df["cia1_pct"] = np.round((df["cia1"] / 20.0) * 100.0, 1)
    df["cia2_pct"] = np.round((df["cia2"] / 50.0) * 100.0, 1)
    df["cia3_pct"] = np.round((df["cia3"] / 20.0) * 100.0, 1)

    df["cia1_w"] = np.round(df["cia1"] * 0.5, 2)   # /10
    df["cia2_w"] = np.round(df["cia2"] * 0.5, 2)   # /25
    df["cia3_w"] = np.round(df["cia3"] * 0.5, 2)   # /10
    df["att_marks"] = attendance_to_marks(df["attendance"].to_numpy())  # /5

    df["internal_50"] = np.round(
        df["cia1_w"] + df["cia2_w"] + df["cia3_w"] + df["att_marks"], 2
    )
    df["internal_pct"] = np.round((df["internal_50"] / 50.0) * 100.0, 1)
    df["ese_50"] = np.round(df["end_sem"] * 0.5, 2)
    df["total_score"] = np.round(df["internal_50"] + df["ese_50"], 2)

    grades, gps, passed = assign_grade_and_gp(
        df["total_score"].to_numpy(),
        df["internal_50"].to_numpy(),
        df["end_sem"].to_numpy(),
    )
    df["grade"] = grades
    df["grade_point"] = gps
    df["is_pass"] = passed
    df["att_eligible"] = df["attendance"] >= MIN_ATTENDANCE_ELIGIBILITY
    df["cia_momentum"] = np.round(df["cia3_pct"] - df["cia1_pct"], 1)

    # Subject-wise class benchmark, Z-score, and percentile standing
    subj_mean = df.groupby("subject_code")["total_score"].transform("mean")
    subj_std = df.groupby("subject_code")["total_score"].transform("std").replace(0, 1.0)
    df["class_avg_score"] = np.round(subj_mean, 1)
    df["class_avg_internal"] = np.round(
        df.groupby("subject_code")["internal_50"].transform("mean"), 2
    )
    df["score_vs_avg"] = np.round(df["total_score"] - df["class_avg_score"], 1)
    df["z_score"] = np.round((df["total_score"] - subj_mean) / subj_std, 2)
    df["percentile"] = np.round(
        df.groupby("subject_code")["total_score"].rank(pct=True) * 100.0, 1
    )

    # Academic standing / risk classification
    df["risk_status"] = np.select(
        [
            (~df["is_pass"]) | (df["attendance"] < 80.0) | (df["internal_50"] < 24.0),
            (~df["att_eligible"]) | (df["total_score"] < 60.0) | (df["internal_50"] < 30.0),
            (df["total_score"] >= 80.0) & df["att_eligible"],
        ],
        ["At Risk", "Watchlist", "Thriving"],
        default="On Track",
    )

    return df


@st.cache_data(show_spinner=False)
def load_enriched_cached(db_version: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fast in-memory cached loader returning (enriched_df, full_leaderboard_df) keyed by db_version."""
    _ = db_version
    raw = load_raw_assessments()
    enriched = enrich_assessments(raw)
    lb = build_student_leaderboard(enriched)
    return enriched, lb


def apply_global_filters(df: pd.DataFrame, filters: GlobalFilters) -> pd.DataFrame:
    """Filter enriched DataFrame according to toolbar filter selections."""
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    if filters.sections:
        mask &= df["section"].isin(filters.sections)
    if filters.subjects:
        mask &= df["subject_code"].isin(filters.subjects)
    if filters.grades:
        mask &= df["grade"].isin(filters.grades)
    if filters.risk_levels:
        mask &= df["risk_status"].isin(filters.risk_levels)
    if filters.att_only_shortage:
        mask &= ~df["att_eligible"]
    return df.loc[mask].copy()


def build_student_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate credit-weighted Sem 2 SGPA, CGPA, CIA trends, and standing per student."""
    if df.empty:
        return pd.DataFrame()

    work = df.copy()
    work["weighted_gp"] = work["grade_point"] * work["credits"]

    grouped = (
        work.groupby(["reg_no", "name", "section", "email", "sem1_sgpa"], as_index=False)
        .agg(
            subjects_taken=("subject_code", "count"),
            total_credits=("credits", "sum"),
            weighted_gp_sum=("weighted_gp", "sum"),
            avg_internal_50=("internal_50", "mean"),
            avg_total_100=("total_score", "mean"),
            avg_attendance=("attendance", "mean"),
            avg_cia1_pct=("cia1_pct", "mean"),
            avg_cia2_pct=("cia2_pct", "mean"),
            avg_cia3_pct=("cia3_pct", "mean"),
            avg_ese=("end_sem", "mean"),
            backlogs=("is_pass", lambda s: int((~s).sum())),
            shortage_subjects=("att_eligible", lambda s: int((~s).sum())),
        )
    )

    grouped["sem2_sgpa"] = np.round(
        grouped["weighted_gp_sum"] / grouped["total_credits"].replace(0, 1), 2
    )
    grouped["cgpa"] = np.round((grouped["sem1_sgpa"] + grouped["sem2_sgpa"]) / 2.0, 2)
    grouped["sgpa_delta"] = np.round(grouped["sem2_sgpa"] - grouped["sem1_sgpa"], 2)
    grouped["avg_internal_50"] = np.round(grouped["avg_internal_50"], 2)
    grouped["avg_total_100"] = np.round(grouped["avg_total_100"], 1)
    grouped["avg_attendance"] = np.round(grouped["avg_attendance"], 1)

    # Sparkline array for Streamlit AreaChartColumn / LineChartColumn: [CIA1%, CIA2%, CIA3%, ESE%]
    grouped["trajectory"] = [
        [round(c1, 1), round(c2, 1), round(c3, 1), round(ese, 1)]
        for c1, c2, c3, ese in zip(
            grouped["avg_cia1_pct"],
            grouped["avg_cia2_pct"],
            grouped["avg_cia3_pct"],
            grouped["avg_ese"],
            strict=False,
        )
    ]

    grouped["standing"] = np.select(
        [
            (grouped["backlogs"] > 0) | (grouped["avg_attendance"] < 82.0),
            (grouped["shortage_subjects"] > 0) | (grouped["sem2_sgpa"] < 6.8),
            grouped["sem2_sgpa"] >= 8.5,
        ],
        ["At Risk", "Watchlist", "Thriving"],
        default="On Track",
    )

    grouped = grouped.sort_values(
        ["sem2_sgpa", "avg_total_100"], ascending=[False, False]
    ).reset_index(drop=True)
    grouped["rank"] = np.arange(1, len(grouped) + 1)
    return grouped


# ---------------------------------------------------------------------------
# Data Manipulation Studio Helpers (GroupBy, Pivot, Normalization, Outliers)
# ---------------------------------------------------------------------------

def build_groupby_summary(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Multi-metric statistical aggregation using Pandas GroupBy & NumPy IQR."""
    if df.empty or not group_cols:
        return pd.DataFrame()

    summary = (
        df.groupby(group_cols, as_index=False)
        .agg(
            Records=("total_score", "count"),
            Mean_Internal_50=("internal_50", "mean"),
            Mean_ESE_100=("end_sem", "mean"),
            Mean_Total=("total_score", "mean"),
            Median_Total=("total_score", "median"),
            Std_Dev=("total_score", "std"),
            IQR_Total=("total_score", lambda s: float(np.percentile(s, 75) - np.percentile(s, 25))),
            Min_Total=("total_score", "min"),
            Max_Total=("total_score", "max"),
            Pass_Rate_Pct=("is_pass", lambda s: float(s.mean() * 100.0)),
            Avg_Attendance_Pct=("attendance", "mean"),
        )
        .round(2)
    )
    summary["Std_Dev"] = summary["Std_Dev"].fillna(0.0)
    return summary


def build_pivot_matrix(
    df: pd.DataFrame,
    index_col: str,
    columns_col: str,
    value_col: str,
    agg_name: str,
) -> pd.DataFrame:
    """Create a dynamic Pivot Table or Cross-Tabulation with margins."""
    if df.empty:
        return pd.DataFrame()

    if agg_name == "Count (Cross-Tab)":
        ct = pd.crosstab(df[index_col], df[columns_col], margins=True, margins_name="All")
        return ct

    agg_map = {
        "Mean": "mean",
        "Median": "median",
        "Max": "max",
        "Min": "min",
        "Std Dev": "std",
    }
    piv = pd.pivot_table(
        df,
        index=index_col,
        columns=columns_col,
        values=value_col,
        aggfunc=agg_map.get(agg_name, "mean"),
        margins=True,
        margins_name="Overall",
    )
    return piv.round(2)


def compute_normalized_and_outliers(df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    """Apply Min-Max normalization, Z-score standardization, percentile rank, and IQR outlier flags."""
    if df.empty:
        return pd.DataFrame()

    out = df[
        ["reg_no", "name", "section", "subject_code", "subject_short", metric_col, "grade"]
    ].copy()
    vals = out[metric_col].to_numpy(dtype=float)
    vmin, vmax = float(np.min(vals)), float(np.max(vals))
    span = (vmax - vmin) if vmax > vmin else 1.0

    mean = float(np.mean(vals))
    std = float(np.std(vals)) or 1.0
    q1, q3 = np.percentile(vals, [25, 75])
    iqr = float(q3 - q1)
    lo_fence, hi_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr

    out["min_max_scaled"] = np.round((vals - vmin) / span, 3)
    out["z_score_global"] = np.round((vals - mean) / std, 2)
    out["percentile_rank"] = np.round(out[metric_col].rank(pct=True) * 100.0, 1)
    out["iqr_outlier"] = np.where(
        vals < lo_fence,
        "Low Outlier",
        np.where(vals > hi_fence, "High Outlier", "Normal Range"),
    )
    return out.sort_values(metric_col, ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# End-Semester Target Score Calculator & scikit-learn Predictive Engine
# ---------------------------------------------------------------------------

def calculate_target_ese_table(
    internal_50: float,
    attendance_pct: float,
) -> pd.DataFrame:
    """Compute exact End-Sem score (/100) required for every CHRIST target grade."""
    rows: list[dict[str, Any]] = []
    tier_lookup = {str(t["grade"]): t for t in GRADE_SCALE}

    for g in TARGET_GRADES:
        tier = tier_lookup[g]
        cutoff = float(tier["min_score"])
        gp = float(tier["gp"])

        if internal_50 < MIN_INTERNAL_PASS_MARKS:
            status = "Internal < 20/50 (Ineligible)"
            feasible = False
            req_ese = np.nan
        else:
            raw_needed = (cutoff - internal_50) / 0.5
            req_ese = max(MIN_ESE_PASS_MARKS, raw_needed)
            if req_ese > 100.0:
                status = "Mathematically Capped (>100)"
                feasible = False
            elif attendance_pct < MIN_ATTENDANCE_ELIGIBILITY:
                status = "Needs Condonation (<85% Att.)"
                feasible = True
            elif req_ese <= 55.0:
                status = "Comfortably Achievable"
                feasible = True
            elif req_ese <= 78.0:
                status = "Focused Preparation"
                feasible = True
            else:
                status = "High-Effort Stretch"
                feasible = True

        rows.append(
            {
                "Target Grade": g,
                "Descriptor": str(tier["label"]),
                "Grade Point": gp,
                "Min Final (/100)": cutoff,
                "Current Internal (/50)": round(internal_50, 2),
                "Required End-Sem (/100)": round(float(req_ese), 1) if not np.isnan(req_ese) else None,
                "Feasible": feasible,
                "Assessment": status,
            }
        )

    return pd.DataFrame(rows)


def recommend_sgpa_plan(student_df: pd.DataFrame, target_sgpa: float) -> pd.DataFrame:
    """Credit-weighted End-Sem score roadmap across all subjects to achieve target SGPA."""
    if student_df.empty:
        return pd.DataFrame()

    plan = student_df[
        ["subject_code", "subject_name", "credits", "internal_50", "attendance", "class_avg_score"]
    ].copy()

    # Start each subject at its highest feasible grade, then greedily relax or tighten toward target_sgpa
    achievable_tiers: list[list[tuple[str, float, float]]] = []
    for row in plan.itertuples(index=False):
        options: list[tuple[str, float, float]] = []
        if float(row.internal_50) >= MIN_INTERNAL_PASS_MARKS:
            for g in TARGET_GRADES:
                cutoff = next(float(t["min_score"]) for t in GRADE_SCALE if t["grade"] == g)
                req = max(MIN_ESE_PASS_MARKS, (cutoff - float(row.internal_50)) / 0.5)
                if req <= 100.0:
                    options.append((g, GRADE_POINTS[g], round(req, 1)))
        if not options:
            options = [("F", 0.0, 100.0)]
        achievable_tiers.append(options)

    # Choose balanced minimum effort combination whose weighted GP >= target_sgpa (or max possible)
    # Start from easiest passable option and upgrade the subject with lowest required ESE jump per credit
    chosen_idx = [len(opts) - 1 for opts in achievable_tiers]
    credits = plan["credits"].to_numpy(dtype=float)
    total_credits = float(np.sum(credits)) or 1.0

    def current_sgpa() -> float:
        gps = np.array([achievable_tiers[i][chosen_idx[i]][1] for i in range(len(chosen_idx))])
        return float(np.sum(gps * credits) / total_credits)

    while current_sgpa() < target_sgpa - 1e-6:
        best_subj = -1
        best_cost = float("inf")
        for i, opts in enumerate(achievable_tiers):
            cur = chosen_idx[i]
            if cur > 0:
                next_ese = opts[cur - 1][2]
                cur_ese = opts[cur][2]
                gp_gain = (opts[cur - 1][1] - opts[cur][1]) * credits[i]
                # Prefer lower absolute required ESE & higher credit leverage
                cost = (next_ese * 0.7 + (next_ese - cur_ese) * 0.3) / max(gp_gain, 0.1)
                if cost < best_cost:
                    best_cost = cost
                    best_subj = i
        if best_subj == -1:
            break
        chosen_idx[best_subj] -= 1

    plan["Recommended Grade"] = [achievable_tiers[i][chosen_idx[i]][0] for i in range(len(plan))]
    plan["Target GP"] = [achievable_tiers[i][chosen_idx[i]][1] for i in range(len(plan))]
    plan["Required End-Sem (/100)"] = [
        achievable_tiers[i][chosen_idx[i]][2] for i in range(len(plan))
    ]
    plan["Effort Band"] = np.select(
        [
            plan["Required End-Sem (/100)"] <= 55,
            plan["Required End-Sem (/100)"] <= 75,
            plan["Required End-Sem (/100)"] <= 90,
        ],
        ["Moderate (<=55)", "Focused (56-75)", "Intensive (76-90)"],
        default="Peak (>90)",
    )
    return plan


@dataclass
class PredictorBundle:
    ridge_pipe: Pipeline
    rf_pipe: Pipeline
    r2_cv: float
    mae_cv: float
    residual_std: float
    feature_importance: pd.DataFrame


FEATURE_COLS = ["cia1_pct", "cia2_pct", "cia3_pct", "attendance", "sem1_sgpa", "credits"]
FEATURE_LABELS = {
    "cia1_pct": "CIA 1 Score (%)",
    "cia2_pct": "Mid-Sem CIA 2 (%)",
    "cia3_pct": "CIA 3 Assignment (%)",
    "attendance": "Attendance (%)",
    "sem1_sgpa": "Sem 1 SGPA",
    "credits": "Course Credits",
}


def train_ml_ese_predictor(df: pd.DataFrame) -> PredictorBundle:
    """Train cross-validated scikit-learn Ridge & Random Forest models on live cohort data."""
    X = df[FEATURE_COLS].to_numpy(dtype=float)
    y = df["end_sem"].to_numpy(dtype=float)

    ridge_pipe = Pipeline(
        [("scaler", StandardScaler()), ("model", Ridge(alpha=2.0))]
    )
    rf_pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=120, max_depth=6, min_samples_leaf=3, random_state=42
                ),
            ),
        ]
    )

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    oof_preds = cross_val_predict(ridge_pipe, X, y, cv=cv)
    r2_cv = float(r2_score(y, oof_preds))
    mae_cv = float(mean_absolute_error(y, oof_preds))
    residual_std = float(np.std(y - oof_preds))

    ridge_pipe.fit(X, y)
    rf_pipe.fit(X, y)

    rf_imp = rf_pipe.named_steps["model"].feature_importances_
    imp_df = (
        pd.DataFrame(
            {
                "Feature": [FEATURE_LABELS[c] for c in FEATURE_COLS],
                "Importance_Pct": np.round(rf_imp * 100.0, 1),
            }
        )
        .sort_values("Importance_Pct", ascending=True)
        .reset_index(drop=True)
    )

    return PredictorBundle(
        ridge_pipe=ridge_pipe,
        rf_pipe=rf_pipe,
        r2_cv=round(r2_cv, 3),
        mae_cv=round(mae_cv, 2),
        residual_std=round(residual_std, 2),
        feature_importance=imp_df,
    )


def predict_ese_score(
    bundle: PredictorBundle,
    cia1: float,
    cia2: float,
    cia3: float,
    attendance: float,
    sem1_sgpa: float,
    credits: int,
    model_choice: str = "Ensemble (Ridge + Random Forest)",
) -> tuple[float, float, float]:
    """Predict expected End-Sem score (/100) with 90% confidence interval."""
    x_row = np.array(
        [[(cia1 / 20.0) * 100.0, (cia2 / 50.0) * 100.0, (cia3 / 20.0) * 100.0, attendance, sem1_sgpa, float(credits)]],
        dtype=float,
    )
    pred_ridge = float(bundle.ridge_pipe.predict(x_row)[0])
    pred_rf = float(bundle.rf_pipe.predict(x_row)[0])

    if model_choice == "Ridge Linear Regression":
        pred = pred_ridge
    elif model_choice == "Random Forest Regressor":
        pred = pred_rf
    else:
        pred = 0.6 * pred_ridge + 0.4 * pred_rf

    pred = float(np.clip(pred, 0.0, 100.0))
    margin = 1.645 * bundle.residual_std
    lo = float(np.clip(pred - margin, 0.0, 100.0))
    hi = float(np.clip(pred + margin, 0.0, 100.0))
    return round(pred, 1), round(lo, 1), round(hi, 1)
