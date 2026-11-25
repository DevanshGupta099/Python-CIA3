"""Academic constants, CHRIST University grading rules, and Solaris palette tokens."""

from __future__ import annotations

from dataclasses import dataclass

SECTIONS: tuple[str, ...] = ("2MCA-A", "2MCA-B")
CURRENT_SEMESTER = "Sem 2"

# Authentic CHRIST University 2MCA Subject Matrix (22 Total Credits)
SUBJECTS: dict[str, dict[str, object]] = {
    "MCA411-2": {
        "name": "Python Programming",
        "short": "Python Prog",
        "credits": 4,
        "category": "Core Lab + Theory",
        "faculty": "Dr. Kavitha R.",
    },
    "MCA412": {
        "name": "Advanced Database Systems",
        "short": "Adv DBMS",
        "credits": 4,
        "category": "Core Systems",
        "faculty": "Dr. Rajesh Menon",
    },
    "MCA413": {
        "name": "Software Engineering & Agile",
        "short": "Software Eng",
        "credits": 3,
        "category": "Engineering",
        "faculty": "Prof. Ananya Sharma",
    },
    "MCA414": {
        "name": "Computer Networks & Security",
        "short": "Networks & Sec",
        "credits": 4,
        "category": "Systems & Security",
        "faculty": "Dr. Thomas Mathew",
    },
    "MCA415": {
        "name": "Machine Learning Foundations",
        "short": "Machine Learning",
        "credits": 4,
        "category": "AI & Data Science",
        "faculty": "Dr. Priya Nair",
    },
    "MCA416": {
        "name": "Cloud Computing & DevOps",
        "short": "Cloud & DevOps",
        "credits": 3,
        "category": "Elective Core",
        "faculty": "Prof. Nikhil Joseph",
    },
}

SUBJECT_CODES: tuple[str, ...] = tuple(SUBJECTS.keys())
SUBJECT_LABELS: dict[str, str] = {
    code: f"{code} · {meta['name']}" for code, meta in SUBJECTS.items()
}

# Maximum Marks & Weightage toward Final 100
MAX_MARKS = {
    "cia1": 20.0,         # Scaled by 0.5 -> 10 internal marks
    "cia2": 50.0,         # Mid-Sem, scaled by 0.5 -> 25 internal marks
    "cia3": 20.0,         # Component 3 Assignment, scaled by 0.5 -> 10 internal marks
    "attendance": 100.0,  # Mapped to 0-5 internal marks; 85% min eligibility
    "end_sem": 100.0,     # Scaled by 0.5 -> 50 external marks; 40/100 min pass
}

MIN_ATTENDANCE_ELIGIBILITY = 85.0
MIN_ESE_PASS_MARKS = 40.0
MIN_INTERNAL_PASS_MARKS = 20.0
MIN_TOTAL_PASS_MARKS = 40.0

# CHRIST University 10-Point Grading Scale (Solaris Palette Mapping)
GRADE_SCALE: list[dict[str, object]] = [
    {"grade": "O",  "label": "Outstanding",     "min_score": 90.0, "gp": 10.0, "badge": "green",  "color": "#10B981"},
    {"grade": "A+", "label": "Excellent",       "min_score": 80.0, "gp": 9.0,  "badge": "blue",   "color": "#2563EB"},
    {"grade": "A",  "label": "Very Good",       "min_score": 70.0, "gp": 8.0,  "badge": "blue",   "color": "#0EA5E9"},
    {"grade": "B+", "label": "Good",            "min_score": 60.0, "gp": 7.0,  "badge": "orange", "color": "#F59E0B"},
    {"grade": "B",  "label": "Above Average",   "min_score": 55.0, "gp": 6.0,  "badge": "orange", "color": "#F97316"},
    {"grade": "C",  "label": "Average",         "min_score": 50.0, "gp": 5.5,  "badge": "yellow", "color": "#EA580C"},
    {"grade": "P",  "label": "Pass",            "min_score": 40.0, "gp": 5.0,  "badge": "gray",   "color": "#64748B"},
    {"grade": "F",  "label": "Reappear / Fail", "min_score": 0.0,  "gp": 0.0,  "badge": "red",    "color": "#E11D48"},
]

GRADE_ORDER: tuple[str, ...] = tuple(str(item["grade"]) for item in GRADE_SCALE)
GRADE_COLORS: dict[str, str] = {str(item["grade"]): str(item["color"]) for item in GRADE_SCALE}
GRADE_BADGES: dict[str, str] = {str(item["grade"]): str(item["badge"]) for item in GRADE_SCALE}
GRADE_POINTS: dict[str, float] = {str(item["grade"]): float(item["gp"]) for item in GRADE_SCALE}
TARGET_GRADES: tuple[str, ...] = ("O", "A+", "A", "B+", "B", "P")

RISK_LEVELS: tuple[str, ...] = ("Thriving", "On Track", "Watchlist", "At Risk")
RISK_BADGES: dict[str, str] = {
    "Thriving": "green",
    "On Track": "blue",
    "Watchlist": "orange",
    "At Risk": "red",
}

# Solaris Editorial Palette (Royal Cobalt x Crimson Rose x Sunset Coral x Champagne Gold)
PALETTE = {
    "cobalt": "#2563EB",
    "navy": "#1D4ED8",
    "sky": "#0EA5E9",
    "rose": "#E11D48",
    "rose_soft": "#FB7185",
    "coral": "#F97316",
    "gold": "#F59E0B",
    "emerald": "#10B981",
    "slate": "#64748B",
}


@dataclass(frozen=True)
class MetricDefinition:
    title: str
    owner: str
    formula: str
    sql: str


DEFINITIONS: dict[str, MetricDefinition] = {
    "cia_internal": MetricDefinition(
        title="Continuous Internal Assessment (CIA / 50)",
        owner="CHRIST Controller of Examinations",
        formula="Internal (50) = 0.5 × CIA1(/20) + 0.5 × MidSem_CIA2(/50) + 0.5 × CIA3(/20) + AttendanceMarks(/5)",
        sql=(
            "SELECT reg_no, subject_code,\n"
            "       ROUND(0.5*cia1 + 0.5*cia2 + 0.5*cia3 + att_marks, 2) AS internal_50\n"
            "FROM assessments\n"
            "WHERE semester = 'Sem 2';"
        ),
    ),
    "final_grade": MetricDefinition(
        title="Composite Course Score & Grade Point",
        owner="Department of Computer Science (2MCA)",
        formula="Final Score (100) = Internal(/50) + 0.5 × EndSem(/100). Pass requires Internal >= 20/50, ESE >= 40/100, Total >= 40/100.",
        sql=(
            "SELECT s.section, a.subject_code,\n"
            "       AVG(0.5*a.cia1 + 0.5*a.cia2 + 0.5*a.cia3 + a.att_marks + 0.5*a.end_sem) AS avg_total\n"
            "FROM assessments a JOIN students s USING (reg_no)\n"
            "GROUP BY s.section, a.subject_code;"
        ),
    ),
    "target_predictor": MetricDefinition(
        title="End-Semester Target Score Predictor",
        owner="ChristGrade Analytics & ML Engine",
        formula="Required ESE (/100) = max(40, (TargetGradeCutoff - Internal_50) / 0.5); paired with Ridge + Random Forest ML forecast.",
        sql=(
            "SELECT reg_no, subject_code,\n"
            "       MAX(40.0, (90.0 - internal_50) / 0.5) AS req_ese_for_O,\n"
            "       MAX(40.0, (80.0 - internal_50) / 0.5) AS req_ese_for_A_plus\n"
            "FROM enriched_assessments;"
        ),
    ),
}
