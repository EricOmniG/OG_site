# ============================================================
#  flask_app/run.py
#  Local development entrypoint
#  Run with: python -m flask_app.run
# ============================================================

from dotenv import load_dotenv
load_dotenv()

from flask_app import create_app

app = create_app()

if __name__ == "__main__":
    import os
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("DEBUG", "true").lower() == "true",
    )
