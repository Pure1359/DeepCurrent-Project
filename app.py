# Importmodules
from flask import Flask, request, render_template, redirect, url_for

# Create an instance of a Flask Application
app = Flask(__name__)

# Route for the home page
@app.route("/")
def index():
    return render_template("register.html") # display register.html by default

# Create a route to handle user registration
@app.route("/register", methods=["POST"])
def register():
    # Fetch data from registration form
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    dob = request.form["dob"]
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    # Display form data for debugging
    print(first_name, last_name, email, dob, password, repeat_password)

    # If registration successful, return successful message
    return "Registration Complete"

# Route to handle user login
@app.route("/login", methods=["GET", "POST"])
def login():
    # If request method is POST, process login
    if request.method == "POST":
        # Fetch login details from form
        email = request.form["email"]
        password = request.form["password"]

        print(email, password) # print login details for debugging
        return "Login Complete" # if login successful, return successful message

    # If request method is GET, display login.html
    return render_template("login.html")

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)