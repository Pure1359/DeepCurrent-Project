# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session, abort
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password

moderator_bp = Blueprint("moderator", __name__)

#before any request within /moderator bp check if client is moderator or not
@moderator_bp.before_app_request
def is_moderator():
    account_id = session.get("account_id")
    #do some sql query to get role
    #e.g. select role from role table where account = account id
    role = None
    #if role is not moderator abort(404) 
    #if role is moderator do nothing


@moderator_bp.route("/view_submission", methods = ["GET", "POST"])
def view_submission():
    return "HELLO MOD"


