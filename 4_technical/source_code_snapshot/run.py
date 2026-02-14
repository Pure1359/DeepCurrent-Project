from dotenv import load_dotenv
from app import create_app
import os
from testing.unit_testing.database_fixture import default_action_list, default_actionType_data, default_challenge_list, defaultDatabase
# Load environment variables from .env file
load_dotenv("secret.env")

app = create_app()

defaultDatabase()
default_actionType_data()
default_challenge_list()
default_action_list()

if __name__ == '__main__':
    print(os.getenv("MYSQL_HOST"))
    app.run(host="localhost", port=5000, debug=True)