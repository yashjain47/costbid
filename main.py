from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import urllib.request
import urllib.error
import json
from datetime import datetime

app = FastAPI(title="CostBid Solutions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BREVO_API_KEY  = os.getenv("BREVO_API_KEY", "")
NOTIFY_EMAIL   = os.getenv("NOTIFY_EMAIL", "4720yashjain@gmail.com")
SHEETS_WEBHOOK = os.getenv("SHEETS_WEBHOOK", "")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET", "costbid-admin-2025")
DB_PATH        = os.getenv("DB_PATH", "costbid.db")

# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            company     TEXT    NOT NULL,
            email       TEXT    NOT NULL,
            service     TEXT    NOT NULL,
            brief       TEXT,
            created_at  TEXT    NOT NULL,
            status      TEXT    DEFAULT 'new'
        )
    """)
    conn.commit()
    conn.close()

init_db()

class EnquiryIn(BaseModel):
    first_name: str
    last_name: str
    company: str
    email: str
    service: str
    brief: str = ""

# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
def send_to_sheets(data: EnquiryIn, timestamp: str):
    if not SHEETS_WEBHOOK:
        print("SHEETS_WEBHOOK not set — skipping.")
        return
    try:
        payload = json.dumps({
            "first_name": data.first_name,
            "last_name":  data.last_name,
            "company":    data.company,
            "email":      data.email,
            "service":    data.service,
            "brief":      data.brief,
            "timestamp":  timestamp,
        }).encode("utf-8")
        req = urllib.request.Request(
            SHEETS_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("Sheets response:", resp.read().decode())
    except Exception as e:
        print(f"Sheets error: {e}")

# ── EMAIL via Brevo (works on Railway) ───────────────────────────────────────
def send_email_notification(data: EnquiryIn, timestamp: str):
    key = BREVO_API_KEY.strip()
    print(f"[Email] Brevo key present: {bool(key)} | Notify: {NOTIFY_EMAIL}")

    if not key:
        print("[Email] No Brevo API key — skipping.")
        return
    try:
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                    background:#0A1628;color:#ffffff;padding:32px;border-radius:8px;">
          <h2 style="color:#C9A84C;margin-bottom:4px;">New Enquiry Received</h2>
          <p style="color:#8A9BB5;font-size:13px;margin-top:0;">{timestamp} UTC</p>
          <hr style="border:none;border-top:1px solid rgba(201,168,76,0.2);margin:20px 0;"/>
          <table style="width:100%;border-collapse:collapse;">
            <tr><td style="padding:8px 0;color:#8A9BB5;font-size:13px;width:140px;">Name</td>
                <td style="padding:8px 0;font-weight:bold;">{data.first_name} {data.last_name}</td></tr>
            <tr><td style="padding:8px 0;color:#8A9BB5;font-size:13px;">Company</td>
                <td style="padding:8px 0;">{data.company}</td></tr>
            <tr><td style="padding:8px 0;color:#8A9BB5;font-size:13px;">Email</td>
                <td style="padding:8px 0;">
                  <a href="mailto:{data.email}" style="color:#C9A84C;">{data.email}</a>
                </td></tr>
            <tr><td style="padding:8px 0;color:#8A9BB5;font-size:13px;">Service</td>
                <td style="padding:8px 0;color:#C9A84C;font-weight:bold;">{data.service}</td></tr>
          </table>
          <hr style="border:none;border-top:1px solid rgba(201,168,76,0.2);margin:20px 0;"/>
          <p style="color:#8A9BB5;font-size:13px;margin-bottom:6px;">Project Brief</p>
          <p style="background:#122040;padding:16px;border-left:3px solid #C9A84C;
                    border-radius:4px;font-size:14px;line-height:1.6;">
            {data.brief or "<em style='color:#8A9BB5;'>No brief provided.</em>"}
          </p>
          <hr style="border:none;border-top:1px solid rgba(201,168,76,0.2);margin:20px 0;"/>
          <p style="font-size:12px;color:#8A9BB5;text-align:center;">
            CostBid Solutions · Gurugram, Haryana, India
          </p>
        </div>
        """

        payload = json.dumps({
            "sender":      {"name": "CostBid Solutions", "email": "4720yashjain@gmail.com"},
            "to":          [{"email": NOTIFY_EMAIL.strip()}],
            "subject":     f"New Enquiry — {data.first_name} {data.last_name} ({data.company})",
            "htmlContent": html,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "api-key":      key,
                "Content-Type": "application/json",
                "Accept":       "application/json",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode()
            print(f"[Email] Success: {result}")

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[Email] HTTP {e.code}: {body}")
    except Exception as e:
        print(f"[Email] Exception: {type(e).__name__}: {e}")

# ── DEBUG ─────────────────────────────────────────────────────────────────────
@app.get("/api/test-email")
async def test_email():
    key = BREVO_API_KEY.strip()
    return {
        "brevo_key_present":   bool(key),
        "brevo_key_prefix":    key[:8] if key else "EMPTY",
        "notify_email":        NOTIFY_EMAIL,
        "sheets_webhook_present": bool(SHEETS_WEBHOOK),
    }

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.post("/api/enquiry")
async def submit_enquiry(data: EnquiryIn):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO enquiries
               (first_name, last_name, company, email, service, brief, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (data.first_name, data.last_name, data.company,
             data.email, data.service, data.brief, now)
        )
        conn.commit()
    finally:
        conn.close()
    send_to_sheets(data, now)
    send_email_notification(data, now)
    return {"success": True, "message": "Enquiry received. We'll contact you within 24 hours."}

@app.get("/api/enquiries")
async def list_enquiries(secret: str = ""):
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = get_db()
    rows = conn.execute("SELECT * FROM enquiries ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse("static/index.html")
