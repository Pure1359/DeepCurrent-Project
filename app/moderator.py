# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session, abort, jsonify
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.challenges import *
from app.services.evidence import *
from app.services.auth import verify_session_role

moderator_bp = Blueprint("moderator", __name__)

#before any request within /moderator bp check if client is moderator or not
@moderator_bp.before_app_request
def is_moderator():
    if (verify_session_role(session.get("role"), "moderator")):
        pass
    else:
        abort(404)

@moderator_bp.route("/view_submission_list", methods = ["GET", "POST"])
def view_submission_list():
    offset = request.args.get("offset", 0)
    limit = request.args.get("limit", 10)
    #validate data type in url parameter
    try:
        offset = int(offset)
        limit = int(limit)    
    except ValueError:
        abort(400, description = "offset or limit data type must be int")

    return list_pending_decision(limit, offset)

@moderator_bp.route("/approve_submission/")
def make_submission_decision(decision, result ,reason):
    evidence_id = request.args.get("evidence_id")
    decision_result = request.args.get("result")
    reason = request.args.get("reason")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    reviewer_id = session.get("account_id")

    create_decision(reviewer_id, decision_result, now, reason, evidence_id)

    
@moderator_bp.route("/create_challenge", methods = ["GET", "POST"])
def moderator_make_challenge():
    created_by = session.get("account_id")
    challenge_type = request.form['challenge_type']
    is_official = True
    title = request.form['title']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    create_challenge(created_by, challenge_type, is_official, title, start_date, end_date)







