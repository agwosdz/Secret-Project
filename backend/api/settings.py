#!/usr/bin/env python3
"""
Settings API endpoints for Piano LED Visualizer
Provides RESTful API access to the centralized settings service
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import settings service - will be initialized in app.py
def get_settings_service():
    """Get the global settings service instance"""
    from app import settings_service
    return settings_service

# Create the blueprint
settings_bp = Blueprint('settings_api', __name__, url_prefix='/api/settings')

@settings_bp.route('/', methods=['GET'])
def get_all_settings():
    """Get all settings organized by category"""
    try:
        settings_service = get_settings_service()
        settings = settings_service.get_all_settings()
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting all settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to retrieve settings'
        }), 500

@settings_bp.route('/<category>', methods=['GET'])
def get_category_settings(category):
    """Get all settings for a specific category"""
    try:
        settings_service = get_settings_service()
        settings = settings_service.get_category_settings(category)
        if settings is None:
            return jsonify({
                'error': 'Not Found',
                'message': f'Category "{category}" not found'
            }), 404
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting category settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'Failed to retrieve settings for category "{category}"'
        }), 500

@settings_bp.route('/<category>/<key>', methods=['GET'])
def get_setting(category, key):
    """Get a specific setting value"""
    try:
        settings_service = get_settings_service()
        value = settings_service.get_setting(category, key)
        if value is None:
            return jsonify({
                'error': 'Not Found',
                'message': f'Setting "{category}.{key}" not found'
            }), 404
        return jsonify({'value': value}), 200
    except Exception as e:
        logger.error(f"Error getting setting: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'Failed to retrieve setting "{category}.{key}"'
        }), 500

@settings_bp.route('/<category>/<key>', methods=['PUT'])
def set_setting(category, key):
    """Set a specific setting value"""
    try:
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request must include "value" field'
            }), 400
        
        settings_service = get_settings_service()
        success = settings_service.set_setting(category, key, data['value'])
        if not success:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Failed to set setting "{category}.{key}"'
            }), 400
        
        return jsonify({'message': 'Setting updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error setting value: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'Failed to set setting "{category}.{key}"'
        }), 500

@settings_bp.route('/', methods=['PUT'])
@settings_bp.route('/bulk', methods=['POST'])
def update_multiple_settings():
    """Update multiple settings at once"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No settings data provided'
            }), 400
        
        settings_service = get_settings_service()
        success = settings_service.update_settings(data)
        if not success:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Failed to update settings'
            }), 400
        
        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to update settings'
        }), 500

@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset all settings to defaults"""
    try:
        data = request.get_json() or {}
        category = data.get('category')
        
        settings_service = get_settings_service()
        settings_service.reset_settings(category)
        
        message = f'Settings for category "{category}" reset to defaults' if category else 'All settings reset to defaults'
        return jsonify({'message': message}), 200
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to reset settings'
        }), 500

@settings_bp.route('/export', methods=['GET'])
def export_settings():
    """Export all settings as JSON"""
    try:
        settings_service = get_settings_service()
        settings = settings_service.export_settings()
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error exporting settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to export settings'
        }), 500

@settings_bp.route('/import', methods=['POST'])
def import_settings():
    """Import settings from JSON"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No settings data provided'
            }), 400
        
        settings_service = get_settings_service()
        success = settings_service.import_settings(data)
        if not success:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Failed to import settings'
            }), 400
        
        return jsonify({'message': 'Settings imported successfully'}), 200
    except Exception as e:
        logger.error(f"Error importing settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to import settings'
        }), 500

@settings_bp.route('/validate', methods=['POST'])
def validate_settings():
    """Validate settings data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No settings data provided'
            }), 400
        
        settings_service = get_settings_service()
        is_valid, errors = settings_service.validate_settings(data)
        
        return jsonify({
            'valid': is_valid,
            'errors': errors
        }), 200
    except Exception as e:
        logger.error(f"Error validating settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to validate settings'
        }), 500

@settings_bp.route('/schema', methods=['GET'])
def get_settings_schema():
    """Get the settings schema"""
    try:
        settings_service = get_settings_service()
        schema = settings_service.get_schema()
        return jsonify(schema), 200
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to retrieve settings schema'
        }), 500

def create_settings_api(settings_service):
    """Create settings API blueprint with the provided settings service."""
    return settings_bp