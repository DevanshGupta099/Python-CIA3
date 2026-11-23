"""Comprehensive input and dataset validations for ChristGrade CRUD & Sync."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from utils.constants import MAX_MARKS, SECTIONS, SUBJECT_CODES

REG_NO_PATTERN = re.compile(r"^2\d{6}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s\.'-]{1,59}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_register_no(reg_no: str | int | None) -> tuple[bool, str, str]:
    """Validate 7-digit CHRIST University register number (e.g., 2547101)."""
    raw = str(reg_no or "").strip()
    if not raw:
        return False, "Register Number is required (e.g., 2547101).", ""
    if not REG_NO_PATTERN.match(raw):
        return (
            False,
            "Register Number must be a 7-digit CHRIST ID starting with '2' (e.g., 2547101).",
            raw,
        )
    return True, "", raw


def validate_student_name(name: str | None) -> tuple[bool, str, str]:
    """Validate student full name (alphabetic characters, spaces, dots, 2-60 chars)."""
    raw = re.sub(r"\s+", " ", str(name or "").strip())
    if not raw:
        return False, "Student Name cannot be empty.", ""
    if len(raw) < 2 or len(raw) > 60:
        return False, "Student Name must be between 2 and 60 characters.", raw
    if not NAME_PATTERN.match(raw):
        return (
            False,
            "Student Name can only contain letters, spaces, dots, hyphens, or apostrophes.",
            raw,
        )
    cleaned = " ".join(part.capitalize() if not part.isupper() else part for part in raw.split(" "))
    return True, "", cleaned


def validate_email(email: str | None, reg_no: str = "") -> tuple[bool, str, str]:
    """Validate student academic email address."""
    raw = str(email or "").strip().lower()
    if not raw:
        if reg_no and REG_NO_PATTERN.match(reg_no):
            return True, "", f"{reg_no}@mca.christuniversity.in"
        return False, "Email address is required.", ""
    if not EMAIL_PATTERN.match(raw):
        return False, "Enter a valid email address (e.g., name@mca.christuniversity.in).", raw
    return True, "", raw


def validate_section(section: str | None) -> tuple[bool, str, str]:
    """Validate MCA cohort section."""
    raw = str(section or "").strip().upper()
    if raw not in SECTIONS:
        return False, f"Section must be one of {', '.join(SECTIONS)}.", raw
    return True, "", raw


def validate_subject_code(subject_code: str | None) -> tuple[bool, str, str]:
    """Validate MCA subject code."""
    raw = str(subject_code or "").strip().upper()
    if raw not in SUBJECT_CODES:
        return False, f"Subject code must be one of {', '.join(SUBJECT_CODES)}.", raw
    return True, "", raw


def _check_numeric_bound(
    value: Any, field_label: str, min_val: float, max_val: float
) -> tuple[bool, str, float]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f"{field_label} is required ({min_val:g} to {max_val:g}).", 0.0
    try:
        num = float(value)
    except (TypeError, ValueError):
        return False, f"{field_label} must be a valid number.", 0.0
    if math.isnan(num) or math.isinf(num):
        return False, f"{field_label} cannot be NaN or infinite.", 0.0
    if num < min_val or num > max_val:
        return False, f"{field_label} must be between {min_val:g} and {max_val:g} (got {num:g}).", num
    return True, "", round(num, 2)


def validate_assessment_scores(
    cia1: Any,
    cia2: Any,
    cia3: Any,
    attendance: Any,
    end_sem: Any,
) -> tuple[bool, list[str], dict[str, float]]:
    """Validate all CIA, attendance, and End-Semester score bounds."""
    errors: list[str] = []
    cleaned: dict[str, float] = {}

    specs = [
        ("cia1", cia1, "CIA 1 Marks", 0.0, MAX_MARKS["cia1"]),
        ("cia2", cia2, "Mid-Sem (CIA 2) Marks", 0.0, MAX_MARKS["cia2"]),
        ("cia3", cia3, "CIA 3 (Assignment) Marks", 0.0, MAX_MARKS["cia3"]),
        ("attendance", attendance, "Attendance %", 0.0, MAX_MARKS["attendance"]),
        ("end_sem", end_sem, "End-Semester Marks", 0.0, MAX_MARKS["end_sem"]),
    ]

    for key, val, label, lo, hi in specs:
        ok, err, num = _check_numeric_bound(val, label, lo, hi)
        if not ok:
            errors.append(err)
        cleaned[key] = num

    return len(errors) == 0, errors, cleaned


def validate_student_record(
    reg_no: Any,
    name: Any,
    section: Any,
    email: Any,
    sem1_sgpa: Any,
    subject_code: Any,
    cia1: Any,
    cia2: Any,
    cia3: Any,
    attendance: Any,
    end_sem: Any,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Full end-to-end validation for creating or updating a student + assessment entry."""
    errors: list[str] = []

    ok_reg, err_reg, clean_reg = validate_register_no(reg_no)
    if not ok_reg:
        errors.append(err_reg)

    ok_name, err_name, clean_name = validate_student_name(name)
    if not ok_name:
        errors.append(err_name)

    ok_sec, err_sec, clean_sec = validate_section(section)
    if not ok_sec:
        errors.append(err_sec)

    ok_mail, err_mail, clean_mail = validate_email(email, clean_reg)
    if not ok_mail:
        errors.append(err_mail)

    ok_sgpa, err_sgpa, clean_sgpa = _check_numeric_bound(sem1_sgpa, "Sem 1 SGPA", 0.0, 10.0)
    if not ok_sgpa:
        errors.append(err_sgpa)

    ok_sub, err_sub, clean_sub = validate_subject_code(subject_code)
    if not ok_sub:
        errors.append(err_sub)

    ok_scores, score_errs, clean_scores = validate_assessment_scores(
        cia1, cia2, cia3, attendance, end_sem
    )
    if not ok_scores:
        errors.extend(score_errs)

    payload = {
        "reg_no": clean_reg,
        "name": clean_name,
        "section": clean_sec,
        "email": clean_mail,
        "sem1_sgpa": clean_sgpa,
        "subject_code": clean_sub,
        **clean_scores,
    }
    return len(errors) == 0, errors, payload


def validate_imported_dataframe(df: pd.DataFrame) -> tuple[bool, list[str], pd.DataFrame]:
    """Validate an uploaded CSV or synced Google Sheet DataFrame before DB merge."""
    required_cols = {
        "reg_no",
        "name",
        "section",
        "subject_code",
        "cia1",
        "cia2",
        "cia3",
        "attendance",
        "end_sem",
    }
    if df is None or df.empty:
        return False, ["Uploaded dataset is empty."], pd.DataFrame()

    normalized = df.copy()
    normalized.columns = [str(c).strip().lower() for c in normalized.columns]
    missing = sorted(required_cols - set(normalized.columns))
    if missing:
        return (
            False,
            [f"Missing required columns: {', '.join(missing)}."],
            pd.DataFrame(),
        )

    if "email" not in normalized.columns:
        normalized["email"] = ""
    if "sem1_sgpa" not in normalized.columns:
        normalized["sem1_sgpa"] = 7.5

    row_errors: list[str] = []
    valid_rows: list[dict[str, Any]] = []

    for idx, row in normalized.iterrows():
        ok, errs, cleaned = validate_student_record(
            reg_no=row.get("reg_no"),
            name=row.get("name"),
            section=row.get("section"),
            email=row.get("email"),
            sem1_sgpa=row.get("sem1_sgpa", 7.5),
            subject_code=row.get("subject_code"),
            cia1=row.get("cia1"),
            cia2=row.get("cia2"),
            cia3=row.get("cia3"),
            attendance=row.get("attendance"),
            end_sem=row.get("end_sem"),
        )
        if not ok:
            row_errors.append(f"Row {int(idx) + 1}: {'; '.join(errs)}")
            if len(row_errors) >= 8:
                row_errors.append("Additional row validation errors truncated...")
                break
        else:
            valid_rows.append(cleaned)

    if row_errors:
        return False, row_errors, pd.DataFrame()

    clean_df = pd.DataFrame(valid_rows)
    dup_mask = clean_df.duplicated(subset=["reg_no", "subject_code"], keep=False)
    if dup_mask.any():
        dups = clean_df.loc[dup_mask, ["reg_no", "subject_code"]].drop_duplicates()
        pairs = ", ".join(f"{r.reg_no}-{r.subject_code}" for r in dups.itertuples())
        return False, [f"Duplicate (reg_no, subject_code) rows found in file: {pairs}"], pd.DataFrame()

    return True, [], clean_df
