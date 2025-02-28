from app import create_app, socketio
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 2000))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"

    socketio.run(app, debug=debug_mode, host=host, port=port, allow_unsafe_werkzeug=True)




