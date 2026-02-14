import pytest
from database_fixture import *


def test_get_register(new_client_function, recorded_template):
    response = new_client_function.get("/register", follow_redirects = True)
    assert len(recorded_template) == 1
    template, context = recorded_template[0]
    assert template.name == "register.html"
    assert response.request.path == "/register"

def test_register_missing_field(new_client_function, recorded_template, module_scope_database):
    response = new_client_function.post("/register", data = {
        "first_name" : "john",
        "email" : "jd123@exeter.ac.uk",
        "dob" : "2000-07-09",
        "user_type" : "student",
        "password" : "jd123tv",
        "repeat_password" : "jd123tv"
    }, follow_redirects = True)
    
    assert len(recorded_template) == 1
    template, context = recorded_template[-1]
    assert context["error"] == "Please fill in all fields."
    assert template.name == "register.html"

def test_register_normal(new_client_module, recorded_template_module, module_scope_database):
    response = new_client_module.post("/register", data = {
        "first_name" : "john",
        "last_name" : "doe",
        "email" : "jd123@exeter.ac.uk",
        "dob" : "2000-07-09",
        "user_type" : "student",
        "password" : "jd123tv",
        "repeat_password" : "jd123tv"
    }, follow_redirects = True)
    
    assert len(recorded_template_module) == 1
    template,context = recorded_template_module[0]
    assert response.request.path == "/login"
    assert template.name == "login.html"

def test_login_normal(new_client_module, recorded_template_module, module_scope_database):
    response = new_client_module.post("/login", data = {
        "email":  "jd123@exeter.ac.uk",
        "password" : "jd123tv"
    }, follow_redirects = True)

    assert len(recorded_template_module) == 2
    template, context = recorded_template_module[-1]
    assert response.request.path == "/dashboard"
    assert template.name == "dashboard.html"

    with new_client_module.session_transaction() as session:
        # set a user id without going through the login route
        assert session.get("account_role") == "user"

def test_login_moderator(new_client_function, recorded_template, module_scope_database):
    response = new_client_function.post("/login", data = {
        "email" : "j.miller@exeter.ac.uk",
        "password" : "moderator456" 
    }, follow_redirects = True)

    assert len(recorded_template) == 1
    template, context = recorded_template[-1]
    assert response.request.path == "/dashboard"
    assert template.name == "dashboard.html"

    with new_client_function.session_transaction() as session:
        assert session.get("account_role") == "moderator"

def test_login_wrong(new_client_function, recorded_template, module_scope_database):
    response = new_client_function.post("/login", data = {
        "email" : "jd123@exeter.ac.uk",
        "password" : "jd12tv"
    }, follow_redirects = True)
    assert len(recorded_template) == 1
    template, context = recorded_template[-1]
    assert context['error'] == "Invalid email or password."
    assert template.name == "login.html"

def test_register_incorrect_credential(new_client_function, recorded_template):
    response = new_client_function.post("/register", data = {
        "first_name" : "john",
        "last_name" : "doe",
        "email" : "jd123@exeter.ac.uk",
        "dob" : "2000-07-09",
        "user_type" : "student",
        "password" : "jd123tv",
        "repeat_password" : "JD123tv"
    }, follow_redirects = True)
    
    assert len(recorded_template) == 1
    template,context = recorded_template[0]
    assert response.request.path == "/register"
    assert template.name == "register.html"
    assert context['error'] == "Passwords do not match."









    
