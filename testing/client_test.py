import pytest
import bcrypt
from datetime import datetime, timezone

# Import Database Functions from services/
from app.services.users import create_user, create_account, update_last_active
from app.services.auth import get_account_by_email_for_login, verify_password, required_role
from app import create_app
from flask import session


@pytest.fixture()
def app():
    app = create_app()
    app.config_update({"TESTING": True})
    yield app
    #some optional teardown
    

@pytest.fixture()
def client(app):
    return app.test_client()

#valid user
@pytest.fixture()
def valid_john_doe():
    return  {
        "first_name" : "John",
        "last_name" : "Doe",
        "email" : "JD123@exeter.ac.uk",
        "dob" : "2001-06-07",
        "user_type" : "normal",
        "password" : "Jd123",
        "repeat_password" : "Jd123"
    }


def test_register_sucessful(client, valid_john_doe):
    response = client.post("/register", data = {valid_john_doe}, follow_redirects = True)
    
    with client:
        assert session["account_id"] == valid_john_doe["account_id"]

    assert response.request.path == "/login"

def test_register_repeatpassword_incorrect(client, valid_john_doe):
    invalid_john_doe = valid_john_doe.copy()
    invalid_john_doe["repeat_password"] == "JD123"
    response = client.post("/register", data = {invalid_john_doe}, follow_redirects = True)
    assert b"Password do not match." in response.data
    assert response.request.path == "/register"


def test_logout_session(client):

    response = client.post("/logout")
    with client:
        assert session["account_id"] is None
    
    assert response.request.path == "/login"



