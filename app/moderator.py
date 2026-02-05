# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session, abort, jsonify
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.challenges import *
from app.services.evidence import *

moderator_bp = Blueprint("moderator", __name__)

#before any request within /moderator bp check if client is moderator or not
@moderator_bp.before_app_request
def is_moderator():
    if ("moderator" != session.get("role")):
        abort(404)
    else:
        pass

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

    sql = """SELECT evidence_id, evidence_type, evidence_url, evidence_date
             FROM Evidence
             ORDER BY evidence_date DESC
             LIMIT %s
             OFFSET %s
          """
    
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit, offset))
        submission_list = cursor.fetchall()

        json_list = []
        for record_tuple in submission_list:
            new_dict = {"evidence_id" : record_tuple[0], "evidence_type" : record_tuple[1], "evidence_url" : record_tuple[2], "evidence_date" : record_tuple[3]}
            json_list.append(new_dict)
        
        return jsonify(json_list)

@moderator_bp.route("/approve_submission<evidence_id><decision><reason>/")
def make_submission_decision(evidence_id, decision, reason):
    sql = """INSERT INTO Decision(evidence_id, reviewer_id, status, timestamp, reason) VALUES (%s, %s, %s, %s, %s)"""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    reviewer_id = session.get("account_id")

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (evidence_id, reviewer_id, decision, now, reason))
    
@moderator_bp.route("/create_challenge", methods = ["GET", "POST"])
def moderator_make_challenge():
    created_by = session.get("account_id")
    challenge_type = request.form['challenge_type']
    is_official = True
    title = request.form['title']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    create_challenge(created_by, challenge_type, is_official, title, start_date, end_date)

    


