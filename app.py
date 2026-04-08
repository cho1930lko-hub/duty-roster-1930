import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import json
import io

# ── IST timezone using stdlib only (no pytz) ──────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

# ✅ STEP 1: set_page_config SABSE PEHLE
st.set_page_config(
    page_title="ड्यूटी रोस्टर | 1930",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ✅ STEP 2: Password Protection
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

# ✅ STEP 3: Password check
if not check_password():
    st.stop()

# ✅ STEP 4: Sheet ID hardcoded
SHEET_ID = "1nwW5UvaMhBdcCQxR6TbPlwydDULS9MWZIml-nryjqRs"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;900&family=Rajdhani:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ══════════════════════════════════════════
   ROOT VARIABLES & BASE RESET
══════════════════════════════════════════ */
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
  --shadow-glow:  0 0 40px rgba(46,117,182,0.25);
}

html, body, [class*="css"] {
    font-family: 'Noto Sans Devanagari', sans-serif;
    background: var(--navy-deep) !important;
    color: var(--text-primary) !important;
}

/* Dark background for entire app */
.stApp {
    background: linear-gradient(135deg, #060d1f 0%, #0a1628 40%, #060d1f 100%) !important;
    min-height: 100vh;
}

/* Main content area */
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1400px !important;
}

/* ══════════════════════════════════════════
   MAGIC LIGHT HEADER — ENHANCED
══════════════════════════════════════════ */
.magic-header-wrap {
    position: relative;
    margin-bottom: 32px;
    border-radius: 20px;
    padding: 3px;
    overflow: visible;
}

.magic-header-wrap::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 22px;
    background: conic-gradient(
        from var(--angle, 0deg),
        #ff0080, #ff6b00, #ffd700, #00ff88,
        #00cfff, #7f5fff, #ff0080
    );
    animation: spin-border 5s linear infinite;
    z-index: 0;
}

.magic-header-wrap::after {
    content: '';
    position: absolute;
    inset: -20px;
    border-radius: 32px;
    background: conic-gradient(
        from 0deg,
        #ff008055, #00cfff55, #7f5fff55, #ff008055
    );
    animation: spin-border 5s linear infinite;
    filter: blur(24px);
    z-index: -1;
    opacity: 0.7;
}

@keyframes spin-border {
    0%   { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.magic-header-inner {
    position: relative;
    z-index: 1;
    background: linear-gradient(135deg,
        #0d1b3e 0%, #132448 30%, #1a2d5a 60%, #0d1b3e 100%);
    border-radius: 18px;
    padding: 28px 36px 24px;
    text-align: center;
    overflow: hidden;
}

/* Noise texture overlay */
.magic-header-inner::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    border-radius: 18px;
    pointer-events: none;
}

/* Diagonal light sweep */
.magic-header-inner::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(
        105deg,
        transparent 40%,
        rgba(255,255,255,0.04) 50%,
        transparent 60%
    );
    animation: sweep 6s ease-in-out infinite;
    pointer-events: none;
}

@keyframes sweep {
    0%   { transform: translateX(-100%) }
    50%, 100% { transform: translateX(100%) }
}

.magic-header-inner h1 {
    font-family: 'Rajdhani', 'Noto Sans Devanagari', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    background: linear-gradient(90deg,
        #fff 0%, #a8d4ff 20%, #ffd700 40%,
        #ffffff 60%, #a8d4ff 80%, #ffd700 100%);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer-text 4s linear infinite;
    letter-spacing: 1.5px;
    position: relative; z-index: 1;
}

@keyframes shimmer-text {
    0%   { background-position: 300% center; }
    100% { background-position: -300% center; }
}

.magic-header-inner .subtitle {
    font-size: 0.88rem;
    color: var(--text-muted);
    letter-spacing: 3px;
    text-transform: uppercase;
    font-weight: 600;
    position: relative; z-index: 1;
}

.header-badge {
    display: inline-block;
    background: rgba(0,212,255,0.12);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    color: #00d4ff;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 10px;
    position: relative; z-index: 1;
}

/* Floating particles */
.particle {
    position: absolute;
    border-radius: 50%;
    animation: float-up 4s ease-in infinite;
    opacity: 0;
    z-index: 2;
}
.p1 { width:5px; height:5px; background:#00cfff; left:8%;  animation-delay:0s; }
.p2 { width:3px; height:3px; background:#ff0080; left:22%; animation-delay:1s; }
.p3 { width:6px; height:6px; background:#ffd700; left:48%; animation-delay:2s; }
.p4 { width:4px; height:4px; background:#00ff88; left:72%; animation-delay:0.5s; }
.p5 { width:5px; height:5px; background:#7f5fff; left:90%; animation-delay:1.5s; }
.p6 { width:3px; height:3px; background:#ff6b00; left:35%; animation-delay:2.5s; }

@keyframes float-up {
    0%   { opacity:0; transform: translateY(40px) scale(0); }
    20%  { opacity:1; }
    80%  { opacity:0.6; }
    100% { opacity:0; transform: translateY(-30px) scale(1.5); }
}

/* ══════════════════════════════════════════
   METRIC CARDS — DARK GLASSMORPHISM
══════════════════════════════════════════ */
.metric-card {
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 20px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    cursor: default;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}

.metric-card:hover {
    transform: translateY(-5px);
}

.metric-card .val {
    font-family: 'Rajdhani', monospace;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 6px;
}

.metric-card .lbl {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 600;
    letter-spacing: 0.5px;
}

.metric-card .icon {
    font-size: 1.4rem;
    margin-bottom: 8px;
    display: block;
}

/* Card colour variants */
.card-blue   { box-shadow: 0 4px 30px rgba(46,117,182,0.2);   border-color: rgba(46,117,182,0.35); }
.card-blue   .val { color: #60a5fa; }
.card-blue::before { background: linear-gradient(90deg, #2E75B6, #60a5fa); }

.card-green  { box-shadow: 0 4px 30px rgba(34,197,94,0.2);    border-color: rgba(34,197,94,0.35); }
.card-green  .val { color: #4ade80; }
.card-green::before { background: linear-gradient(90deg, #16a34a, #4ade80); }

.card-orange { box-shadow: 0 4px 30px rgba(249,115,22,0.2);   border-color: rgba(249,115,22,0.35); }
.card-orange .val { color: #fb923c; }
.card-orange::before { background: linear-gradient(90deg, #ea580c, #fb923c); }

.card-purple { box-shadow: 0 4px 30px rgba(168,85,247,0.2);   border-color: rgba(168,85,247,0.35); }
.card-purple .val { color: #c084fc; }
.card-purple::before { background: linear-gradient(90deg, #9333ea, #c084fc); }

.card-red    { box-shadow: 0 4px 30px rgba(239,68,68,0.2);    border-color: rgba(239,68,68,0.35); }
.card-red    .val { color: #f87171; }
.card-red::before { background: linear-gradient(90deg, #dc2626, #f87171); }

/* ══════════════════════════════════════════
   SHIFT BADGES
══════════════════════════════════════════ */
.shift-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    border: 1px solid transparent;
}
.s1 {
    background: rgba(255,192,0,0.15);
    color: #ffd700;
    border-color: rgba(255,192,0,0.4);
}
.s2 {
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border-color: rgba(34,197,94,0.4);
}
.s3 {
    background: rgba(96,165,250,0.15);
    color: #60a5fa;
    border-color: rgba(96,165,250,0.4);
}
.leave-badge {
    background: rgba(239,68,68,0.15);
    color: #f87171;
    border-color: rgba(239,68,68,0.4);
}

/* ══════════════════════════════════════════
   SECTION TITLE
══════════════════════════════════════════ */
.section-title {
    font-family: 'Rajdhani', 'Noto Sans Devanagari', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 1px;
    padding: 10px 16px;
    margin: 24px 0 14px 0;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-left: 4px solid var(--accent-blue);
    border-radius: 0 10px 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ══════════════════════════════════════════
   SHIFT CARD (Tab 1)
══════════════════════════════════════════ */
.shift-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 18px 16px 12px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease;
    margin-bottom: 12px;
}
.shift-card:hover { transform: translateY(-3px); }
.shift-card .count {
    font-family: 'Rajdhani', monospace;
    font-size: 2.8rem;
    font-weight: 700;
    line-height: 1;
}
.shift-card .unit {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Gradient top strip */
.sc-s1 { border-top: 3px solid #ffd700; box-shadow: 0 4px 20px rgba(255,215,0,0.12); }
.sc-s1 .count { color: #ffd700; }
.sc-s2 { border-top: 3px solid #4ade80; box-shadow: 0 4px 20px rgba(74,222,128,0.12); }
.sc-s2 .count { color: #4ade80; }
.sc-s3 { border-top: 3px solid #60a5fa; box-shadow: 0 4px 20px rgba(96,165,250,0.12); }
.sc-s3 .count { color: #60a5fa; }

/* ══════════════════════════════════════════
   STREAMLIT COMPONENT OVERRIDES (dark theme)
══════════════════════════════════════════ */

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--navy-glow), var(--accent-blue)) !important;
    color: white !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Text inputs */
.stTextInput > div > div > input {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    color: #000000 !important;
    caret-color: #000000 !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(46,117,182,0.25) !important;
    color: #000000 !important;
}
/* Autofill override - browser autofill background fix */
.stTextInput > div > div > input:-webkit-autofill,
.stTextInput > div > div > input:-webkit-autofill:hover,
.stTextInput > div > div > input:-webkit-autofill:focus,
.stTextInput > div > div > input:-webkit-autofill:active {
    -webkit-text-fill-color: #000000 !important;
    -webkit-box-shadow: 0 0 0 30px #ffffff inset !important;
    box-shadow: 0 0 0 30px #ffffff inset !important;
    background-color: #ffffff !important;
    color: #000000 !important;
    caret-color: #000000 !important;
}
/* Placeholder color */
.stTextInput > div > div > input::placeholder {
    color: #888888 !important;
    opacity: 1 !important;
}
/* Focused state - white background for maximum readability */
.stTextInput > div > div > input:focus,
.stTextInput > div > div > input:not(:placeholder-shown) {
    background: #ffffff !important;
    color: #000000 !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--navy-mid), var(--accent-blue)) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border-radius: 10px !important;
    border: 1px solid rgba(46,117,182,0.5) !important;
    padding: 10px 22px !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--accent-blue), #1a4d8a) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(46,117,182,0.4) !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
    border: 1px solid rgba(34,197,94,0.4) !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(22,163,74,0.4) !important;
}

/* Info/Success/Warning/Error boxes */
.stAlert {
    border-radius: 10px !important;
    border-left: 4px solid !important;
}
[data-testid="stInfoMessage"] {
    background: rgba(46,117,182,0.1) !important;
    border-color: var(--accent-blue) !important;
}
[data-testid="stSuccessMessage"] {
    background: rgba(34,197,94,0.1) !important;
    border-color: var(--accent-green) !important;
}
[data-testid="stWarningMessage"] {
    background: rgba(249,115,22,0.1) !important;
    border-color: var(--accent-orange) !important;
}

/* Date input */
.stDateInput > div > div > input {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    color: #000000 !important;
    caret-color: #000000 !important;
}
.stDateInput > div > div > input:-webkit-autofill,
.stDateInput > div > div > input:-webkit-autofill:hover,
.stDateInput > div > div > input:-webkit-autofill:focus {
    -webkit-text-fill-color: #000000 !important;
    -webkit-box-shadow: 0 0 0 30px #ffffff inset !important;
    color: #000000 !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: var(--accent-cyan) !important;
}

/* Horizontal rule */
hr {
    border-color: var(--glass-border) !important;
    margin: 20px 0 !important;
}

/* Caption text */
.stCaption {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
}

/* ══════════════════════════════════════════
   SIDEBAR — DARK GLASS
══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0a1220, #0d1b3e) !important;
    border-right: 1px solid var(--glass-border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ── Clock Box ── */
.clock-box {
    background: linear-gradient(135deg, var(--navy-deep), var(--navy-mid));
    border-radius: 14px;
    padding: 18px 16px;
    text-align: center;
    border: 1px solid rgba(0,212,255,0.2);
    box-shadow: 0 0 30px rgba(0,212,255,0.12), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-top: 8px;
    position: relative;
    overflow: hidden;
}
.clock-box::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(0,212,255,0.04) 0%, transparent 60%);
    pointer-events: none;
}
.clock-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.clock-date {
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent-gold);
    margin-bottom: 6px;
    font-family: 'Noto Sans Devanagari', sans-serif;
}
.clock-time {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-cyan);
    font-family: 'Space Mono', 'Rajdhani', monospace;
    letter-spacing: 3px;
    text-shadow: 0 0 20px rgba(0,212,255,0.5);
}
.clock-city {
    font-size: 0.65rem;
    color: var(--text-muted);
    margin-top: 6px;
    letter-spacing: 1.5px;
}

/* ══════════════════════════════════════════
   FOOTER
══════════════════════════════════════════ */
.footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
    padding: 16px;
    border-top: 1px solid var(--glass-border);
    margin-top: 32px;
    letter-spacing: 0.5px;
}

/* ══════════════════════════════════════════
   SCROLLBAR (webkit)
══════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--navy-deep); }
::-webkit-scrollbar-thumb {
    background: var(--navy-glow);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

/* ══════════════════════════════════════════
   PULSE ANIMATION for live dot
══════════════════════════════════════════ */
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(1.5); }
}
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    animation: pulse-dot 1.5s ease-in-out infinite;
    box-shadow: 0 0 6px #22c55e;
    margin-right: 6px;
    vertical-align: middle;
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


# ── Helper: Active leaves today (date-aware) ──────────────────────────────────
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
            to_date   = pd.to_datetime(row.get("Leave_To",   ""), dayfirst=True).date()
            if from_date <= today <= to_date:
                active.append(mob)
        except:
            active.append(mob)
    return active


def run_assignment(sheet_id):
    """Core duty assignment logic with date-aware leave check."""
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

    today_dt  = now_ist()
    today_str = today_dt.strftime("%d-%m-%Y")
    now_time  = today_dt.strftime("%H:%M")

    # Double-run protection
    last_run = main_ws.acell("L1").value
    if last_run == today_str:
        return False, f"🛑 आज ({today_str}) ड्यूटी पहले ही लग चुकी है।"

    df = pd.DataFrame(main_ws.get_all_records())
    mob_col        = "Mobile_No"
    name_col       = "Employee_Name"
    status_col     = "STATUS"
    shift_col      = "Current_Shift"
    date_col       = "Shift_Start_Date"
    days_col       = "Days_On_Duty"
    duty_count_col = "Total_Duty_3M"
    s1_cnt, s2_cnt, s3_cnt = "Shift1count","Shift2count","Shift3count"

    if mob_col not in df.columns:
        return False, f"❌ Column '{mob_col}' नहीं मिला।"

    df[mob_col] = df[mob_col].astype(str).str.strip()
    df.set_index(mob_col, inplace=True)
    for c in [status_col, duty_count_col, s1_cnt, s2_cnt, s3_cnt, days_col]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    shift_rules = {}
    for row in config_ws.get_all_values()[1:]:
        if row[0]:
            try:
                shift_rules[row[0]] = {"req": int(float(row[1])), "max": int(float(row[3]))}
            except:
                continue

    leave_data = pd.DataFrame(leave_ws.get_all_records())
    leave_list = get_active_leave_ids(leave_data)

    logs = []

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
                df.at[m, shift_col]      = s_name
                df.at[m, date_col]       = today_str
                df.at[m, days_col]       = 0
                df.at[m, duty_count_col] += 1
                if t_cnt in df.columns:
                    df.at[m, t_cnt] += 1
                logs.append([today_str, now_time, m, df.at[m, name_col], "Assigned", s_name, "Success"])

    df_export  = df.reset_index()
    final_data = [df_export.columns.values.tolist()] + df_export.fillna("").values.tolist()
    main_ws.update(final_data)
    main_ws.update("L1", [[today_str]])
    if logs:
        audit_ws.append_rows(logs)

    load_sheet_data.clear()
    return True, f"✅ {today_str} की ड्यूटी सफलतापूर्वक लग गई! कुल {len(logs)} बदलाव हुए।"


# ── Helper: DataFrame → Excel bytes ──────────────────────────────────────────
def df_to_excel_bytes(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


# ── Magic Light Header ────────────────────────────────────────────────────────
st.markdown("""
<div class="magic-header-wrap">
  <div class="magic-header-inner">
    <div class="particle p1"></div>
    <div class="particle p2"></div>
    <div class="particle p3"></div>
    <div class="particle p4"></div>
    <div class="particle p5"></div>
    <div class="particle p6"></div>
    <h1>🚨 साइबर क्राइम हेल्पलाइन 1930</h1>
    <div class="subtitle">✦ ड्यूटी रोस्टर प्रबंधन प्रणाली ✦</div>
    <div class="header-badge"><span class="live-dot"></span>LIVE SYSTEM • ACTIVE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ सेटिंग्स")
    st.markdown("---")

    now = now_ist()

    hindi_months = {
        1:"जनवरी", 2:"फ़रवरी", 3:"मार्च", 4:"अप्रैल",
        5:"मई", 6:"जून", 7:"जुलाई", 8:"अगस्त",
        9:"सितम्बर", 10:"अक्टूबर", 11:"नवम्बर", 12:"दिसम्बर"
    }
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

# ── Load Data ─────────────────────────────────────────────────────────────────
with st.spinner("डेटा लोड हो रहा है..."):
    try:
        main_df, config_df, leave_df, audit_df = load_sheet_data(SHEET_ID)
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

on_duty    = main_df[main_df[shift_col].str.strip() != ""]
leave_ids  = get_active_leave_ids(leave_df)
on_leave   = main_df[main_df[mob_col].isin(leave_ids)]
inactive   = main_df[main_df[status_col] == 0]
unassigned = main_df[(main_df[shift_col].str.strip() == "") &
                     (~main_df[mob_col].isin(leave_ids)) &
                     (main_df[status_col] == 1)]

# ── Summary Cards ─────────────────────────────────────────────────────────────
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
          <div class="val">{val}</div>
          <div class="lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Run Assignment Button ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ ड्यूटी लगाएं</div>', unsafe_allow_html=True)
col_btn, col_info = st.columns([1, 2])
with col_btn:
    run_clicked = st.button("🔄 आज की ड्यूटी लगाएं", use_container_width=True)
with col_info:
    today_str_ist = now_ist().strftime("%d-%m-%Y")
    try:
        client   = get_client()
        sh       = client.open_by_key(SHEET_ID)
        last_run = sh.worksheet("Main_Duty").acell("L1").value or "कभी नहीं"
    except:
        last_run = "—"
    st.info(f"📅 आज: **{today_str_ist}**  |  अंतिम रन: **{last_run}**")

if run_clicked:
    with st.spinner("ड्यूटी लग रही है..."):
        success, msg = run_assignment(SHEET_ID)
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
        st.markdown('<div class="section-title">📥 शिफ्ट रिपोर्ट डाउनलोड करें</div>', unsafe_allow_html=True)

        dl_cols = [c for c in [mob_col, name_col, "Designation", shift_col, "Days_On_Duty"] if c in main_df.columns]

        dcol1, dcol2, dcol3, dcol4 = st.columns(4)

        with dcol1:
            s1_name = next((s for s in sorted(shifts) if "1" in s), None)
            if s1_name:
                s1_df = on_duty[on_duty[shift_col] == s1_name][dl_cols]
                st.download_button(
                    label=f"⬇️ {s1_name} डाउनलोड",
                    data=df_to_excel_bytes(s1_df, s1_name),
                    file_name=f"{s1_name}_{today_str_ist}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with dcol2:
            s2_name = next((s for s in sorted(shifts) if "2" in s), None)
            if s2_name:
                s2_df = on_duty[on_duty[shift_col] == s2_name][dl_cols]
                st.download_button(
                    label=f"⬇️ {s2_name} डाउनलोड",
                    data=df_to_excel_bytes(s2_df, s2_name),
                    file_name=f"{s2_name}_{today_str_ist}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with dcol3:
            s3_name = next((s for s in sorted(shifts) if "3" in s), None)
            if s3_name:
                s3_df = on_duty[on_duty[shift_col] == s3_name][dl_cols]
                st.download_button(
                    label=f"⬇️ {s3_name} डाउनलोड",
                    data=df_to_excel_bytes(s3_df, s3_name),
                    file_name=f"{s3_name}_{today_str_ist}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with dcol4:
            all_duty_df = on_duty[dl_cols].copy()
            st.download_button(
                label="⬇️ सभी शिफ्ट (एक साथ)",
                data=df_to_excel_bytes(all_duty_df, "All_Shifts"),
                file_name=f"All_Shifts_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        st.markdown("---")

        shift_colors = {0: ("s1", "sc-s1"), 1: ("s2", "sc-s2"), 2: ("s3", "sc-s3")}
        cols = st.columns(len(shifts))
        for idx, s in enumerate(sorted(shifts)):
            s_df = on_duty[on_duty[shift_col] == s]
            badge_cls, card_cls = shift_colors.get(idx % 3, ("s1", "sc-s1"))
            with cols[idx]:
                st.markdown(f"""
                <div class="shift-card {card_cls}">
                  <span class="shift-badge {badge_cls}">{s}</span>
                  <div class="count">{len(s_df)}</div>
                  <div class="unit">कर्मचारी</div>
                </div>""", unsafe_allow_html=True)

                disp_cols  = [c for c in [name_col, "Designation", "Days_On_Duty"] if c in main_df.columns]
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
        search_clean = search.strip()
        mask = disp[name_col].str.contains(search_clean, case=False, na=False)
        if mob_col in disp.columns:
            mask |= disp[mob_col].astype(str).str.contains(search_clean, case=False, na=False)
        disp = disp[mask]
    if status_filter == "ड्यूटी पर":
        disp = disp[disp[shift_col].str.strip() != ""]
    elif status_filter == "अवकाश पर":
        disp = disp[disp[mob_col].isin(leave_ids)]
    elif status_filter == "प्रतीक्षारत":
        disp = disp[(disp[shift_col].str.strip() == "") & (~disp[mob_col].isin(leave_ids)) & (disp[status_col] == 1)]
    elif status_filter == "निष्क्रिय":
        disp = disp[disp[status_col] == 0]

    show_cols  = [c for c in [mob_col, name_col, "Designation", shift_col, "Days_On_Duty",
                               "Total_Duty_3M", status_col] if c in disp.columns]
    rename_map = {mob_col: "मोबाइल", name_col: "नाम", "Designation": "पद",
                  shift_col: "वर्तमान शिफ्ट", "Days_On_Duty": "दिन",
                  "Total_Duty_3M": "3M ड्यूटी", status_col: "स्थिति"}
    st.dataframe(disp[show_cols].rename(columns=rename_map),
                 use_container_width=True, hide_index=True, height=380)

    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="⬇️ पूरी सूची डाउनलोड (.xlsx)",
            data=df_to_excel_bytes(disp[show_cols].rename(columns=rename_map), "Staff_List"),
            file_name=f"Staff_List_{today_str_ist}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.caption(f"कुल: {len(disp)} कर्मचारी")

# ── TAB 3: Leave List ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">🌴 अवकाश पर कर्मचारी</div>', unsafe_allow_html=True)

    if leave_df.empty:
        st.info("कोई कर्मचारी अवकाश पर नहीं है।")
    else:
        today_date    = now_ist().date()
        leave_display = leave_df.copy()

        def leave_status(row):
            try:
                f = pd.to_datetime(row.get("Leave_From",""), dayfirst=True).date()
                t = pd.to_datetime(row.get("Leave_To",""), dayfirst=True).date()
                if f <= today_date <= t:
                    return "✅ आज सक्रिय"
                elif today_date < f:
                    return "⏳ आने वाली"
                else:
                    return "❌ समाप्त"
            except:
                return "—"

        leave_display["अवकाश स्थिति"] = leave_display.apply(leave_status, axis=1)
        st.dataframe(leave_display, use_container_width=True, hide_index=True, height=320)

        col_ldl, _ = st.columns([1, 3])
        with col_ldl:
            st.download_button(
                label="⬇️ अवकाश सूची डाउनलोड (.xlsx)",
                data=df_to_excel_bytes(leave_display, "Leave_List"),
                file_name=f"Leave_List_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        st.caption(f"कुल अवकाश: {len(leave_df)}")

    st.markdown("---")
    st.markdown("**नया अवकाश जोड़ें**")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        l_mob  = st.text_input("मोबाइल नं.", key="l_mob")
    with lc2:
        l_from = st.date_input("से तारीख (Leave_From)", key="l_from")
    with lc3:
        l_to   = st.date_input("तक तारीख (Leave_To)", key="l_to")
    l_reason = st.text_input("कारण", key="l_reason")

    if st.button("✅ अवकाश दर्ज करें"):
        if l_mob:
            try:
                client = get_client()
                sh     = client.open_by_key(SHEET_ID)
                sh.worksheet("Leave").append_row([
                    l_mob,
                    l_from.strftime("%d-%m-%Y"),
                    l_to.strftime("%d-%m-%Y"),
                    l_reason,
                ])
                st.success(f"✅ अवकाश दर्ज हो गया! ({l_from.strftime('%d-%m-%Y')} से {l_to.strftime('%d-%m-%Y')} तक)")
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

        a_df_sorted = a_df.sort_values("Date", ascending=False) if "Date" in a_df.columns else a_df
        st.dataframe(a_df_sorted, use_container_width=True, hide_index=True, height=360)

        col_adl, _ = st.columns([1, 3])
        with col_adl:
            st.download_button(
                label="⬇️ Audit Log डाउनलोड (.xlsx)",
                data=df_to_excel_bytes(a_df_sorted, "Audit_Log"),
                file_name=f"Audit_Log_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        st.caption(f"कुल रिकॉर्ड: {len(a_df)}")

# ── TAB 5: Add / Edit Staff ───────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">➕ नया कर्मचारी जोड़ें</div>', unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        e_mob   = st.text_input("मोबाइल नं. *", key="e_mob")
        e_name  = st.text_input("नाम (हिंदी) *", key="e_name")
        e_desig = st.text_input("पद / पदनाम", key="e_desig")
    with ec2:
        e_rank       = st.text_input("रैंक", key="e_rank")
        e_status     = st.selectbox("स्थिति", [1, 0], format_func=lambda x: "सक्रिय" if x == 1 else "निष्क्रिय")
        e_shift_pref = st.selectbox("शिफ्ट वरीयता", ["", "Shift1", "Shift2", "Shift3"])

    if st.button("💾 कर्मचारी सहेजें"):
        if e_mob and e_name:
            try:
                client = get_client()
                sh     = client.open_by_key(SHEET_ID)
                ws     = sh.worksheet("Main_Duty")
                # Dynamic column mapping - sheet ke headers ke according row banao
                headers = ws.row_values(1)
                col_map = {
                    "Mobile_No":       str(e_mob).strip(),
                    "Employee_Name":   e_name.strip(),
                    "Designation":     e_desig.strip(),
                    "Rank":            e_rank.strip(),
                    "STATUS":          int(e_status),
                    "Shift_Preference": e_shift_pref,
                    "Current_Shift":   "",
                    "Shift_Start_Date": "",
                    "Days_On_Duty":    0,
                    "Total_Duty_3M":   0,
                    "Shift1count":     0,
                    "Shift2count":     0,
                    "Shift3count":     0,
                }
                new_row = [col_map.get(h, "") for h in headers]
                ws.append_row(new_row)
                st.success(f"✅ {e_name} जोड़ा गया! (वरीयता: {e_shift_pref or 'कोई नहीं'})")
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
st.markdown(f"""
<div class="footer">
  🚨 साइबर क्राइम हेल्पलाइन <strong>1930</strong> &nbsp;|&nbsp;
  ड्यूटी रोस्टर प्रणाली &nbsp;|&nbsp;
  <span class="live-dot"></span>
  {now_ist().strftime('%d-%m-%Y %H:%M')} IST
</div>
""", unsafe_allow_html=True)
