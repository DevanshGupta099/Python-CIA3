"""Live CIA Marks Manager: Full CRUD (Create, Read, Update, Delete), Validations & Live Sync."""

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
)
from utils.database import (
    CSV_SEED_PATH,
    bulk_update_from_editor,
    delete_assessment_record,
    delete_student_profile,
    fetch_google_sheets_dataframe,
    get_audit_log_df,
    init_database,
    sync_validated_dataframe,
    upsert_student_assessment,
)
from utils.ui import card_header, render_hero_strip
from utils.validators import validate_assessment_scores, validate_imported_dataframe, validate_student_record

full_df: pd.DataFrame = st.session_state["full_df"]
audit_df_top = get_audit_log_df(limit=25)

render_hero_strip(
    eyebrow="SQLite3 Persistence · Strict Input Validation · Google Sheets / CSV Live Sync",
    title="CIA Marks & Student Records Manager (Full CRUD)",
    subtitle=(
        "Create new student CIA records, update marks via validated forms or inline spreadsheet "
        "editors, remove records with confirmation guards, or sync live CSV / Google Sheets data."
    ),
    chips=[
        f"{full_df['reg_no'].nunique()} Stored Students",
        f"{len(full_df)} Subject Assessments",
        f"{len(audit_df_top)} Recent Audit Events",
        "Regex + Bound Validated",
    ],
)

tab_create, tab_update, tab_delete, tab_sync = st.tabs(
    [
        ":material/person_add: Create Record",
        ":material/edit_square: Read & Update Marks",
        ":material/delete_sweep: Delete Records",
        ":material/sync: Live Sync & Audit Log",
    ]
)

# ---------------------------------------------------------------------------
# Tab 1: CREATE — Add Student / Subject CIA Record with Full Validation
# ---------------------------------------------------------------------------
with tab_create:
    with st.container(border=True):
        card_header(
            "Add New Student or Subject CIA Assessment",
            "All fields enforce CHRIST University ID patterns and exact component mark limits",
            verified=True,
        )
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

# ---------------------------------------------------------------------------
# Tab 2: READ & UPDATE — Search, Form Update, or Spreadsheet Inline Bulk Edit
# ---------------------------------------------------------------------------
with tab_update:
    with st.container(border=True):
        u_ctrl = card_header(
            "Search, Inspect & Update CIA Marks",
            "Filter records instantaneously and edit via validated Single-Record Form or Inline Table Editor",
        )
        edit_mode = u_ctrl.segmented_control(
            "Edit Style",
            ["Inline Spreadsheet Editor", "Single Record Form"],
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

        view_df = full_df.copy()
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
                u1, u2, u3, u4, u5 = st.columns(5)
                up_cia1 = u1.number_input("CIA 1 (/20)", 0.0, 20.0, float(cur_row["cia1"]), 0.5)
                up_cia2 = u2.number_input("Mid-Sem (/50)", 0.0, 50.0, float(cur_row["cia2"]), 0.5)
                up_cia3 = u3.number_input("CIA 3 (/20)", 0.0, 20.0, float(cur_row["cia3"]), 0.5)
                up_att = u4.number_input("Attendance %", 0.0, 100.0, float(cur_row["attendance"]), 0.5)
                up_ese = u5.number_input("End-Sem (/100)", 0.0, 100.0, float(cur_row["end_sem"]), 1.0)

                if st.form_submit_button("Update Assessment", type="primary", icon=":material/check:"):
                    ok, errs, cleaned = validate_student_record(
                        reg_no=cur_row["reg_no"],
                        name=cur_row["name"],
                        section=cur_row["section"],
                        email=cur_row["email"],
                        sem1_sgpa=cur_row["sem1_sgpa"],
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

# ---------------------------------------------------------------------------
# Tab 3: DELETE — Safe Record or Full Student Profile Removal
# ---------------------------------------------------------------------------
with tab_delete:
    d_left, d_right = st.columns(2)

    with d_left.container(border=True, height="stretch"):
        card_header(
            "Delete Single Subject Assessment",
            "Removes one (Student × Subject) CIA entry from SQLite",
        )
        ass_opts = full_df["assessment_id"].tolist()
        ass_map = {
            int(r.assessment_id): f"{r.reg_no} · {r.name} · {r.subject_code} ({r.subject_short})"
            for r in full_df.itertuples(index=False)
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
        stu_uniq = full_df[["reg_no", "name", "section"]].drop_duplicates("reg_no")
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

# ---------------------------------------------------------------------------
# Tab 4: LIVE SYNC (Google Sheets / CSV Import) + Factory Reset + Audit Log
# ---------------------------------------------------------------------------
with tab_sync:
    sy_left, sy_right = st.columns([3, 2])

    with sy_left.container(border=True, height="stretch"):
        card_header(
            "Live CSV & Google Sheets Sync",
            "Import validated live CIA sheets directly into SQLite and st.session_state",
            verified=True,
        )
        sync_src = st.segmented_control(
            "Sync Source",
            ["Upload CSV File", "Google Sheets Public Link"],
            default="Upload CSV File",
            required=True,
            key="sync_src_mode",
            label_visibility="collapsed",
        )
        replace_mode = st.checkbox(
            "Replace entire database (uncheck to merge/upsert into existing records)",
            value=False,
        )

        incoming_df: pd.DataFrame | None = None
        if sync_src == "Upload CSV File":
            up_file = st.file_uploader("Select CHRIST MCA CIA CSV file", type=["csv"])
            if up_file is not None:
                try:
                    incoming_df = pd.read_csv(up_file)
                except Exception as exc:
                    st.error(f"Could not parse CSV file: {exc}")
        else:
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
                    "Download Sample CSV Template",
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
            "Live SQLite Audit Trail",
            "Timestamped log of Create, Update, Bulk Edit, Delete & Sync events",
        )
        st.dataframe(
            audit_df_top,
            column_config={
                "action": st.column_config.TextColumn("Operation", width="small"),
                "target_ref": st.column_config.TextColumn("Target"),
                "details": st.column_config.TextColumn("Details"),
                "created_at": st.column_config.TextColumn("Timestamp"),
            },
            hide_index=True,
            height=330,
            width="stretch",
        )
