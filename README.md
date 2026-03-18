# CostBid Solutions — Setup Guide

Every enquiry from your website goes to **two places**:
1. 📊 **Google Sheets** — a live spreadsheet log of all enquiries
2. 📧 **Gmail** — instant email notification to 4720yashjain@gmail.com

---

## PART 1 — Google Sheets Setup (10 minutes)

### Step 1 — Create the Spreadsheet
1. Go to [sheets.google.com](https://sheets.google.com)
2. Click **Blank** → name it **CostBid Enquiries**
3. Keep this tab open

### Step 2 — Open Apps Script
1. Click **Extensions** → **Apps Script**
2. Delete everything in the editor
3. Copy the entire contents of `google_apps_script.js` and paste it in
4. Click **Save** — name it `CostBid`

### Step 3 — Deploy as Web App
1. Click **Deploy** → **New deployment**
2. Click the ⚙️ gear → choose **Web app**
3. Set: Execute as = **Me** | Who has access = **Anyone**
4. Click **Deploy** → **Authorize access** → Allow
5. **Copy the Web App URL** (looks like `https://script.google.com/macros/s/XXX/exec`)

### Step 4 — Add to Railway
Railway dashboard → your service → **Variables** tab → Add:
- Key: `SHEETS_WEBHOOK` | Value: *(paste the URL)*

---

## PART 2 — Gmail Setup (5 minutes)

### Step 1 — Enable 2-Step Verification
Go to [myaccount.google.com/security](https://myaccount.google.com/security) → turn on 2-Step Verification

### Step 2 — Create App Password
Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → App name: `CostBid` → Create
Copy the 16-character password shown (no spaces when you paste it)

### Step 3 — Add to Railway Variables

| Key | Value |
|-----|-------|
| `GMAIL_SENDER` | your Gmail (e.g. `hkhimanshu645@gmail.com`) |
| `GMAIL_APP_PASSWORD` | 16-char password (no spaces) |

---

## PART 3 — Test It
1. Open your live site → submit the contact form
2. Check Google Sheet — new row appears ✅
3. Check Gmail inbox at `4720yashjain@gmail.com` ✅

---

## All Railway Variables (summary)

| Variable | What it is |
|----------|-----------|
| `SHEETS_WEBHOOK` | Apps Script Web App URL |
| `GMAIL_SENDER` | Gmail address sending the notification |
| `GMAIL_APP_PASSWORD` | 16-char App Password from Google |
| `NOTIFY_EMAIL` | Already set to `4720yashjain@gmail.com` in code |
| `ADMIN_SECRET` | Change to secure your `/api/enquiries` endpoint |

---

## Troubleshooting

**No email?** → Check spam | Verify App Password has no spaces | Confirm 2-Step is ON

**Sheet not updating?** → Re-deploy Apps Script (Deploy → Manage → edit → New version)

**Check Railway logs** → Dashboard → service → Logs tab → look for `Sheets error:` or `Email error:`
