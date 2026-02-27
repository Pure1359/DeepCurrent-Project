from flask import Response, jsonify

from app.db_config import db_cursor

# Placeholder for now
# Create functions that have to do with groups
# Follow templates in users.py and auth.py
# Some Ideas:
# create_group
# add_account_to_group
# list_group_members
# remove_account_from_group
# get_group_id

def UserCreateGroup(account_id) -> int:
    return 0

def UserJoinGroup(account_id, group_id) -> Response:
    return jsonify(None)

def UserLeaveGroup(account_id, group_id) -> Response:
    return jsonify(None)

def getGroupMember(group_id) -> Response:
    return jsonify(None)

def getUserGroups(account_id) -> Response:
    return jsonify(None)


