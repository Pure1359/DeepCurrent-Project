from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor

def test_create_group(new_client_function, module_scope_database, populated_database):
    response = new_client_function.post("/login", data = {
        "email" : 'jdsiki@fakemail.com',
        "password" : 'johndoe123'
    }, follow_redirects = True)

    #create a group
    response = new_client_function.post("/user_access/create_group", json = {"group_name" : "JackGroup"})

    result = response.get_json()
    assert result["group_id"] == 1
    assert result["message"] == "You have successfully create a group name : JackGroup"
    with db_cursor() as (connection, cursor):
        sql = """SELECT * FROM UserGroup WHERE group_id = %s"""
        cursor.execute(sql , (result["group_id"],))
        query_result = cursor.fetchone()
        assert query_result is not None
        assert query_result["group_name"] == "JackGroup"
        assert query_result["group_id"] == 1

def test_join_group(new_client_function, module_scope_database, populated_database):
    
    response = new_client_function.post("/login", data = {"email" : "e.watson@exeter.ac.uk", "password" : "password123"})

    response = new_client_function.post("/user_access/join_group", json = {"group_id" : 1})
    result = response.get_json()
    assert result["success"] == True
    assert result["message"] == "Successfully join a group id : 1"

    with db_cursor() as (connection, cursor):
        sql = """SELECT * FROM AccountGroup WHERE account_id = %s AND group_id = %s"""
        with new_client_function.session_transaction() as session:
            account_id = session.get("account_id")
        cursor.execute(sql, (account_id, 1))
        query_result= cursor.fetchall()

        assert len(query_result) == 1

def test_leave_group(new_client_function, module_scope_database, populated_database):
    #check that owner can not left the group
    response = new_client_function.post("/login", data = {
        "email" : 'jdsiki@fakemail.com',
        "password" : 'johndoe123'
    }, follow_redirects = True)
    
    response = new_client_function.post("/user_access/leave_group", json = {"group_id" : 1})

    result = response.get_json()

    assert response.status_code == 409
    assert result["error"] == "Can not leave group that you are owner"

    response = new_client_function.post("/login", data = {"email" : "e.watson@exeter.ac.uk", "password" : "password123"})

    response = new_client_function.post("/user_access/leave_group", json = {"group_id" : 1})
    result = response.get_json()
    assert result["success"] == True
    assert result["message"] == "Successfully leave the group"

    with db_cursor() as (connection, cursor):
        with new_client_function.session_transaction() as session:
            account_id = session.get("account_id")
        sql = """SELECT * FROM AccountGroup WHERE group_id = %s AND account_id = %s"""
        cursor.execute(sql, (1, account_id))
        result = cursor.fetchall()
        assert len(result) == 0

@pytest.mark.skip(reason = "Leaderboard not implemented yet")
def test_group_leaderboard():
    pass