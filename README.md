# HectorHosting

A VPS + game server hosting marketing site with a working account system, built with
Flask. Black/purple theme, built around the provided logo.

## Pages

- `/` — Home
- `/vps` — VPS Hosting plans
- `/game-servers` — Game Server plans
- `/features` — Features
- `/pricing` — Pricing overview
- `/about` — About
- `/contact` — Contact form (writes to database)
- `/register`, `/login`, `/logout` — Account system
- `/dashboard` — Placeholder logged-in area (wire up real server management here)

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set a real SECRET_KEY, and set FORCE_HTTPS=false for local http testing
python -c "import secrets; print(secrets.token_hex(32))"   # generates a SECRET_KEY

python app.py
```

Visit `http://127.0.0.1:5000`. The SQLite database is created automatically on
first run at `instance/hectorhosting.db`.

**Important:** with `FORCE_HTTPS=true` (the production default), the app refuses
to set cookies over plain HTTP and Talisman will redirect to HTTPS. Keep
`FORCE_HTTPS=false` in `.env` only for local development.

## Deploying to production

1. Put this behind a real WSGI server — do **not** use `python app.py` in
   production. Use gunicorn, e.g.:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```
2. Put a reverse proxy (nginx/Caddy) in front with a real TLS certificate
   (e.g. via Let's Encrypt). Set `FORCE_HTTPS=true`.
3. Set a strong, random `SECRET_KEY` as an environment variable — never commit
   it to source control.
4. Point `DATABASE_URL` at a real database (Postgres recommended) for anything
   beyond a small deployment — SQLite is fine to start.
5. Put `Flask-Limiter` on a real backing store (Redis) instead of the default
   in-memory store, so rate limits survive process restarts and work across
   multiple workers.
6. Review and tighten the Content-Security-Policy in `app.py` if you add any
   third-party scripts, analytics, or payment widgets.

## Security measures already in place

- **Passwords:** hashed with PBKDF2-SHA256 (Werkzeug's `generate_password_hash`),
  never stored or logged in plaintext. Registration requires 10+ characters
  with upper/lowercase and a number.
- **CSRF protection:** every form (`login`, `register`, `contact`) is protected
  via Flask-WTF's CSRF tokens. Verified: POSTs without a valid token are
  rejected with HTTP 400.
- **Session cookies:** `HttpOnly`, `SameSite=Lax`, and `Secure` (in production),
  with a 2-hour lifetime.
- **Security headers:** Flask-Talisman sets a Content-Security-Policy,
  `X-Content-Type-Options`, `X-Frame-Options: DENY`, and HSTS.
- **Rate limiting:** login (10/min), registration (10/hour), and the contact
  form (5/min) are throttled per-IP to slow brute-force and spam attempts.
- **Input handling:** all form input is validated server-side with WTForms
  (length limits, email format, password rules) and free-text fields are
  passed through `bleach` to strip any HTML/script content before it's stored
  or rendered — this closes the standard stored-XSS path.
- **SQL injection:** all database access goes through SQLAlchemy's ORM with
  parameterized queries — no raw string-built SQL anywhere in the app.
- **User enumeration:** login failures return the same generic "Incorrect
  email or password" message whether the account exists or not.
- **Open redirect protection:** the post-login `next` redirect only accepts
  same-site relative paths.

## What's genuinely still on you

No app is "fully secured" forever — that depends on how you deploy and
maintain it. In particular:
- Keep dependencies updated (`pip list --outdated`) — most real-world Flask
  breaches come from an old dependency, not this code.
- Add real email delivery for the contact form and account verification if
  you want confirmed emails (not wired to an SMTP/API provider by default).
- If you add payment processing, use a PCI-compliant provider (Stripe, etc.)
  — never handle raw card numbers in this codebase.
- The `/dashboard` route is a placeholder. Real server provisioning
  (VPS/game server control) will need its own hardening once you wire it to
  actual infrastructure APIs.
