import os
import re

import bleach
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_talisman import Talisman
from flask_wtf import CSRFProtect

from config import Config
from forms import ContactForm, LoginForm, RegisterForm
from models import ContactMessage, User, db

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# --- Database ---
db.init_app(app)

# --- CSRF protection on every state-changing form ---
csrf = CSRFProtect(app)

# --- Rate limiting: slows down brute-force / spam automatically ---
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour"])

# --- Security headers (CSP, HSTS, X-Frame-Options, etc.) ---
csp = {
    "default-src": "'self'",
    "img-src": "'self' data:",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src": "'self' https://fonts.gstatic.com",
    "script-src": "'self'",
}
Talisman(
    app,
    content_security_policy=csp,
    force_https=app.config["FORCE_HTTPS"],
    strict_transport_security=True,
    session_cookie_secure=app.config["SESSION_COOKIE_SECURE"],
    x_content_type_options=True,
    frame_options="DENY",
)

# --- Login manager ---
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    os.makedirs("/tmp/instance", exist_ok=True)
    db.create_all()


def clean_text(value: str) -> str:
    """Strip any HTML/script content from free-text user input before storage."""
    return bleach.clean(value or "", tags=[], attributes={}, strip=True).strip()


# ---------------------------------------------------------------------------
# Static marketing pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/vps")
def vps():
    return render_template("vps.html")


@app.route("/game-servers")
def game_servers():
    return render_template("game_servers.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@app.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=clean_text(form.name.data)[:120],
            email=form.email.data.strip().lower(),
            subject=clean_text(form.subject.data)[:200],
            message=clean_text(form.message.data)[:4000],
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent. Our team will reply within one business day.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", form=form)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return render_template("register.html", form=form)

        user = User(
            email=email,
            display_name=clean_text(form.display_name.data)[:80],
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        # Constant-shape response whether or not the account exists, to avoid
        # leaking which emails are registered.
        if user and user.check_password(form.password.data):
            login_user(user, remember=False)
            user.failed_login_attempts = 0
            db.session.commit()
            flash("Signed in successfully.", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        flash("Incorrect email or password.", "error")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(429)
def ratelimited(_e):
    return render_template("429.html"), 429


@app.errorhandler(500)
def server_error(_e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    # debug=False by default — never run debug mode with a real SECRET_KEY.
    app.run(host="127.0.0.1", port=5000, debug=False)
