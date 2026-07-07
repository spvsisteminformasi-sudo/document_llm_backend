from dotenv import load_dotenv
from pathlib import Path
from app import create_app

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

flask_app = create_app()
celery_app = flask_app.extensions["celery"]