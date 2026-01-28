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

def test_register(new_client):
    print("hi")
    with captured_template(new_client.application) as recorded_template:
        response = new_client.get("/register", follow_redirects = True)
        assert len(recorded_template) == 1
        template, context = recorded_template[0]
        assert template.name == "register.html"
        assert response.request.path == "/register"
    
        response = new_client.post("/register", data = {
            "first_name" : "john",
            "last_name" : "doe",
            "email" : "jd123@exeter.ac.uk",
            "dob" : "2000-07-09",
            "user_type" : "normal",
            "password" : "jd123tv",
            "repeat_password" : "JD123tv"
        }, follow_redirects = True)

        assert len(recorded_template) == 2
        template,context = recorded_template[1]
        assert response.request.path == "/register"
        assert template.name == "register.html"
        assert context['error'] == "Passwords do not match."



    
