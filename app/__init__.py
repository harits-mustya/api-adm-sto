from flask import Flask
import logging
import os
from logging.handlers import RotatingFileHandler
from app.routes import init_routes
from config import SECRET_KEY

class Config:
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't'] 
    SECRET_KEY = SECRET_KEY

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'app.log')

    # Set up logging
    handler = RotatingFileHandler(log_path, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))

    app.logger.addHandler(handler)

    init_routes(app)

    return app

app = create_app()