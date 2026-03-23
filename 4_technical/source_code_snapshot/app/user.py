# Import modules
from flask import abort, jsonify, make_response, request, render_template, redirect, url_for, Blueprint, session
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users_service import create_user, create_account, update_last_active, get_monthly_saved, get_weekly_saved, get_yearly_saved
from app.services.actions import *
from app.services.auth import get_account_by_email_for_login, verify_password, verify_session_role
from app.db_config import db_cursor
from app.services.challenges import join_challenge_individual, join_challenge_group
from custom_error.Challenge_Exception import *
from custom_error.Group_Exception import *
from app.services.groups import *
from app.services.challenges import *
from app.services.challenges import get_all_active_challenges, get_challenge_for_user as get_challenge_for_user_service

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

@user_bp.route("/user-history")
def moderator_list():
    return render_template("user_history.html")

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
    
    if category != "food" and quantity <= 0:
        error_message = "Quantity can not be 0 or have negative value"
        return make_response(jsonify(error = error_message), 400)

    #if we pass all check
    #then we log an action
    try:
        response = log_action(account_id, action_name, category, quantity, challenge_id, evidence_url)
    except ValueError as error:
        return make_response(jsonify(error = str(error)), 400)

    return jsonify({"success" :True, "message":"Successfully log an action", **response}), 200
    

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
    challenge_result = get_challenge_for_user_service(account_id)
    return jsonify(challenge_result)

@user_bp.route("/get_all_challenges", methods = ["POST"])
def list_all_challenges():
    account_id = session.get("account_id")
    challenges = get_all_active_challenges()
    joined_ids = [row["challenge_id"] for row in get_challenge_for_user_service(account_id)]

    #Find what group this user owns (if any)
    owned_group_id = None
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT group_id FROM UserGroup WHERE group_creator_id = %s", (account_id,))
        owned_group = cursor.fetchone()
        if owned_group:
            owned_group_id = owned_group["group_id"]

        #Get group challenge IDs that this users owned group has joined
        group_joined_ids = []
        if owned_group_id:
            cursor.execute("SELECT challenge_id FROM GroupParticipation WHERE group_id = %s", (owned_group_id,))
            group_joined_ids = [row["challenge_id"] for row in cursor.fetchall()]

    for c in challenges:
        if c["challenge_type"] == "Personal":
            c["joined"] = c["challenge_id"] in joined_ids
        else:
            c["joined"] = c["challenge_id"] in group_joined_ids
        c["owned_group_id"] = owned_group_id

    return jsonify(challenges)
    
@user_bp.route("/get_challenges_for_category", methods = ["POST"])
def get_challenges_for_category():
    account_id = session.get("account_id")
    data = request.get_json()
    category = data.get("category")
    challenges = get_user_active_challenges_by_category(account_id)
    return jsonify(challenges)

@user_bp.route("/get_weekly_co2e_saving", methods = ["POST"])
def get_user_weekly_saving():
    account_id = session.get("account_id")
    data = request.get_json()
    category = data.get("category") if data else None
    result = get_weekly_saved(account_id, category)
    return jsonify({"total_saving":result})

@user_bp.route("/get_monthly_co2e_saving", methods = ["POST"])
def get_user_monthly_saving():
    account_id = session.get("account_id")
    data = request.get_json()
    category = data.get("category") if data else None
    result = get_monthly_saved(account_id, category)
    return jsonify({"total_saving":result})

@user_bp.route("/get_yearly_co2e_saving", methods = ["POST"])
def get_user_yearly_saving():
    account_id = session.get("account_id")
    data = request.get_json()
    category = data.get("category") if data else None
    result = get_yearly_saved(account_id, category)
    return jsonify({"total_saving":result})

@user_bp.route("/get_food_types", methods=["POST"])
def get_food_types():
    sql = "SELECT actionName FROM ActionType WHERE category = 'food' ORDER BY actionName ASC"
    with db_cursor() as (connection, cursor):
        cursor.execute(sql)
        result = cursor.fetchall()
    return jsonify([row["actionName"] for row in result])

@user_bp.route("/get_all_active_challenges", methods=["POST"])
def get_all_active_challenges_route():
    result = get_all_active_challenges()
    return jsonify(result)

@user_bp.route("/get_individual_leaderboard", methods=["POST"])
def get_individual_leaderboard():
    data = request.get_json()
    challenge_id = data.get("challenge_id")
    try:
        result = challenge_leaderboard_individual(challenge_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route("/get_group_leaderboard", methods=["POST"])
def get_group_leaderboard():
    data = request.get_json()
    challenge_id = data.get("challenge_id")
    try:
        result = challenge_leaderboard_group(challenge_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/create_group", methods = ["POST"])
def user_create_group():
    data = request.get_json();
    group_name = data.get("group_name")
    account_id = session.get("account_id")
    try:
        group_id = UserCreateGroup(account_id, group_name)
    except (DuplicateGroupName, UserAlreadyJoinGroup) as error:
        error_message = str(error)
        return make_response(jsonify(error = error_message), 409)

    return jsonify({"success" : True, "message" : f"You have successfully create a group name : {group_name}", "group_id" : group_id}), 200

@user_bp.route("/join_group", methods = ["POST"])
def user_join_group():
    data = request.get_json()
    group_id = data.get("group_id")
    account_id = session.get("account_id")
    try:
        UserJoinGroup(account_id, group_id)
    except UserAlreadyJoinGroup as error:
        error_message = str(error)
        return make_response(jsonify(error = error_message), 409)
    
    return jsonify({"success" : True, "message" : f"Successfully join a group id : {group_id}"}), 200

@user_bp.route("/leave_group", methods = ["POST"])
def user_leave_group():
    data = request.get_json()
    group_id = data.get("group_id")
    account_id = session.get("account_id")
    try:
        UserLeaveGroup(account_id, group_id)
    except LeaveGroupError as error:
        error_message = str(error)
        return make_response(jsonify(error = error_message), 409)
    
    return jsonify({"success" : True, "message" : "Successfully leave the group"}), 200

@user_bp.route("/get_group_member", methods = ["POST"])
def get_group_member():
    data = request.get_json()
    group_id = data.get("group_id")
    member_list = getGroupMember(group_id)

    return jsonify({"success" : True, "member" : member_list}), 200

@user_bp.route("/get_user_groups", methods = ["POST"])
def get_user_groups():
    account_id = session.get("account_id")
    group_list = getUserGroups(account_id)
    return jsonify({"success" : True, "member" : group_list}), 200

@user_bp.route("/join_group_challenge", methods = ["POST"])
def join_group_challenge():
    account_id = session.get("account_id")
    data = request.get_json()
    challenge_id = data.get("challenge_id")
    group_id = data.get("group_id")
    try:
        join_challenge_group(challenge_id, group_id, account_id)
        return {"success" :True, "message":f"Successfully added the group to challenge : {challenge_id}"}, 200
    except (GroupPermissionError, ChallengeIdNotFound, GroupAlreadyJoinChallenge, InvalidChallengeDate) as error:
        error_message = str(error)
        return make_response(jsonify(error = error_message), 409)

@user_bp.route("/get_all_groups", methods = ["POST"])
def list_all_groups():
    account_id = session.get("account_id")
    groups = getAllGroups()
    user_groups = getUserGroups(account_id)
    for group in groups:
        group["is_member"] = group["group_name"] in user_groups
        group["is_owner"] = group["group_creator_id"] == account_id
    return jsonify(groups)

@user_bp.route("/get_category_stats", methods=["POST"])
def get_category_stats():
    account_id = session.get("account_id")
    get_stats = """
        SELECT 
            at.category,
            SUM(al.co2e_saved) AS total_saved
        FROM ActionLog al
        JOIN ActionType at
            ON al.actionType_id = at.actionType_id
        WHERE al.submitted_by = %s
        GROUP BY at.category
        ORDER BY total_saved DESC
    """

    with db_cursor() as (connection, cursor):
        cursor.execute(get_stats, (account_id,))
        stats_result = cursor.fetchall()

        total = sum((row["total_saved"] or 0) for row in stats_result)

        colors = ["#378ADD", "#1D9E75", "#D85A30", "#7F77DD", "#E0B43B", "#D94F70"]

        data = []
        for i, row in enumerate(stats_result):
            pct = ((row["total_saved"] or 0) / total * 100) if total else 0
            data.append({
                "label": row["category"],
                "pct": round(pct, 1),
                "color": colors[i % len(colors)]
            })

        return jsonify(data)


    