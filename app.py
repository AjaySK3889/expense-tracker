import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
# ✅ Use environment variable for secret key
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

bcrypt = Bcrypt(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------- DATABASE CONNECTION -------------------


def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT", 5432)
    )
    return conn

# ------------------- USER CLASS -------------------
class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    db.close()
    if user:
        return User(user["user_id"], user["username"], user["email"])
    return None

# ------------------- AUTH ROUTES -------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # ✅ Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        db = get_db_connection()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                (username, hashed_password, email)
            )
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("Username or Email already exists!", "danger")
            return redirect(url_for("register"))
        finally:
            db.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        db.close()

        if user and bcrypt.check_password_hash(user["password"], password):
            user_obj = User(user["user_id"], user["username"], user["email"])
            login_user(user_obj)
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# ------------------- EXPENSE ROUTES -------------------
@app.route("/")
@login_required
def index():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.category_name, SUM(e.amount) AS total_spent
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = %s
        GROUP BY c.category_name
        ORDER BY total_spent DESC
    """, (current_user.id,))
    summary = cursor.fetchall()
    db.close()
    return render_template("index.html", summary=summary, user=current_user)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_expense():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    if request.method == "POST":
        category_id = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]
        date = request.form["date"]

        cursor.execute(
            "INSERT INTO expenses (user_id, category_id, amount, description, expense_date) VALUES (%s, %s, %s, %s, %s)",
            (current_user.id, category_id, amount, description, date)
        )
        db.commit()
        db.close()
        return redirect("/")

    db.close()
    return render_template("add_expense.html", categories=categories)

@app.route("/view")
@login_required
def view_expenses():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.expense_id, c.category_name, e.amount, e.description, e.expense_date
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = %s
        ORDER BY e.expense_date DESC
    """, (current_user.id,))
    expenses = cursor.fetchall()
    db.close()
    return render_template("view_expenses.html", expenses=expenses)

# ------------------- MAIN -------------------
if __name__ == "__main__":
    # ✅ host 0.0.0.0 is important for Heroku
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




