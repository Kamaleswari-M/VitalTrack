from flask import Flask, Blueprint, render_template, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
import json
import os

# Constants for Swagger UI
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

def create_swagger_json():
    """Create swagger.json from OpenAPI YAML"""
    yaml_file = os.path.join('docs', 'openapi.yaml')
    with open(yaml_file, 'r') as f:
        swagger_data = yaml.safe_load(f)
    
    # Save as JSON
    json_file = os.path.join('static', 'swagger.json')
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    with open(json_file, 'w') as f:
        json.dump(swagger_data, f, indent=2)

def init_swagger_ui(app):
    """Initialize Swagger UI with Flask app"""
    # Create swagger.json from YAML
    create_swagger_json()
    
    # Configure Swagger UI
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Vital Watch API Documentation",
            'layout': "BaseLayout",
            'deepLinking': True,
            'showExtensions': True,
            'showCommonExtensions': True,
            'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
        }
    )
    
    # Register blueprint
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    
    # Serve swagger.json
    @app.route(API_URL)
    def send_swagger_json():
        return send_from_directory('static', 'swagger.json')

swagger_bp = Blueprint('swagger', __name__, url_prefix='/swagger')

# Load OpenAPI spec
def load_swagger_spec():
    spec_path = os.path.join(os.path.dirname(__file__), 'docs', 'openapi.yaml')
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)

@swagger_bp.route('/')
def swagger_ui():
    """Serve custom Swagger UI"""
    return render_template('swagger.html')

@swagger_bp.route('/spec')
def send_swagger_json_custom():
    """Serve OpenAPI specification"""
    return jsonify(load_swagger_spec())

@swagger_bp.route('/oauth2-redirect.html')
def oauth2_redirect():
    """Serve OAuth2 redirect page for Swagger UI"""
    return send_from_directory('static', 'oauth2-redirect.html')
