from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv("secret.env")

app = create_app()

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)