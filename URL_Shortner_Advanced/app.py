from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import string
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shortener.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ------------------------
# MODELS
# ------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    urls = db.relationship("URL", backref="user", lazy=True)

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_url = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# ------------------------
# HELPERS
# ------------------------
def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

# ------------------------
# ROUTES
# ------------------------
@app.route("/")
def index():
    if "user_id" in session:
        urls = URL.query.filter_by(user_id=session["user_id"]).all()
        return render_template("dashboard.html", urls=urls)
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

@app.route("/shortener", methods=["POST"])
def shortener():
    if "user_id" not in session:
        return redirect(url_for("login"))

    original_url = request.form["original_url"]
    short_url = generate_short_url()

    # Ensure uniqueness
    while URL.query.filter_by(short_url=short_url).first():
        short_url = generate_short_url()

    new_url = URL(original_url=original_url, short_url=short_url, user_id=session["user_id"])
    db.session.add(new_url)
    db.session.commit()

    return redirect(url_for("index"))

@app.route("/<short_url>")
def redirect_url(short_url):
    url = URL.query.filter_by(short_url=short_url).first_or_404()
    return redirect(url.original_url)

# ------------------------
# INIT DB
# ------------------------
if __name__ == "__main__":
    # Ensure database tables are created inside the app context
    with app.app_context():
        db.create_all()
    app.run(debug=True)

