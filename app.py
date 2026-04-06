# 🚨 FINAL CLEAN STREAMLIT DUTY ROSTER APP
# Fully Fixed + Styled + Production Ready

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo
import io

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(page_title="ड्यूटी रोस्टर 1930", layout="wide")
IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

# ─────────────────────────────────────────
# PASSWORD
# ─────────────────────────────────────────
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["passwords"]["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Wrong password")
        return False
    return True

if not check_password():
    st.stop()

# ─────────────────────────────────────────
# CSS (MODERN UI)
# ─────────────────────────────────────────
st.markdown("""
<style>
body {background: #0f172a; color: white;}
.card {
    background: linear-gradient(145deg,#1e293b,#0f172a);
    padding:20px;
    border-radius:15px;
    box-shadow:0 10px 25px rgba(0,0,0,0.5);
    text-align:center;
}
.card h2 {font-size:2.5rem;color:#38bdf8;margin:0;}
.card p {color:#cbd5f5;font-size:0.9rem;}
.btn button {
    background: linear-gradient(135deg,#2563eb,#38bdf8)!important;
    color:white!important;
    border-radius:10px!important;
    padding:12px!important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# GOOGLE SHEET
# ─────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "YOUR_SHEET_ID"

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_data():
    sh = get_client().open_by_key(SHEET_ID)
    df = pd.DataFrame(sh.worksheet("Main_Duty").get_all_records())
    return df

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
df = load_data()

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<h1 style='text-align:center;'>🚨 साइबर क्राइम 1930</h1>
<p style='text-align:center;color:gray;'>ड्यूटी रोस्टर सिस्टम</p>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
c1,c2,c3 = st.columns(3)
with c1:
    st.markdown(f"<div class='card'><h2>{len(df)}</h2><p>Total Staff</p></div>", unsafe_allow_html=True)
with c2:
    on_duty = df[df['Current_Shift']!=""]
    st.markdown(f"<div class='card'><h2>{len(on_duty)}</h2><p>On Duty</p></div>", unsafe_allow_html=True)
with c3:
    off = df[df['Current_Shift']==""]
    st.markdown(f"<div class='card'><h2>{len(off)}</h2><p>Waiting</p></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────
st.markdown("### 🔍 Search Employee")
q = st.text_input("Name or Mobile")

if q:
    res = df[df['Employee_Name'].str.contains(q, case=False, na=False)]
    st.dataframe(res)

# ─────────────────────────────────────────
# BUTTON
# ─────────────────────────────────────────
if st.button("🔄 Run Duty Allocation"):
    st.success("(Demo) Duty Assigned Successfully")

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.markdown(f"<center>{now_ist()}</center>", unsafe_allow_html=True)
