import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import json

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ड्यूटी रोस्टर | 1930",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans Devanagari', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #1F3864, #2E75B6);
    padding: 18px 24px; border-radius: 12px;
    color: white; text-align: center; margin-bottom: 20px;
}
.main-header h1 { font-size: 1.6rem; margin: 0; font-weight: 700; }
.main-header p  { font-size: 0.9rem; margin: 4px 0 0 0; opacity: 0.85; }

.metric-card {
    background: white; border-radius: 10px; padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 5px solid;
    text-align: center;
}
.metric-card .val  { font-size: 2.2rem; font-weight: 700; line-height: 1.1; }
.metric-card .lbl  { font-size: 0.82rem; color: #666; margin-top: 2px; }
.card-blue   { border-color: #2E75B6; color: #2E75B6; }
.card-green  { border-color: #70AD47; color: #70AD47; }
.card-orange { border-color: #FFC000; color: #FFC000; }
.card-red    { border-color: #FF0000; color: #FF0000; }
.card-purple { border-color: #7030A0; color: #7030A0; }

.shift-badge {
    display:inline-block; padding:3px 10px; border-radius:12px;
    font-size:0.8rem; font-weight:600; color:white;
}
.s1 { background:#FFC000; color:#000; }
.s2 { background:#70AD47; }
.s3 { background:#2E75B6; }
.leave-badge { background:#FF4444; }

.section-title {
    font-size:1.1rem; font-weight:700; color:#1F3864;
    border-bottom:3px solid #2E75B6; padding-bottom:6px;
    margin:20px 0 12px 0;
}
.run-btn button {
    background:linear-gradient(135deg,#1F3864,#2E75B6) !important;
    color:white !important; font-weight:700 !important;
    font-size:1rem !important; border-radius:8px !important;
    padding:10px 24px !important; width:100%;
}
</style>
""", unsafe_allow_html=True)

# ── Google Sheet Connection ───────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(show_spinner=False)
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=60, show_spinner=False)
def load_sheet_data(sheet_id):
    client = get_client()
    sh = client.open_by_key(sheet_id)

    main_df   = pd.DataFrame(sh.worksheet("Main_Duty").get_all_records())
    config_df = pd.DataFrame(sh.worksheet("Config").get_all_values()[1:],
                              columns=sh.worksheet("Config").get_all_values()[0])
    leave_df  = pd.DataFrame(sh.worksheet("Leave").get_all_records())
    try:
        audit_df = pd.DataFrame(sh.worksheet("Audit_Log").get_all_records())
    except:
        audit_df = pd.DataFrame(columns=["Date","Time","Mobile","Name_Rank","Action","Shift","Status"])

    return main_df, config_df, leave_df, audit_df

def run_assignment(sheet_id):
    """Core duty assignment logic — adapted from your original code."""
    client = get_client()
    sh     = client.open_by_key(sheet_id)

    main_ws   = sh.worksheet("Main_Duty")
    config_ws = sh.worksheet("Config")
    leave_ws  = sh.worksheet("Leave")

    try:
        audit_ws = sh.worksheet("Audit_Log")
    except:
        audit_ws = sh.add_worksheet("Audit_Log", rows="10000", cols="7")
        audit_ws.append_row(["Date","Time","Mobile","Name_Rank","Action","Shift","Status"])

    today_dt  = datetime.now()
    today_str = today_dt.strftime("%d-%m-%Y")
    now_time  = today_dt.strftime("%H:%M")

    # Double-run protection
    last_run = main_ws.acell("L1").value
    if last_run == today_str:
        return False, f"🛑 आज ({today_str}) ड्यूटी पहले ही लग चुकी है।"

    # Load data
    df = pd.DataFrame(main_ws.get_all_records())
    mob_col       = "Mobile_No"
    name_col      = "Employee_Name"
    status_col    = "STATUS"
    shift_col     = "Current_Shift"
    date_col      = "Shift_Start_Date"
    days_col      = "Days_On_Duty"
    duty_count_col= "Total_Duty_3M"
    s1_cnt, s2_cnt, s3_cnt = "Shift1count","Shift2count","Shift3count"

    if mob_col not in df.columns:
        return False, f"❌ Column '{mob_col}' नहीं मिला।"

    df[mob_col] = df[mob_col].astype(str).str.strip()
    df.set_index(mob_col, inplace=True)
    for c in [status_col, duty_count_col, s1_cnt, s2_cnt, s3_cnt, days_col]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # Config rules
    shift_rules = {}
    for row in config_ws.get_all_values()[1:]:
        if row[0]:
            try:
                shift_rules[row[0]] = {"req": int(float(row[1])), "max": int(float(row[3]))}
            except:
                continue

    # Leave list
    leave_data = pd.DataFrame(leave_ws.get_all_records())
    leave_list = leave_data["Mobile_No"].astype(str).tolist() if "Mobile_No" in leave_data.columns else []

    logs = []

    # Rotation / removal
    for mobile, row in df.iterrows():
        if not row[shift_col] or str(row[shift_col]).strip() == "":
            df.at[mobile, days_col] = 0
            continue
        try:
            start_date = pd.to_datetime(row[date_col], dayfirst=True).date()
            diff = (today_dt.date() - start_date).days
            df.at[mobile, days_col] = max(0, diff)
            rule = shift_rules.get(row[shift_col])
            if (rule and diff >= rule["max"]) or (mobile in leave_list) or (row[status_col] == 0):
                logs.append([today_str, now_time, mobile, row[name_col], "Removed", row[shift_col], "Success"])
                df.at[mobile, shift_col] = ""
                df.at[mobile, date_col]  = ""
                df.at[mobile, days_col]  = 0
        except:
            df.at[mobile, days_col] = 0

    # Assignment
    for s_name, rule in shift_rules.items():
        current_count = len(df[df[shift_col] == s_name])
        needed = rule["req"] - current_count
        if needed > 0:
            pool = df[(df[status_col] == 1) & (df[shift_col] == "") & (~df.index.isin(leave_list))]
            if pool.empty:
                continue
            t_cnt = s1_cnt if "1" in s_name else (s2_cnt if "2" in s_name else s3_cnt)
            sort_cols = [t_cnt, duty_count_col] if t_cnt in df.columns else [duty_count_col]
            selected = pool.sort_values(by=sort_cols).head(needed)
            for m in selected.index:
                df.at[m, shift_col]     = s_name
                df.at[m, date_col]      = today_str
                df.at[m, days_col]      = 0
                df.at[m, duty_count_col]+= 1
                if t_cnt in df.columns:
                    df.at[m, t_cnt] += 1
                logs.append([today_str, now_time, m, df.at[m, name_col], "Assigned", s_name, "Success"])

    # Export
    df_export  = df.reset_index()
    final_data = [df_export.columns.values.tolist()] + df_export.fillna("").values.tolist()
    main_ws.update(final_data)
    main_ws.update("L1", [[today_str]])
    if logs:
        audit_ws.append_rows(logs)

    load_sheet_data.clear()  # Cache clear
    return True, f"✅ {today_str} की ड्यूटी सफलतापूर्वक लग गई! कुल {len(logs)} बदलाव हुए।"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🚨 साइबर क्राइम हेल्पलाइन 1930</h1>
  <p>ड्यूटी रोस्टर प्रबंधन प्रणाली</p>
</div>
""", unsafe_allow_html=True)

# ── Sheet ID input (sidebar) ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ सेटिंग्स")
    sheet_id = st.text_input("Google Sheet ID", value=st.secrets.get("SHEET_ID",""),
                              help="Sheet URL में /d/ के बाद का हिस्सा")
    st.markdown("---")
    st.markdown("**आज की तारीख**")
    st.markdown(f"📅 {datetime.now().strftime('%d %B %Y')}")
    st.markdown(f"🕐 {datetime.now().strftime('%H:%M')} बजे")

if not sheet_id:
    st.warning("⚠️ Sidebar में Google Sheet ID डालें।")
    st.stop()

# ── Load Data ─────────────────────────────────────────────────────────────────
with st.spinner("डेटा लोड हो रहा है..."):
    try:
        main_df, config_df, leave_df, audit_df = load_sheet_data(sheet_id)
    except Exception as e:
        st.error(f"❌ Sheet connect नहीं हुई: {e}")
        st.stop()

# ── Derived Data ──────────────────────────────────────────────────────────────
shift_col  = "Current_Shift"
status_col = "STATUS"
name_col   = "Employee_Name"
mob_col    = "Mobile_No"

main_df[mob_col]    = main_df[mob_col].astype(str).str.strip()
main_df[status_col] = pd.to_numeric(main_df[status_col], errors="coerce").fillna(0).astype(int)

on_duty  = main_df[main_df[shift_col].str.strip() != ""]
leave_ids= leave_df["Mobile_No"].astype(str).tolist() if "Mobile_No" in leave_df.columns else []
on_leave = main_df[main_df[mob_col].isin(leave_ids)]
inactive = main_df[main_df[status_col] == 0]
unassigned = main_df[(main_df[shift_col].str.strip() == "") &
                     (~main_df[mob_col].isin(leave_ids)) &
                     (main_df[status_col] == 1)]

# ── Summary Cards ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 सारांश</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    (c1, len(main_df),   "कुल कर्मचारी",    "card-blue"),
    (c2, len(on_duty),   "ड्यूटी पर",        "card-green"),
    (c3, len(on_leave),  "अवकाश पर",         "card-orange"),
    (c4, len(unassigned),"प्रतीक्षारत",       "card-purple"),
    (c5, len(inactive),  "निष्क्रिय",         "card-red"),
]
for col, val, lbl, cls in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card {cls}">
          <div class="val">{val}</div>
          <div class="lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Run Assignment Button ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ ड्यूटी लगाएं</div>', unsafe_allow_html=True)
col_btn, col_info = st.columns([1, 2])
with col_btn:
    st.markdown('<div class="run-btn">', unsafe_allow_html=True)
    run_clicked = st.button("🔄 आज की ड्यूटी लगाएं", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with col_info:
    today_str = datetime.now().strftime("%d-%m-%Y")
    last_run  = ""
    try:
        client = get_client()
        sh = client.open_by_key(sheet_id)
        last_run = sh.worksheet("Main_Duty").acell("L1").value or "कभी नहीं"
    except:
        last_run = "—"
    st.info(f"📅 आज: **{today_str}**  |  अंतिम रन: **{last_run}**")

if run_clicked:
    with st.spinner("ड्यूटी लग रही है..."):
        success, msg = run_assignment(sheet_id)
    if success:
        st.success(msg)
        st.balloons()
        st.rerun()
    else:
        st.warning(msg)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 शिफ्ट-वाइज ड्यूटी",
    "👥 सभी कर्मचारी",
    "🌴 अवकाश सूची",
    "📜 Audit Log",
    "➕ कर्मचारी जोड़ें / संपादित करें",
])

# ── TAB 1: Shift-wise Duty ────────────────────────────────────────────────────
with tab1:
    shifts = main_df[shift_col].dropna().unique()
    shifts = [s for s in shifts if str(s).strip() != ""]

    if not shifts:
        st.info("अभी कोई ड्यूटी नहीं लगी है। ऊपर 'ड्यूटी लगाएं' बटन दबाएं।")
    else:
        shift_colors = {0: "s1", 1: "s2", 2: "s3"}
        shift_labels = {0: "प्रातः शिफ्ट", 1: "सायं शिफ्ट", 2: "रात्रि शिफ्ट"}

        cols = st.columns(len(shifts))
        for idx, s in enumerate(sorted(shifts)):
            s_df = on_duty[on_duty[shift_col] == s][
                [name_col, "Designation" if "Designation" in main_df.columns else name_col,
                 "Days_On_Duty"] if "Days_On_Duty" in main_df.columns else [name_col]
            ].copy()

            badge_cls = shift_colors.get(idx % 3, "s1")
            label     = shift_labels.get(idx % 3, s)

            with cols[idx]:
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:14px;
                     box-shadow:0 2px 8px rgba(0,0,0,0.1);min-height:200px;">
                  <div style="text-align:center;margin-bottom:10px;">
                    <span class="shift-badge {badge_cls}">{s} — {label}</span>
                    <div style="font-size:1.6rem;font-weight:700;color:#1F3864;margin-top:6px;">
                      {len(s_df)}
                    </div>
                    <div style="font-size:0.75rem;color:#888;">कर्मचारी</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                disp_cols = [c for c in [name_col, "Designation", "Days_On_Duty"] if c in main_df.columns]
                rename_map = {name_col: "नाम", "Designation": "पद", "Days_On_Duty": "दिन"}
                st.dataframe(
                    on_duty[on_duty[shift_col] == s][disp_cols].rename(columns=rename_map),
                    use_container_width=True, hide_index=True
                )

# ── TAB 2: All Staff ──────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">👥 सम्पूर्ण कर्मचारी सूची</div>', unsafe_allow_html=True)

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search = st.text_input("🔍 नाम / मोबाइल खोजें", placeholder="नाम टाइप करें...")
    with col_filter:
        status_filter = st.selectbox("स्थिति", ["सभी", "ड्यूटी पर", "अवकाश पर", "प्रतीक्षारत", "निष्क्रिय"])

    disp = main_df.copy()
    if search:
        mask = disp[name_col].str.contains(search, case=False, na=False)
        if mob_col in disp.columns:
            mask |= disp[mob_col].str.contains(search, na=False)
        disp = disp[mask]
    if status_filter == "ड्यूटी पर":
        disp = disp[disp[shift_col].str.strip() != ""]
    elif status_filter == "अवकाश पर":
        disp = disp[disp[mob_col].isin(leave_ids)]
    elif status_filter == "प्रतीक्षारत":
        disp = disp[(disp[shift_col].str.strip() == "") & (~disp[mob_col].isin(leave_ids)) & (disp[status_col] == 1)]
    elif status_filter == "निष्क्रिय":
        disp = disp[disp[status_col] == 0]

    show_cols = [c for c in [mob_col, name_col, "Designation", shift_col, "Days_On_Duty",
                              "Total_Duty_3M", status_col] if c in disp.columns]
    rename_map = {mob_col: "मोबाइल", name_col: "नाम", "Designation": "पद",
                  shift_col: "वर्तमान शिफ्ट", "Days_On_Duty": "दिन",
                  "Total_Duty_3M": "3M ड्यूटी", status_col: "स्थिति"}
    st.dataframe(disp[show_cols].rename(columns=rename_map),
                 use_container_width=True, hide_index=True, height=420)
    st.caption(f"कुल: {len(disp)} कर्मचारी")

# ── TAB 3: Leave List ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">🌴 अवकाश पर कर्मचारी</div>', unsafe_allow_html=True)
    if leave_df.empty:
        st.info("कोई कर्मचारी अवकाश पर नहीं है।")
    else:
        st.dataframe(leave_df, use_container_width=True, hide_index=True, height=380)
        st.caption(f"कुल अवकाश: {len(leave_df)}")

    st.markdown("---")
    st.markdown("**नया अवकाश जोड़ें**")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        l_mob  = st.text_input("मोबाइल नं.", key="l_mob")
    with lc2:
        l_from = st.date_input("से तारीख", key="l_from")
    with lc3:
        l_to   = st.date_input("तक तारीख", key="l_to")
    l_reason = st.text_input("कारण", key="l_reason")

    if st.button("✅ अवकाश दर्ज करें"):
        if l_mob:
            try:
                client = get_client()
                sh = client.open_by_key(sheet_id)
                sh.worksheet("Leave").append_row([
                    l_mob,
                    l_from.strftime("%d-%m-%Y"),
                    l_to.strftime("%d-%m-%Y"),
                    l_reason,
                ])
                st.success("अवकाश दर्ज हो गया!")
                load_sheet_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("मोबाइल नं. भरें।")

# ── TAB 4: Audit Log ──────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">📜 Audit Log</div>', unsafe_allow_html=True)
    if audit_df.empty:
        st.info("अभी कोई लॉग नहीं है।")
    else:
        ac1, ac2 = st.columns([1, 1])
        with ac1:
            date_filter = st.text_input("तारीख फ़िल्टर (DD-MM-YYYY)", placeholder="जैसे: 15-06-2025")
        with ac2:
            action_filter = st.selectbox("Action", ["सभी", "Assigned", "Removed"])

        a_df = audit_df.copy()
        if date_filter:
            a_df = a_df[a_df["Date"].str.contains(date_filter, na=False)]
        if action_filter != "सभी":
            a_df = a_df[a_df["Action"] == action_filter]

        st.dataframe(a_df.sort_values("Date", ascending=False) if "Date" in a_df.columns else a_df,
                     use_container_width=True, hide_index=True, height=400)
        st.caption(f"कुल रिकॉर्ड: {len(a_df)}")

# ── TAB 5: Add / Edit Staff ───────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">➕ नया कर्मचारी जोड़ें</div>', unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        e_mob  = st.text_input("मोबाइल नं. *", key="e_mob")
        e_name = st.text_input("नाम (हिंदी) *", key="e_name")
        e_desig= st.text_input("पद / पदनाम", key="e_desig")
    with ec2:
        e_rank = st.text_input("रैंक", key="e_rank")
        e_status = st.selectbox("स्थिति", [1, 0], format_func=lambda x: "सक्रिय" if x == 1 else "निष्क्रिय")
        e_shift_pref = st.selectbox("शिफ्ट वरीयता", ["", "Shift1", "Shift2", "Shift3"])

    if st.button("💾 कर्मचारी सहेजें"):
        if e_mob and e_name:
            try:
                client = get_client()
                sh = client.open_by_key(sheet_id)
                ws = sh.worksheet("Main_Duty")
                ws.append_row([e_mob, e_name, e_desig, e_rank, e_status,
                                "", "", 0, 0, 0, 0, 0])
                st.success(f"✅ {e_name} जोड़ा गया!")
                load_sheet_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("मोबाइल नं. और नाम ज़रूरी है।")

    st.markdown("---")
    st.markdown('<div class="section-title">🔄 Cache रिफ्रेश करें</div>', unsafe_allow_html=True)
    if st.button("🔃 डेटा रिफ्रेश करें"):
        load_sheet_data.clear()
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.8rem;'>"
    "साइबर क्राइम हेल्पलाइन 1930 | ड्यूटी रोस्टर प्रणाली"
    "</div>",
    unsafe_allow_html=True
)
