from typing import Any, Literal
from flask import Response, jsonify
from app.db_config import db_cursor
from datetime import datetime
from custom_error.Group_Exception import *

def UserCreateGroup(account_id, group_name) -> int | DuplicateGroupName:
    time: datetime = datetime.now()
    with db_cursor() as (connection, cursor):
        #check if user already belongs to a group
        sql = """SELECT * FROM AccountGroup WHERE account_id = %s"""
        cursor.execute(sql, (account_id,))
        if cursor.fetchone() is not None:
            raise UserAlreadyJoinGroup("You already belong to a group, leave it first before creating a new one")

        #check for duplicate group_name
        sql = """SELECT * FROM UserGroup WHERE group_name = %s"""
        cursor.execute(sql, (group_name,))
        result = cursor.fetchone()
        if result is not None:
            raise DuplicateGroupName("Group Name already exists")
        sql = """INSERT INTO UserGroup(group_creator_id, group_name, group_created) VALUES(%s, %s, %s)"""
        cursor.execute(sql, (account_id, group_name, time))
        UserGroupID = cursor.lastrowid
        if UserGroupID is None:
            raise Exception("Failed to insert UserGroup")
        #Insert user into AccountGroup
        UserJoinGroup(account_id, UserGroupID)
        return UserGroupID


def UserJoinGroup(account_id, group_id):
    with db_cursor() as (connection, cursor):
        time: datetime = datetime.now()
        #check if the user already belongs to any group
        sql = """SELECT * FROM AccountGroup WHERE account_id = %s"""
        cursor.execute(sql, (account_id,))
        result = cursor.fetchone()
        if result is not None:
            raise UserAlreadyJoinGroup("You already belong to a group, leave it first before joining another")

        sql = """INSERT INTO AccountGroup(account_id, group_id, roles, joined) VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql, (account_id, group_id, "Normal", time))

        return True

def UserLeaveGroup(account_id, group_id):
    with db_cursor() as (connection, cursor):
        #User can not leave the group if they are the owner
        sql = """SELECT * FROM UserGroup WHERE group_id = %s AND group_creator_id = %s"""
        cursor.execute(sql, (group_id, account_id))
        result = cursor.fetchone()
        if result is not None:
            raise LeaveGroupError("Can not leave group that you are owner")
        #User is not the owner of group then do
        sql = """DELETE FROM AccountGroup WHERE account_id = %s AND group_id = %s"""
        cursor.execute(sql, (account_id, group_id))
        return True

def getGroupMember(group_id) -> list[str]:
    #check if group_id exists
    sql = """SELECT username FROM AccountGroup INNER JOIN Accounts ON AccountGroup.account_id = Accounts.account_id WHERE group_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (group_id,))
        result = cursor.fetchall()
    return [record["username"] for record in result]

def getUserGroups(account_id) -> list[str]:
    #Join AccountGroup and UserGroup to get the group name
    sql = """ SELECT group_name FROM AccountGroup INNER JOIN UserGroup ON AccountGroup.group_id = UserGroup.group_id WHERE AccountGroup.account_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id,))
        result = cursor.fetchall()
    return [record["group_name"] for record in result]

def getAllGroups():
    sql = """SELECT UserGroup.group_id, UserGroup.group_name, UserGroup.group_creator_id,
                    (SELECT COUNT(*) FROM AccountGroup WHERE AccountGroup.group_id = UserGroup.group_id) as member_count
             FROM UserGroup ORDER BY UserGroup.group_name ASC"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql)
        return cursor.fetchall()
