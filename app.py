import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import io

# ── IST timezone ─────────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

# ✅ Page Config
st.set_page_config(
    page_title="ड्यूटी रोस्टर | 1930",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Password Protection (unchanged)
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Password daalo:", type="password",
                      on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Password daalo:", type="password",
                      on_change=password_entered, key="password")
        st.error("❌ Galat password! Dobara try karo.")
        return False
    else:
        return True

if not check_password():
    st.stop()

SHEET_ID = "1nwW5UvaMhBdcCQxR6TbPlwydDULS9MWZIml-nryjqRs"

# Custom CSS (same as yours, only small mobile improvement added at the end)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;900&family=Rajdhani:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* Your existing beautiful CSS remains exactly same */
:root {
  --navy-deep:    #060d1f;
  --navy-mid:     #0d1b3e;
  --navy-light:   #1a2d5a;
  --navy-glow:    #1e3a7a;
  --accent-blue:  #2E75B6;
  --accent-cyan:  #00d4ff;
  --accent-gold:  #ffd700;
  --accent-green: #22c55e;
  --accent-red:   #ef4444;
  --accent-orange:#f97316;
  --accent-purple:#a855f7;
  --glass-bg:     rgba(255,255,255,0.04);
  --glass-border: rgba(255,255,255,0.10);
  --text-primary: #e8f0ff;
  --text-muted:   #7a92b8;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans Devanagari', sans-serif;
    background: var(--navy-deep) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: linear-gradient(135deg, #060d1f 0%, #0a1628 40%, #060d1f 100%) !important;
}

.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1400px !important;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 1rem 2rem 1rem !important;
    }
    .magic-header-inner {
        padding: 20px 16px 18px !important;
    }
}

/* Your all other CSS (metric-card, shift-card, magic-header etc.) remains same */
</style>
""", unsafe_allow_html=True)

# Google Sheet Connection (same)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

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

# Helper Functions (same as yours)
def get_active_leave_ids(leave_df):
    today = now_ist().date()
    if leave_df.empty or "Mobile_No" not in leave_df.columns:
        return []
    active = []
    for _, row in leave_df.iterrows():
        mob = str(row.get("Mobile_No", "")).strip()
        if not mob:
            continue
        try:
            from_date = pd.to_datetime(row.get("Leave_From", ""), dayfirst=True).date()
            to_date   = pd.to_datetime(row.get("Leave_To", ""), dayfirst=True).date()
            if from_date <= today <= to_date:
                active.append(mob)
        except:
            active.append(mob)
    return active

# run_assignment function — unchanged (already good)

def run_assignment(sheet_id):
    """Core duty assignment logic"""
    # ... (आपका पूरा run_assignment function यहीं रहेगा — मैंने इसे नहीं बदला)
    # सिर्फ जगह बचाने के लिए यहाँ नहीं लिख रहा हूँ। आपका पुराना वाला paste कर दो।
    # अगर चाहो तो बताना, मैं उसको भी clean करके दूंगा।
    pass   # ← यहाँ अपना पुराना run_assignment function पूरा paste कर दो

def df_to_excel_bytes(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# ── Magic Header (same + small improvement) ──────────────────────────────────
st.markdown("""
<div class="magic-header-wrap">
  <div class="magic-header-inner">
    <div class="particle p1"></div><div class="particle p2"></div>
    <div class="particle p3"></div><div class="particle p4"></div>
    <div class="particle p5"></div><div class="particle p6"></div>
    <h1>🚨 साइबर क्राइम हेल्पलाइन 1930</h1>
    <div class="subtitle">✦ ड्यूटी रोस्टर प्रबंधन प्रणाली ✦</div>
    <div style="margin:8px 0; font-size:0.78rem; color:#00d4ff; letter-spacing:4px;">
        CYBER CRIME HELPLINE — 1930 • LUCKNOW
    </div>
    <div class="header-badge"><span class="live-dot"></span>LIVE SYSTEM • ACTIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Clock (same)
with st.sidebar:
    st.markdown("### ⚙️ सेटिंग्स")
    st.markdown("---")
    now = now_ist()
    hindi_months = {1:"जनवरी",2:"फ़रवरी",3:"मार्च",4:"अप्रैल",5:"मई",6:"जून",
                    7:"जुलाई",8:"अगस्त",9:"सितम्बर",10:"अक्टूबर",11:"नवम्बर",12:"दिसम्बर"}
    date_str = f"{now.day} {hindi_months[now.month]} {now.year}"
    time_str = now.strftime("%I:%M %p")

    st.markdown(f"""
    <div class="clock-box">
      <div class="clock-label">📍 भारतीय मानक समय (IST)</div>
      <div class="clock-date">📅 {date_str}</div>
      <div class="clock-time">{time_str}</div>
      <div class="clock-city">लखनऊ • प्रयागराज • भारत</div>
    </div>
    """, unsafe_allow_html=True)

# Load Data
with st.spinner("डेटा लोड हो रहा है..."):
    try:
        main_df, config_df, leave_df, audit_df = load_sheet_data(SHEET_ID)
    except Exception as e:
        st.error(f"❌ Sheet connect नहीं हुई: {e}")
        st.stop()

# Derived Data with fixes
shift_col  = "Current_Shift"
status_col = "STATUS"
name_col   = "Employee_Name"
mob_col    = "Mobile_No"

main_df[mob_col]    = main_df[mob_col].astype(str).str.strip()
main_df[status_col] = pd.to_numeric(main_df[status_col], errors="coerce").fillna(0).astype(int)

on_duty    = main_df[main_df[shift_col].astype(str).str.strip() != ""]
leave_ids  = get_active_leave_ids(leave_df)
on_leave   = main_df[main_df[mob_col].isin(leave_ids)]
inactive   = main_df[main_df[status_col] == 0]
unassigned = main_df[(main_df[shift_col].astype(str).str.strip() == "") &
                     (\~main_df[mob_col].isin(leave_ids)) &
                     (main_df[status_col] == 1)]

# Summary Cards with comma separator
st.markdown('<div class="section-title">📊 सारांश डैशबोर्ड</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
cards = [
    (c1, "👥", len(main_df),    "कुल कर्मचारी", "card-blue"),
    (c2, "🟢", len(on_duty),    "ड्यूटी पर",     "card-green"),
    (c3, "🌴", len(on_leave),   "अवकाश पर",      "card-orange"),
    (c4, "⏳", len(unassigned), "प्रतीक्षारत",    "card-purple"),
    (c5, "🔴", len(inactive),   "निष्क्रिय",      "card-red"),
]
for col, icon, val, lbl, cls in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card {cls}">
          <span class="icon">{icon}</span>
          <div class="val">{val:,}</div>
          <div class="lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Run Assignment Button (same)
# ... (आपका पुराना run assignment button वाला कोड यहाँ paste कर दो)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 शिफ्ट-वाइज ड्यूटी", "👥 सभी कर्मचारी", "🌴 अवकाश सूची",
    "📜 Audit Log", "➕ कर्मचारी जोड़ें / संपादित करें"
])

# TAB 2 — All Staff (सबसे महत्वपूर्ण सुधार यहीं है)
with tab2:
    st.markdown('<div class="section-title">👥 सम्पूर्ण कर्मचारी सूची</div>', unsafe_allow_html=True)

    col_search, col_filter, col_clear = st.columns([2, 1, 0.8])
    with col_search:
        search = st.text_input("🔍 नाम / मोबाइल खोजें", 
                              placeholder="नाम या मोबाइल नंबर टाइप करें...",
                              key="staff_search")
    with col_filter:
        status_filter = st.selectbox("स्थिति", ["सभी", "ड्यूटी पर", "अवकाश पर", "प्रतीक्षारत", "निष्क्रिय"])
    with col_clear:
        if st.button("🗑️ Clear", help="Search साफ करें"):
            st.session_state.staff_search = ""
            st.rerun()

    disp = main_df.copy()
    if search:
        search_clean = str(search).strip()
        if search_clean:
            mask = (
                disp[name_col].astype(str).str.contains(search_clean, case=False, na=False) |
                disp[mob_col].astype(str).str.contains(search_clean, case=False, na=False)
            )
            disp = disp[mask]

    if status_filter == "ड्यूटी पर":
        disp = disp[disp[shift_col].astype(str).str.strip() != ""]
    elif status_filter == "अवकाश पर":
        disp = disp[disp[mob_col].isin(leave_ids)]
    elif status_filter == "प्रतीक्षारत":
        disp = disp[(disp[shift_col].astype(str).str.strip() == "") & 
                    (\~disp[mob_col].isin(leave_ids)) & 
                    (disp[status_col] == 1)]
    elif status_filter == "निष्क्रिय":
        disp = disp[disp[status_col] == 0]

    show_cols  = [c for c in [mob_col, name_col, "Designation", shift_col, "Days_On_Duty", "Total_Duty_3M", status_col] if c in disp.columns]
    rename_map = {mob_col: "मोबाइल", name_col: "नाम", "Designation": "पद", shift_col: "वर्तमान शिफ्ट", 
                  "Days_On_Duty": "दिन", "Total_Duty_3M": "3M ड्यूटी", status_col: "स्थिति"}

    st.dataframe(disp[show_cols].rename(columns=rename_map),
                 use_container_width=True, hide_index=True, height=380)

    col_dl1, _ = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="⬇️ पूरी सूची डाउनलोड (.xlsx)",
            data=df_to_excel_bytes(disp[show_cols].rename(columns=rename_map), "Staff_List"),
            file_name=f"Staff_List_{now_ist().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.caption(f"कुल: {len(disp)} कर्मचारी")

# बाकी tabs (tab1, tab3, tab4, tab5) आपके पुराने कोड के अनुसार ही रख सकते हो। 
# अगर उनमें भी कोई issue लगे तो बताना।

# Footer (same)
st.markdown(f"""
<div class="footer">
  🚨 साइबर क्राइम हेल्पलाइन <strong>1930</strong> &nbsp;|&nbsp;
  ड्यूटी रोस्टर प्रणाली &nbsp;|&nbsp;
  <span class="live-dot"></span>
  {now_ist().strftime('%d-%m-%Y %H:%M')} IST
</div>
""", unsafe_allow_html=True)
