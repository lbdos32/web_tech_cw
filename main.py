from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "your-secret-key"

# -----------------------------
# Helpers
# -----------------------------
def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row  # (id, username, password_hash, role)


def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return route_function(*args, **kwargs)
    return wrapper


def admin_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return "Access denied: Admins only", 403
        return route_function(*args, **kwargs)
    return wrapper


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def root():
    return render_template('index.html')


@app.route("/healthAndSafety")
def health_and_safety():
    return render_template('healthAndSafety.html')


@app.route("/committee")
def committee():
    return render_template('committee.html')


# -----------------------------
# Login Page
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = get_user(username)
        if user and check_password_hash(user[2], password):
            # Store login session
            session["username"] = user[1]
            session["role"] = user[3]

            if user[3] == "admin":
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("root"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("root"))


# -----------------------------
# Admin-Only Page
# -----------------------------
@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin.html", username=session.get("username"))


# -----------------------------
# Database Setup (run once)
# -----------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('user','admin'))
        )
    """)

    # Add default admin if none exists
    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("user1", generate_password_hash("password123"), "user")
        )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
