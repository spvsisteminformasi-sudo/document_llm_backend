from datetime import timedelta
import os

class Config():
    DEBUG = True

class DevelopmentConfig (Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND=os.getenv('CELERY_RESULT_BACKEND')
    JWT_TOKEN_LOCATION = ['headers', 'query_string']
    JWT_QUERY_STRING_NAME = 'token'
    PROPAGATE_EXCEPTIONS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
config_settings = {'development': DevelopmentConfig}