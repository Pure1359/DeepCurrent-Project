# DeepCurrent

DeepCurrent is a Flask-based web application that aims to record user actions for their environmental impact and calculate their total CO2e savings over time. The application includes user accounts, activity logging, group challenges, and evidence submission, with the use of a MySQL database.

---

## Tech Stack

* Python 3.9+
* Flask
* MySQL
* PyMySQL
* python-dotenv
* bcrypt

---

## Project Structure

```
DeepCurrent-Project/
  app/
    __init__.py
    app.py
    db_config.py
    services/
      actions.py
      auth.py
      challenges.py
      evidence.py
      groups.py
      stats.py
      users.py
    templates/
      login.html
      register.html
      dashboard.html
  secret.env
  requirements.txt
  run.py
  README.md
```

---

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```txt
bcrypt
Cryptography
Flask
PyMySQL
python-dotenv
```

---

## Environment Variables Setup

Create a file named `secret.env` in the project root:
(.gitignore already includes secret.env so you don't have to worry)

```
FLASK_APP=DeepCurrent
FLASK_SECRET_KEY=<FlaskSecretKey>
MYSQL_HOST=<DatabaseIP>
MYSQL_USER=<UserName>
MYSQL_PASSWORD=<Password>
MYSQL_DB=<Database>
```

Replace variables in `<>` with the according information provided

---

## Running the Project

From the project root directory:

```bash
python run.py
```

The app will run at:

```
http://localhost:5000
```

---

## License

`<Insert License Here>`

## Author

DeepCurrent Development Team