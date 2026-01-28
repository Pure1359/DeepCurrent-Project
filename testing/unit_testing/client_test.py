import pytest
from flask import template_rendered
from contextlib import contextmanager
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
        template_rendered.disconnect(recorded_template, app)


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING" : True})
    yield app

@pytest.fixture()
def new_client(app):
    return app.test_client()

@pytest.fixture()
def recorded_template(app):
    with captured_template(app) as recorder:
        yield recorder

def test_get_register(new_client, recorded_template):
    response = new_client.get("/register", follow_redirects = True)
    assert len(recorded_template) == 1
    template, context = recorded_template[0]
    assert template.name == "register.html"
    assert response.request.path == "/register"

@pytest.mark.skip(reason = "Need database to be setup")
def test_register_correctpassword(new_client, recorded_template):
    response = new_client.post("/register", data = {
        "first_name" : "john",
        "last_name" : "doe",
        "email" : "jd123@exeter.ac.uk",
        "dob" : "2000-07-09",
        "user_type" : "normal",
        "password" : "jd123tv",
        "repeat_password" : "jd123tv"
    }, follow_redirects = True)
    
    assert len(recorded_template) == 1
    template,context = recorded_template[0]
    assert response.request.path == "/login"
    assert template.name == "login.html"


def test_register_wrongpassword(new_client, recorded_template):
    response = new_client.post("/register", data = {
        "first_name" : "john",
        "last_name" : "doe",
        "email" : "jd123@exeter.ac.uk",
        "dob" : "2000-07-09",
        "user_type" : "normal",
        "password" : "jd123tv",
        "repeat_password" : "JD123tv"
    }, follow_redirects = True)
    
    assert len(recorded_template) == 1
    template,context = recorded_template[0]
    assert response.request.path == "/register"
    assert template.name == "register.html"
    assert context['error'] == "Passwords do not match."



    
