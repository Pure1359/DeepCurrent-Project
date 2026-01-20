from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    dob = request.form["dob"]
    password = request.form["password"]
    repeat_password = request.form["repeat_password"]

    print(first_name, last_name, email, dob, password, repeat_password)

    return "Registration Complete"

if __name__ == '__main__':
    app.run(debug=True)