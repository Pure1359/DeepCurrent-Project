# DeepCurrent

DeepCurrent is a Flask-based web application that aims to record user actions for their environmental impact and calculate their total CO2e savings over time. The application includes user accounts, activity logging, group challenges, and evidence submission, with the use of a MySQL database.

The platform promotes climate-positive behaviour through:
* Personal Tracking
* Group Challenges
* Evidence Submissions

---

## Features

* User authentication and profiles
* Environmental action logging
* CO<sub>2</sub>e savings calculations
* Group challenges and leaderboards
* Evidence submission and moderation
* Personal and group statistics dashboard

---

## Tech Stack

| Layer 					| Technology		   |
|--------------			|----------		   |
| Backend 					| Flask (Python 3.10+) |
| Database 					| MySQL / SQLite 	   |
| ORM / DB Driver 			| PyMySQL 			   |
| Authentication & Security | bcrypt 			   |
| Environment Config 		| python-dotenv 	   |
| Testing 					| pytest 			   |

---

## Project Structure

```code
DeepCurrent-Project/
  app/
    app.py				# Flask app factory
	api.py				# API routes
	db_config.py		# Database connection
	services/			# Business logic layer
	templates/			# HTML views
	__init__.py
  run.py				# App entry point
  requirements.txt
  README.md
  LICENSE
```

---

## Installation & Setup

### Clone the repository
```bash
git clone https://github.com/Pure1359/DeepCurrent-Project.git
cd "DeepCurrent-Project"
```

---

### Create virtual environment
```bash
python -m venv venv
source venv/bin/activate		# Linux / Mac
venv\Scripts\activate 			# Windows
```

---

### Install dependencies
```bash
pip install -r requirements.txt
```

---

### Environment Variables
Create secret.env in the root directory

```env
# Flask
FLASK_APP=DeepCurrent
FLASK_SECRET_KEY=<FlaskSecretKey>

# Database Engine Selector (mysql for deployment, sqlite for testing)
DB_ENGINE=mysql

# MySQL Configuration
MYSQL_HOST=<DatabaseIP>
MYSQL_USER=<UserName>
MYSQL_PASSWORD=<Password>
MYSQL_DB=<Database>

# SQLite Configuration
SQLITE_PATH=<SQLite Database Path>
```

---

## Running the Project

From the project root directory:

```bash
python run.py
```

The app will run at:

```code
http://localhost:5020
```

---

## Running Tests

From the project root directory:

```bash
python -m pytest testing/unit_testing -v
```

---

## License

MIT (See LICENSE)

---

## Author(s)

DeepCurrent Development Team

| Name                   | Assignment  | Notes |
|----------------        |------------ |--------|
| Joaquin Bradley Rigunay| Frontend    | Co-designed cards for front end and merging with backend |
| Xuan Ting Pheng        | Frontend    | Co-designed cards for front end and helped take meeting notes |
| Farzad Rezaei Kohvadeh | Frontend    | Frontend UI designer, Figma designs, HTML, CSS, and JavaScript. |
| Pure Nantasuwan        | Backend     | Backend, GitHub, testing, food and waste research |
| Carlin Barlow          | Backend     | Backend, deployment, documentation, partial testing |
| Rumi Mansoubi          | Backend     | Project lead: man management, workload spread/advice/direction, documentation, backend development, presentation slides and scripts, scheduled meetings, travel research    |
| Akkshay Sharrma        | Backend     | Documentation and research for backend    |
| Jayden Kam             | Database    | Database design, seeded data, documentation, energy research |
