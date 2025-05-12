import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from models import db
from auth import login_manager
from auth import authenticate_user
from database import init_db, get_connection_string
import json

def create_app():
    app = Flask(__name__)
    
    # Configure the application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_jjm_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = get_connection_string()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.data_management import data_management_bp
    # Historical Progress blueprint removed as requested
    from blueprints.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(data_management_bp, url_prefix='/data-management')
    # Historical Progress blueprint removed as requested
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # Root route redirects to dashboard or login
    @app.route('/')
    def index():
        return redirect(url_for('dashboard.index'))
    
    # Handle 404 errors
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404
    
    # Handle 500 errors
    @app.errorhandler(500)
    def server_error(e):
        return render_template('error/500.html'), 500
    
    # Custom template filters
    @app.template_filter('tojson_pretty')
    def tojson_pretty(obj):
        return json.dumps(obj, indent=4)
    
    return app

if __name__ == '__main__':
    app = create_app()
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)