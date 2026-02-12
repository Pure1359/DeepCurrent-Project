import pytest
from flask import template_rendered, session
from contextlib import contextmanager
from database_fixture import function_scope_database, module_scope_database
from app import create_app

#check for rendering template
@contextmanager
def captured_template(app):
    recorded_template = []
    def record_template(sender, template, context, **extra):
        recorded_template.append((template, context))
    template_rendered.connect(record_template, app)
    try:
        yield recorded_template
    finally:
        template_rendered.disconnect(record_template, app)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING" : True})
    yield app

@pytest.fixture(scope = "module")
def app_module():
    app = create_app()
    app.config.update({"TESTING" : True})
    yield app

@pytest.fixture()
def new_client_function(app):
    return app.test_client()


@pytest.fixture(scope="module")
def new_client_module(app_module):
    return app_module.test_client()

@pytest.fixture()
def recorded_template(app):
    with captured_template(app) as recorder:
        yield recorder

@pytest.fixture(scope = "module")
def recorded_template_module(app_module):
    with captured_template(app_module) as recorder:
        yield recorder
    

def test_get_register(new_client_function, recorded_template):
    response = new_client_function.get("/register", follow_redirects = True)
    assert len(recorded_template) == 1
    template, context = recorded_template[0]
    assert template.name == "register.html"
    assert response.request.path == "/register"

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
        assert session.get("account_role") == "student"
    


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









    
