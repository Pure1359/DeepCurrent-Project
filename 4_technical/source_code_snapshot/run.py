from dotenv import load_dotenv
from app import create_app

load_dotenv("secret.env")

app = create_app()

if __name__ == "__main__":
    app.run(host="localhost", port=5020, debug=True, use_reloader=False)