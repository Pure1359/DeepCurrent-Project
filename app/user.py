# Import modules
from flask import abort, request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users_service import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password, verify_session_role
from app.db_config import db_cursor

#need to do required login 
user_bp = Blueprint("user", __name__)


@user_bp.before_app_request
def is_login():
    is_user = verify_session_role(session.get("role"), "user")
    is_moderator = verify_session_role(session.get("role"), "moderator")

    if (not(is_user) and not(is_moderator)):
        abort(404)
    else:
        pass

#have to find some link between action log and challenge, as it should contain the status of the decision
@user_bp.route("/get_action_history", methods = "POST")
def get_action_history():
    pass

    

        