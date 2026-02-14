# Import modules
from flask import abort, jsonify, make_response, request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users_service import create_user, create_account, update_last_active, join_challenge_individual, get_monthly_saved, get_weekly_saved, get_yearly_saved
from app.services.actions import *
from app.services.auth import get_account_by_email_for_login, verify_password, verify_session_role
from app.db_config import db_cursor
from custom_error.Challenge_Exception import *

#need to do required login 
user_bp = Blueprint("user", __name__)



@user_bp.before_request
def is_login():
    is_user = verify_session_role(session.get("account_role"), "user")
    is_moderator = verify_session_role(session.get("account_role"), "moderator")
    if (not(is_user) and not(is_moderator)):
        return redirect(url_for("app.login"))
    else:
        pass

#have to find some link between action log and challenge, as it should contain the status of the decision
@user_bp.route("/get_action_history", methods = ["POST"])
def list_action_history():
    
    data = request.get_json()
    offset = data.get("offset", 0)
    offset = 0
    limit = 100
    limit = data.get("limit", 30)
    account_id = session.get("account_id")
    return get_action_history(account_id, limit, offset)

#The app.service.actions already implement automatic challenge distribution
@user_bp.route("/submit_action",  methods = ["POST"])
def submit_action():
    #abort with message telling user is not logged in
    account_id = session.get("account_id")
    if not account_id:
        abort(400, description = "User is not logged in")
    
    data = request.get_json()
    action_name = data.get("action_name")
    category = data.get("category")
    quantity = data.get("quantity")
    challenge_id = data.get("challenge_id")
    #if user don't submit evidence then data.get("evidence") return None
    evidence_url = data.get("evidence_url")

    # if action_name not in permitted_action_name:
    #     error_message = f"Action name : {action_name} is not recognized as a valid action name"
    #     return make_response(jsonify(error = error_message), 400)
    
    # if category not in permitted_category_name:
    #     error_message = f"Category name : {category} is not recognized as a valid category name"
    #     return make_response(jsonify(error = error_message), 400)
    
    if quantity <= 0:
        error_message = "Quantity can not be 0 or have negative value"
        return make_response(jsonify(error = error_message), 400)

    #if we pass all check
    #then we log an action
    response = log_action(account_id, action_name, category, quantity, challenge_id, evidence_url)

    action_log_id = response["action_log_id"]
    evidence_id = response["evidence_id"]
    decision_id = response["decision_id"]
    challenge_id = response["challenge_id"]
    co2e_factor = response["co2e_factor"]

    return jsonify({"success" :True, "message":"Successfully log an action", "action_log_id" : action_log_id, "evidence_id" : evidence_id, "decision_id" : decision_id, "challenge_id" : challenge_id, "co2e_factor" : co2e_factor, "quantity" : quantity}), 200
    

@user_bp.route("/join_challenge",  methods = ["POST"])
def join_challenge():
    account_id = session.get("account_id")
    data = request.get_json()

    challenge_id = data.get("challenge_id")
    try:
        join_challenge_individual(challenge_id, account_id)
        return {"success" :True, "message":f"Successfully added the user to challenge : {challenge_id}"}, 200
    except (UserAlreadyJoinChallenge, InvalidChallengeDate, ChallengeIdNotFound) as error:
        error_message =str(error)
        return make_response(jsonify(error = error_message), 400)
    
@user_bp.route("/get_challenge_for_user", methods = ["POST"])
def get_challenge_for_user():
    account_id = session.get("account_id")
    get_challenge = """SELECT challenge_id FROM IndividualParticipation WHERE account_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(get_challenge, (account_id,))
        challenge_result = cursor.fetchall()    
        response = jsonify(challenge_result)
        return response
    
@user_bp.route("/get_weekly_co2e_saving", methods = ["POST"])
def get_user_weekly_saving():
    account_id = session.get("account_id")
    result = get_weekly_saved(account_id)
    return jsonify({"total_saving":result})

@user_bp.route("/get_monthly_co2e_saving", methods = ["POST"])
def get_user_monthly_saving():
    account_id = session.get("account_id")
    result = get_monthly_saved(account_id)
    return jsonify({"total_saving":result})

@user_bp.route("/get_yearly_co2e_saving", methods = ["POST"])
def get_user_yearly_saving():
    account_id = session.get("account_id")
    result = get_yearly_saved(account_id)
    return jsonify({"total_saving":result})


    