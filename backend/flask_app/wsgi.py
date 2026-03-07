# ============================================================
#  flask_app/wsgi.py
#  AWS Lambda handler for the Flask app
#  Uses apig-wsgi to adapt Flask's WSGI interface to Lambda events
#
#  In template.yaml, set this Lambda's Handler to:
#    flask_app.wsgi.handler
# ============================================================

from dotenv import load_dotenv
load_dotenv()

from apig_wsgi import make_lambda_handler
from flask_app import create_app

flask_app = create_app()

# Lambda handler — equivalent to Mangum for FastAPI
handler = make_lambda_handler(flask_app)
