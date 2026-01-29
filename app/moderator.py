# Import modules
from flask import request, render_template, redirect, url_for, Blueprint, session, abort
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.challenges import *
from app.services.evidence import *

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


@moderator_bp.route("/view_submission_list", methods = ["GET", "POST"])
def view_submission_list():
    #return list of submission
    return "HELLO MOD"

@moderator_bp.route("/view_submission<id>")
def view_specific_submission(id):
    #render evidence detail
    #return evidence URL
    pass

@moderator_bp.route("/view_submission<id><decision>/")
def approved_specific_submission(id, decision):
    pass



