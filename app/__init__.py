from flask import Flask
from .db_config import close_connection

def create_app():
    # Load templates from templates/
    app = Flask(__name__, template_folder="templates")

    # Close Database connection at the end of each request to prevent memory leaks
    app.teardown_appcontext(lambda _error: close_connection())

    return app