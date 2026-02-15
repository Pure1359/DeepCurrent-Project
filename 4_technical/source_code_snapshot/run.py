from dotenv import load_dotenv
from app import create_app
import os
from set_up.database_setup import *
# Load environment variables from .env file
load_dotenv("secret.env")

app = create_app()
deleterecord()
default_actionType_data()
defaultDatabase()
production_setup()


if __name__ == '__main__':
    print(os.getenv("MYSQL_HOST"))
    app.run(host="localhost", port=5020, debug=True)