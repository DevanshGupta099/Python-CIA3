"""Live CIA Marks Manager: Editorial Layout, Lazy Single-Workflow CRUD, Validations & Batch Sync."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.analytics import assign_grade_and_gp, attendance_to_marks
from utils.constants import (
    GRADE_BADGES,
    GRADE_ORDER,
    SECTIONS,
    SUBJECT_CODES,
    SUBJECT_LABELS,
    SUBJECTS,
)
from utils.database import (
    CSV_SEED_PATH,
    bulk_update_from_editor,
    delete_assessment_record,
    delete_student_profile,
    fetch_google_sheets_dataframe,
    get_audit_log_cached,
    get_db_version,
    init_database,
    sync_validated_dataframe,
    upsert_student_assessment,
)
from utils.ui import card_header, render_page_header
from utils.validators import (
    validate_assessment_scores,
    validate_imported_dataframe,
    validate_student_record,
)

full_df: pd.DataFrame = st.session_state["full_df"]
audit_df_top = get_audit_log_cached(get_db_version(), limit=25)

render_page_header(
    title="Marks & Student Records Manager",
    subtitle="Create single or 6-subject student profiles, edit CIA marks inline, remove records with confirmation guards, or sync batch sheets.",
    meta_summary=f"{full_df['reg_no'].nunique()} Students · {len(full_df)} Records",
)

CRUD_SECTIONS = [
    "Create Record",
    "Read & Update Marks",
    "Delete Records",
    "Live Sync & Audit Log",
]


@st.fragment
def _render_crud_workspace(df_all: pd.DataFrame, audit_df: pd.DataFrame) -> None:
    active_tab = st.segmented_control(
        "CRUD Workflow",
        CRUD_SECTIONS,
        default="Create Record",
        required=True,
        key="crud_active_workflow",
        label_visibility="collapsed",
    )

    if active_tab == "Create Record":
        with st.container(border=True):
            c_ctrl = card_header(
                "Create Student & Subject CIA Assessment",
                "Add a single subject assessment or onboard a new scholar across all 6 MCA subjects",
            )
            create_mode = c_ctrl.segmented_control(
                "Entry Mode",
                ["Single Subject Form", "Full 6-Subject Student Sheet"],
                default="Single Subject Form",
                required=True,
                key="crud_create_mode",
                label_visibility="collapsed",
            )

            if create_mode == "Single Subject Form":
                with st.form("crud_create_form", clear_on_submit=False):
                    r1c1, r1c2, r1c3, r1c4 = st.columns([1.2, 2.0, 1.1, 2.0])
                    in_reg = r1c1.text_input("Register No. *", placeholder="2547131", help="7-digit CHRIST ID starting with 2")
                    in_name = r1c2.text_input("Student Full Name *", placeholder="Aarav Nair")
                    in_sec = r1c3.selectbox("Cohort *", options=list(SECTIONS))
                    in_mail = r1c4.text_input(
                        "University Email (auto-filled if blank)",
                        placeholder="aarav.nair@mca.christuniversity.in",
                    )

                    r2c1, r2c2, r2c3 = st.columns([2.2, 1.2, 1.6])
                    in_sub = r2c1.selectbox(
                        "MCA Subject *",
                        options=list(SUBJECT_CODES),
                        format_func=lambda c: SUBJECT_LABELS[c],
                    )
                    in_sem1 = r2c2.number_input("Sem 1 SGPA *", min_value=0.0, max_value=10.0, value=7.8, step=0.1)
                    allow_upsert = r2c3.checkbox(
                        "Update if (Reg No + Subject) exists",
                        value=False,
                        help="Keep unchecked to strictly prevent duplicate records.",
                    )

                    r3c1, r3c2, r3c3, r3c4, r3c5 = st.columns(5)
                    in_cia1 = r3c1.number_input("CIA 1 (/20) *", min_value=0.0, max_value=20.0, value=16.0, step=0.5)
                    in_cia2 = r3c2.number_input("Mid-Sem CIA 2 (/50) *", min_value=0.0, max_value=50.0, value=38.0, step=0.5)
                    in_cia3 = r3c3.number_input("CIA 3 Assign. (/20) *", min_value=0.0, max_value=20.0, value=17.0, step=0.5)
                    in_att = r3c4.number_input("Attendance (%) *", min_value=0.0, max_value=100.0, value=91.0, step=0.5)
                    in_ese = r3c5.number_input("End-Sem (/100) *", min_value=0.0, max_value=100.0, value=78.0, step=1.0)

                    prev_int = round(0.5 * in_cia1 + 0.5 * in_cia2 + 0.5 * in_cia3 + float(attendance_to_marks(in_att)), 2)
                    prev_tot = round(prev_int + 0.5 * in_ese, 2)
                    prev_g, prev_gp, _ = assign_grade_and_gp(
                        pd.Series([prev_tot]).to_numpy(),
                        pd.Series([prev_int]).to_numpy(),
                        pd.Series([in_ese]).to_numpy(),
                    )
                    st.caption(
                        f"Live Preview → Internal: **{prev_int:.2f}/50** · Final Score: **{prev_tot:.1f}/100** · "
                        f"Computed Grade: **{prev_g[0]}** (GP {prev_gp[0]:.1f})"
                    )

                    submitted = st.form_submit_button(
                        "Validate & Save Record", type="primary", icon=":material/save:"
                    )

                if submitted:
                    is_ok, errors, cleaned = validate_student_record(
                        reg_no=in_reg,
                        name=in_name,
                        section=in_sec,
                        email=in_mail,
                        sem1_sgpa=in_sem1,
                        subject_code=in_sub,
                        cia1=in_cia1,
                        cia2=in_cia2,
                        cia3=in_cia3,
                        attendance=in_att,
                        end_sem=in_ese,
                    )
                    if not is_ok:
                        for err in errors:
                            st.error(err, icon=":material/error:")
                    else:
                        saved, msg = upsert_student_assessment(cleaned, allow_overwrite=allow_upsert)
                        if saved:
                            st.toast(msg, icon=":material/check_circle:")
                            st.success(msg, icon=":material/check_circle:")
                            st.rerun()
                        else:
                            st.error(msg, icon=":material/warning:")

            else:
                st.caption(
                    "Enter student details below and fill marks across all **6 MCA subjects** "
                    "to populate their Radar profile and 22-credit SGPA Planner in one step."
                )
                m1, m2, m3, m4, m5 = st.columns([1.2, 1.9, 1.0, 1.9, 1.0])
                m_reg = m1.text_input("Register No. *", placeholder="2547131", key="m6_reg")
                m_name = m2.text_input("Student Full Name *", placeholder="Aarav Nair", key="m6_name")
                m_sec = m3.selectbox("Cohort *", options=list(SECTIONS), key="m6_sec")
                m_mail = m4.text_input("University Email", placeholder="Auto-generated if blank", key="m6_mail")
                m_sem1 = m5.number_input("Sem 1 SGPA *", 0.0, 10.0, 8.0, 0.1, key="m6_sem1")

                template_6 = pd.DataFrame(
                    [
                        {
                            "subject_code": code,
                            "subject_name": str(SUBJECTS[code]["name"]),
                            "credits": int(SUBJECTS[code]["credits"]),
                            "cia1": 15.0,
                            "cia2": 36.0,
                            "cia3": 16.0,
                            "attendance": 90.0,
                            "end_sem": 75.0,
                        }
                        for code in SUBJECT_CODES
                    ]
                )
                edited_6 = st.data_editor(
                    template_6,
                    column_config={
                        "subject_code": st.column_config.TextColumn("Code", disabled=True),
                        "subject_name": st.column_config.TextColumn("Subject Name", disabled=True),
                        "credits": st.column_config.NumberColumn("Cr.", disabled=True, width="small"),
                        "cia1": st.column_config.NumberColumn("CIA 1 (/20) *", step=0.5, required=True),
                        "cia2": st.column_config.NumberColumn("Mid-Sem (/50) *", step=0.5, required=True),
                        "cia3": st.column_config.NumberColumn("CIA 3 (/20) *", step=0.5, required=True),
                        "attendance": st.column_config.NumberColumn("Attendance (%) *", step=0.5, required=True),
                        "end_sem": st.column_config.NumberColumn("End-Sem (/100) *", step=1.0, required=True),
                    },
                    hide_index=True,
                    width="stretch",
                    key="crud_m6_editor",
                )
                m_overwrite = st.checkbox(
                    "Allow updating if this Register No. already exists",
                    value=False,
                    key="m6_overwrite",
                )

                if st.button("Validate & Onboard All 6 Subjects", type="primary", icon=":material/person_add:"):
                    if not m_overwrite and str(m_reg).strip() in set(df_all["reg_no"].values):
                        st.error(
                            f"Student {m_reg.strip()} already exists. Enable the overwrite checkbox above or enter a new Register No.",
                            icon=":material/warning:",
                        )
                    else:
                        batch_df = edited_6.copy()
                        batch_df["reg_no"] = m_reg
                        batch_df["name"] = m_name
                        batch_df["section"] = m_sec
                        batch_df["email"] = m_mail
                        batch_df["sem1_sgpa"] = m_sem1

                        ok_all, row_errs, clean_6 = validate_imported_dataframe(batch_df)
                        if not ok_all:
                            for err in row_errs:
                                st.error(err, icon=":material/error:")
                        else:
                            cnt, _ = sync_validated_dataframe(clean_6, replace_all=False)
                            st.toast(
                                f"Onboarded {clean_6.iloc[0]['name']} ({clean_6.iloc[0]['reg_no']}) across {cnt} subjects!",
                                icon=":material/check_circle:",
                            )
                            st.rerun()

    elif active_tab == "Read & Update Marks":
        with st.container(border=True):
            u_ctrl = card_header(
                "Search, Inspect & Update Student Marks",
                "Filter records instantaneously and edit via Inline Spreadsheet or Record Form",
            )
            edit_mode = u_ctrl.segmented_control(
                "Edit Style",
                ["Inline Spreadsheet Editor", "Single Record & Profile Form"],
                default="Inline Spreadsheet Editor",
                required=True,
                key="crud_edit_style",
                label_visibility="collapsed",
            )

            f1, f2, f3 = st.columns([2.2, 1.2, 1.6])
            q_search = f1.text_input(
                "Search by Register No. or Student Name",
                placeholder="Type e.g. 2547101 or Devansh...",
                key="crud_search_q",
            )
            q_sec = f2.selectbox("Filter Cohort", ["All", *SECTIONS], key="crud_sec_flt")
            q_sub = f3.selectbox(
                "Filter Subject",
                ["All", *SUBJECT_CODES],
                format_func=lambda c: "All Subjects" if c == "All" else SUBJECT_LABELS[c],
                key="crud_sub_flt",
            )

            view_df = df_all
            if q_search.strip():
                needle = q_search.strip().lower()
                view_df = view_df[
                    view_df["reg_no"].str.lower().str.contains(needle)
                    | view_df["name"].str.lower().str.contains(needle)
                ]
            if q_sec != "All":
                view_df = view_df[view_df["section"] == q_sec]
            if q_sub != "All":
                view_df = view_df[view_df["subject_code"] == q_sub]

            if view_df.empty:
                st.info("No records match your search query.")
            elif edit_mode == "Inline Spreadsheet Editor":
                st.caption(
                    f"Showing **{len(view_df)}** matching records. Double-click any CIA, Attendance, or End-Sem cell to edit."
                )
                editor_src = view_df[
                    [
                        "assessment_id",
                        "reg_no",
                        "name",
                        "section",
                        "subject_code",
                        "cia1",
                        "cia2",
                        "cia3",
                        "attendance",
                        "end_sem",
                        "internal_50",
                        "total_score",
                        "grade",
                    ]
                ].copy()
                editor_src["grade_badge"] = editor_src["grade"].map(lambda g: [g])

                edited_table = st.data_editor(
                    editor_src.drop(columns=["grade"]),
                    column_config={
                        "assessment_id": None,
                        "reg_no": st.column_config.TextColumn("Reg. No.", disabled=True),
                        "name": st.column_config.TextColumn("Student Name", disabled=True),
                        "section": st.column_config.TextColumn("Cohort", disabled=True),
                        "subject_code": st.column_config.TextColumn("Subject", disabled=True),
                        "cia1": st.column_config.NumberColumn("CIA 1 (/20)", min_value=0.0, max_value=20.0, step=0.5, required=True),
                        "cia2": st.column_config.NumberColumn("CIA 2 (/50)", min_value=0.0, max_value=50.0, step=0.5, required=True),
                        "cia3": st.column_config.NumberColumn("CIA 3 (/20)", min_value=0.0, max_value=20.0, step=0.5, required=True),
                        "attendance": st.column_config.NumberColumn("Att. %", min_value=0.0, max_value=100.0, step=0.5, required=True),
                        "end_sem": st.column_config.NumberColumn("End-Sem (/100)", min_value=0.0, max_value=100.0, step=1.0, required=True),
                        "internal_50": st.column_config.NumberColumn("Int. (/50)", format="%.2f", disabled=True),
                        "total_score": st.column_config.NumberColumn("Total (/100)", format="%.1f", disabled=True),
                        "grade_badge": st.column_config.MultiselectColumn(
                            "Grade",
                            options=list(GRADE_ORDER),
                            color=[GRADE_BADGES[g] for g in GRADE_ORDER],
                            disabled=True,
                        ),
                    },
                    hide_index=True,
                    height=360,
                    width="stretch",
                    key="crud_inline_editor",
                )

                editable_fields = ["cia1", "cia2", "cia3", "attendance", "end_sem"]
                changed_mask = (
                    edited_table[editable_fields].round(2) != editor_src[editable_fields].round(2)
                ).any(axis=1)
                changed_rows = edited_table.loc[changed_mask]

                with st.container(horizontal=True, vertical_alignment="center"):
                    st.caption(f"Pending modified rows: **{len(changed_rows)}**")
                    if st.button(
                        f"Save {len(changed_rows)} Modified Row(s) to SQLite",
                        type="primary",
                        icon=":material/published_with_changes:",
                        disabled=changed_rows.empty,
                    ):
                        all_valid = True
                        for row in changed_rows.itertuples(index=False):
                            ok, errs, _ = validate_assessment_scores(
                                row.cia1, row.cia2, row.cia3, row.attendance, row.end_sem
                            )
                            if not ok:
                                all_valid = False
                                st.error(f"{row.reg_no} ({row.subject_code}): {'; '.join(errs)}")
                        if all_valid:
                            _, msg = bulk_update_from_editor(changed_rows)
                            st.toast(msg, icon=":material/check_circle:")
                            st.rerun()
            else:
                rec_options = view_df["assessment_id"].tolist()
                rec_labels = {
                    int(r.assessment_id): f"{r.reg_no} · {r.name} · {r.subject_code} (Current: {r.total_score:.1f}/100, Grade {r.grade})"
                    for r in view_df.itertuples(index=False)
                }
                chosen_id = st.selectbox(
                    "Select Assessment Record to Edit",
                    options=rec_options,
                    format_func=lambda i: rec_labels[int(i)],
                )
                cur_row = view_df[view_df["assessment_id"] == chosen_id].iloc[0]

                with st.form("crud_single_update_form"):
                    p1, p2, p3, p4 = st.columns([1.8, 1.1, 2.0, 1.1])
                    up_name = p1.text_input("Student Name *", value=str(cur_row["name"]))
                    up_sec = p2.selectbox(
                        "Cohort *",
                        options=list(SECTIONS),
                        index=list(SECTIONS).index(str(cur_row["section"])),
                    )
                    up_mail = p3.text_input("University Email *", value=str(cur_row["email"]))
                    up_sem1 = p4.number_input("Sem 1 SGPA *", 0.0, 10.0, float(cur_row["sem1_sgpa"]), 0.1)

                    u1, u2, u3, u4, u5 = st.columns(5)
                    up_cia1 = u1.number_input("CIA 1 (/20)", 0.0, 20.0, float(cur_row["cia1"]), 0.5)
                    up_cia2 = u2.number_input("Mid-Sem (/50)", 0.0, 50.0, float(cur_row["cia2"]), 0.5)
                    up_cia3 = u3.number_input("CIA 3 (/20)", 0.0, 20.0, float(cur_row["cia3"]), 0.5)
                    up_att = u4.number_input("Attendance %", 0.0, 100.0, float(cur_row["attendance"]), 0.5)
                    up_ese = u5.number_input("End-Sem (/100)", 0.0, 100.0, float(cur_row["end_sem"]), 1.0)

                    if st.form_submit_button("Update Profile & Assessment", type="primary", icon=":material/check:"):
                        ok, errs, cleaned = validate_student_record(
                            reg_no=cur_row["reg_no"],
                            name=up_name,
                            section=up_sec,
                            email=up_mail,
                            sem1_sgpa=up_sem1,
                            subject_code=cur_row["subject_code"],
                            cia1=up_cia1,
                            cia2=up_cia2,
                            cia3=up_cia3,
                            attendance=up_att,
                            end_sem=up_ese,
                        )
                        if not ok:
                            for e in errs:
                                st.error(e)
                        else:
                            _, msg = upsert_student_assessment(cleaned, allow_overwrite=True)
                            st.toast(msg, icon=":material/check_circle:")
                            st.rerun()

    elif active_tab == "Delete Records":
        d_left, d_right = st.columns(2)

        with d_left.container(border=True, height="stretch"):
            card_header(
                "Delete Single Subject Assessment",
                "Removes one (Student × Subject) CIA entry from SQLite",
            )
            ass_opts = df_all["assessment_id"].tolist()
            ass_map = {
                int(r.assessment_id): f"{r.reg_no} · {r.name} · {r.subject_code} ({r.subject_short})"
                for r in df_all.itertuples(index=False)
            }
            del_ass_id = st.selectbox(
                "Assessment Record",
                options=ass_opts,
                format_func=lambda i: ass_map[int(i)],
                key="del_single_id",
            )
            confirm_single = st.checkbox(
                "Confirm deletion of this subject assessment record",
                key="del_single_confirm",
            )
            if st.button(
                "Delete Subject Record",
                type="secondary",
                icon=":material/delete:",
                disabled=not confirm_single,
            ):
                ok, msg = delete_assessment_record(int(del_ass_id))
                if ok:
                    st.toast(msg, icon=":material/delete:")
                    st.rerun()
                else:
                    st.error(msg)

        with d_right.container(border=True, height="stretch"):
            card_header(
                "Delete Entire Student Profile (Cascade)",
                "Removes the student and all linked subject assessments",
            )
            stu_uniq = df_all[["reg_no", "name", "section"]].drop_duplicates("reg_no")
            stu_map = {
                r.reg_no: f"{r.reg_no} · {r.name} ({r.section})"
                for r in stu_uniq.itertuples(index=False)
            }
            del_reg = st.selectbox(
                "Student Profile",
                options=stu_uniq["reg_no"].tolist(),
                format_func=lambda r: stu_map[r],
                key="del_stu_reg",
            )
            confirm_stu = st.checkbox(
                f"Confirm permanent cascade removal of {del_reg}",
                key="del_stu_confirm",
            )
            if st.button(
                "Remove Student & All Marks",
                type="secondary",
                icon=":material/person_remove:",
                disabled=not confirm_stu,
            ):
                ok, msg = delete_student_profile(str(del_reg))
                if ok:
                    st.toast(msg, icon=":material/delete_forever:")
                    st.rerun()
                else:
                    st.error(msg)

    else:
        sy_left, sy_right = st.columns([3.1, 1.9])

        with sy_left.container(border=True, height="stretch"):
            card_header(
                "Batch Sheet, CSV & Google Sheets Sync",
                "Stage manual batch rows, upload a CSV, or fetch a public Google Sheet",
            )
            sync_src = st.segmented_control(
                "Sync Source",
                ["Manual Batch Sheet", "Upload CSV File", "Google Sheets Link"],
                default="Manual Batch Sheet",
                required=True,
                key="sync_src_mode",
                label_visibility="collapsed",
            )

            incoming_df: pd.DataFrame | None = None
            replace_mode = False

            if sync_src == "Manual Batch Sheet":
                st.caption(
                    "Add or edit rows directly in the staging sheet below (`+` adds new rows), then validate "
                    "and commit your batch to SQLite."
                )
                blank_stage = pd.DataFrame(
                    [
                        {
                            "reg_no": "2547101",
                            "name": "Devansh Gupta",
                            "section": "2MCA-A",
                            "subject_code": "MCA411-2",
                            "sem1_sgpa": 8.8,
                            "cia1": 19.0,
                            "cia2": 46.0,
                            "cia3": 19.5,
                            "attendance": 96.0,
                            "end_sem": 92.0,
                        }
                    ]
                )
                staged_rows = st.data_editor(
                    blank_stage,
                    num_rows="dynamic",
                    column_config={
                        "reg_no": st.column_config.TextColumn("Reg. No. *", required=True),
                        "name": st.column_config.TextColumn("Name *", required=True),
                        "section": st.column_config.SelectboxColumn("Section *", options=list(SECTIONS), required=True),
                        "subject_code": st.column_config.SelectboxColumn("Subject *", options=list(SUBJECT_CODES), required=True),
                        "sem1_sgpa": st.column_config.NumberColumn("Sem1 SGPA", step=0.1),
                        "cia1": st.column_config.NumberColumn("CIA1 (/20)", step=0.5),
                        "cia2": st.column_config.NumberColumn("CIA2 (/50)", step=0.5),
                        "cia3": st.column_config.NumberColumn("CIA3 (/20)", step=0.5),
                        "attendance": st.column_config.NumberColumn("Att %", step=0.5),
                        "end_sem": st.column_config.NumberColumn("ESE (/100)", step=1.0),
                    },
                    hide_index=True,
                    width="stretch",
                    key="sync_manual_stage_grid",
                )
                if st.button("Validate & Sync Staged Batch", type="primary", icon=":material/fact_check:"):
                    ok, errs, clean_df = validate_imported_dataframe(staged_rows)
                    if not ok:
                        st.error("Batch validation caught input errors:")
                        for e in errs:
                            st.caption(f"• {e}")
                    else:
                        _, msg = sync_validated_dataframe(clean_df, replace_all=False)
                        st.toast(msg, icon=":material/check_circle:")
                        st.rerun()

            elif sync_src == "Upload CSV File":
                replace_mode = st.checkbox(
                    "Replace entire database (uncheck to merge/upsert into existing records)",
                    value=False,
                    key="sync_csv_replace",
                )
                up_file = st.file_uploader("Select CHRIST MCA CIA CSV file", type=["csv"])
                if up_file is not None:
                    try:
                        incoming_df = pd.read_csv(up_file)
                    except Exception as exc:
                        st.error(f"Could not parse CSV file: {exc}")
            else:
                replace_mode = st.checkbox(
                    "Replace entire database (uncheck to merge/upsert into existing records)",
                    value=False,
                    key="sync_gs_replace",
                )
                gs_url = st.text_input(
                    "Paste Public Google Sheets URL",
                    placeholder="https://docs.google.com/spreadsheets/d/.../edit#gid=0",
                )
                if gs_url.strip() and st.button("Fetch & Validate Sheet", icon=":material/cloud_download:"):
                    try:
                        incoming_df = fetch_google_sheets_dataframe(gs_url)
                    except Exception as exc:
                        st.error(f"Unable to fetch Google Sheet CSV: {exc}")

            if incoming_df is not None:
                ok, errs, clean_df = validate_imported_dataframe(incoming_df)
                if not ok:
                    st.error("Validation failed on imported data:")
                    for e in errs:
                        st.caption(f"• {e}")
                else:
                    st.success(f"Validated **{len(clean_df)}** assessment rows ready to sync.")
                    if st.button("Commit Validated Data to SQLite", type="primary", icon=":material/sync:"):
                        _, msg = sync_validated_dataframe(clean_df, replace_all=replace_mode)
                        st.toast(msg, icon=":material/check_circle:")
                        st.rerun()

            st.divider()
            with st.container(horizontal=True, vertical_alignment="center"):
                if CSV_SEED_PATH.exists():
                    st.download_button(
                        "Download CSV Template",
                        data=CSV_SEED_PATH.read_bytes(),
                        file_name="christ_mca_cia_template.csv",
                        mime="text/csv",
                        icon=":material/download:",
                    )
                if st.button(
                    "Reset Database to Default 60-Student Seed",
                    icon=":material/settings_backup_restore:",
                ):
                    init_database(force_reset=True)
                    st.toast("Database restored to clean 60-student CHRIST 2MCA seed.", icon=":material/restore:")
                    st.rerun()

        with sy_right.container(border=True, height="stretch"):
            card_header(
                "SQLite Audit Trail",
                "Timestamped log of Create, Update, Bulk Edit, Delete & Sync events",
            )
            st.dataframe(
                audit_df,
                column_config={
                    "action": st.column_config.TextColumn("Operation", width="small"),
                    "target_ref": st.column_config.TextColumn("Target"),
                    "details": st.column_config.TextColumn("Details"),
                    "created_at": st.column_config.TextColumn("Timestamp"),
                },
                hide_index=True,
                height=345,
                width="stretch",
            )


_render_crud_workspace(full_df, audit_df_top)
