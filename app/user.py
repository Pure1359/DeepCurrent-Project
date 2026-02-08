# Import modules
from flask import abort, jsonify, make_response, request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users_service import create_user, create_account, update_last_active, join_challenge_individual
from app.services.actions import log_action
from app.services.auth import get_account_by_email_for_login, verify_password, verify_session_role
from app.db_config import db_cursor
from custom_error.Challenge_Exception import *

#need to do required login 
user_bp = Blueprint("user", __name__)

permitted_action_name = ["car, walking, bus, train, cycling"]
permitted_category_name = ["travel, food, energy, waste"]

@user_bp.before_app_request
def is_login():
    is_user = verify_session_role(session.get("role"), "user")
    is_moderator = verify_session_role(session.get("role"), "moderator")

    if (not(is_user) and not(is_moderator)):
        redirect(url_for("login"))
    else:
        pass

#have to find some link between action log and challenge, as it should contain the status of the decision
@user_bp.route("/get_action_history", methods = "POST")
def get_action_history():
    offset = request.get("offset")
    limit = request.get("limit")


    

#The app.service.actions already implement automatic challenge distribution
@user_bp.route("/submit_action")
def submit_action():
    data = request.get_json()

    action_name = data.get("data")
    category = data.get("category")
    quantity = data.get("quantity")
    #if user don't submit evidence then data.get("evidence") return None
    evidence_url = data.get("evidence_url")

    #abort with message telling user is not logged in
    account_id = session.get("account_id")
    if not account_id:
        abort(400, description = "User is not logged in")

    if action_name not in permitted_action_name:
        error_message = f"Action name : {action_name} is not recognized as a valid action name"
        return make_response(jsonify(error = error_message), 400)

    if category not in permitted_category_name:
        error_message = f"Category name : {category} is not recognized as a valid category name"
        return make_response(jsonify(error = error_message), 400)
    
    if quantity <= 0:
        error_message = "Quantity can not be 0 or have negative value"
        return make_response(jsonify(error = error_message), 400)

    #if we pass all check
    #then we log an action
    log_action(account_id, action_name, category, quantity, evidence_url)
    

@user_bp.route("/join_challenge")
def join_challenge():
    account_id = session.get(account_id)
    challenge_id = request.args.get("challenge_id")
    try:
        join_challenge_individual(challenge_id, account_id)
    
    except (UserAlreadyJoinChallenge, InvalidChallengeDate, ChallengeIdNotFound) as error:
        error_message =str(error)
        return make_response(jsonify(error = error_message), 400)



    