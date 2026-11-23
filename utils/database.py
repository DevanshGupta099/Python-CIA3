"""SQLite3 persistence, realistic CHRIST 2MCA dataset seeding, CRUD, and Live Sync."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterator
import urllib.request

import numpy as np
import pandas as pd

from utils.constants import CURRENT_SEMESTER, SECTIONS, SUBJECT_CODES, SUBJECTS

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "christgrade.db"
CSV_SEED_PATH = DATA_DIR / "christ_mca_cia_dataset.csv"

_FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Bhavya", "Chaitanya", "Deepika",
    "Devansh", "Diya", "Gaurav", "Harshita", "Ishaan", "Jhanvi", "Karthik", "Kavya",
    "Lakshya", "Meera", "Nandini", "Nikhil", "Pranav", "Priya", "Rahul", "Rhea",
    "Rohan", "ritika", "Sahil", "Sanjana", "Shreya", "Siddharth", " Sneha", "Tanvi",
    "Varun", "Vedant", "Vidya", "Vikram", "Yash", "Zoya", "Abhinav", "aiswarya",
    "Amrita", "Anirudh", "Aparna", "Ashwin", "Darshan", "Divya", "Esha", "Gautam",
    "Hrithik", "Keerthana", "Madhav", "Malavika", "Naveen", "Neha", "Pooja", "Raghav",
    "ritvik", "Swathi", "Tejas", "vishnu",
]

_LAST_NAMES = [
    "Gupta", "Sharma", "Nair", "Menon", "Reddy", "Iyer", "Mathew", "Joseph",
    "Verma", "Kulkarni", "Patel", "Rao", "Krishnan", "Thomas", "George", "Shetty",
    "Deshmukh", "Chatterjee", "Bhat", "pillai", "Agarwal", "Mishra", "Joshi", "Hegde",
    "kapoor", "varma", "Banerjee", "Nambiar", "Kurian", "ferns",
]


@contextmanager
def _get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            reg_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            section TEXT NOT NULL,
            email TEXT NOT NULL,
            sem1_sgpa REAL NOT NULL DEFAULT 7.5,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            semester TEXT NOT NULL DEFAULT 'Sem 2',
            cia1 REAL NOT NULL CHECK(cia1 >= 0 AND cia1 <= 20),
            cia2 REAL NOT NULL CHECK(cia2 >= 0 AND cia2 <= 50),
            cia3 REAL NOT NULL CHECK(cia3 >= 0 AND cia3 <= 20),
            attendance REAL NOT NULL CHECK(attendance >= 0 AND attendance <= 100),
            end_sem REAL NOT NULL CHECK(end_sem >= 0 AND end_sem <= 100),
            updated_at TEXT NOT NULL,
            UNIQUE(reg_no, subject_code, semester),
            FOREIGN KEY (reg_no) REFERENCES students(reg_no) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_ref TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def _generate_seed_dataframe() -> pd.DataFrame:
    """Generate a realistic 60-student (360-assessment) CHRIST 2MCA dataset."""
    rng = np.random.default_rng(2026)
    rows: list[dict[str, Any]] = []

    # Subject difficulty offsets so box/radar plots show meaningful variation
    subj_offsets = {
        "MCA411-2": 3.5,   # Python Programming (strong practical engagement)
        "MCA412": -1.5,    # Adv DBMS
        "MCA413": 2.5,     # Software Engineering
        "MCA414": -3.5,    # Networks & Security (toughest theory)
        "MCA415": -2.0,    # Machine Learning
        "MCA416": 2.0,     # Cloud & DevOps
    }

    used_names: set[str] = set()
    for idx in range(60):
        section = SECTIONS[0] if idx < 30 else SECTIONS[1]
        serial = (idx + 1) if idx < 30 else (idx - 29)
        prefix = "25471" if idx < 30 else "25472"
        reg_no = f"{prefix}{serial:02d}"

        if idx == 0:
            full_name = "Devansh Gupta"
        else:
            fname = _FIRST_NAMES[idx % len(_FIRST_NAMES)].strip().title()
            lname = _LAST_NAMES[(idx * 7 + 3) % len(_LAST_NAMES)].strip().title()
            full_name = f"{fname} {lname}"
            if full_name in used_names:
                full_name = f"{fname} {lname} {chr(65 + (idx % 5))}"
        used_names.add(full_name)

        email_slug = re.sub(r"[^a-z0-9]", ".", full_name.lower()).strip(".")
        email = f"{email_slug}.{reg_no[-3:]}@mca.christuniversity.in"

        # Assign realistic student archetype
        archetype_roll = idx % 10
        if idx == 0 or archetype_roll in (0, 1):
            base_ability = rng.uniform(82, 93)    # High achiever
            att_base = rng.uniform(92, 99)
        elif archetype_roll in (2, 3, 4, 5):
            base_ability = rng.uniform(68, 82)    # Solid mid-upper cohort
            att_base = rng.uniform(87, 96)
        elif archetype_roll in (6, 7, 8):
            base_ability = rng.uniform(54, 69)    # Developing / mixed strengths
            att_base = rng.uniform(84, 92)
        else:
            base_ability = rng.uniform(41, 56)    # At-risk / condonation zone
            att_base = rng.uniform(76, 86)

        sem1_sgpa = float(np.clip((base_ability / 10.0) + rng.normal(0.15, 0.35), 5.2, 9.8))
        sem1_sgpa = round(sem1_sgpa, 2)

        for sub_code in SUBJECT_CODES:
            offset = subj_offsets[sub_code]
            # Individual subject affinity so radar chart reveals genuine weak/strong subjects
            affinity = rng.normal(0.0, 6.5)
            latent_pct = np.clip(base_ability + offset + affinity, 30.0, 98.5)

            cia1 = np.clip((latent_pct / 100.0) * 20.0 + rng.normal(0, 1.3), 5.0, 20.0)
            cia2 = np.clip((latent_pct / 100.0) * 50.0 + rng.normal(-0.6, 3.2), 12.0, 50.0)
            # Slight positive momentum in CIA3 assignment for dedicated students
            cia3 = np.clip((latent_pct / 100.0) * 20.0 + rng.normal(0.7, 1.2), 6.0, 20.0)
            attendance = np.clip(att_base + rng.normal(0, 2.8), 72.0, 100.0)
            end_sem = np.clip(latent_pct + rng.normal(0, 5.2), 28.0, 99.0)

            rows.append(
                {
                    "reg_no": reg_no,
                    "name": full_name,
                    "section": section,
                    "email": email,
                    "sem1_sgpa": sem1_sgpa,
                    "subject_code": sub_code,
                    "semester": CURRENT_SEMESTER,
                    "cia1": round(float(cia1), 1),
                    "cia2": round(float(cia2), 1),
                    "cia3": round(float(cia3), 1),
                    "attendance": round(float(attendance), 1),
                    "end_sem": round(float(end_sem), 1),
                }
            )

    return pd.DataFrame(rows)


def _log_audit(conn: sqlite3.Connection, action: str, target_ref: str, details: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO audit_log (action, target_ref, details, created_at) VALUES (?, ?, ?, ?)",
        (action, target_ref, details, now),
    )


def init_database(force_reset: bool = False) -> None:
    """Initialize SQLite schema and seed CHRIST 2MCA dataset if empty or requested."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seed_df = _generate_seed_dataframe()
    if not CSV_SEED_PATH.exists() or force_reset:
        seed_df.to_csv(CSV_SEED_PATH, index=False)

    with _get_connection() as conn:
        _create_tables(conn)
        if force_reset:
            conn.execute("DELETE FROM assessments;")
            conn.execute("DELETE FROM students;")
            conn.execute("DELETE FROM audit_log;")

        cur = conn.execute("SELECT COUNT(*) AS cnt FROM assessments;")
        count = int(cur.fetchone()["cnt"])
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            students_df = seed_df[
                ["reg_no", "name", "section", "email", "sem1_sgpa"]
            ].drop_duplicates(subset=["reg_no"])

            conn.executemany(
                """
                INSERT INTO students (reg_no, name, section, email, sem1_sgpa, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (r.reg_no, r.name, r.section, r.email, float(r.sem1_sgpa), now)
                    for r in students_df.itertuples(index=False)
                ],
            )
            conn.executemany(
                """
                INSERT INTO assessments (
                    reg_no, subject_code, semester, cia1, cia2, cia3, attendance, end_sem, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.reg_no,
                        r.subject_code,
                        r.semester,
                        float(r.cia1),
                        float(r.cia2),
                        float(r.cia3),
                        float(r.attendance),
                        float(r.end_sem),
                        now,
                    )
                    for r in seed_df.itertuples(index=False)
                ],
            )
            _log_audit(
                conn,
                "SEED",
                "2MCA Cohort",
                f"Initialized SQLite database with {len(students_df)} students and {len(seed_df)} CIA records.",
            )
            conn.commit()


def load_raw_assessments() -> pd.DataFrame:
    """Read joined student and assessment records from SQLite."""
    init_database(force_reset=False)
    query = """
        SELECT
            a.id AS assessment_id,
            s.reg_no,
            s.name,
            s.section,
            s.email,
            s.sem1_sgpa,
            a.subject_code,
            a.semester,
            a.cia1,
            a.cia2,
            a.cia3,
            a.attendance,
            a.end_sem,
            a.updated_at
        FROM assessments a
        JOIN students s ON s.reg_no = a.reg_no
        ORDER BY s.reg_no ASC, a.subject_code ASC;
    """
    with _get_connection() as conn:
        df = pd.read_sql_query(query, conn)

    df["subject_name"] = df["subject_code"].map(lambda c: str(SUBJECTS[c]["name"]))
    df["subject_short"] = df["subject_code"].map(lambda c: str(SUBJECTS[c]["short"]))
    df["credits"] = df["subject_code"].map(lambda c: int(SUBJECTS[c]["credits"]))
    df["faculty"] = df["subject_code"].map(lambda c: str(SUBJECTS[c]["faculty"]))
    return df


def upsert_student_assessment(payload: dict[str, Any], allow_overwrite: bool = True) -> tuple[bool, str]:
    """Create or update a student profile and subject CIA assessment record."""
    init_database(force_reset=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _get_connection() as conn:
        existing_ass = conn.execute(
            """
            SELECT id FROM assessments
            WHERE reg_no = ? AND subject_code = ? AND semester = ?
            """,
            (payload["reg_no"], payload["subject_code"], CURRENT_SEMESTER),
        ).fetchone()

        if existing_ass and not allow_overwrite:
            return (
                False,
                f"Assessment for {payload['reg_no']} in {payload['subject_code']} already exists. "
                "Use the Update tab or enable overwrite.",
            )

        existing_stu = conn.execute(
            "SELECT reg_no FROM students WHERE reg_no = ?",
            (payload["reg_no"],),
        ).fetchone()

        if existing_stu:
            conn.execute(
                """
                UPDATE students
                SET name = ?, section = ?, email = ?, sem1_sgpa = ?
                WHERE reg_no = ?
                """,
                (
                    payload["name"],
                    payload["section"],
                    payload["email"],
                    float(payload["sem1_sgpa"]),
                    payload["reg_no"],
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO students (reg_no, name, section, email, sem1_sgpa, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["reg_no"],
                    payload["name"],
                    payload["section"],
                    payload["email"],
                    float(payload["sem1_sgpa"]),
                    now,
                ),
            )

        if existing_ass:
            conn.execute(
                """
                UPDATE assessments
                SET cia1 = ?, cia2 = ?, cia3 = ?, attendance = ?, end_sem = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    float(payload["cia1"]),
                    float(payload["cia2"]),
                    float(payload["cia3"]),
                    float(payload["attendance"]),
                    float(payload["end_sem"]),
                    now,
                    int(existing_ass["id"]),
                ),
            )
            action = "UPDATE"
            msg = f"Updated {payload['subject_code']} scores for {payload['name']} ({payload['reg_no']})."
        else:
            conn.execute(
                """
                INSERT INTO assessments (
                    reg_no, subject_code, semester, cia1, cia2, cia3, attendance, end_sem, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["reg_no"],
                    payload["subject_code"],
                    CURRENT_SEMESTER,
                    float(payload["cia1"]),
                    float(payload["cia2"]),
                    float(payload["cia3"]),
                    float(payload["attendance"]),
                    float(payload["end_sem"]),
                    now,
                ),
            )
            action = "CREATE"
            msg = f"Created {payload['subject_code']} record for {payload['name']} ({payload['reg_no']})."

        _log_audit(
            conn,
            action,
            f"{payload['reg_no']} · {payload['subject_code']}",
            f"CIA1={payload['cia1']}, CIA2={payload['cia2']}, CIA3={payload['cia3']}, "
            f"Att={payload['attendance']}%, ESE={payload['end_sem']}",
        )
        conn.commit()
    return True, msg


def bulk_update_from_editor(edited_df: pd.DataFrame) -> tuple[int, str]:
    """Persist inline table edits from st.data_editor directly to SQLite."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated = 0
    with _get_connection() as conn:
        for row in edited_df.itertuples(index=False):
            conn.execute(
                """
                UPDATE assessments
                SET cia1 = ?, cia2 = ?, cia3 = ?, attendance = ?, end_sem = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    round(float(row.cia1), 2),
                    round(float(row.cia2), 2),
                    round(float(row.cia3), 2),
                    round(float(row.attendance), 2),
                    round(float(row.end_sem), 2),
                    now,
                    int(row.assessment_id),
                ),
            )
            updated += 1
        _log_audit(
            conn,
            "BULK_EDIT",
            f"{updated} rows",
            f"Saved inline score updates across {updated} assessment records.",
        )
        conn.commit()
    return updated, f"Saved updates across {updated} records to SQLite."


def delete_assessment_record(assessment_id: int) -> tuple[bool, str]:
    """Delete a single subject assessment row; cleans up orphan student if none remain."""
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT reg_no, subject_code FROM assessments WHERE id = ?",
            (int(assessment_id),),
        ).fetchone()
        if not row:
            return False, "Assessment record not found."

        reg_no, sub_code = str(row["reg_no"]), str(row["subject_code"])
        conn.execute("DELETE FROM assessments WHERE id = ?", (int(assessment_id),))

        rem = conn.execute(
            "SELECT COUNT(*) AS cnt FROM assessments WHERE reg_no = ?",
            (reg_no,),
        ).fetchone()
        if int(rem["cnt"]) == 0:
            conn.execute("DELETE FROM students WHERE reg_no = ?", (reg_no,))

        _log_audit(conn, "DELETE", f"{reg_no} · {sub_code}", "Deleted subject assessment record.")
        conn.commit()
    return True, f"Deleted {sub_code} record for Register No. {reg_no}."


def delete_student_profile(reg_no: str) -> tuple[bool, str]:
    """Delete a student and cascade-remove all their subject assessments."""
    with _get_connection() as conn:
        stu = conn.execute(
            "SELECT name FROM students WHERE reg_no = ?",
            (reg_no,),
        ).fetchone()
        if not stu:
            return False, f"Student {reg_no} not found."

        name = str(stu["name"])
        conn.execute("DELETE FROM students WHERE reg_no = ?", (reg_no,))
        _log_audit(
            conn,
            "DELETE_STUDENT",
            reg_no,
            f"Removed student {name} ({reg_no}) and all linked CIA records.",
        )
        conn.commit()
    return True, f"Removed student {name} ({reg_no}) and all linked CIA assessments."


def sync_validated_dataframe(clean_df: pd.DataFrame, replace_all: bool = False) -> tuple[int, str]:
    """Merge or replace SQLite records from a validated CSV / Google Sheets DataFrame."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_connection() as conn:
        if replace_all:
            conn.execute("DELETE FROM assessments;")
            conn.execute("DELETE FROM students;")

        for row in clean_df.itertuples(index=False):
            conn.execute(
                """
                INSERT INTO students (reg_no, name, section, email, sem1_sgpa, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(reg_no) DO UPDATE SET
                    name = excluded.name,
                    section = excluded.section,
                    email = excluded.email,
                    sem1_sgpa = excluded.sem1_sgpa;
                """,
                (row.reg_no, row.name, row.section, row.email, float(row.sem1_sgpa), now),
            )
            conn.execute(
                """
                INSERT INTO assessments (
                    reg_no, subject_code, semester, cia1, cia2, cia3, attendance, end_sem, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(reg_no, subject_code, semester) DO UPDATE SET
                    cia1 = excluded.cia1,
                    cia2 = excluded.cia2,
                    cia3 = excluded.cia3,
                    attendance = excluded.attendance,
                    end_sem = excluded.end_sem,
                    updated_at = excluded.updated_at;
                """,
                (
                    row.reg_no,
                    row.subject_code,
                    CURRENT_SEMESTER,
                    float(row.cia1),
                    float(row.cia2),
                    float(row.cia3),
                    float(row.attendance),
                    float(row.end_sem),
                    now,
                ),
            )

        mode_label = "Replaced database with" if replace_all else "Synced & merged"
        _log_audit(conn, "LIVE_SYNC", f"{len(clean_df)} rows", f"{mode_label} {len(clean_df)} records.")
        conn.commit()
    return len(clean_df), f"{mode_label} {len(clean_df)} validated assessment records."


def fetch_google_sheets_dataframe(url: str) -> pd.DataFrame:
    """Convert a public Google Sheets link or CSV URL into a pandas DataFrame."""
    clean_url = url.strip()
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", clean_url)
    if match and "export?format=csv" not in clean_url and "output=csv" not in clean_url:
        sheet_id = match.group(1)
        gid_match = re.search(r"[#&?]gid=(\d+)", clean_url)
        gid_part = f"&gid={gid_match.group(1)}" if gid_match else ""
        clean_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_part}"

    req = urllib.request.Request(clean_url, headers={"User-Agent": "ChristGrade-Dashboard/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return pd.read_csv(resp)


def get_audit_log_df(limit: int = 25) -> pd.DataFrame:
    """Return recent CRUD and Live Sync audit entries."""
    init_database(force_reset=False)
    with _get_connection() as conn:
        return pd.read_sql_query(
            "SELECT action, target_ref, details, created_at FROM audit_log ORDER BY id DESC LIMIT ?",
            conn,
            params=(int(limit),),
        )
