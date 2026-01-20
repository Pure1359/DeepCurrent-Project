from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def register():
    return render_template("register.html")

if __name__ == '__main__':
    app.run(debug=True)