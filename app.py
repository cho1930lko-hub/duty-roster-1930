import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import json
import io

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

st.set_page_config(
    page_title="ड्यूटी रोस्टर | 1930",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS SABSE PEHLE — taaki login page bhi styled rahe
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;900&family=Rajdhani:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap');

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
    min-height: 100vh;
}
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1400px !important;
}

/* ══ LOGIN CARD ══ */
.login-wrap {
    max-width: 420px;
    margin: 60px auto 0 auto;
    background: linear-gradient(135deg, rgba(13,27,62,0.98), rgba(26,45,90,0.90));
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 24px;
    padding: 44px 36px 16px;
    text-align: center;
    box-shadow: 0 0 60px rgba(46,117,182,0.25), inset 0 1px 0 rgba(255,255,255,0.06);
}
.login-icon  { font-size: 3rem; margin-bottom: 10px; display: block; }
.login-title { font-size: 1.4rem; font-weight: 800; color: var(--text-primary); margin-bottom: 4px;
               font-family: 'Rajdhani', sans-serif; letter-spacing: 1px; }
.login-sub   { font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0px;
               letter-spacing: 2px; text-transform: uppercase; }

/* ══ MAGIC HEADER ══ */
.magic-header-wrap {
    position: relative; margin-bottom: 32px;
    border-radius: 20px; padding: 3px; overflow: visible;
}
.magic-header-wrap::before {
    content: ''; position: absolute; inset: -2px; border-radius: 22px;
    background: conic-gradient(from var(--angle,0deg),#ff0080,#ff6b00,#ffd700,#00ff88,#00cfff,#7f5fff,#ff0080);
    animation: spin-border 5s linear infinite; z-index: 0;
}
.magic-header-wrap::after {
    content: ''; position: absolute; inset: -20px; border-radius: 32px;
    background: conic-gradient(from 0deg,#ff008055,#00cfff55,#7f5fff55,#ff008055);
    animation: spin-border 5s linear infinite; filter: blur(24px); z-index: -1; opacity: 0.7;
}
@keyframes spin-border { 0%{transform:rotate(0deg)} 100%{transform:rotate(360deg)} }
.magic-header-inner {
    position: relative; z-index: 1;
    background: linear-gradient(135deg, #0d1b3e 0%, #132448 30%, #1a2d5a 60%, #0d1b3e 100%);
    border-radius: 18px; padding: 28px 36px 24px; text-align: center; overflow: hidden;
}
.magic-header-inner::before {
    content: ''; position: absolute; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    border-radius: 18px; pointer-events: none;
}
.magic-header-inner::after {
    content: ''; position: absolute; top:-50%; left:-50%; width:200%; height:200%;
    background: linear-gradient(105deg,transparent 40%,rgba(255,255,255,0.04) 50%,transparent 60%);
    animation: sweep 6s ease-in-out infinite; pointer-events: none;
}
@keyframes sweep { 0%{transform:translateX(-100%)} 50%,100%{transform:translateX(100%)} }
.magic-header-inner h1 {
    font-family: 'Rajdhani','Noto Sans Devanagari',sans-serif;
    font-size: 2.2rem; font-weight: 700; margin: 0 0 8px 0;
    background: linear-gradient(90deg,#fff 0%,#a8d4ff 20%,#ffd700 40%,#ffffff 60%,#a8d4ff 80%,#ffd700 100%);
    background-size: 300% auto; -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; background-clip: text;
    animation: shimmer-text 4s linear infinite; letter-spacing: 1.5px; position: relative; z-index:1;
}
@keyframes shimmer-text { 0%{background-position:300% center} 100%{background-position:-300% center} }
.magic-header-inner .subtitle {
    font-size: 0.88rem; color: var(--text-muted); letter-spacing: 3px;
    text-transform: uppercase; font-weight: 600; position: relative; z-index:1;
}
.header-badge {
    display: inline-block; background: rgba(0,212,255,0.12);
    border: 1px solid rgba(0,212,255,0.3); border-radius: 20px;
    padding: 4px 14px; font-size: 0.72rem; color: #00d4ff;
    letter-spacing: 2px; text-transform: uppercase; margin-top: 10px; position:relative; z-index:1;
}
.particle { position:absolute; border-radius:50%; animation:float-up 4s ease-in infinite; opacity:0; z-index:2; }
.p1{width:5px;height:5px;background:#00cfff;left:8%;animation-delay:0s}
.p2{width:3px;height:3px;background:#ff0080;left:22%;animation-delay:1s}
.p3{width:6px;height:6px;background:#ffd700;left:48%;animation-delay:2s}
.p4{width:4px;height:4px;background:#00ff88;left:72%;animation-delay:0.5s}
.p5{width:5px;height:5px;background:#7f5fff;left:90%;animation-delay:1.5s}
.p6{width:3px;height:3px;background:#ff6b00;left:35%;animation-delay:2.5s}
@keyframes float-up {
    0%{opacity:0;transform:translateY(40px) scale(0)} 20%{opacity:1}
    80%{opacity:0.6} 100%{opacity:0;transform:translateY(-30px) scale(1.5)}
}

/* ══ METRIC CARDS ══ */
.metric-card {
    background:var(--glass-bg); backdrop-filter:blur(12px); border:1px solid var(--glass-border);
    border-radius:16px; padding:20px 16px; text-align:center; position:relative;
    overflow:hidden; transition:transform 0.25s,box-shadow 0.25s; cursor:default;
}
.metric-card::before { content:''; position:absolute; top:0;left:0;right:0; height:3px; border-radius:16px 16px 0 0; }
.metric-card:hover { transform:translateY(-5px); }
.metric-card .val { font-family:'Rajdhani',monospace; font-size:3rem; font-weight:700; line-height:1; margin-bottom:6px; }
.metric-card .lbl { font-size:0.78rem; color:var(--text-muted); font-weight:600; letter-spacing:0.5px; }
.metric-card .icon { font-size:1.4rem; margin-bottom:8px; display:block; }
.card-blue{box-shadow:0 4px 30px rgba(46,117,182,0.2);border-color:rgba(46,117,182,0.35)}
.card-blue .val{color:#60a5fa} .card-blue::before{background:linear-gradient(90deg,#2E75B6,#60a5fa)}
.card-green{box-shadow:0 4px 30px rgba(34,197,94,0.2);border-color:rgba(34,197,94,0.35)}
.card-green .val{color:#4ade80} .card-green::before{background:linear-gradient(90deg,#16a34a,#4ade80)}
.card-orange{box-shadow:0 4px 30px rgba(249,115,22,0.2);border-color:rgba(249,115,22,0.35)}
.card-orange .val{color:#fb923c} .card-orange::before{background:linear-gradient(90deg,#ea580c,#fb923c)}
.card-purple{box-shadow:0 4px 30px rgba(168,85,247,0.2);border-color:rgba(168,85,247,0.35)}
.card-purple .val{color:#c084fc} .card-purple::before{background:linear-gradient(90deg,#9333ea,#c084fc)}
.card-red{box-shadow:0 4px 30px rgba(239,68,68,0.2);border-color:rgba(239,68,68,0.35)}
.card-red .val{color:#f87171} .card-red::before{background:linear-gradient(90deg,#dc2626,#f87171)}

/* ══ SHIFT BADGES & CARDS ══ */
.shift-badge { display:inline-block; padding:4px 14px; border-radius:20px;
               font-size:0.78rem; font-weight:700; border:1px solid transparent; }
.s1{background:rgba(255,192,0,0.15);color:#ffd700;border-color:rgba(255,192,0,0.4)}
.s2{background:rgba(34,197,94,0.15);color:#4ade80;border-color:rgba(34,197,94,0.4)}
.s3{background:rgba(96,165,250,0.15);color:#60a5fa;border-color:rgba(96,165,250,0.4)}
.shift-card { background:var(--glass-bg); border:1px solid var(--glass-border);
    border-radius:16px; padding:18px 16px 12px; text-align:center;
    transition:transform 0.2s; margin-bottom:12px; }
.shift-card:hover{transform:translateY(-3px)}
.shift-card .count{font-family:'Rajdhani',monospace;font-size:2.8rem;font-weight:700;line-height:1}
.shift-card .unit{font-size:0.72rem;color:var(--text-muted);font-weight:600}
.sc-s1{border-top:3px solid #ffd700;box-shadow:0 4px 20px rgba(255,215,0,0.12)} .sc-s1 .count{color:#ffd700}
.sc-s2{border-top:3px solid #4ade80;box-shadow:0 4px 20px rgba(74,222,128,0.12)} .sc-s2 .count{color:#4ade80}
.sc-s3{border-top:3px solid #60a5fa;box-shadow:0 4px 20px rgba(96,165,250,0.12)} .sc-s3 .count{color:#60a5fa}

/* ══ SECTION TITLE ══ */
.section-title {
    font-family:'Rajdhani','Noto Sans Devanagari',sans-serif; font-size:1.05rem; font-weight:700;
    color:var(--text-primary); letter-spacing:1px; padding:10px 16px; margin:24px 0 14px 0;
    background:var(--glass-bg); border:1px solid var(--glass-border);
    border-left:4px solid var(--accent-blue); border-radius:0 10px 10px 0;
    display:flex; align-items:center; gap:8px;
}

/* ══ STREAMLIT OVERRIDES ══ */
.stTabs [data-baseweb="tab-list"] {
    background:var(--glass-bg)!important; border:1px solid var(--glass-border)!important;
    border-radius:12px!important; padding:4px!important; gap:4px!important;
}
.stTabs [data-baseweb="tab"] {
    background:transparent!important; border-radius:8px!important;
    color:var(--text-muted)!important; font-weight:600!important;
    font-size:0.82rem!important; padding:8px 16px!important;
    transition:all 0.2s!important; border:none!important;
}
.stTabs [aria-selected="true"] {
    background:linear-gradient(135deg,var(--navy-glow),var(--accent-blue))!important; color:white!important;
}
[data-testid="stDataFrame"] { border:1px solid var(--glass-border)!important; border-radius:12px!important; overflow:hidden!important; }

/* ══ ALL TEXT INPUTS — DARK FORCE ══ */
.stTextInput>div>div>input,
div[data-testid="stTextInput"] input {
    background:#0d1b3e!important;
    background-color:#0d1b3e!important;
    border:1px solid rgba(255,255,255,0.12)!important;
    border-radius:10px!important;
    color:#e8f0ff!important;
    caret-color:#00d4ff!important;
    font-family:'Noto Sans Devanagari',sans-serif!important;
    transition:border-color 0.2s,box-shadow 0.2s!important;
}
.stTextInput>div>div>input:focus,
div[data-testid="stTextInput"] input:focus {
    border-color:var(--accent-blue)!important;
    box-shadow:0 0 0 3px rgba(46,117,182,0.2)!important;
    outline:none!important;
}
.stTextInput>div>div>input::placeholder,
div[data-testid="stTextInput"] input::placeholder {
    color:#4a6080!important; opacity:1!important;
}
.stTextInput label, .stTextInput label p,
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p {
    color:#a0b8d8!important; font-weight:600!important; font-size:0.85rem!important;
}

/* Password input specifically */
input[type="password"] {
    background:#0d1b3e!important;
    background-color:#0d1b3e!important;
    color:#e8f0ff!important;
    border:1px solid rgba(255,255,255,0.12)!important;
    border-radius:10px!important;
    caret-color:#00d4ff!important;
}
input[type="password"]::placeholder { color:#4a6080!important; opacity:1!important; }

.stSelectbox>div>div { background:#0d1b3e!important; border:1px solid rgba(255,255,255,0.12)!important; border-radius:10px!important; color:var(--text-primary)!important; }
.stButton>button {
    background:linear-gradient(135deg,var(--navy-mid),var(--accent-blue))!important;
    color:white!important; font-weight:700!important; font-size:0.9rem!important;
    border-radius:10px!important; border:1px solid rgba(46,117,182,0.5)!important;
    padding:10px 22px!important; transition:all 0.25s!important;
}
.stButton>button:hover {
    background:linear-gradient(135deg,var(--accent-blue),#1a4d8a)!important;
    transform:translateY(-2px)!important; box-shadow:0 6px 20px rgba(46,117,182,0.4)!important;
}
.stDownloadButton>button {
    background:linear-gradient(135deg,#16a34a,#15803d)!important; color:white!important;
    font-weight:700!important; font-size:0.82rem!important; border-radius:8px!important;
    border:1px solid rgba(34,197,94,0.4)!important; transition:all 0.2s!important;
}
.stDownloadButton>button:hover { transform:translateY(-2px)!important; box-shadow:0 6px 18px rgba(22,163,74,0.4)!important; }
.stAlert{border-radius:10px!important; border-left:4px solid!important;}
[data-testid="stInfoMessage"]{background:rgba(46,117,182,0.1)!important; border-color:var(--accent-blue)!important;}
[data-testid="stSuccessMessage"]{background:rgba(34,197,94,0.1)!important; border-color:var(--accent-green)!important;}
[data-testid="stWarningMessage"]{background:rgba(249,115,22,0.1)!important; border-color:var(--accent-orange)!important;}
.stDateInput>div>div>input{background:#0d1b3e!important; border:1px solid rgba(255,255,255,0.12)!important; border-radius:8px!important; color:var(--text-primary)!important;}
.stSpinner>div{border-top-color:var(--accent-cyan)!important;}
hr{border-color:var(--glass-border)!important; margin:20px 0!important;}
.stCaption{color:var(--text-muted)!important; font-size:0.78rem!important;}
[data-testid="stSidebar"]{background:linear-gradient(160deg,#0a1220,#0d1b3e)!important; border-right:1px solid var(--glass-border)!important;}
[data-testid="stSidebar"] *{color:var(--text-primary)!important;}

/* Clock */
.clock-box{background:linear-gradient(135deg,var(--navy-deep),var(--navy-mid)); border-radius:14px; padding:18px 16px; text-align:center; border:1px solid rgba(0,212,255,0.2); box-shadow:0 0 30px rgba(0,212,255,0.12); margin-top:8px; position:relative; overflow:hidden;}
.clock-label{font-size:0.65rem;color:var(--text-muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.clock-date{font-size:1rem;font-weight:700;color:var(--accent-gold);margin-bottom:6px}
.clock-time{font-size:2rem;font-weight:700;color:var(--accent-cyan);font-family:'Space Mono',monospace;letter-spacing:3px;text-shadow:0 0 20px rgba(0,212,255,0.5)}
.clock-city{font-size:0.65rem;color:var(--text-muted);margin-top:6px;letter-spacing:1.5px}

/* Footer */
.footer{text-align:center;color:var(--text-muted);font-size:0.75rem;padding:16px;border-top:1px solid var(--glass-border);margin-top:32px;letter-spacing:0.5px;}

/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--navy-deep)}
::-webkit-scrollbar-thumb{background:var(--navy-glow);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--accent-blue)}

/* Live dot */
@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(1.5)}}
.live-dot{display:inline-block;width:8px;height:8px;background:#22c55e;border-radius:50%;animation:pulse-dot 1.5s ease-in-out infinite;box-shadow:0 0 6px #22c55e;margin-right:6px;vertical-align:middle;}

/* ══ RESPONSIVE UI: phones and tablets ══ */
@media (max-width: 900px) {
  .main .block-container {
    padding: 1rem 1rem 2rem 1rem !important;
    max-width: 100% !important;
  }
  .magic-header-wrap { margin-bottom: 20px; }
  .magic-header-inner { padding: 22px 18px 20px; }
  .magic-header-inner h1 { font-size: clamp(1.35rem, 5vw, 2rem); letter-spacing: .5px; }
  .magic-header-inner .subtitle { font-size: .75rem; letter-spacing: 1px; }
  .metric-card { padding: 15px 8px; border-radius: 12px; }
  .metric-card .val { font-size: clamp(1.6rem, 5vw, 2.4rem); }
  .metric-card .lbl { font-size: .72rem; letter-spacing: 0; }
  .metric-card .icon { font-size: 1.1rem; }
  .shift-card { padding: 14px 8px 10px; }
  .shift-card .count { font-size: 2.15rem; }
  .section-title { font-size: .95rem; padding: 10px 12px; margin: 18px 0 10px; }
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    scrollbar-width: thin;
    max-width: 100%;
  }
  .stTabs [data-baseweb="tab"] {
    flex: 0 0 auto !important;
    white-space: nowrap !important;
    padding: 9px 12px !important;
    font-size: .78rem !important;
  }
  [data-testid="stDataFrame"], [data-testid="stTable"] {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
  .stButton > button, .stDownloadButton > button {
    min-height: 42px;
    white-space: normal !important;
    line-height: 1.25 !important;
    padding: 9px 12px !important;
  }
  .clock-time { font-size: 1.55rem; letter-spacing: 1px; }
  .login-wrap { margin-top: 24px; padding: 30px 20px 16px; }
}

/* Small phones: allow Streamlit columns to wrap instead of squeezing content. */
@media (max-width: 640px) {
  .main .block-container {
    padding: .7rem .65rem 1.5rem .65rem !important;
  }
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: .65rem !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: min(100%, 145px) !important;
    flex: 1 1 145px !important;
  }
  /* Keep paired search controls usable on phones. */
  .metric-card { min-height: 112px; }
  .metric-card .val { font-size: 1.8rem; }
  .metric-card .lbl { font-size: .68rem; }
  .shift-card .count { font-size: 1.9rem; }
  .magic-header-inner { padding: 20px 12px 18px; }
  .magic-header-inner h1 { line-height: 1.35; }
  .header-badge { font-size: .65rem; letter-spacing: 1px; }
  .section-title { font-size: .88rem; letter-spacing: .2px; }
  .stTabs [data-baseweb="tab"] { padding: 8px 10px !important; }
  .stTextInput input, .stSelectbox, .stDateInput { font-size: 16px !important; }
  .footer { font-size: .68rem; line-height: 1.7; }
  .login-title { font-size: 1.2rem; }
  .login-sub { letter-spacing: 1px; }
}

/* Part 3: readable shift reports and download controls */
.report-intro {
  color: #91a7c9; font-size: .86rem; line-height: 1.65;
  margin: 0 0 14px 2px;
}
.shift-report-card {
  display: flex; flex-direction: column; align-items: stretch;
  padding: 14px 18px 12px; margin: 12px 0 8px;
  min-height: 0; text-align: left;
}
.shift-card-heading {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; flex-wrap: wrap; margin-bottom: 8px;
}
.shift-card-caption { color: #9bb0d0; font-size: .78rem; font-weight: 600; }
.shift-report-card .count { font-size: 2.2rem; }
.shift-report-card .unit { margin-top: 2px; }
.stDownloadButton > button {
  min-height: 48px !important;
  white-space: normal !important;
  line-height: 1.35 !important;
  padding: 10px 12px !important;
}
@media (min-width: 900px) {
  .shift-report-card { padding: 16px 20px 14px; }
}
@media (max-width: 640px) {
  .report-intro { font-size: .78rem; margin-bottom: 10px; }
  .shift-report-card { padding: 12px 13px 10px; margin-top: 9px; }
  .shift-card-heading { align-items: flex-start; }
  .shift-card-caption { font-size: .72rem; }
  .shift-report-card .count { font-size: 1.9rem !important; }
  .stDownloadButton > button { min-height: 44px !important; font-size: .78rem !important; }
}

/* Part 2: refined header and dashboard summary cards */
.header-kicker {
  color: #8fa9d4; font-size: .68rem; font-weight: 700;
  letter-spacing: 2.2px; margin-bottom: 8px; position: relative; z-index: 1;
}
.header-emblem {
  display: inline-flex; align-items: center; justify-content: center;
  width: 48px; height: 48px; margin: 0 auto 8px; border-radius: 15px;
  background: rgba(0,212,255,.10); border: 1px solid rgba(0,212,255,.22);
  font-size: 1.65rem; position: relative; z-index: 1;
}
.magic-header-wrap { margin-bottom: 22px; }
.magic-header-inner {
  padding: 24px 30px 22px;
  background: radial-gradient(ellipse at 50% 0%, rgba(46,117,182,.23), transparent 58%),
              linear-gradient(135deg, #0b1730 0%, #12264b 52%, #0b1730 100%);
}
.magic-header-inner h1 {
  font-family: 'Noto Sans Devanagari','Rajdhani',sans-serif;
  font-size: clamp(1.45rem, 3.4vw, 2.15rem);
  letter-spacing: .2px; line-height: 1.4; margin-bottom: 8px;
}
.magic-header-inner .subtitle {
  letter-spacing: .4px; text-transform: none; font-size: .9rem;
  color: #b7c9e8;
}
.header-badge {
  letter-spacing: .5px; padding: 6px 14px;
  background: rgba(34,197,94,.09); border-color: rgba(34,197,94,.25);
  color: #86efac;
}
.dashboard-intro {
  color: #91a7c9; font-size: .86rem; line-height: 1.6;
  margin: -4px 0 14px 2px;
}
.metric-card {
  min-height: 148px; padding: 17px 14px 14px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: linear-gradient(155deg, rgba(255,255,255,.055), rgba(255,255,255,.018));
}
.metric-top {
  display: flex; align-items: center; justify-content: space-between;
  width: 100%; margin-bottom: 5px;
}
.metric-card .icon { margin: 0; }
.metric-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: currentColor; opacity: .75;
}
.metric-card .val { font-size: clamp(2rem, 3vw, 2.7rem); margin: 1px 0 5px; }
.metric-card .lbl { color: #dce7fb; font-size: .83rem; }
.metric-hint { color: #8197ba; font-size: .67rem; margin-top: 5px; text-align: center; }
.dashboard-spacer { height: 10px; }
@media (max-width: 640px) {
  .magic-header-wrap { margin-bottom: 16px; }
  .magic-header-inner { padding: 18px 12px 17px; }
  .header-kicker { font-size: .57rem; letter-spacing: 1.2px; }
  .header-emblem { width: 40px; height: 40px; border-radius: 12px; font-size: 1.35rem; }
  .magic-header-inner h1 { font-size: clamp(1.15rem, 5.5vw, 1.55rem); }
  .magic-header-inner .subtitle { font-size: .78rem; }
  .header-badge { font-size: .66rem; margin-top: 8px; }
  .dashboard-intro { font-size: .78rem; margin-bottom: 10px; }
  .metric-card { min-height: 124px !important; padding: 11px 7px !important; }
  .metric-card .val { font-size: clamp(1.55rem, 7vw, 1.9rem) !important; }
  .metric-card .lbl { font-size: .72rem; line-height: 1.4; }
  .metric-hint { font-size: .61rem; line-height: 1.35; }
  .metric-top { margin-bottom: 3px; }
  .metric-card .icon { font-size: 1rem; }
}

/* Part 1 UI polish: consistent spacing, readable controls, mobile-first dashboard */
.stApp { overflow-x: hidden; }
.main .block-container { width: 100%; }
[data-testid="stSidebar"] { min-width: 0 !important; }
[data-testid="stMetric"] {
  background: rgba(255,255,255,.035);
  border: 1px solid rgba(255,255,255,.09);
  padding: 12px 14px;
  border-radius: 12px;
}
.stTextInput input, .stTextArea textarea, .stSelectbox [role="combobox"],
.stDateInput input, .stNumberInput input {
  min-height: 42px !important;
}
.stButton > button, .stDownloadButton > button {
  min-height: 42px;
  font-weight: 700 !important;
  letter-spacing: .1px;
}
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent-cyan) !important; }
.stTabs [data-baseweb="tab-border"] { background: transparent !important; }
[data-testid="stDataFrame"] { width: 100% !important; }
[data-testid="stDataFrame"] iframe { max-width: 100% !important; }
.stAlert p { line-height: 1.55; }
@media (max-width: 640px) {
  /* Avoid a permanently reserved desktop-style sidebar gutter on narrow screens. */
  section[data-testid="stSidebar"] { width: min(86vw, 320px) !important; }
  .main .block-container { padding-left: .65rem !important; padding-right: .65rem !important; }
  [data-testid="stHorizontalBlock"] { gap: .55rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: min(100%, 135px) !important;
    flex: 1 1 135px !important;
  }
  .metric-card { padding: 12px 6px !important; }
  .metric-card .val { font-size: clamp(1.45rem, 7vw, 1.9rem) !important; }
  .metric-card .lbl { overflow-wrap: anywhere; }
  .shift-card { padding: 12px 6px 9px !important; }
  .shift-card .count { font-size: clamp(1.6rem, 7vw, 2rem) !important; }
  .stTabs [data-baseweb="tab-list"] { justify-content: flex-start !important; }
  .stTabs [data-baseweb="tab"] { flex-shrink: 0 !important; }
  [data-testid="stDataFrame"] { font-size: .8rem !important; }
}

/* Respect accessibility preferences and avoid motion on reduced-motion devices. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}

</style>
""", unsafe_allow_html=True)

# ── Password ──────────────────────────────────────────────────────────────────
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("""
        <div class="login-wrap">
            <span class="login-icon">🔐</span>
            <div class="login-title">साइबर क्राइम 1930</div>
            <div class="login-sub">ड्यूटी रोस्टर प्रणाली</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("पासवर्ड दर्ज करें", type="password",
                                key="pwd_input", placeholder="••••••••")
            login_btn = st.button("🔓 लॉगिन करें", use_container_width=True, key="login_btn")
            if login_btn:
                if pwd == st.secrets["passwords"]["app_password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ गलत पासवर्ड! दोबारा कोशिश करें।")
        return False
    return True

if not check_password():
    st.stop()

SHEET_ID = "1nwW5UvaMhBdcCQxR6TbPlwydDULS9MWZIml-nryjqRs"

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

def get_active_leave_ids(leave_df):
    today = now_ist().date()
    if leave_df.empty or "Mobile_No" not in leave_df.columns:
        return []
    from_col = next((c for c in ("Leave_From", "From_Date") if c in leave_df.columns), None)
    to_col = next((c for c in ("Leave_To", "To_Date") if c in leave_df.columns), None)
    active = []
    for _, row in leave_df.iterrows():
        mob = str(row.get("Mobile_No", "")).strip()
        if not mob:
            continue
        try:
            if not from_col or not to_col:
                raise ValueError("Leave date columns are missing")
            from_date = pd.to_datetime(row.get(from_col, ""), dayfirst=True).date()
            to_date = pd.to_datetime(row.get(to_col, ""), dayfirst=True).date()
            if from_date <= today <= to_date:
                active.append(mob)
        except (TypeError, ValueError, OverflowError):
            # Fail closed: malformed leave entries must not make an employee eligible for duty.
            active.append(mob)
    return active

def run_assignment(sheet_id):
    client    = get_client()
    sh        = client.open_by_key(sheet_id)
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

    last_run = main_ws.acell("L1").value
    if last_run == today_str:
        return False, f"🛑 आज ({today_str}) ड्यूटी पहले ही लग चुकी है।"

    df = pd.DataFrame(main_ws.get_all_records())
    mob_col="Mobile_No"; name_col="Employee_Name"; status_col="STATUS"
    shift_col="Current_Shift"; date_col="Shift_Start_Date"; days_col="Days_On_Duty"
    duty_count_col="Total_Duty_3M"; s1_cnt,s2_cnt,s3_cnt="Shift1count","Shift2count","Shift3count"

    required_cols = [mob_col, name_col, status_col, shift_col, date_col, days_col,
                     duty_count_col, s1_cnt, s2_cnt, s3_cnt]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return False, "❌ Main_Duty में आवश्यक कॉलम नहीं मिले: " + ", ".join(missing_cols)
    if df.empty:
        return False, "❌ Main_Duty में कोई कर्मचारी रिकॉर्ड नहीं है।"

    df[mob_col] = df[mob_col].astype(str).str.strip()
    if (df[mob_col] == "").any():
        return False, "❌ Main_Duty में कुछ कर्मचारियों का मोबाइल नंबर खाली है। पहले उसे ठीक करें।"
    duplicate_mobiles = df.loc[df[mob_col].duplicated(keep=False), mob_col].unique().tolist()
    if duplicate_mobiles:
        sample = ", ".join(duplicate_mobiles[:5])
        extra = " आदि" if len(duplicate_mobiles) > 5 else ""
        return False, f"❌ Main_Duty में डुप्लिकेट मोबाइल नंबर मिले ({sample}{extra})। ड्यूटी लगाने से पहले रिकॉर्ड ठीक करें।"

    # Keep the original row order so only intended cells are updated later.
    sheet_headers = list(df.columns)
    sheet_row_by_mobile = {mobile: row_number for row_number, mobile in enumerate(df[mob_col].tolist(), start=2)}
    original_records = {
        row[mob_col]: row.to_dict()
        for _, row in df.iterrows()
    }
    df.set_index(mob_col, inplace=True)
    for c in [status_col, duty_count_col, s1_cnt, s2_cnt, s3_cnt, days_col]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df[shift_col] = df[shift_col].fillna("").astype(str).str.strip()
    df[date_col] = df[date_col].fillna("").astype(str).str.strip()

    shift_rules = {}
    invalid_shift_configs = []
    for row_number, row in enumerate(config_ws.get_all_values()[1:], start=2):
        if not row or not str(row[0]).strip():
            continue
        shift_name = str(row[0]).strip()
        try:
            if len(row) < 4:
                raise ValueError("चार कॉन्फ़िगरेशन कॉलम उपलब्ध नहीं हैं")
            required_staff = int(float(row[1]))
            max_days = int(float(row[3]))
            if required_staff < 0 or max_days <= 0:
                raise ValueError("Required staff शून्य से कम या Max days शून्य/ऋणात्मक है")
            shift_rules[shift_name] = {"req": required_staff, "max": max_days}
        except (TypeError, ValueError, OverflowError):
            invalid_shift_configs.append(f"पंक्ति {row_number} ({shift_name})")

    if not shift_rules:
        return False, "❌ Config शीट में कोई मान्य शिफ्ट नियम नहीं मिला। Required Staff और Max Days जांचें।"

    leave_data = pd.DataFrame(leave_ws.get_all_records())
    leave_list = get_active_leave_ids(leave_data)
    logs = []

    for mobile, row in df.iterrows():
        current_shift = str(row[shift_col]).strip()
        if not current_shift:
            df.at[mobile, days_col] = 0
            continue

        # Safety removals must not depend on the shift-start date being valid.
        inactive = int(row[status_col]) != 1
        on_leave = mobile in leave_list
        if inactive or on_leave:
            logs.append([today_str,now_time,mobile,row[name_col],"Removed",current_shift,"Success"])
            df.at[mobile,shift_col]=""
            df.at[mobile,date_col]=""
            df.at[mobile,days_col]=0
            continue

        try:
            start_date = pd.to_datetime(row[date_col], dayfirst=True, errors="raise").date()
            diff = (today_dt.date() - start_date).days
            df.at[mobile, days_col] = max(0, diff)
            rule = shift_rules.get(current_shift)
            if diff < 0:
                # Future start dates are invalid; do not let them bypass rotation limits.
                df.at[mobile, days_col] = 0
            elif rule and diff >= rule["max"]:
                logs.append([today_str,now_time,mobile,row[name_col],"Removed",current_shift,"Success"])
                df.at[mobile,shift_col]=""
                df.at[mobile,date_col]=""
                df.at[mobile,days_col]=0
        except (TypeError, ValueError, OverflowError):
            # Keep the current assignment rather than silently resetting its duty age.
            # Invalid dates are surfaced via a zero-day display and should be corrected in the sheet.
            df.at[mobile, days_col] = 0

    staffing_shortfalls = []
    for s_name, rule in shift_rules.items():
        needed = int(rule["req"]) - int((df[shift_col].astype(str).str.strip() == str(s_name).strip()).sum())
        if needed > 0:
            pool = df[
                (df[status_col] == 1)
                & (df[shift_col].astype(str).str.strip() == "")
                & (~df.index.isin(leave_list))
            ]
            if pool.empty:
                staffing_shortfalls.append(f"{s_name}: {needed}")
                continue
            # Select the counter for this exact shift number; never silently use Shift3
            # as a fallback for an unrecognized shift name.
            shift_number = "".join(ch for ch in str(s_name) if ch.isdigit())
            shift_counter_map = {"1": s1_cnt, "2": s2_cnt, "3": s3_cnt}
            t_cnt = shift_counter_map.get(shift_number)
            if t_cnt is None:
                staffing_shortfalls.append(f"{s_name}: {needed} (शिफ्ट नाम/काउंटर कॉन्फ़िगरेशन जांचें)")
                continue
            sort_cols = [t_cnt, duty_count_col]
            selected = pool.sort_values(by=sort_cols).head(needed).index
            for m in selected:
                df.at[m,shift_col]=s_name
                df.at[m,date_col]=today_str
                df.at[m,days_col]=0
                df.at[m,duty_count_col]+=1
                df.at[m,t_cnt]+=1
                logs.append([today_str,now_time,m,df.at[m,name_col],"Assigned",s_name,"Success"])
            remaining = needed - len(selected)
            if remaining > 0:
                staffing_shortfalls.append(f"{s_name}: {remaining}")

    # Write only duty-related cells, not the whole worksheet. This preserves
    # unrelated columns/formulas and avoids rewriting employee master data.
    duty_columns = [shift_col, date_col, days_col, duty_count_col, s1_cnt, s2_cnt, s3_cnt]
    header_positions = {str(header): position for position, header in enumerate(sheet_headers, start=1)}

    def column_letter(column_number):
        result = ""
        while column_number:
            column_number, remainder = divmod(column_number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    cell_updates = []
    for mobile, row in df.iterrows():
        sheet_row = sheet_row_by_mobile[mobile]
        original = original_records[mobile]
        for column in duty_columns:
            new_value = row[column]
            if pd.isna(new_value):
                new_value = ""
            elif hasattr(new_value, "item"):
                new_value = new_value.item()
            old_value = original.get(column, "")
            old_text = "" if pd.isna(old_value) else str(old_value).strip()
            new_text = "" if new_value == "" else str(new_value).strip()
            if old_text != new_text:
                col_letter = column_letter(header_positions[column])
                cell_updates.append({
                    "range": f"{col_letter}{sheet_row}",
                    "values": [[new_value]],
                })

    # Update duty cells and the once-per-day marker in one Sheets batch request,
    # so a successful duty write cannot be followed by a separate marker failure.
    cell_updates.append({"range": "L1", "values": [[today_str]]})
    main_ws.batch_update(cell_updates, value_input_option="USER_ENTERED")
    if logs: audit_ws.append_rows(logs)
    load_sheet_data.clear()
    messages = []
    if invalid_shift_configs:
        messages.append("⚠️ Config की अमान्य पंक्तियां: " + ", ".join(invalid_shift_configs))
    if staffing_shortfalls:
        shortfall_text = " | ".join(staffing_shortfalls)
        messages.append("⚠️ कुछ शिफ्टों में स्टाफ/काउंटर की समस्या: " + shortfall_text)
    if messages:
        return True, (f"⚠️ {today_str} की ड्यूटी प्रक्रिया पूरी हुई। "
                      + " ".join(messages) + f" कुल {len(logs)} बदलाव हुए।")
    return True, f"✅ {today_str} की ड्यूटी सफलतापूर्वक लग गई! कुल {len(logs)} बदलाव हुए।"

def df_to_excel_bytes(df, sheet_name="Sheet1"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="magic-header-wrap">
  <div class="magic-header-inner">
    <div class="header-kicker">UTTAR PRADESH • DUTY MANAGEMENT</div>
    <div class="header-emblem">🚨</div>
    <h1>साइबर क्राइम हेल्पलाइन 1930</h1>
    <div class="subtitle">ड्यूटी रोस्टर प्रबंधन प्रणाली</div>
    <div class="header-badge"><span class="live-dot"></span>डैशबोर्ड तैयार</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ सेटिंग्स")
    st.markdown("---")
    now = now_ist()
    hindi_months={1:"जनवरी",2:"फ़रवरी",3:"मार्च",4:"अप्रैल",5:"मई",6:"जून",
                  7:"जुलाई",8:"अगस्त",9:"सितम्बर",10:"अक्टूबर",11:"नवम्बर",12:"दिसम्बर"}
    st.markdown(f"""<div class="clock-box">
      <div class="clock-label">📍 भारतीय मानक समय (IST)</div>
      <div class="clock-date">📅 {now.day} {hindi_months[now.month]} {now.year}</div>
      <div class="clock-time">{now.strftime("%I:%M %p")}</div>
      <div class="clock-city">लखनऊ • प्रयागराज • भारत</div>
    </div>""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
with st.spinner("डेटा लोड हो रहा है..."):
    try:
        main_df, config_df, leave_df, audit_df = load_sheet_data(SHEET_ID)
    except Exception as e:
        st.error(f"❌ Sheet connect नहीं हुई: {e}"); st.stop()

shift_col="Current_Shift"; status_col="STATUS"; name_col="Employee_Name"; mob_col="Mobile_No"
main_df[mob_col]    = main_df[mob_col].astype(str).str.strip()
main_df[status_col] = pd.to_numeric(main_df[status_col], errors="coerce").fillna(0).astype(int)
on_duty    = main_df[main_df[shift_col].str.strip() != ""]
leave_ids  = get_active_leave_ids(leave_df)
on_leave   = main_df[main_df[mob_col].isin(leave_ids)]
inactive   = main_df[main_df[status_col] == 0]
unassigned = main_df[(main_df[shift_col].str.strip()=="") & (~main_df[mob_col].isin(leave_ids)) & (main_df[status_col]==1)]

# ── Summary Cards ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 कर्मचारी स्थिति का सारांश</div>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-intro">आज की ड्यूटी, अवकाश और उपलब्ध स्टाफ की एक नज़र में स्थिति</p>', unsafe_allow_html=True)
summary_cards = [
    ("👥", len(main_df), "कुल कर्मचारी", "पंजीकृत स्टाफ", "card-blue"),
    ("🟢", len(on_duty), "ड्यूटी पर", "वर्तमान आवंटन", "card-green"),
    ("🌴", len(on_leave), "अवकाश पर", "आज सक्रिय अवकाश", "card-orange"),
    ("⏳", len(unassigned), "प्रतीक्षारत", "आवंटन शेष", "card-purple"),
    ("🔴", len(inactive), "निष्क्रिय", "ड्यूटी से बाहर", "card-red"),
]
summary_cols = st.columns(5)
for col, (icon, val, label, hint, cls) in zip(summary_cols, summary_cards):
    with col:
        st.markdown(
            f'<div class="metric-card {cls}">'
            f'<div class="metric-top"><span class="icon">{icon}</span><span class="metric-dot"></span></div>'
            f'<div class="val">{val}</div><div class="lbl">{label}</div>'
            f'<div class="metric-hint">{hint}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<div class='dashboard-spacer'></div>", unsafe_allow_html=True)

# ── Run Assignment ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ ड्यूटी लगाएं</div>', unsafe_allow_html=True)
col_btn, col_info = st.columns([1, 2])
with col_btn:
    run_clicked = st.button("🔄 आज की ड्यूटी लगाएं", use_container_width=True)
with col_info:
    today_str_ist = now_ist().strftime("%d-%m-%Y")
    try:
        client=get_client(); sh=client.open_by_key(SHEET_ID)
        last_run=sh.worksheet("Main_Duty").acell("L1").value or "कभी नहीं"
    except: last_run="—"
    st.info(f"📅 आज: **{today_str_ist}**  |  अंतिम रन: **{last_run}**")
if run_clicked:
    with st.spinner("ड्यूटी लग रही है..."):
        success, msg = run_assignment(SHEET_ID)
    if success: st.success(msg); st.balloons(); st.rerun()
    else: st.warning(msg)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs(["📋 शिफ्ट-वाइज ड्यूटी","👥 सभी कर्मचारी","🌴 अवकाश सूची","📜 Audit Log","➕ कर्मचारी जोड़ें / संपादित करें"])

with tab1:
    def shift_sort_key(value):
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        return (0, int(digits), str(value).casefold()) if digits else (1, 0, str(value).casefold())

    shifts = sorted(
        [str(s).strip() for s in main_df[shift_col].dropna().unique() if str(s).strip()],
        key=shift_sort_key,
    )
    st.markdown(
        '<p class="report-intro">शिफ्ट के अनुसार तैनात कर्मचारियों की सूची देखें और ज़रूरत के अनुसार रिपोर्ट डाउनलोड करें।</p>',
        unsafe_allow_html=True,
    )
    if not shifts:
        st.info("अभी कोई ड्यूटी नहीं लगी है। ऊपर ‘आज की ड्यूटी लगाएं’ बटन से प्रक्रिया शुरू करें।")
    else:
        st.markdown('<div class="section-title">📥 शिफ्ट रिपोर्ट डाउनलोड करें</div>', unsafe_allow_html=True)
        dl_cols = [c for c in [mob_col, name_col, "Designation", shift_col, "Days_On_Duty"] if c in main_df.columns]
        dl_names = {
            mob_col: "मोबाइल नंबर", name_col: "कर्मचारी का नाम", "Designation": "पद",
            shift_col: "वर्तमान शिफ्ट", "Days_On_Duty": "ड्यूटी के दिन",
        }
        download_cols = st.columns(4)
        for slot, snum in enumerate(("1", "2", "3")):
            shift_name = next(
                (s for s in shifts if "".join(ch for ch in s if ch.isdigit()) == snum),
                None,
            )
            if shift_name:
                with download_cols[slot]:
                    shift_data = on_duty[on_duty[shift_col].astype(str).str.strip() == shift_name][dl_cols]
                    st.download_button(
                        label=f"⬇️ {shift_name} रिपोर्ट",
                        data=df_to_excel_bytes(shift_data.rename(columns=dl_names), f"Shift_{snum}"),
                        file_name=f"Shift_{snum}_{today_str_ist}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key=f"download_shift_{snum}",
                    )
        with download_cols[3]:
            st.download_button(
                label="⬇️ सभी शिफ्ट रिपोर्ट",
                data=df_to_excel_bytes(on_duty[dl_cols].rename(columns=dl_names), "All_Shifts"),
                file_name=f"All_Shifts_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_all_shifts",
            )

        st.markdown('<div class="section-title">👥 शिफ्ट के अनुसार कर्मचारी</div>', unsafe_allow_html=True)
        shift_styles = {
            "1": ("s1", "sc-s1"),
            "2": ("s2", "sc-s2"),
            "3": ("s3", "sc-s3"),
        }
        for shift_name in shifts:
            shift_data = on_duty[on_duty[shift_col].astype(str).str.strip() == shift_name].copy()
            shift_number = "".join(ch for ch in shift_name if ch.isdigit())
            badge_class, card_class = shift_styles.get(shift_number, ("s1", "sc-s1"))
            st.markdown(
                f'<div class="shift-card shift-report-card {card_class}">'
                f'<div class="shift-card-heading"><span class="shift-badge {badge_class}">{shift_name}</span>'
                f'<span class="shift-card-caption">तैनात कर्मचारी</span></div>'
                f'<div class="count">{len(shift_data)}</div>'
                f'<div class="unit">कर्मचारी</div></div>',
                unsafe_allow_html=True,
            )
            display_cols = [col for col in [name_col, "Designation", "Days_On_Duty", mob_col] if col in shift_data.columns]
            display_names = {
                name_col: "कर्मचारी का नाम", "Designation": "पद",
                "Days_On_Duty": "ड्यूटी के दिन", mob_col: "मोबाइल नंबर",
            }
            st.dataframe(
                shift_data[display_cols].rename(columns=display_names),
                use_container_width=True,
                hide_index=True,
                height=min(420, max(110, 38 * (len(shift_data) + 1))),
            )

with tab2:
    st.markdown('<div class="section-title">👥 सम्पूर्ण कर्मचारी सूची</div>', unsafe_allow_html=True)
    cs,cf=st.columns([2,1])
    with cs: search=st.text_input("🔍 नाम / मोबाइल खोजें",placeholder="नाम टाइप करें...")
    with cf: status_filter=st.selectbox("स्थिति",["सभी","ड्यूटी पर","अवकाश पर","प्रतीक्षारत","निष्क्रिय"])
    disp=main_df.copy()
    if search:
        mask=disp[name_col].str.contains(search,case=False,na=False)
        if mob_col in disp.columns: mask|=disp[mob_col].str.contains(search,na=False)
        disp=disp[mask]
    if status_filter=="ड्यूटी पर": disp=disp[disp[shift_col].str.strip()!=""]
    elif status_filter=="अवकाश पर": disp=disp[disp[mob_col].isin(leave_ids)]
    elif status_filter=="प्रतीक्षारत": disp=disp[(disp[shift_col].str.strip()=="")&(~disp[mob_col].isin(leave_ids))&(disp[status_col]==1)]
    elif status_filter=="निष्क्रिय": disp=disp[disp[status_col]==0]
    sc=[c for c in [mob_col,name_col,"Designation",shift_col,"Days_On_Duty","Total_Duty_3M",status_col] if c in disp.columns]
    rm={mob_col:"मोबाइल",name_col:"नाम","Designation":"पद",shift_col:"वर्तमान शिफ्ट","Days_On_Duty":"दिन","Total_Duty_3M":"3M ड्यूटी",status_col:"स्थिति"}
    st.dataframe(disp[sc].rename(columns=rm),use_container_width=True,hide_index=True,height=380)
    cd1,cd2=st.columns([1,3])
    with cd1:
        st.download_button(label="⬇️ पूरी सूची डाउनलोड (.xlsx)",
            data=df_to_excel_bytes(disp[sc].rename(columns=rm),"Staff_List"),
            file_name=f"Staff_List_{today_str_ist}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    st.caption(f"कुल: {len(disp)} कर्मचारी")

with tab3:
    st.markdown('<div class="section-title">🌴 अवकाश पर कर्मचारी</div>', unsafe_allow_html=True)
    if leave_df.empty:
        st.info("कोई कर्मचारी अवकाश पर नहीं है।")
    else:
        td=now_ist().date(); ld=leave_df.copy()
        leave_from_col = next((c for c in ("Leave_From", "From_Date") if c in ld.columns), None)
        leave_to_col = next((c for c in ("Leave_To", "To_Date") if c in ld.columns), None)
        def leave_status(row):
            try:
                if not leave_from_col or not leave_to_col:
                    return "⚠️ तारीख कॉलम नहीं मिले"
                f=pd.to_datetime(row.get(leave_from_col,""),dayfirst=True).date()
                t=pd.to_datetime(row.get(leave_to_col,""),dayfirst=True).date()
                return "✅ आज सक्रिय" if f<=td<=t else ("⏳ आने वाली" if td<f else "❌ समाप्त")
            except (TypeError, ValueError, OverflowError): return "—"
        ld["अवकाश स्थिति"]=ld.apply(leave_status,axis=1)
        st.dataframe(ld,use_container_width=True,hide_index=True,height=320)
        cll,_=st.columns([1,3])
        with cll:
            st.download_button(label="⬇️ अवकाश सूची डाउनलोड (.xlsx)",
                data=df_to_excel_bytes(ld,"Leave_List"),
                file_name=f"Leave_List_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        st.caption(f"कुल अवकाश: {len(leave_df)}")
    st.markdown("---")
    st.markdown("**नया अवकाश जोड़ें**")
    lc1,lc2,lc3=st.columns(3)
    with lc1: l_mob=st.text_input("मोबाइल नं.",key="l_mob")
    with lc2: l_from=st.date_input("से तारीख",key="l_from")
    with lc3: l_to=st.date_input("तक तारीख",key="l_to")
    l_reason=st.text_input("कारण",key="l_reason")
    if st.button("✅ अवकाश दर्ज करें"):
        if not l_mob.strip():
            st.warning("मोबाइल नं. भरें।")
        elif l_from > l_to:
            st.warning("अवकाश की प्रारंभ तारीख, समाप्ति तारीख से बाद की नहीं हो सकती।")
        else:
            try:
                client=get_client(); sh=client.open_by_key(SHEET_ID)
                leave_ws=sh.worksheet("Leave")
                leave_headers=leave_ws.row_values(1)
                from_col=next((c for c in ("Leave_From","From_Date") if c in leave_headers),None)
                to_col=next((c for c in ("Leave_To","To_Date") if c in leave_headers),None)
                reason_col=next((c for c in ("Leave_Reason","Reason") if c in leave_headers),None)
                if "Mobile_No" not in leave_headers or not from_col or not to_col:
                    raise ValueError("Leave शीट में Mobile_No, From_Date/Leave_From और To_Date/Leave_To हेडर आवश्यक हैं।")
                leave_values={
                    "Mobile_No":l_mob.strip(),
                    from_col:l_from.strftime("%d-%m-%Y"),
                    to_col:l_to.strftime("%d-%m-%Y"),
                }
                if reason_col:
                    leave_values[reason_col]=l_reason.strip()
                leave_ws.append_row([leave_values.get(h,"") for h in leave_headers],value_input_option="USER_ENTERED")
                st.success("✅ अवकाश दर्ज हो गया!"); load_sheet_data.clear(); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

with tab4:
    st.markdown('<div class="section-title">📜 Audit Log</div>', unsafe_allow_html=True)
    if audit_df.empty:
        st.info("अभी कोई लॉग नहीं है।")
    else:
        ac1,ac2=st.columns([1,1])
        with ac1: date_filter=st.text_input("तारीख फ़िल्टर (DD-MM-YYYY)",placeholder="जैसे: 15-06-2025")
        with ac2: action_filter=st.selectbox("Action",["सभी","Assigned","Removed"])
        a_df=audit_df.copy()
        if date_filter: a_df=a_df[a_df["Date"].str.contains(date_filter,na=False)]
        if action_filter!="सभी": a_df=a_df[a_df["Action"]==action_filter]
        a_df_sorted=a_df.sort_values("Date",ascending=False) if "Date" in a_df.columns else a_df
        st.dataframe(a_df_sorted,use_container_width=True,hide_index=True,height=360)
        cal,_=st.columns([1,3])
        with cal:
            st.download_button(label="⬇️ Audit Log डाउनलोड (.xlsx)",
                data=df_to_excel_bytes(a_df_sorted,"Audit_Log"),
                file_name=f"Audit_Log_{today_str_ist}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        st.caption(f"कुल रिकॉर्ड: {len(a_df)}")

with tab5:
    st.markdown('<div class="section-title">➕ नया कर्मचारी जोड़ें</div>', unsafe_allow_html=True)
    ec1,ec2=st.columns(2)
    employee_headers=list(main_df.columns)
    rank_col=next((c for c in ("Rank","Employee_Rank") if c in employee_headers),None)
    pref_col=next((c for c in ("Shift_Preference","Shift_Pref") if c in employee_headers),None)
    e_rank=""
    e_shift_pref=""
    with ec1:
        e_mob=st.text_input("मोबाइल नं. *",key="e_mob")
        e_name=st.text_input("नाम (हिंदी) *",key="e_name")
        e_desig=st.text_input("पद / पदनाम",key="e_desig")
    with ec2:
        if rank_col:
            e_rank=st.text_input("रैंक",key="e_rank")
        e_status=st.selectbox("स्थिति",[1,0],format_func=lambda x:"सक्रिय" if x==1 else "निष्क्रिय")
        if pref_col:
            e_shift_pref=st.selectbox("शिफ्ट वरीयता",["","Shift1","Shift2","Shift3"],key="e_shift_pref")
    if st.button("💾 कर्मचारी सहेजें"):
        new_mobile = e_mob.strip()
        if not new_mobile or not e_name.strip():
            st.warning("मोबाइल नं. और नाम ज़रूरी है।")
        elif not (new_mobile.isascii() and new_mobile.isdigit() and len(new_mobile) == 10):
            st.warning("⚠️ मोबाइल नंबर 10 अंकों का होना चाहिए।")
        else:
            try:
                client=get_client(); sh=client.open_by_key(SHEET_ID)
                main_ws=sh.worksheet("Main_Duty")
                employee_headers=main_ws.row_values(1)
                required_headers=("Mobile_No","Employee_Name","Designation","Current_Shift","Shift_Start_Date",
                                  "Days_On_Duty","STATUS","Total_Duty_3M","Shift1count","Shift2count","Shift3count")
                missing=[h for h in required_headers if h not in employee_headers]
                if missing:
                    raise ValueError("Main_Duty शीट में आवश्यक कॉलम नहीं मिले: " + ", ".join(missing))

                # Avoid duplicate employee records for the same mobile number.
                existing_rows = main_ws.get_all_records()
                def normalized_mobile(value):
                    digits = "".join(ch for ch in str(value).strip() if ch.isdigit())
                    if len(digits) == 12 and digits.startswith("91"):
                        digits = digits[2:]
                    return digits if len(digits) == 10 else ""

                duplicate = any(
                    normalized_mobile(row.get("Mobile_No", "")) == new_mobile
                    for row in existing_rows
                )
                if duplicate:
                    st.warning("⚠️ इस मोबाइल नंबर से कर्मचारी पहले से दर्ज है। दोबारा जोड़ने के बजाय कर्मचारी सूची में उसे खोजें।")
                else:
                    employee_values={
                        "Mobile_No":new_mobile,
                        "Employee_Name":e_name.strip(),
                        "Designation":e_desig.strip(),
                        "Current_Shift":"",
                        "Shift_Start_Date":"",
                        "Days_On_Duty":0,
                        "STATUS":int(e_status),
                        "Total_Duty_3M":0,
                        "Shift1count":0,
                        "Shift2count":0,
                        "Shift3count":0,
                    }
                    if rank_col:
                        employee_values[rank_col]=e_rank.strip()
                    if pref_col:
                        employee_values[pref_col]=e_shift_pref
                    main_ws.append_row([employee_values.get(h,"") for h in employee_headers],
                                      value_input_option="USER_ENTERED")
                    st.success(f"✅ {e_name.strip()} जोड़ा गया!"); load_sheet_data.clear(); st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.markdown("---")
    st.markdown('<div class="section-title">🔄 Cache रिफ्रेश करें</div>', unsafe_allow_html=True)
    if st.button("🔃 डेटा रिफ्रेश करें"):
        load_sheet_data.clear(); st.rerun()

# ── Mobile Search ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">🔍 मोबाइल नंबर से कर्मचारी खोजें</div>', unsafe_allow_html=True)

sc1, sc2 = st.columns([3, 1])
with sc1:
    search_mobile = st.text_input(
        "📱 मोबाइल नंबर",
        placeholder="10 अंकों का मोबाइल नंबर दर्ज करें...",
        key="mob_search_input",
        max_chars=10
    )
with sc2:
    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
    search_btn = st.button("🔍 खोजें", use_container_width=True, key="mob_search_btn")

if search_btn or (search_mobile and len(search_mobile.strip()) == 10):
    mob_q = search_mobile.strip()
    if not mob_q:
        st.info("ℹ️ खोजने के लिए मोबाइल नंबर दर्ज करें।")
    elif not mob_q.isdigit() or len(mob_q) != 10:
        st.warning("⚠️ कृपया 10 अंकों का सही मोबाइल नंबर दर्ज करें।")
    else:
        result = main_df[main_df[mob_col].str.strip() == mob_q]
        if result.empty:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);
                border-radius:14px;padding:20px 24px;margin-top:12px;text-align:center;">
                <div style="font-size:2rem;">🔍</div>
                <div style="color:#f87171;font-weight:700;font-size:1rem;margin-top:8px;">
                    मोबाइल नं. <strong>{mob_q}</strong> से कोई कर्मचारी नहीं मिला
                </div>
                <div style="color:#7a92b8;font-size:0.82rem;margin-top:4px;">
                    नंबर जांचें या Tab 5 में नया कर्मचारी जोड़ें
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            row        = result.iloc[0]
            emp_name   = row.get("Employee_Name","—")
            emp_desig  = row.get("Designation","—")
            emp_shift  = str(row.get("Current_Shift","")).strip()
            emp_days   = int(row.get("Days_On_Duty",0) or 0)
            emp_total  = int(row.get("Total_Duty_3M",0) or 0)
            emp_status = int(row.get("STATUS",0) or 0)
            emp_mob    = str(row.get(mob_col,"—")).strip()
            is_leave   = emp_mob in leave_ids

            if is_leave:
                ds,sc,sd,glow,bc = "🌴 अवकाश पर","#f97316","अवकाश","rgba(249,115,22,0.15)","rgba(249,115,22,0.4)"
            elif emp_shift:
                ds,sc,sd,glow,bc = "🟢 ड्यूटी पर","#22c55e",emp_shift,"rgba(34,197,94,0.15)","rgba(34,197,94,0.4)"
            elif emp_status==0:
                ds,sc,sd,glow,bc = "🔴 निष्क्रिय","#ef4444","निष्क्रिय","rgba(239,68,68,0.15)","rgba(239,68,68,0.4)"
            else:
                ds,sc,sd,glow,bc = "⏳ प्रतीक्षारत","#a855f7","अभी नहीं","rgba(168,85,247,0.15)","rgba(168,85,247,0.4)"

            leave_html=""
            if is_leave and not leave_df.empty and "Mobile_No" in leave_df.columns:
                lv=leave_df[leave_df["Mobile_No"].astype(str).str.strip()==emp_mob]
                if not lv.empty:
                    lr=lv.iloc[0]
                    leave_from_value=lr.get("Leave_From",lr.get("From_Date","—"))
                    leave_to_value=lr.get("Leave_To",lr.get("To_Date","—"))
                    leave_reason=lr.get("Leave_Reason",lr.get("Reason",""))
                    reason_txt=f"&nbsp;|&nbsp; कारण: {leave_reason}" if leave_reason else ""
                    leave_html=f"""<div style="background:rgba(249,115,22,0.1);border:1px solid rgba(249,115,22,0.25);
                        border-radius:10px;padding:10px 16px;margin-top:14px;font-size:0.83rem;color:#fb923c;">
                        📅 अवकाश: <strong>{leave_from_value}</strong> से <strong>{leave_to_value}</strong> तक{reason_txt}
                    </div>"""

            st.markdown(f"""
            <div style="
                background:linear-gradient(135deg,rgba(13,27,62,0.97),rgba(26,45,90,0.82));
                border:1px solid {bc}; border-left:5px solid {sc}; border-radius:20px;
                padding:28px 32px; margin-top:16px;
                box-shadow:0 8px 40px {glow},inset 0 1px 0 rgba(255,255,255,0.04);
            ">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#e8f0ff;margin-bottom:6px;
                            font-family:'Rajdhani','Noto Sans Devanagari',sans-serif;">
                            👤 {emp_name}
                        </div>
                        <div style="font-size:0.85rem;color:#7a92b8;margin-bottom:3px;">
                            🏷️ &nbsp;<span style="color:#a0b8d8;">{emp_desig}</span>
                        </div>
                        <div style="font-size:0.85rem;color:#7a92b8;">
                            📱 &nbsp;<span style="color:#a0b8d8;font-family:'Space Mono',monospace;">{emp_mob}</span>
                        </div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4);border:1px solid {bc};border-radius:16px;
                        padding:16px 28px;text-align:center;min-width:150px;">
                        <div style="font-size:1.05rem;font-weight:700;color:{sc};margin-bottom:6px;">{ds}</div>
                        <div style="font-size:1.5rem;font-weight:800;color:#e8f0ff;
                            font-family:'Rajdhani',monospace;">{sd}</div>
                    </div>
                </div>
                <hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:18px 0;">
                <div style="display:flex;gap:40px;flex-wrap:wrap;align-items:center;">
                    <div style="text-align:center;">
                        <div style="font-size:2.2rem;font-weight:800;color:#60a5fa;
                            font-family:'Rajdhani',monospace;line-height:1;">{emp_days}</div>
                        <div style="font-size:0.7rem;color:#7a92b8;margin-top:4px;">वर्तमान ड्यूटी (दिन)</div>
                    </div>
                    <div style="width:1px;height:44px;background:rgba(255,255,255,0.07);"></div>
                    <div style="text-align:center;">
                        <div style="font-size:2.2rem;font-weight:800;color:#c084fc;
                            font-family:'Rajdhani',monospace;line-height:1;">{emp_total}</div>
                        <div style="font-size:0.7rem;color:#7a92b8;margin-top:4px;">कुल ड्यूटी (3 माह)</div>
                    </div>
                    <div style="width:1px;height:44px;background:rgba(255,255,255,0.07);"></div>
                    <div style="text-align:center;">
                        <div style="font-size:1rem;font-weight:700;
                            color:{'#4ade80' if emp_status==1 else '#f87171'};">
                            {'● सक्रिय' if emp_status==1 else '● निष्क्रिय'}
                        </div>
                        <div style="font-size:0.7rem;color:#7a92b8;margin-top:4px;">खाता स्थिति</div>
                    </div>
                </div>
                {leave_html}
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  🚨 साइबर क्राइम हेल्पलाइन <strong>1930</strong> &nbsp;|&nbsp;
  ड्यूटी रोस्टर प्रणाली &nbsp;|&nbsp;
  <span class="live-dot"></span>
  {now_ist().strftime('%d-%m-%Y %H:%M')} IST
</div>
""", unsafe_allow_html=True)
