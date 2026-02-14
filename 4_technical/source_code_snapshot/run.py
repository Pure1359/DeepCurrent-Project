from dotenv import load_dotenv
from app import create_app
import os
from testing.unit_testing.database_fixture import default_actionType_data, defaultDatabase
from testing.unit_testing.delete_record import deleterecord
# Load environment variables from .env file
load_dotenv("secret.env")

app = create_app()
deleterecord()
defaultDatabase()
default_actionType_data()

if __name__ == '__main__':
    print(os.getenv("MYSQL_HOST"))
    app.run(host="localhost", port=5020, debug=True)