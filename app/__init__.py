from flask import Flask, jsonify, make_response
from flask_restful import Api
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.sql import text
from flask.cli import with_appcontext
import click
import os

# from dotenv import load_dotenv

from app.resources.chat_history import ChatHistoryResource
from app.resources.chat_session import ChatSessionResource
from config import config_settings
from app.models import db
from app.resources.user import UserResource
from app.resources.tag import TagResource
from app.resources.auth.login import LoginController
from app.resources.auth.register import RegisterController
from app.resources.auth.profile import ProfileController
from app.resources.document import DocumentResource
from app.resources.chatbot_resource import ChatbotHistoryResource
from app.resources.document_vector import DocumentVectorResource
from app.resources.portal import PortalResource
from app.resources.chat_completion import ChatCompletionResource
from app.commands.seed import seed_command
from app.models.document import UPLOAD_FOLDER
from celery import Celery, Task

# load_dotenv() 

# Initialize the database and migration objects
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config_settings["development"])
    
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/document'
    
    # app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

    # Add Celery configuration
    app.config.update(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    # Initialize Celery
    celery_init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    configure_jwt(app)
    CORS(app=app)
    
    api = Api(app)
    api.add_resource(UserResource, '/api/users', '/api/users/<int:id>')
    api.add_resource(TagResource, '/api/tags', '/api/tags/<int:id>')
    api.add_resource(DocumentResource, '/api/documents', '/api/documents/<int:id>')
    api.add_resource(ChatbotHistoryResource, '/api/chatbot')
    api.add_resource(ChatSessionResource, '/api/chat-sessions', '/api/chat-sessions/<int:id>')
    api.add_resource(ChatHistoryResource, '/api/chat-histories', '/api/chat-histories/<int:id>')
    api.add_resource(LoginController, '/api/login')
    api.add_resource(RegisterController, '/api/register')
    api.add_resource(ProfileController, '/api/profile')
    api.add_resource(ChatCompletionResource, '/api/chat-completion')
    app.route('/api/portal/tags')(PortalResource.tags)
    app.route('/api/portal/tags/<int:id>')(PortalResource.tags)
    app.route('/api/portal/qa')(PortalResource.qa)
    app.route('/api/portal/qa2')(PortalResource.qa2)
    app.route('/api/portal/documents/<int:id>')(PortalResource.documents)
    app.route('/api/portal/documents')(PortalResource.documents)
    app.route('/api/portal/document-search')(PortalResource.document_search)
    app.route('/uploads/<path:filename>')(PortalResource.uploaded_file)
    
    app.config['SQLALCHENY_TRACK MODIFICATIONS'] = False
    
    # Register commands
    app.cli.add_command(seed_command)
    app.cli.add_command(init_vector_extension)
    
    return app

@click.command('init-vector-extension')
@with_appcontext
def init_vector_extension():
    """Initialize the vector extension in PostgreSQL."""
    try:
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
        db.session.commit()
        click.echo('Vector extension created successfully.')
    except Exception as e:
        click.echo(f'Error creating vector extension: {e}')
        db.session.rollback()
        
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def configure_jwt(app: Flask) -> None:
    """Configure JWT settings."""
    jwt = JWTManager(app)
    
    print("JWT Manager initialized")
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Signature verification failed.", "error": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"description": "Request does not contain an access token.", "error": "authorization_required"}), 401
        
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "The token has been revoked.", "error": "token_revoked"}), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Fresh token required.", "error": "fresh_token_required"}), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token verification failed.", "error": "token_verification_failed"}), 401
    
    @jwt.user_lookup_error_loader
    def user_lookup_error_callback(_error):
        return jsonify({"message": "User not found.", "error": "user_not_found"}), 401
