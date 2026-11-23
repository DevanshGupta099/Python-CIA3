"""End-to-end automated tests for ChristGrade: DB, CRUD, Validations, Analytics, Advisor, Charts & UI."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.advisor import _answer_academic_query, generate_student_html_report
from utils.analytics import (
    GlobalFilters,
    apply_global_filters,
    build_groupby_summary,
    build_pivot_matrix,
    build_student_leaderboard,
    calculate_target_ese_table,
    compute_normalized_and_outliers,
    enrich_assessments,
    predict_ese_score,
    recommend_sgpa_plan,
    train_ml_ese_predictor,
)
from utils.charts import (
    cia_progression_area_chart,
    grade_distribution_chart,
    ml_feature_importance_chart,
    predictor_feasibility_curve,
    render_seaborn_png_cached,
    seaborn_statistical_figure,
    semester_gpa_trend_chart,
    student_radar_chart,
    subject_box_with_student_chart,
    subject_cia_breakdown_chart,
)
from utils.constants import GRADE_ORDER, RISK_LEVELS, SUBJECT_CODES
from utils.database import (
    CSV_SEED_PATH,
    DB_PATH,
    bulk_update_from_editor,
    delete_assessment_record,
    delete_student_profile,
    get_audit_log_df,
    init_database,
    load_raw_assessments,
    sync_validated_dataframe,
    upsert_student_assessment,
)
from utils.validators import (
    validate_assessment_scores,
    validate_email,
    validate_imported_dataframe,
    validate_register_no,
    validate_student_name,
    validate_student_record,
)


def test_validations() -> None:
    ok, _, reg = validate_register_no("2547199")
    assert ok and reg == "2547199"
    bad_ok, err, _ = validate_register_no("ABC123")
    assert not bad_ok and "7-digit" in err

    ok_n, _, name = validate_student_name("  devansh gupta ")
    assert ok_n and name == "Devansh Gupta"
    bad_n, _, _ = validate_student_name("12345!!")
    assert not bad_n

    ok_e, _, mail = validate_email("", "2547199")
    assert ok_e and mail == "2547199@mca.christuniversity.in"
    bad_e, _, _ = validate_email("not-an-email")
    assert not bad_e

    ok_s, errs, _ = validate_assessment_scores(22.0, 55.0, -1.0, 105.0, 120.0)
    assert not ok_s and len(errs) == 5

    ok_rec, errs_rec, payload = validate_student_record(
        "2547901", "Rohan Nair", "2MCA-A", "", 8.2, "MCA411-2", 18, 42, 19, 93, 86
    )
    assert ok_rec and not errs_rec and payload["email"] == "2547901@mca.christuniversity.in"
    print("[PASS] Input & CSV validations verified.")


def test_crud_and_sync() -> None:
    init_database(force_reset=True)
    assert DB_PATH.exists() and CSV_SEED_PATH.exists()

    base = load_raw_assessments()
    assert len(base) == 360 and base["reg_no"].nunique() == 60

    _, _, payload = validate_student_record(
        "2547999", "Test Scholar", "2MCA-B", "scholar@mca.christuniversity.in",
        8.4, "MCA411-2", 19.0, 44.0, 18.5, 96.0, 90.0
    )
    saved, _ = upsert_student_assessment(payload, allow_overwrite=False)
    assert saved

    dup_saved, _ = upsert_student_assessment(payload, allow_overwrite=False)
    assert not dup_saved

    payload["cia3"] = 20.0
    up_saved, _ = upsert_student_assessment(payload, allow_overwrite=True)
    assert up_saved

    after_create = load_raw_assessments()
    created_row = after_create[
        (after_create["reg_no"] == "2547999") & (after_create["subject_code"] == "MCA411-2")
    ]
    assert len(created_row) == 1 and float(created_row.iloc[0]["cia3"]) == 20.0

    edit_slice = created_row.copy()
    edit_slice["end_sem"] = 94.0
    cnt, _ = bulk_update_from_editor(edit_slice)
    assert cnt == 1

    ass_id = int(created_row.iloc[0]["assessment_id"])
    del_ok, _ = delete_assessment_record(ass_id)
    assert del_ok

    upsert_student_assessment(payload, allow_overwrite=True)
    payload2 = {**payload, "subject_code": "MCA412"}
    upsert_student_assessment(payload2, allow_overwrite=True)
    del_stu_ok, _ = delete_student_profile("2547999")
    assert del_stu_ok

    csv_sample = pd.read_csv(CSV_SEED_PATH).head(6)
    v_ok, v_errs, clean_csv = validate_imported_dataframe(csv_sample)
    assert v_ok and not v_errs
    synced_cnt, _ = sync_validated_dataframe(clean_csv, replace_all=False)
    assert synced_cnt == 6

    logs = get_audit_log_df(limit=10)
    assert not logs.empty

    init_database(force_reset=True)
    print("[PASS] SQLite3 CRUD, duplicate guard, bulk edit, sync, and audit log verified.")


def test_analytics_advisor_and_charts() -> None:
    raw = load_raw_assessments()
    df = enrich_assessments(raw)
    assert {"internal_50", "total_score", "grade", "z_score", "percentile", "risk_status"}.issubset(df.columns)

    flt = GlobalFilters(
        sections=("2MCA-A",),
        subjects=SUBJECT_CODES[:4],
        grades=GRADE_ORDER,
        risk_levels=RISK_LEVELS,
        att_only_shortage=False,
    )
    sub_df = apply_global_filters(df, flt)
    assert not sub_df.empty and set(sub_df["section"].unique()) == {"2MCA-A"}

    lb = build_student_leaderboard(df)
    assert len(lb) == 60 and "sem2_sgpa" in lb.columns and "cgpa" in lb.columns

    stu_df = df[df["reg_no"] == "2547101"]
    stu_meta = lb[lb["reg_no"] == "2547101"].iloc[0]
    html_bytes = generate_student_html_report(stu_df, stu_meta)
    assert b"ChristGrade CIA Progress Card" in html_bytes and b"2547101" in html_bytes

    for q in (
        "Executive summary",
        "Toughest subjects",
        "Attendance < 85%",
        "CIA3 top improvers",
        "Devansh",
        "2547101",
        "Compare 2MCA-A",
        "Top 5",
    ):
        ans = _answer_academic_query(q, df)
        assert len(ans) > 30

    sb_cols = [
        "section", "cia1_pct", "cia2_pct", "cia3_pct",
        "attendance", "internal_50", "end_sem", "total_score",
    ]
    png_bytes = render_seaborn_png_cached(df[sb_cols], "Correlation Heatmap", False)
    assert png_bytes.startswith(b"\x89PNG") and len(png_bytes) > 5000

    grp = build_groupby_summary(df, ["section", "subject_code"])
    assert len(grp) == 12 and "IQR_Total" in grp.columns

    piv = build_pivot_matrix(df, "subject_short", "section", "total_score", "Mean")
    assert not piv.empty

    norm = compute_normalized_and_outliers(df, "total_score")
    assert norm["min_max_scaled"].between(0.0, 1.0).all()

    tgt_tbl = calculate_target_ese_table(42.0, 92.0)
    o_row = tgt_tbl[tgt_tbl["Target Grade"] == "O"].iloc[0]
    assert float(o_row["Required End-Sem (/100)"]) == 96.0

    plan = recommend_sgpa_plan(stu_df, 8.8)
    assert len(plan) == 6

    bundle = train_ml_ese_predictor(df)
    assert bundle.r2_cv > 0.35
    pred, lo, hi = predict_ese_score(bundle, 17.0, 40.0, 18.0, 92.0, 8.3, 4)
    assert lo <= pred <= hi

    assert subject_cia_breakdown_chart(df, "Stacked CIA").data
    assert cia_progression_area_chart(df).data
    assert grade_distribution_chart(df, "Donut").data
    assert student_radar_chart(stu_df, df).data
    assert subject_box_with_student_chart(df, stu_df, "total_score", "Violin Plot").data
    assert semester_gpa_trend_chart(8.1, 8.5, 8.9, 7.4, 7.6).data
    assert predictor_feasibility_curve(41.0, "A+", pred, lo, hi).data
    assert ml_feature_importance_chart(bundle.feature_importance).data

    sb_fig1 = seaborn_statistical_figure(df, "Correlation Heatmap", is_dark=False)
    plt.close(sb_fig1)
    print(f"[PASS] Analytics, Advisor, HTML Report, ML Predictor (CV R2={bundle.r2_cv}), and Solaris charts verified.")


def test_streamlit_pages_headless() -> None:
    app_path = str(ROOT / "app.py")
    at = AppTest.from_file(app_path, default_timeout=30)
    at.run()
    assert not at.exception, f"Overview page raised exception: {at.exception}"

    for view_rel in [
        "views/student_analytics.py",
        "views/predictor.py",
        "views/data_lab.py",
        "views/crud_manager.py",
    ]:
        at.switch_page(view_rel)
        at.run()
        assert not at.exception, f"{view_rel} raised exception: {at.exception}"
    print("[PASS] All 5 upgraded Solaris Streamlit views rendered headlessly with zero exceptions.")


if __name__ == "__main__":
    test_validations()
    test_crud_and_sync()
    test_analytics_advisor_and_charts()
    test_streamlit_pages_headless()
    print("\nALL CHRISTGRADE V2 SOLARIS CHECKS PASSED SUCCESSFULLY!")
