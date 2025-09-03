from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "any_random_string_here"


DB_NAME = "expenses.db"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    # Expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    if "user_id" in session:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, amount, description FROM expenses WHERE user_id=?", (session["user_id"],))
        expenses = cursor.fetchall()
        conn.close()
        return render_template("index.html", expenses=expenses, user={"username": session["username"]})
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template("register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
           session["user_id"] = user[0]  
           session["username"] = username
           return redirect(url_for("home"))

        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        # Connect to the database
        conn = sqlite3.connect("expenses.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO expenses (category, amount, description) VALUES (?, ?, ?)",
            (category, amount, description)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("view_expenses"))  # make sure route exists

    return render_template("add_expense.html")


@app.route('/view_expenses')
def view_expenses():
    if "user_id" not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT category, amount, description FROM expenses WHERE user_id=?", (session["user_id"],))
    expenses = cursor.fetchall()
    conn.close()
    return render_template("view_expenses.html", expenses=expenses)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)





