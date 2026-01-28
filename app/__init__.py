import os
from flask import Flask

from .db_config import close_connection
from .app import bp

def create_app():
    # Load templates from templates/
    app = Flask(__name__, template_folder="templates")

    # Used for session cookies (i.e. logging in)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # Register Blueprints
    app.register_blueprint(bp)

    # Close Database connection at the end of each request to prevent memory leaks
    app.teardown_appcontext(lambda _error: close_connection())

    return app