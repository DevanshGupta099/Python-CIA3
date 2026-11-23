# ChristGrade: Real-Time CIA Academic Performance Analytics & End-Semester Target Score Predictor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://christgrade.streamlit.app/)

- **Live Deployed Application:** [https://christgrade.streamlit.app/](https://christgrade.streamlit.app/)
- **GitHub Repository:** [https://github.com/DevanshGupta099/Python-CIA3](https://github.com/DevanshGupta099/Python-CIA3)
- **Course:** 2MCA-A & B — Python Programming (`MCA411-2`) · **Component 3 (Smart Dashboard Application)**
- **Institution:** CHRIST (Deemed to be University) — Department of Computer Science

---

## Overview

**ChristGrade (`v2.2.0`)** is an interactive, real-time Academic Performance Analytics Dashboard and End-Semester Target Score Predictor built with **Python** and **Streamlit** for CHRIST University MCA students and faculty. Styled with the **Solaris Editorial** design system (**Royal Cobalt × Crimson Rose × Sunset Coral × Champagne Gold**) and accelerated with `@st.fragment` partial reruns and `@st.cache_data` pipelines, it tracks **CIA 1 (`/20`)**, **Mid-Semester / CIA 2 (`/50`)**, **CIA 3 Assignment (`/20`)**, **Attendance eligibility (`85%` rule, `/5`)**, and **End-Semester Exam (`/100`)** outcomes across `2MCA-A` and `2MCA-B`.

### Core Modules & Capabilities
1. **Executive Cohort Overview (`views/overview.py`)**
   - Elevated Bento KPI cards with embedded sparklines, bidirectional URL query-parameter filters (`?cohort=2MCA-A`), switchable **Stacked CIA / CIA % / Section A vs B** bars, **CIA Momentum & Cohort Sem 1 → Sem 2 GPA Trend** spline charts, CHRIST 10-point **Donut & Sunburst** grade mix, row-clickable **Scholar Leaderboard** (launching a Student Profile & Printable HTML Marksheet modal), and cached **Seaborn** correlation heatmaps & bivariate KDE plots.
2. **Academic Insights Assistant (`utils/advisor.py`)**
   - Global **Academic Insights** modal answering instant questions over the active filtered cohort (attendance `<85%` condonation audits, toughest subjects, CIA 1 → CIA 3 top improvers, `2MCA-A` vs `2MCA-B` comparisons, and direct Student Name / Register No. lookups).
3. **Student Standing & Weak-Subject Radar (`views/student_analytics.py`)**
   - 6-axis **Interactive Radar Plot** (Student vs. Class Average vs. Subject Topper), cohort quartile **Box & Violin Plots** with student markers, automatic weak-subject diagnostics, **Semester SGPA/CGPA progression**, **Live `st.session_state` What-If Sandbox**, and **Official Printable HTML Marksheet Export**.
4. **End-Semester Target Score & CGPA Predictor (`views/predictor.py`)**
   - Exact CHRIST University grading formula calculator computing required End-Sem marks (`/100`) for `O`, `A+`, `A`, `B+`, `B`, and `P`, paired with a 5-fold cross-validated **`scikit-learn`** ensemble (`Ridge` + `RandomForestRegressor`, CV $R^2 = 0.84$) and a 22-credit **Semester SGPA & CGPA Planner**.
5. **Data Manipulation, Graph Studio & Policy Simulator (`views/data_lab.py`)**
   - Real-time numeric range slicers driving 6 Plotly chart families (with NumPy OLS regression lines), multi-column **Pandas GroupBy** summaries (Mean, Median, Std Dev, NumPy IQR), dynamic **Pivot Tables & Cross-Tabulations**, **Min-Max / Z-Score / `1.5×IQR` Outlier Detection**, and a **Faculty Moderation & Condonation Simulator**.
6. **Full CRUD Marks Manager & Live Sync (`views/crud_manager.py`)**
   - **Create** (both Single-Subject Form and **Full 6-Subject Manual Student Sheet**), **Read/Search**, **Update** (Profile + Marks Form and Inline `st.data_editor`), and **Delete** (single assessment or cascade student removal) backed by **SQLite3** (`data/christgrade.db`), regex/bound validations (`utils/validators.py`), timestamped audit trail, and **Manual Batch Sheet / CSV / Google Sheets Live Sync**.

---

## Tech Stack
- **Frontend, Routing & Partial Reruns:** `Streamlit` (`st.navigation`, `@st.fragment`, `@st.dialog`, `@st.cache_data`, `st.query_params`, `st.data_editor`)
- **Data Engineering:** `Pandas`, `NumPy`
- **Interactive & Statistical Charts:** `Plotly`, `Seaborn`, `Matplotlib`
- **Persistence:** `SQLite3` (`data/christgrade.db`) + seed CSV (`data/christ_mca_cia_dataset.csv`)
- **Machine Learning:** `scikit-learn` (`Pipeline`, `StandardScaler`, `Ridge`, `RandomForestRegressor`, 5-fold `KFold` CV)

> **Persistence Note (Local vs. Streamlit Cloud):** Locally, all CRUD and Sync writes persist permanently to `data/christgrade.db` on disk. On Streamlit Community Cloud, SQLite updates persist live across sessions while the container is active; use **Export CSV** / **Live Sync** to archive or restore custom snapshots across container restarts.

---

## Git Branching Workflow

- `main` — Production release branch auto-deployed to https://christgrade.streamlit.app/ (`v2.2.0`)
- `develop` — Integration branch merging feature milestones
- `feat/database-and-validations` — SQLite3 schema, 60-student 2MCA seed, CRUD & regex/bound validators
- `feat/analytics-and-ml-predictor` — Grading math, GroupBy/Pivot/Outlier studio & `scikit-learn` predictor
- `feat/solaris-ui-and-visualizations` — Solaris Editorial theme, SVG assets, Plotly & Seaborn charts, Insights advisor
- `feat/dashboard-views-and-tests` — 5 Streamlit views, printable HTML marksheet, moderation simulator & `AppTest` suite
- `feat/smooth-fragments-and-bugfixes` — `@st.fragment` isolation, PNG/SQLite caching & 60fps CSS/Plotly transitions
- `feat/viva-workflows-and-gpa-trends` — Bidirectional URL query sync, cohort GPA trend, 6-subject onboarding & manual batch staging

---

## Quick Start (Local Run)

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell
# source .venv/bin/activate # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

---

## VIVA Quick Formula & Walkthrough Sheet

- **Internal Assessment (`/50`):**
  $$\text{Internal}_{50} = 0.5 \times \text{CIA}_1(/20) + 0.5 \times \text{CIA}_2(/50) + 0.5 \times \text{CIA}_3(/20) + \text{AttendanceMarks}(/5)$$
- **Composite Final Score (`/100`):**
  $$\text{Final}_{100} = \text{Internal}_{50} + 0.5 \times \text{EndSem}(/100)$$
- **Eligibility & Pass Rules:** Attendance $\ge 85\%$ (80–84.9% medical condonation zone), Internal $\ge 20/50$, End-Sem $\ge 40/100$, Total $\ge 40/100$.
- **Required End-Sem Formula:**
  $$\text{Required ESE} = \max\left(40,\; \frac{\text{TargetCutoff} - \text{Internal}_{50}}{0.5}\right)$$

### Suggested 5-Minute Live VIVA Flow
1. **Overview:** Filter `2MCA-A` (show URL updating to `?cohort=2MCA-A`), toggle `Sem 1→2 GPA`, click a scholar row to inspect their modal, and open **Academic Insights**.
2. **Marks & CRUD:** Switch to `Full 6-Subject Student Sheet` (or `Single Subject Form`), intentionally enter `25` in `CIA 1` to demonstrate live validation catching the error, fix it, and onboard a new student (`2547131`).
3. **Student Radar:** Select `2547131`, show their live 6-axis Radar polygon & Box/Violin standing, and export their **Official HTML Marksheet**.
4. **Score Predictor:** Adjust CIA/Attendance sliders to show required End-Sem marks for `O` / `A+` alongside the `scikit-learn` ensemble forecast and 22-credit SGPA roadmap.
5. **Data Studio:** Slice numeric ranges to dynamically update Scatter+OLS / Pivot Heatmaps and test the **Faculty Policy Simulator**.
