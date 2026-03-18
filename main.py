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

RESEND_API_KEY  = os.getenv("RESEND_API_KEY", "")
NOTIFY_EMAIL    = os.getenv("NOTIFY_EMAIL", "4720yashjain@gmail.com")
SHEETS_WEBHOOK  = os.getenv("SHEETS_WEBHOOK", "")
ADMIN_SECRET    = os.getenv("ADMIN_SECRET", "costbid-admin-2025")
DB_PATH         = os.getenv("DB_PATH", "costbid.db")

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

# ── EMAIL via Resend ──────────────────────────────────────────────────────────
def send_email_notification(data: EnquiryIn, timestamp: str):
    key = RESEND_API_KEY.strip()
    print(f"[Email] Key present: {bool(key)} | Key prefix: {key[:6] if key else 'EMPTY'} | Notify: {NOTIFY_EMAIL}")

    if not key:
        print("[Email] No API key — skipping.")
        return
    try:
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0A1628;color:#ffffff;padding:32px;">
          <h2 style="color:#C9A84C;">New Enquiry — CostBid Solutions</h2>
          <p><b>Name:</b> {data.first_name} {data.last_name}</p>
          <p><b>Company:</b> {data.company}</p>
          <p><b>Email:</b> {data.email}</p>
          <p><b>Service:</b> {data.service}</p>
          <p><b>Brief:</b> {data.brief or 'None'}</p>
          <p style="color:#8A9BB5;font-size:12px;">{timestamp} UTC</p>
        </div>
        """
        payload = json.dumps({
            "from":    "CostBid Solutions <onboarding@resend.dev>",
            "to":      [NOTIFY_EMAIL.strip()],
            "subject": f"New Enquiry — {data.first_name} {data.last_name}",
            "html":    html,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
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

# ── DEBUG ROUTE — visit this URL to test email instantly ──────────────────────
@app.get("/api/test-email")
async def test_email():
    key = RESEND_API_KEY.strip()
    return {
        "resend_key_present": bool(key),
        "resend_key_prefix": key[:8] if key else "EMPTY",
        "notify_email": NOTIFY_EMAIL,
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
