# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session, abort
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password, required_role

moderator_bp = Blueprint("moderator", __name__)

@moderator_bp.before_app_request
def is_moderator():
    if (session.get("account_type")) != "moderator":
        abort(404)


@moderator_bp.route("/view_submission", methods = ["GET", "POST"])
def view_submission():
    return "HELLO MOD"
