"""Smart Academic Insights Drawer, Deep-Link Student Modal & Printable HTML Report Generator."""

from __future__ import annotations

from datetime import datetime
import html

import pandas as pd
import streamlit as st

from utils.analytics import build_student_leaderboard, calculate_target_ese_table
from utils.charts import student_radar_chart
from utils.constants import GRADE_BADGES, GRADE_ORDER, RISK_BADGES


def generate_student_html_report(student_rows: pd.DataFrame, stu_meta: pd.Series) -> bytes:
    """Build a clean, printable CHRIST University HTML Academic Progress & Target Card."""
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    reg_no = html.escape(str(stu_meta["reg_no"]))
    name = html.escape(str(stu_meta["name"]))
    section = html.escape(str(stu_meta["section"]))
    standing = html.escape(str(stu_meta["standing"]))

    rows_html = ""
    for r in student_rows.itertuples(index=False):
        tgt = calculate_target_ese_table(float(r.internal_50), float(r.attendance))
        req_o = tgt.loc[tgt["Target Grade"] == "O", "Required End-Sem (/100)"].iloc[0]
        req_ap = tgt.loc[tgt["Target Grade"] == "A+", "Required End-Sem (/100)"].iloc[0]
        req_o_txt = f"{req_o:.1f}" if pd.notna(req_o) else "Capped"
        req_ap_txt = f"{req_ap:.1f}" if pd.notna(req_ap) else "Capped"
        rows_html += f"""
        <tr>
            <td><b>{html.escape(str(r.subject_code))}</b></td>
            <td>{html.escape(str(r.subject_name))}</td>
            <td style="text-align:center">{int(r.credits)}</td>
            <td style="text-align:right">{r.cia1:.1f}</td>
            <td style="text-align:right">{r.cia2:.1f}</td>
            <td style="text-align:right">{r.cia3:.1f}</td>
            <td style="text-align:right">{r.attendance:.1f}%</td>
            <td style="text-align:right"><b>{r.internal_50:.2f}</b></td>
            <td style="text-align:right">{r.end_sem:.1f}</td>
            <td style="text-align:right"><b>{r.total_score:.1f}</b></td>
            <td style="text-align:center"><span class="badge">{html.escape(str(r.grade))}</span></td>
            <td style="text-align:right">{req_ap_txt} / {req_o_txt}</td>
        </tr>
        """

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>ChristGrade Transcript - {reg_no}</title>
<style>
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #0F172A; margin: 32px; background: #F8FAFC; }}
  .sheet {{ max-width: 960px; margin: auto; background: #FFFFFF; border-radius: 16px; padding: 32px; border: 1px solid #E2E8F0; box-shadow: 0 8px 24px rgba(15,23,42,0.06); }}
  .bar {{ height: 5px; border-radius: 999px; background: linear-gradient(90deg, #1D4ED8, #E11D48, #F97316); margin-bottom: 20px; }}
  h1 {{ margin: 0; font-size: 22px; }}
  .sub {{ color: #475569; font-size: 13px; margin-top: 4px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
  .kpi {{ padding: 14px; border-radius: 12px; background: #F8FAFC; border: 1px solid #E2E8F0; }}
  .kpi-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; }}
  .kpi-val {{ font-size: 22px; font-weight: 800; color: #1E293B; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 12px; }}
  th {{ background: #F1F5F9; color: #334155; padding: 9px 8px; text-align: left; border-bottom: 2px solid #CBD5E1; }}
  td {{ padding: 9px 8px; border-bottom: 1px solid #E2E8F0; }}
  .badge {{ background: #DBEAFE; color: #1D4ED8; font-weight: 700; padding: 2px 8px; border-radius: 999px; }}
  .foot {{ margin-top: 22px; font-size: 11.5px; color: #64748B; display: flex; justify-content: space-between; }}
</style>
</head>
<body>
<div class="sheet">
  <div class="bar"></div>
  <h1>CHRIST (Deemed to be University) · ChristGrade CIA Progress Card</h1>
  <div class="sub">Department of Computer Science · 2MCA Sem 2 · Generated {now_str}</div>
  <div class="kpis">
    <div class="kpi"><div class="kpi-label">Student</div><div class="kpi-val" style="font-size:16px">{name}<br/><span style="font-size:12px;color:#64748B">{reg_no} · {section}</span></div></div>
    <div class="kpi"><div class="kpi-label">Sem 2 SGPA</div><div class="kpi-val">{stu_meta['sem2_sgpa']:.2f}</div></div>
    <div class="kpi"><div class="kpi-label">Cumulative CGPA</div><div class="kpi-val">{stu_meta['cgpa']:.2f} / 10</div></div>
    <div class="kpi"><div class="kpi-label">Standing &amp; Attendance</div><div class="kpi-val" style="font-size:16px">{standing}<br/><span style="font-size:12px;color:#64748B">Avg Att: {stu_meta['avg_attendance']:.1f}%</span></div></div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Code</th><th>Subject</th><th>Cr</th><th>CIA1 /20</th><th>CIA2 /50</th><th>CIA3 /20</th>
        <th>Att %</th><th>Int /50</th><th>ESE /100</th><th>Total /100</th><th>Grade</th><th>Req ESE (A+ / O)</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="foot">
    <span>Eligibility Rule: Attendance &ge; 85%, Internal &ge; 20/50, End-Sem &ge; 40/100</span>
    <span>ChristGrade Academic Performance Intelligence</span>
  </div>
</div>
</body>
</html>"""
    return doc.encode("utf-8")


@st.dialog("Student Profile & Marksheet", width="large", icon=":material/badge:")
def open_student_drawer(reg_no: str, full_df: pd.DataFrame) -> None:
    """Slide-over modal showing complete student standing, radar, deep-links & printable report."""
    lb = build_student_leaderboard(full_df)
    stu_match = lb[lb["reg_no"] == reg_no]
    if stu_match.empty:
        st.warning("Student record not found.")
        return

    meta = stu_match.iloc[0]
    stu_rows = full_df[full_df["reg_no"] == reg_no].copy()

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.subheader(f"{meta['name']} ({reg_no})", anchor=False)
        st.badge(str(meta["section"]), icon=":material/groups:", color="blue")
        st.badge(
            str(meta["standing"]),
            icon=":material/verified:",
            color=RISK_BADGES.get(str(meta["standing"]), "blue"),
        )
        st.badge(f"Rank #{int(meta['rank'])}", icon=":material/emoji_events:", color="orange")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sem 2 SGPA", f"{meta['sem2_sgpa']:.2f}", f"{meta['sgpa_delta']:+.2f} vs Sem 1", border=True)
    c2.metric("CGPA", f"{meta['cgpa']:.2f}", "10-Pt Scale", border=True)
    c3.metric("Internal Avg", f"{meta['avg_internal_50']:.1f}/50", f"{meta['avg_total_100']:.1f}/100 Final", border=True)
    c4.metric("Attendance", f"{meta['avg_attendance']:.1f}%", "85% Min Rule", border=True)

    col_r, col_t = st.columns([2, 3])
    with col_r:
        st.plotly_chart(
            student_radar_chart(stu_rows, full_df),
            width="stretch",
            config={"displayModeBar": False},
        )
    with col_t:
        disp = stu_rows.copy()
        disp["grade_badge"] = disp["grade"].map(lambda g: [g])
        st.dataframe(
            disp[["subject_code", "subject_short", "internal_50", "end_sem", "total_score", "grade_badge"]],
            column_config={
                "subject_code": st.column_config.TextColumn("Code"),
                "subject_short": st.column_config.TextColumn("Subject"),
                "internal_50": st.column_config.NumberColumn("Int /50", format="%.1f"),
                "end_sem": st.column_config.NumberColumn("ESE /100", format="%.0f"),
                "total_score": st.column_config.ProgressColumn("Final /100", min_value=0, max_value=100, format="%.1f"),
                "grade_badge": st.column_config.MultiselectColumn(
                    "Grade", options=list(GRADE_ORDER), color=[GRADE_BADGES[g] for g in GRADE_ORDER]
                ),
            },
            hide_index=True,
            height=265,
            width="stretch",
        )

    report_bytes = generate_student_html_report(stu_rows, meta)
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Open in Student Radar", icon=":material/person_search:"):
            st.session_state["_jump_stu_reg"] = reg_no
            st.session_state["_pending_page_jump"] = "views/student_analytics.py"
            st.rerun()
        if st.button("Predict End-Sem Targets", icon=":material/ads_click:"):
            st.session_state["_jump_pred_reg"] = reg_no
            st.session_state["_pending_page_jump"] = "views/predictor.py"
            st.rerun()
        st.download_button(
            "Download Official HTML Marksheet",
            data=report_bytes,
            file_name=f"ChristGrade_Marksheet_{reg_no}.html",
            mime="text/html",
            type="primary",
            icon=":material/download:",
        )


def _answer_academic_query(prompt: str, df: pd.DataFrame) -> str:
    """Deterministic data-grounded Academic BI Assistant over active cohort filters."""
    if df.empty:
        return "No assessment rows are currently active. Reset filters to analyze the cohort."

    q = prompt.strip().lower()
    lb = build_student_leaderboard(df)

    # Direct student lookup by Register Number or Student Name
    stu_hit = lb[
        lb["reg_no"].str.lower().apply(lambda r: r in q)
        | lb["name"].str.lower().apply(lambda n: any(tok in q for tok in n.split() if len(tok) >= 4))
    ]
    if not stu_hit.empty and not any(k in q for k in ("compare", "top", "toughest", "executive", "audit")):
        s = stu_hit.iloc[0]
        s_rows = df[df["reg_no"] == s["reg_no"]].sort_values("total_score", ascending=True)
        weakest = s_rows.iloc[0]
        strongest = s_rows.iloc[-1]
        return (
            f"**Scholar Brief — {s['name']} (`{s['reg_no']}`, {s['section']}):**\n"
            f"- **Rank:** `#{int(s['rank'])}` · **Sem 2 SGPA:** `{s['sem2_sgpa']:.2f}` · **CGPA:** `{s['cgpa']:.2f}`\n"
            f"- **Mean Internal:** `{s['avg_internal_50']:.2f}/50` · **Attendance:** `{s['avg_attendance']:.1f}%`\n"
            f"- **Strongest Subject:** `{strongest['subject_code']} ({strongest['subject_short']})` at `{strongest['total_score']:.1f}/100` (Grade **{strongest['grade']}**)\n"
            f"- **Focus Subject:** `{weakest['subject_code']} ({weakest['subject_short']})` at `{weakest['total_score']:.1f}/100` (Internal `{weakest['internal_50']:.1f}/50`)"
        )

    if any(k in q for k in ("attendance", "condonation", "85", "shortage", "detain")):
        short = df[~df["att_eligible"]]
        stu_cnt = short["reg_no"].nunique()
        by_sub = short.groupby("subject_short").size().sort_values(ascending=False)
        top_sub = f"{by_sub.index[0]} ({by_sub.iloc[0]} cases)" if not by_sub.empty else "None"
        return (
            f"**Attendance Eligibility Audit (<85% Rule):**\n"
            f"- **{len(short)}** subject rows across **{stu_cnt}** unique students are currently below 85%.\n"
            f"- Highest concentration: **{top_sub}**.\n"
            f"- Overall 85%+ compliance stands at **{df['att_eligible'].mean() * 100:.1f}%**."
        )

    if any(k in q for k in ("momentum", "improv", "cia3", "growth")):
        imp = (
            df.groupby(["reg_no", "name", "section"], as_index=False)["cia_momentum"]
            .mean()
            .sort_values("cia_momentum", ascending=False)
            .head(5)
        )
        lines = [
            f"- **{r.name}** (`{r.reg_no}`, {r.section}): `{r.cia_momentum:+.1f}%` avg gain from CIA 1 to CIA 3"
            for r in imp.itertuples(index=False)
        ]
        return "**Top 5 CIA 1 → CIA 3 Momentum Improvers:**\n" + "\n".join(lines)

    if any(k in q for k in ("weak", "hard", "toughest", "lowest", "subject")):
        sub_stats = (
            df.groupby(["subject_code", "subject_name"], as_index=False)
            .agg(avg=("total_score", "mean"), internal=("internal_50", "mean"), pass_r=("is_pass", "mean"))
            .sort_values("avg", ascending=True)
        )
        w = sub_stats.iloc[0]
        b = sub_stats.iloc[-1]
        return (
            f"**Subject Difficulty & Performance Spread:**\n"
            f"- Toughest subject: **{w['subject_code']} ({w['subject_name']})** — Mean **{w['avg']:.1f}/100** "
            f"(Internal **{w['internal']:.1f}/50**, Pass rate **{w['pass_r']*100:.1f}%**).\n"
            f"- Highest scoring subject: **{b['subject_code']} ({b['subject_name']})** — Mean **{b['avg']:.1f}/100**."
        )

    if any(k in q for k in ("compare", "section", "2mca-a", "2mca-b", "cohort")):
        sec = df.groupby("section").agg(
            mean_tot=("total_score", "mean"),
            mean_int=("internal_50", "mean"),
            att_ok=("att_eligible", lambda s: s.mean() * 100),
            pass_r=("is_pass", lambda s: s.mean() * 100),
        )
        lines = [
            f"- **{idx}**: Mean **{r.mean_tot:.1f}/100** · Internal **{r.mean_int:.2f}/50** · "
            f"Pass **{r.pass_r:.1f}%** · Att>=85% **{r.att_ok:.1f}%**"
            for idx, r in sec.iterrows()
        ]
        return "**Section-by-Section Cohort Comparison:**\n" + "\n".join(lines)

    if any(k in q for k in ("top", "rank", "leader", "best", "topper")):
        top5 = lb.head(5)
        items = [
            f"{int(r.rank)}. **{r.name}** (`{r.reg_no}`, {r.section}) — Sem 2 SGPA **{r.sem2_sgpa:.2f}**, CGPA **{r.cgpa:.2f}**"
            for r in top5.itertuples(index=False)
        ]
        return "**Top 5 Cohort Scholars (Active Filter):**\n" + "\n".join(items)

    return (
        f"**Executive Cohort Summary ({df['reg_no'].nunique()} Students · {len(df)} Assessments):**\n"
        f"- **Mean Composite Score:** `{df['total_score'].mean():.1f} / 100` (Internal `{df['internal_50'].mean():.2f} / 50`)\n"
        f"- **Pass Rate:** `{df['is_pass'].mean() * 100:.1f}%` · **O & A+ Share:** `{df['grade'].isin(['O', 'A+']).mean() * 100:.1f}%`\n"
        f"- **Top Cohort SGPA:** `{lb['sem2_sgpa'].max():.2f}` ({lb.iloc[0]['name']})\n"
        f"- Ask about *toughest subjects*, *attendance <85%*, *CIA3 improvers*, *2MCA-A vs 2MCA-B*, or type any *Student Name / Reg. No.*!"
    )


@st.dialog("ChristGrade Academic Insights", width="medium", icon=":material/auto_awesome:")
def open_insights_drawer(df: pd.DataFrame) -> None:
    """Interactive data-grounded Academic Insights assistant over live filtered data."""
    st.caption("Answers instantaneously from your live SQLite database and active filters.")
    presets = [
        "Executive summary",
        "Toughest subjects",
        "Attendance < 85% audit",
        "CIA3 top improvers",
        "Compare 2MCA-A vs 2MCA-B",
        "Top 5 rankers",
    ]
    picked = st.pills("Quick Prompts", presets, key="insights_quick_pill")

    filter_sig = (len(df), round(float(df["total_score"].sum()), 1) if not df.empty else 0.0)
    if (
        "advisor_messages" not in st.session_state
        or st.session_state.get("_advisor_sig") != filter_sig
    ):
        st.session_state["_advisor_sig"] = filter_sig
        st.session_state["advisor_messages"] = [
            {
                "role": "assistant",
                "content": _answer_academic_query("Executive summary", df),
            }
        ]

    user_q = st.chat_input("Ask about subjects, attendance, rankers, or a student's name/ID...")
    trigger = user_q or (picked if picked and st.session_state.get("_last_pill") != picked else None)
    if picked:
        st.session_state["_last_pill"] = picked

    if trigger:
        st.session_state["advisor_messages"].append({"role": "user", "content": trigger})
        st.session_state["advisor_messages"].append(
            {"role": "assistant", "content": _answer_academic_query(trigger, df)}
        )

    with st.container(height=300, border=False):
        for msg in st.session_state["advisor_messages"][-6:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
