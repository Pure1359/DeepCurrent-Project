from flask import Blueprint, jsonify, request, session, abort

from app.services.auth import get_account_by_email_for_login, verify_password, derive_role
from app.services.actions import log_action, personal_dashboard, leaderboard
from app.services.challenges import join_challenge_individual
from app.services.evidence import list_pending_decision, create_decision

api_bp = Blueprint("qpi", __name__)

def require_login():
    account_id = session.get("account_id")
    if not account_id:
        abort(401, description = "User is not logged in")
    return int(account_id)

def require_role(role):
    if session.get("role") != role:
        abort(403, description = "User is not authorized")

@api_bp.post("/auth/login")
def api_login():
    data = request.get_json(force = True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        abort(400, description = "Missing email or password")
    
    account = get_account_by_email_for_login(email)
    if not account or not verify_password(password, account.get("password")):
        abort(401, description = "Invalid email or password")
    
    session["account_id"] = account.get("account_id")
    session["role"] = derive_role(account)
    return jsonify({"message": "Login successful", "role": session["role"], "account_id": session["account_id"]})

@api_bp.post("/actions")
def api_log_action():
    account_id = require_login()
    data = request.get_json(force = True)
    action_name = data.get("action_name")
    category = data.get("category")
    quantity = data.get("quantity")
    challenge_id = data.get("challenge_id")
    evidence_url = data.get("evidence_url")

    if not action_name or not category or quantity is None:
        abort(400, description = "Missing action name, category, or quantity")

    try:
        quantity = float(quantity)
    except Exception:
        abort(400, description = "Quantity must be a number")
    if quantity <= 0:
        abort(400, description = "Quantity must be greater than 0")

    if challenge_id is not None:
        try:
            challenge_id = int(challenge_id)
        except Exception:
            abort(400, description = "Challenge ID must be an integer")
        
    try:
        result = log_action(
            account_id=account_id,
            action_name=str(action_name),
            category=str(category),
            quantity=quantity,
            challenge_id=challenge_id,
            evidence_url=evidence_url
        )
    except ValueError as e:
        abort(400, description = str(e))

    action_id = result["action_log_id"]
    decision_id = result["decision_id"]
    evidence_id = result["evidence_id"]
    challenge_id = result["challenge_id"]


    return jsonify({"message": "Action logged successfully", "action_id": action_id, "decision_id" : decision_id, "evidence_id" : evidence_id, "challenge_id" : challenge_id})

@api_bp.post("/challenges/join")
def api_join_challenge():
    account_id = require_login()
    data = request.get_json(force = True)
    challenge_id = data.get("challenge_id")

    if challenge_id is None:
        abort(400, description = "Missing challenge ID")
    
    try:
        challenge_id = int(challenge_id)
    except Exception:
        abort(400, description = "Challenge ID must be an integer")
    
    join_challenge_individual(account_id, challenge_id)
    return jsonify({"message": "Challenge joined successfully", "challenge_id": challenge_id})

@api_bp.get("/dashboard/personal")
def api_personal_dashboard():
    account_id = require_login()
    return jsonify(personal_dashboard(account_id))

@api_bp.get("/dashboard/leaderboard")
def api_leaderboard():
    limit = request.args.get("limit", 10)
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    return jsonify({"leaderboard": leaderboard(limit)})

@api_bp.get("moderation/pending")
def api_pending_decisions():
    require_login()
    require_role("moderator")
    data = request.get_json()
    offset = data.get("offset", 0)
    limit = data.get("limit", 10)
    return jsonify({"pending": list_pending_decision(limit, offset)})

@api_bp.post("moderation/decision")
def api_make_decision():
    reviewer_id = require_login()
    require_role("moderator")
    data = request.get_json(force = True)
    evidence_id = data.get("evidence_id")
    status = data.get("status")
    reason = data.get("reason")

    if evidence_id is None or not status:
        abort(400, description = "Missing evidence ID or status")
    
    if status not in {"approved", "rejected"}:
        abort(400, description = "Status must be 'approved' or 'rejected'")

    create_decision(reviewer_id, status, reason, int(evidence_id))
    return jsonify({"message": "Decision made successfully"})