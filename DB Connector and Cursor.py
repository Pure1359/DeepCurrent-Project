from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="DeepCurrent-Project\secret.env")

DeepCurrent = os.getenv('FLASK_APP', 'DeepCurrent') # Sets the Flask app name from an environment variable to "DeepCurrent" - Uses os module to get environment variable

app = Flask(DeepCurrent) # Replace all of the placeholders with actual values (Denoted by __e.g.__)
print("MYSQL_USER:", os.getenv('MYSQL_USER'))
print("MYSQL_PASSWORD:", os.getenv('MYSQL_PASSWORD'))
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
connection = pymysql.connect(host=app.config['MYSQL_HOST'],
                            user=app.config['MYSQL_USER'],
                            password=app.config['MYSQL_PASSWORD'],
                            db=app.config['MYSQL_DB'])
cursor = connection.cursor() # Establishes a cursor for database operations - needed for getters and setters

def Database_Overview():
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"table list is {tables}")

Database_Overview()


@app.route('/data', methods=['GET']) # Handles GET requests to retrieve data as a "getter"
def get_data():
    cursor.execute("SELECT * FROM yourtable")
    data = cursor.fetchall()
    return jsonify(data)

@app.route('/data', methods=['POST']) # Handles POST requests to add new data as a "setter"
def set_data():
    new_data = request.json
    cursor.execute("INSERT INTO __yourtable__ (__column1__, __column2__) VALUES (%s, %s)", (new_data['__column1__'], new_data['__column2__'])) # Insert the actual column and table names into the placeholders
    connection.commit()
    return jsonify({'message': 'Data added successfully!'}), 201


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)