from dotenv import load_dotenv
from app import create_app
import os
# Load environment variables from .env file
load_dotenv("4_technical/source_code_snapshot/secret.env")

app = create_app()

if __name__ == '__main__':
    print(os.getenv("MYSQL_HOST"))
    app.run(host="localhost", port=5000, debug=True)