==============================

DUTY ROSTER APP (REFINED)

Error-safe, optimized, clean

==============================

import streamlit as st import pandas as pd import gspread from google.oauth2.service_account import Credentials from datetime import datetime, timezone, timedelta import io

──────────────────────────────

CONFIG

──────────────────────────────

IST = timezone(timedelta(hours=5, minutes=30)) SHEET_ID = "1nwW5UvaMhBdcCQxR6TbPlwydDULS9MWZIml-nryjqRs"

MOBILE_COL = "Mobile_No" NAME_COL = "Employee_Name" STATUS_COL = "STATUS" SHIFT_COL = "Current_Shift" DATE_COL = "Shift_Start_Date" DAYS_COL = "Days_On_Duty" TOTAL_COL = "Total_Duty_3M"

SHIFT_MAP = { "Shift1": "Shift1count", "Shift2": "Shift2count", "Shift3": "Shift3count", }

──────────────────────────────

TIME

──────────────────────────────

def now_ist(): return datetime.now(IST)

──────────────────────────────

PAGE

──────────────────────────────

st.set_page_config(page_title="Duty Roster", layout="wide")

──────────────────────────────

PASSWORD (Protected + limited tries)

──────────────────────────────

def check_password(): if "attempts" not in st.session_state: st.session_state.attempts = 0

def verify():
    if st.session_state.pw == st.secrets["passwords"]["app_password"]:
        st.session_state.ok = True
    else:
        st.session_state.attempts += 1
        st.session_state.ok = False

if "ok" not in st.session_state or not st.session_state.ok:
    st.text_input("Password", type="password", key="pw", on_change=verify)
    if st.session_state.attempts > 5:
        st.error("Too many attempts!")
        st.stop()
    return False
return True

if not check_password(): st.stop()

──────────────────────────────

GOOGLE SHEETS

──────────────────────────────

@st.cache_resource def get_client(): creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"])) return gspread.authorize(creds)

@st.cache_data(ttl=60) def load_data(): sh = get_client().open_by_key(SHEET_ID)

main = pd.DataFrame(sh.worksheet("Main_Duty").get_all_records())
config_vals = sh.worksheet("Config").get_all_values()
config = pd.DataFrame(config_vals[1:], columns=config_vals[0])
leave = pd.DataFrame(sh.worksheet("Leave").get_all_records())

return main, config, leave, sh

──────────────────────────────

SAFE DATE PARSE

──────────────────────────────

def safe_date(val): try: return pd.to_datetime(val, dayfirst=True).date() except: return None

──────────────────────────────

ACTIVE LEAVE

──────────────────────────────

def get_active_leave_ids(df): today = now_ist().date() active = []

for row in df.to_dict("records"):
    mob = str(row.get(MOBILE_COL, "")).strip()
    if not mob:
        continue

    f = safe_date(row.get("Leave_From"))
    t = safe_date(row.get("Leave_To"))

    if f and t and f <= today <= t:
        active.append(mob)

return active

──────────────────────────────

ASSIGNMENT ENGINE

──────────────────────────────

def run_assignment(): main, config, leave, sh = load_data() ws = sh.worksheet("Main_Duty")

today = now_ist().date()
today_str = today.strftime("%d-%m-%Y")

last_run = str(ws.acell("L1").value).strip()
if last_run == today_str:
    return False, "Already executed today"

df = main.copy()

# clean
df[MOBILE_COL] = df[MOBILE_COL].astype(str).str.strip()
df.set_index(MOBILE_COL, inplace=True)

for col in [STATUS_COL, TOTAL_COL, DAYS_COL] + list(SHIFT_MAP.values()):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# rules
rules = {}
for row in config.to_dict("records"):
    try:
        rules[row["Shift"]] = {
            "req": int(row["Required"]),
            "max": int(row["MaxDays"])
        }
    except:
        continue

leave_ids = get_active_leave_ids(leave)
logs = []

# remove invalid
for mob, r in df.iterrows():
    shift = str(r.get(SHIFT_COL, "")).strip()

    if not shift:
        df.at[mob, DAYS_COL] = 0
        continue

    start = safe_date(r.get(DATE_COL))
    diff = (today - start).days if start else 0
    df.at[mob, DAYS_COL] = diff

    rule = rules.get(shift)

    if (rule and diff >= rule["max"]) or mob in leave_ids or r[STATUS_COL] == 0:
        df.at[mob, SHIFT_COL] = ""
        df.at[mob, DATE_COL] = None
        df.at[mob, DAYS_COL] = 0
        logs.append([mob, "Removed", shift])

# assign
for shift, rule in rules.items():
    current = len(df[df[SHIFT_COL] == shift])
    need = rule["req"] - current

    if need <= 0:
        continue

    pool = df[(df[STATUS_COL] == 1) & (df[SHIFT_COL] == "") & (~df.index.isin(leave_ids))]

    if pool.empty:
        logs.append(["-", "No Staff", shift])
        continue

    cnt_col = SHIFT_MAP.get(shift, TOTAL_COL)
    sort_cols = [cnt_col, TOTAL_COL]

    selected = pool.sort_values(by=sort_cols).head(need)

    for m in selected.index:
        df.at[m, SHIFT_COL] = shift
        df.at[m, DATE_COL] = today_str
        df.at[m, TOTAL_COL] += 1

        if cnt_col in df.columns:
            df.at[m, cnt_col] += 1

        logs.append([m, "Assigned", shift])

# save
export = df.reset_index()
ws.update([export.columns.tolist()] + export.fillna("").values.tolist())
ws.update("L1", [[today_str]])

load_data.clear()
return True, f"Done: {len(logs)} updates"

──────────────────────────────

UI

──────────────────────────────

st.title("🚨 Duty Roster System")

if st.button("Run Duty Assignment"): ok, msg = run_assignment() if ok: st.success(msg) else: st.warning(msg)

──────────────────────────────

DOWNLOAD

──────────────────────────────

def to_excel(df): buf = io.BytesIO() with pd.ExcelWriter(buf, engine="openpyxl") as writer: df.to_excel(writer, index=False) return buf.getvalue()

main, _, _, _ = load_data()

st.download_button("Download Excel", to_excel(main), "roster.xlsx")

──────────────────────────────

MODERN CSS (Clean + Glass UI)

──────────────────────────────

st.markdown("""

<style>
body {background: #0b1220; color:white}
.stButton button {
    background: linear-gradient(135deg,#1e3a8a,#2563eb);
    color:white;
    border-radius:10px;
    font-weight:bold;
}
.stButton button:hover {
    transform: scale(1.05);
}
</style>""", unsafe_allow_html=True)
