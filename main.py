from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = FastAPI(title="CostBid Solutions API")

# CORS — allow all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DATABASE ──────────────────────────────────────────────────────────────────
DB_PATH = "costbid.db"

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

# ── SCHEMA ────────────────────────────────────────────────────────────────────
class EnquiryIn(BaseModel):
    first_name: str
    last_name: str
    company: str
    email: str
    service: str
    brief: str = ""

# ── ROUTES ───────────────────────────────────────────────────────────────────
@app.post("/api/enquiry")
async def submit_enquiry(data: EnquiryIn):
    """Save enquiry to SQLite and return confirmation."""
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

    return {"success": True, "message": "Enquiry received. We'll contact you within 24 hours."}


@app.get("/api/enquiries")
async def list_enquiries(secret: str = ""):
    """Admin endpoint — protect with a secret key in production."""
    if secret != os.getenv("ADMIN_SECRET", "costbid-admin-2025"):
        raise HTTPException(status_code=403, detail="Forbidden")
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM enquiries ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── SERVE FRONTEND ────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse("static/index.html")
