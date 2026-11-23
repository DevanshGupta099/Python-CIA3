# ChristGrade: Real-Time CIA Academic Performance Analytics & End-Semester Target Score Predictor

**Course:** 2MCA-A & B — Python Programming (`MCA411-2`) · **Component 3 (Smart Dashboard Application)**  
**Institution:** CHRIST (Deemed to be University) — Department of Computer Science  
**Repository:** [https://github.com/DevanshGupta099/Python-CIA3](https://github.com/DevanshGupta099/Python-CIA3)

---

## Overview

**ChristGrade** is an interactive, real-time Academic Performance Analytics Dashboard and Target Score Predictor built with **Python** and **Streamlit** for CHRIST University MCA students and faculty. Styled with the **Solaris Editorial** design system (**Royal Cobalt × Crimson Rose × Sunset Coral × Champagne Gold**), it tracks **CIA 1 (`/20`)**, **Mid-Semester / CIA 2 (`/50`)**, **CIA 3 Assignment (`/20`)**, **Attendance eligibility (`85%` rule, `/5`)**, and **End-Semester Exam (`/100`)** performance across `2MCA-A` and `2MCA-B`.

### Key Capabilities
1. **Executive Cohort Overview (`views/overview.py`)**
   - Elevated Bento KPI cards with embedded sparklines, URL-bound filter pills & segmented controls (`bind="query-params"`), stacked/grouped CIA architecture bars, smooth spline CIA progression curves, CHRIST 10-point grade Donut/Sunburst charts, **row-clickable Scholar Leaderboard opening a Student Profile & Printable HTML Marksheet modal**, and **Seaborn** correlation heatmaps & KDE joint plots.
2. **Academic Insights Assistant (`utils/advisor.py`)**
   - Global `:material/auto_awesome: Academic Insights` drawer in the header answering instant questions over the active filtered cohort (attendance condonation audit, toughest subjects, 2MCA-A vs 2MCA-B comparison, top rankers).
3. **Student Standing & Weak-Subject Radar (`views/student_analytics.py`)**
   - Multi-axis **Radar Plot** (Student vs. Class Average vs. Subject Topper), cohort quartile **Box & Violin Plots** with student markers, automated weak-subject diagnostics, **Semester SGPA/CGPA progression**, **Live Session-State What-If Sandbox**, and **Official Printable HTML Marksheet Export**.
4. **End-Semester Target Score & CGPA Predictor (`views/predictor.py`)**
   - Deterministic CHRIST University grading calculator computing exact End-Sem marks (`/100`) needed for `O`, `A+`, `A`, `B+`, `B`, or `P`, paired with a 5-fold cross-validated **scikit-learn** ensemble (`Ridge` + `RandomForestRegressor`) and a credit-weighted **Semester SGPA/CGPA Planner**.
5. **Data Manipulation, Graph Studio & Policy Simulator (`views/data_lab.py`)**
   - Real-time numeric range slicers driving 6 interactive Plotly chart types (including NumPy OLS regression lines), multi-dimensional **Pandas GroupBy** summaries (Mean, Median, Std Dev, IQR), dynamic **Pivot Tables & Cross-Tabulations**, **Min-Max / Z-Score / 1.5×IQR Outlier Detection**, and a **Faculty Moderation & Attendance Condonation Simulator**.
6. **Full CRUD Marks Manager & Live Sync (`views/crud_manager.py`)**
   - **Create, Read, Update (Form + Inline `st.data_editor`), and Delete** backed by **SQLite3** (`data/christgrade.db`), comprehensive input validations (`utils/validators.py`), timestamped audit trail, and **CSV / Google Sheets Live Sync**.

---

## Git Branching Workflow

This repository follows a structured **Gitflow / Feature-Branch** workflow:
- `main` — Production-ready release branch deployed to Streamlit Community Cloud (`v2.0.0`)
- `develop` — Integration branch merging feature milestones
- `feat/database-and-validations` — SQLite3 schema, 60-student 2MCA dataset seed, CRUD & regex/bound validations
- `feat/analytics-and-ml-predictor` — Pandas/NumPy grading engine, GroupBy/Pivot/Outlier studio & `scikit-learn` predictor
- `feat/solaris-ui-and-visualizations` — Solaris Editorial theme, SVG assets, Plotly & Seaborn charts, and Insights advisor
- `feat/dashboard-views-and-tests` — 5 Streamlit views, printable HTML marksheet, moderation simulator & automated `AppTest` suite

---

## Quick Start (Local Run)

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell
# source .venv/bin/activate # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch ChristGrade
streamlit run app.py
```

---

## CHRIST University Grading Formula Reference (VIVA Quick Sheet)

- **Internal Assessment (`/50`):**
  $$\text{Internal}_{50} = 0.5 \times \text{CIA}_1(/20) + 0.5 \times \text{CIA}_2(/50) + 0.5 \times \text{CIA}_3(/20) + \text{AttendanceMarks}(/5)$$
- **Composite Final Score (`/100`):**
  $$\text{Final}_{100} = \text{Internal}_{50} + 0.5 \times \text{EndSem}(/100)$$
- **Eligibility & Pass Rules:** Attendance $\ge 85\%$ (80–84.9% condonation zone), Internal $\ge 20/50$, End-Sem $\ge 40/100$, Total $\ge 40/100$.
- **Required End-Sem Formula:**
  $$\text{Required ESE} = \max\left(40,\; \frac{\text{TargetCutoff} - \text{Internal}_{50}}{0.5}\right)$$
