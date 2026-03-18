# CostBid Solutions — Full-Stack Website

A production-ready website with Python (FastAPI) backend and SQLite database.

## Project Structure

```
costbid/
├── main.py              # FastAPI backend (API + static file serving)
├── requirements.txt     # Python dependencies
├── Procfile             # For Railway / Heroku
├── railway.json         # Railway config
├── render.yaml          # Render config
├── README.md
└── static/
    └── index.html       # Full frontend (served by FastAPI)
```

---

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload --port 8000

# 3. Open browser
# http://localhost:8000
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/enquiry` | Save form submission to DB |
| GET | `/api/enquiries?secret=YOUR_SECRET` | List all enquiries (admin) |
| GET | `/api/health` | Health check |

### View Enquiries (Admin)
```
https://your-domain.com/api/enquiries?secret=costbid-admin-2025
```
Change the secret by setting the `ADMIN_SECRET` environment variable.

---

## Deploy to Railway (Recommended — Free tier available)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/costbid.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
   - Select your repo
   - Railway auto-detects Python and deploys
   - Your site will be live at `https://costbid-xxx.railway.app`

3. **Set environment variable** (optional, for admin security)
   - In Railway dashboard → Variables → Add `ADMIN_SECRET=your-secret-here`

---

## Deploy to Render (Free tier)

1. Push code to GitHub (same as above)
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add a **Disk** (for SQLite persistence):
   - Mount path: `/data`
   - Then update `DB_PATH` in `main.py` to `/data/costbid.db`
6. Click Deploy

---

## Deploy to VPS (DigitalOcean / AWS / Hetzner)

```bash
# On your server
sudo apt update && sudo apt install python3-pip nginx -y
pip3 install -r requirements.txt

# Run with systemd (recommended)
sudo nano /etc/systemd/system/costbid.service
```

Paste:
```ini
[Unit]
Description=CostBid FastAPI App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/costbid
ExecStart=/usr/local/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable costbid
sudo systemctl start costbid

# Nginx reverse proxy
sudo nano /etc/nginx/sites-available/costbid
```

Nginx config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/costbid /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# Add SSL (free)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## SQLite Database

The database file `costbid.db` is auto-created on first run.

**Table: enquiries**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| first_name | TEXT | Submitter's first name |
| last_name | TEXT | Submitter's last name |
| company | TEXT | Company name |
| email | TEXT | Email address |
| service | TEXT | Service requested |
| brief | TEXT | Project description |
| created_at | TEXT | UTC timestamp |
| status | TEXT | new / contacted / closed |

---

## Upgrading to PostgreSQL (Production)

For heavy traffic, swap SQLite for PostgreSQL:

```bash
pip install asyncpg databases[postgresql]
```

Update `DB_PATH` connection string in `main.py`:
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host/db")
```

---

## Security Checklist for Production

- [ ] Change `ADMIN_SECRET` environment variable
- [ ] Add rate limiting (e.g., `slowapi`)
- [ ] Enable HTTPS (SSL certificate)
- [ ] Restrict CORS `allow_origins` to your domain
- [ ] Move SQLite to persistent disk or switch to PostgreSQL
- [ ] Add input sanitization / honeypot fields
