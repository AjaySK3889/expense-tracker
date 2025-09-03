
from flask import Flask, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to something secret

DATABASE = "expense_tracker.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """)

    # Create expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

# Initialize tables
init_db()

# ---------------- HELPER ----------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already exists. Choose another.")
            return redirect("/register")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            flash("Logged in successfully!")
            return redirect("/")
        else:
            flash("Invalid username or password")
            return redirect("/login")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect("/login")

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    )
    expenses = cursor.fetchall()
    conn.close()

    return render_template("index.html", expenses=expenses)

# ---------------- ADD EXPENSE ----------------
@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        amount = float(request.form["amount"])
        category = request.form.get("category", "")
        date = request.form.get("date", datetime.now().strftime("%Y-%m-%d"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], title, amount, category, date)
        )
        conn.commit()
        conn.close()

        flash("Expense added successfully!")
        return redirect("/")

    return render_template("add_expense.html")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)

