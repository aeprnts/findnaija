from flask import Flask
from flasgger import Swagger
from app.extensions import db, bcrypt, login_manager, csrf

def create_app(testing=False):
    app = Flask(__name__)

    # Basic config
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SWAGGER'] = {
        'title': 'FindNaija Lost & Found API',
        'uiversion': 3
    }

    if testing:
        # Use in-memory database for clean test runs
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # Use the persistent database in normal mode
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///findnaija.db'

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Enable Swagger UI
    Swagger(app)

    # Register routes
    from app.routes import main
    from app.api_routes import api_bp
    app.register_blueprint(main)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Auto-create tables in testing mode
    if testing:
        with app.app_context():
            db.create_all()

    return app
