# 🚨 साइबर क्राइम 1930 — ड्यूटी रोस्टर Dashboard
## GitHub + Streamlit Setup Guide

---

## 📁 Project Structure
```
duty_roster_app/
├── app.py                          ← Main Streamlit App
├── requirements.txt                ← Python dependencies
├── .gitignore                      ← Secrets को छुपाता है
├── .streamlit/
│   └── secrets.toml.template       ← Template (actual file GitHub पर नहीं जाएगी)
└── SETUP_GUIDE.md                  ← यह file
```

---

## STEP 1 — Google Service Account बनाएं

1. https://console.cloud.google.com पर जाएं
2. नया Project बनाएं (या पुराना चुनें)
3. **APIs & Services → Enable APIs** में जाकर enable करें:
   - ✅ Google Sheets API
   - ✅ Google Drive API
4. **APIs & Services → Credentials → Create Credentials → Service Account**
5. Service Account बनाने के बाद → **Keys → Add Key → JSON** download करें
6. इस JSON file को संभालकर रखें (यही secrets में जाएगी)

---

## STEP 2 — Google Sheet Share करें

1. अपनी Google Sheet खोलें
2. ऊपर **Share** बटन दबाएं
3. Service Account की email (JSON में `client_email`) को **Editor** permission दें
4. Sheet का ID copy करें (URL में `/d/` और `/edit` के बीच का हिस्सा)

---

## STEP 3 — GitHub पर Upload करें

```bash
# Terminal में:
git init
git add app.py requirements.txt .gitignore .streamlit/secrets.toml.template
git commit -m "Initial: Duty Roster Dashboard"
git remote add origin https://github.com/AAPKA_USERNAME/duty-roster-1930.git
git push -u origin main
```

⚠️ `.streamlit/secrets.toml` को कभी push मत करें — .gitignore में है

---

## STEP 4 — Streamlit Cloud पर Deploy करें

1. https://share.streamlit.io पर जाएं
2. **New App** → GitHub repo select करें
3. **Main file path**: `app.py`
4. **Advanced Settings → Secrets** में यह paste करें:

```toml
SHEET_ID = "आपका-sheet-id-यहाँ"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "roster@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

5. **Deploy!** — कुछ मिनट में app live हो जाएगा ✅

---

## STEP 5 — Google Sheet Structure

आपकी Sheet में ये worksheets होनी चाहिए:

### Main_Duty Sheet — Columns:
| Mobile_No | Employee_Name | Designation | Current_Shift | Shift_Start_Date | Days_On_Duty | STATUS | Total_Duty_3M | Shift1count | Shift2count | Shift3count |
|-----------|--------------|-------------|--------------|-----------------|-------------|--------|--------------|------------|------------|------------|
| 9876543210 | राकेश कुमार | आरक्षी | Shift1 | 01-06-2025 | 5 | 1 | 12 | 4 | 4 | 4 |

- **STATUS**: 1 = सक्रिय, 0 = निष्क्रिय
- **L1 cell**: Last run date (auto-fill होती है)

### Config Sheet — Columns:
| Shift_Name | Required | Min_Days | Max_Days |
|-----------|---------|---------|---------|
| Shift1 | 15 | 1 | 7 |
| Shift2 | 15 | 1 | 7 |
| Shift3 | 15 | 1 | 7 |

### Leave Sheet — Columns:
| Mobile_No | From_Date | To_Date | Reason |
|-----------|----------|---------|--------|

### Audit_Log Sheet — Auto-create होती है

---

## Dashboard Features

| Feature | Description |
|---------|-------------|
| 📊 Summary Cards | On duty / Leave / Waiting / Inactive count |
| ⚡ ड्यूटी लगाएं | Manual button — एक click में ड्यूटी assign |
| 🛡️ Double-run Protection | एक दिन में एक बार ही चलेगा |
| 📋 Shift-wise View | S1/S2/S3 अलग-अलग column में |
| 👥 Staff Search | नाम/मोबाइल से खोजें + filter |
| 🌴 Leave Management | देखें + नया अवकाश जोड़ें |
| 📜 Audit Log | कब किसे कौन सी shift लगाई |
| ➕ Staff Add | नया कर्मचारी जोड़ें |

---

## Mobile पर इस्तेमाल

Streamlit का URL mobile browser में खुलता है।
**Add to Home Screen** करने के लिए:
- Chrome → ⋮ menu → "Add to Home Screen"
- Safari → Share → "Add to Home Screen"

यह एक PWA जैसा काम करेगा! 📱
