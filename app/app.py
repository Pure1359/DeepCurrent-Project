# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password

# Instance for application is created in __init__.py

# Create Blueprint to allow for modularity
bp = Blueprint("app", __name__)

# Helper function to handle login
def require_login():
    account_id = session.get("account_id")
    if not account_id:
        return None
    return int(account_id)

# Route for the home page
@bp.route("/")
def index():
    return render_template("register.html") # display register.html by default

# Create a route to handle user registration
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    # Fetch data from registration form
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    dob = request.form["dob"]
    user_type = request.form["user_type"]
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    if not all([first_name, last_name, email, dob, user_type, password, repeat_password]):
        return render_template("register.html", error="Please fill in all fields.")

    if password != repeat_password:
        return render_template("register.html", error="Passwords do not match.")

    # Display form data for debugging
    print(first_name, last_name, email, dob, user_type, password, repeat_password)

    # Hash password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Input user into database
    user_id = create_user(
        first_name=first_name,
        last_name=last_name,
        email=email,
        dob=dob,
        user_type=user_type
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Input account into database (Currently not asking for username so we use email)
    create_account(
        user_id=user_id,
        username=email,
        password=password_hash,
        date_created=now,
        last_active=now
    )

    # Take user to login page
    return redirect(url_for("app.login"))

# Route to handle user login
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    # Fetch login details from form
    email = request.form["email"]
    password = request.form["password"]

    # Check if login details are valid
    account = get_account_by_email_for_login(email)
    if not account or not verify_password(password, account["password"]):
        return render_template("login.html", error="Invalid email or password.")
    
    # Store account_id in session
    session["account_id"] = account["account_id"]

    # Update Last Active
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    update_last_active(account["account_id"], now)

    print(email, password) # print login details for debugging
    return redirect(url_for("app.dashboard")) # if login successful, redirect to dashboard

# Route to handle dashboard
@bp.get("/dashboard")
def dashboard():
    # Ensure user is logged in before accessing dashboard
    account_id = require_login()
    if not account_id:
        return redirect(url_for("app.login"))
    
    return render_template("dashboard.html")

# Route to handle logout
@bp.post("/logout")
def logout():
    session.pop("account_id", None)
    return redirect(url_for("app.login"))