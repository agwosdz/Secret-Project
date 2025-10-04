#!/usr/bin/env python3
"""
Settings Service for Piano LED Visualizer
Provides centralized, persistent configuration management with real-time synchronization
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SettingsService:
    """
    Centralized settings management service with database persistence
    and real-time WebSocket synchronization capabilities.
    """
    
    def __init__(self, db_path: Optional[str] = None, websocket_callback=None):
        """
        Initialize the settings service.
        
        Args:
            db_path: Path to SQLite database file
            websocket_callback: Callback function for WebSocket events
        """
        self.db_path = db_path or self._get_default_db_path()
        self.websocket_callback = websocket_callback
        self._init_database()
        self._load_default_settings()
        
    def _get_default_db_path(self) -> str:
        """Get the default database path."""
        backend_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
        return str(backend_dir / "settings.db")
    
    def _init_database(self):
        """Initialize the SQLite database with settings table."""
        try:
            with self._get_db_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category VARCHAR(50) NOT NULL,
                        key VARCHAR(100) NOT NULL,
                        value TEXT NOT NULL,
                        data_type VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(category, key)
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)')
                
                conn.commit()
                logger.info("Settings database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize settings database: {e}")
            raise
    
    @contextmanager
    def _get_db_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _load_default_settings(self):
        """Load default settings into the database if they don't exist."""
        default_settings = self._get_default_settings_schema()
        
        for category, settings in default_settings.items():
            for key, config in settings.items():
                if not self._setting_exists(category, key):
                    self._create_setting(category, key, config['default'], config['type'])
    
    def _get_default_settings_schema(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get the default settings schema with types and constraints."""
        return {
            'audio': {
                'enabled': {'type': 'boolean', 'default': False},
                'volume': {'type': 'number', 'default': 50, 'min': 0, 'max': 100},
                'inputDevice': {'type': 'string', 'default': 'default'},
                'gain': {'type': 'number', 'default': 1.0, 'min': 0, 'max': 2.0},
                'latencyMs': {'type': 'number', 'default': 50, 'min': 0, 'max': 500},
                'sampleRate': {'type': 'number', 'default': 44100},
                'bufferSize': {'type': 'number', 'default': 1024}
            },
            'piano': {
                'enabled': {'type': 'boolean', 'default': False},
                'octave': {'type': 'number', 'default': 4, 'min': 0, 'max': 8},
                'velocity_sensitivity': {'type': 'number', 'default': 64, 'min': 0, 'max': 127},
                'channel': {'type': 'number', 'default': 1, 'min': 1, 'max': 16}
            },
            'gpio': {
                'enabled': {'type': 'boolean', 'default': False},
                'pins': {'type': 'array', 'default': []},
                'debounce_time': {'type': 'number', 'default': 50, 'min': 0, 'max': 1000}
            },
            'led': {
                'enabled': {'type': 'boolean', 'default': False},
                'led_count': {'type': 'number', 'default': 88, 'min': 1, 'max': 1000},
                'max_led_count': {'type': 'number', 'default': 1000, 'min': 1, 'max': 1000},
                'brightness': {'type': 'number', 'default': 50, 'min': 0, 'max': 100},
                'led_type': {'type': 'string', 'default': 'WS2812B', 'enum': ['WS2812B', 'WS2813', 'WS2815', 'APA102', 'SK6812']},
                'led_orientation': {'type': 'string', 'default': 'normal', 'enum': ['normal', 'reversed']},
                'led_strip_type': {'type': 'string', 'default': 'WS2811_STRIP_GRB', 'enum': ['WS2811_STRIP_GRB', 'WS2811_STRIP_RGB', 'WS2811_STRIP_BRG', 'WS2811_STRIP_BGR']},
                'power_supply_voltage': {'type': 'number', 'default': 5.0, 'min': 3.0, 'max': 24.0},
                'power_supply_current': {'type': 'number', 'default': 10.0, 'min': 0.1, 'max': 100.0},
                'color_profile': {'type': 'string', 'default': 'Standard RGB', 'enum': ['Standard RGB', 'sRGB', 'Adobe RGB', 'Wide Gamut']},
                'performance_mode': {'type': 'string', 'default': 'Balanced', 'enum': ['Power Saving', 'Balanced', 'Performance', 'Maximum']},
                'gamma_correction': {'type': 'number', 'default': 2.2, 'min': 1.0, 'max': 3.0},
                'white_balance': {'type': 'object', 'default': {'r': 1.0, 'g': 1.0, 'b': 1.0}},
                'color_temperature': {'type': 'number', 'default': 6500, 'min': 2000, 'max': 10000},
                'dither_enabled': {'type': 'boolean', 'default': False},
                'update_rate': {'type': 'number', 'default': 60, 'min': 1, 'max': 120},
                'power_limiting_enabled': {'type': 'boolean', 'default': False},
                'max_power_watts': {'type': 'number', 'default': 100, 'min': 1, 'max': 1000},
                'thermal_protection_enabled': {'type': 'boolean', 'default': False},
                'max_temperature_celsius': {'type': 'number', 'default': 80, 'min': 40, 'max': 100},
                'data_pin': {'type': 'number', 'default': 18, 'min': 1, 'max': 40},
                'clock_pin': {'type': 'number', 'default': 19, 'min': 1, 'max': 40},
                'reverse_order': {'type': 'boolean', 'default': False},
                'color_mode': {'type': 'string', 'default': 'velocity', 'enum': ['rainbow', 'velocity', 'note', 'custom']},
                'colorScheme': {'type': 'string', 'default': 'rainbow'},
                'animationSpeed': {'type': 'number', 'default': 1.0, 'min': 0.1, 'max': 3.0},
                'ledCount': {'type': 'number', 'default': 246, 'min': 1, 'max': 300},
                'gpioPin': {'type': 'number', 'default': 19},
                'ledOrientation': {'type': 'string', 'default': 'normal', 'enum': ['normal', 'reversed']},
                'ledType': {'type': 'string', 'default': 'WS2812B'},
                'gammaCorrection': {'type': 'number', 'default': 2.2, 'min': 1.0, 'max': 3.0}
            },
            'hardware': {
                'auto_detect_midi': {'type': 'boolean', 'default': True},
                'auto_detect_gpio': {'type': 'boolean', 'default': True},
                'auto_detect_led': {'type': 'boolean', 'default': True},
                'midi_device_id': {'type': 'string', 'default': ''},
                'rtpmidi_enabled': {'type': 'boolean', 'default': False},
                'rtpmidi_port': {'type': 'number', 'default': 5004, 'min': 1024, 'max': 65535}
            },
            'system': {
                'theme': {'type': 'string', 'default': 'auto', 'enum': ['light', 'dark', 'auto']},
                'debug': {'type': 'boolean', 'default': False},
                'log_level': {'type': 'string', 'default': 'info', 'enum': ['debug', 'info', 'warn', 'error']},
                'auto_save': {'type': 'boolean', 'default': True},
                'backup_settings': {'type': 'boolean', 'default': True},
                'performanceMode': {'type': 'string', 'default': 'balanced', 'enum': ['power_save', 'balanced', 'performance']},
                'autoSave': {'type': 'boolean', 'default': True},
                'debugMode': {'type': 'boolean', 'default': False},
                'logLevel': {'type': 'string', 'default': 'INFO', 'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR']}
            },
            'user': {
                'name': {'type': 'string', 'default': 'User'},
                'email': {'type': 'string', 'default': ''},
                'preferences': {'type': 'object', 'default': {}},
                'favoriteSchemes': {'type': 'array', 'default': []},
                'recentConfigs': {'type': 'array', 'default': []},
                'lastUsedDevice': {'type': 'string', 'default': ''},
                'navigationCollapsed': {'type': 'boolean', 'default': False}
            },
            'upload': {
                'autoUpload': {'type': 'boolean', 'default': False},
                'rememberLastDirectory': {'type': 'boolean', 'default': True},
                'showFilePreview': {'type': 'boolean', 'default': True},
                'confirmBeforeReset': {'type': 'boolean', 'default': True},
                'lastUploadedFile': {'type': 'string', 'default': ''}
            },
            'ui': {
                'theme': {'type': 'string', 'default': 'auto', 'enum': ['light', 'dark', 'auto']},
                'reducedMotion': {'type': 'boolean', 'default': False},
                'showTooltips': {'type': 'boolean', 'default': True},
                'tooltipDelay': {'type': 'number', 'default': 300, 'min': 0, 'max': 2000},
                'animationSpeed': {'type': 'string', 'default': 'normal', 'enum': ['slow', 'normal', 'fast']}
            },
            'a11y': {
                'highContrast': {'type': 'boolean', 'default': False},
                'largeText': {'type': 'boolean', 'default': False},
                'keyboardNavigation': {'type': 'boolean', 'default': True},
                'screenReaderOptimized': {'type': 'boolean', 'default': False}
            },
            'help': {
                'showOnboarding': {'type': 'boolean', 'default': True},
                'showHints': {'type': 'boolean', 'default': True},
                'completedTours': {'type': 'array', 'default': []},
                'skippedTours': {'type': 'array', 'default': []},
                'tourCompleted': {'type': 'boolean', 'default': False}
            },
            'history': {
                'maxHistorySize': {'type': 'number', 'default': 50, 'min': 10, 'max': 200},
                'autosaveInterval': {'type': 'number', 'default': 30000, 'min': 5000, 'max': 300000},
                'persistHistory': {'type': 'boolean', 'default': True}
            }
        }
    
    def _setting_exists(self, category: str, key: str) -> bool:
        """Check if a setting exists in the database."""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    'SELECT 1 FROM settings WHERE category = ? AND key = ?',
                    (category, key)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking setting existence: {e}")
            return False
    
    def _create_setting(self, category: str, key: str, value: Any, data_type: str):
        """Create a new setting in the database."""
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    '''INSERT INTO settings (category, key, value, data_type) 
                       VALUES (?, ?, ?, ?)''',
                    (category, key, json.dumps(value), data_type)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error creating setting {category}.{key}: {e}")
            raise
    
    def get_setting(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a single setting value.
        
        Args:
            category: Setting category
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value or default
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    'SELECT value, data_type FROM settings WHERE category = ? AND key = ?',
                    (category, key)
                )
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row['value'])
                return default
        except Exception as e:
            logger.error(f"Error getting setting {category}.{key}: {e}")
            return default
    
    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """
        Set a single setting value.
        
        Args:
            category: Setting category
            key: Setting key
            value: Setting value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate the setting
            if not self._validate_setting(category, key, value):
                return False
            
            data_type = self._get_data_type(value)
            
            with self._get_db_connection() as conn:
                conn.execute(
                    '''INSERT OR REPLACE INTO settings 
                       (category, key, value, data_type, updated_at) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (category, key, json.dumps(value), data_type, datetime.now().isoformat())
                )
                conn.commit()
            
            # Broadcast the change via WebSocket
            self._broadcast_setting_change(category, key, value)
            
            logger.info(f"Setting updated: {category}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting {category}.{key}: {e}")
            return False
    
    def get_category_settings(self, category: str) -> Dict[str, Any]:
        """
        Get all settings for a specific category.
        
        Args:
            category: Setting category
            
        Returns:
            Dictionary of settings for the category
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    'SELECT key, value FROM settings WHERE category = ?',
                    (category,)
                )
                
                settings = {}
                for row in cursor.fetchall():
                    settings[row['key']] = json.loads(row['value'])
                
                return settings
        except Exception as e:
            logger.error(f"Error getting category settings {category}: {e}")
            return {}
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings organized by category.
        
        Returns:
            Dictionary of all settings organized by category
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute('SELECT category, key, value FROM settings')
                
                settings = {}
                for row in cursor.fetchall():
                    category = row['category']
                    if category not in settings:
                        settings[category] = {}
                    settings[category][row['key']] = json.loads(row['value'])
                
                return settings
        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}
    
    def update_settings(self, settings: Dict[str, Dict[str, Any]]) -> bool:
        """
        Update multiple settings at once.
        
        Args:
            settings: Dictionary of settings organized by category
            
        Returns:
            True if all updates successful, False otherwise
        """
        try:
            updated_settings = []
            
            for category, category_settings in settings.items():
                for key, value in category_settings.items():
                    if self.set_setting(category, key, value):
                        updated_settings.append((category, key, value))
            
            # Broadcast bulk update
            if updated_settings:
                self._broadcast_bulk_update(updated_settings)
            
            return len(updated_settings) == sum(len(cat_settings) for cat_settings in settings.values())
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    def reset_category(self, category: str) -> bool:
        """
        Reset all settings in a category to defaults.
        
        Args:
            category: Category to reset
            
        Returns:
            True if successful, False otherwise
        """
        try:
            default_settings = self._get_default_settings_schema()
            if category not in default_settings:
                logger.error(f"Unknown category: {category}")
                return False
            
            category_defaults = default_settings[category]
            updated_settings = []
            
            for key, config in category_defaults.items():
                if self.set_setting(category, key, config['default']):
                    updated_settings.append((category, key, config['default']))
            
            logger.info(f"Reset category {category} to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting category {category}: {e}")
            return False
    
    def reset_all_settings(self) -> bool:
        """
        Reset all settings to defaults.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            default_settings = self._get_default_settings_schema()
            
            for category in default_settings.keys():
                if not self.reset_category(category):
                    return False
            
            self._broadcast_settings_reset()
            logger.info("All settings reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting all settings: {e}")
            return False
    
    def export_settings(self) -> Dict[str, Any]:
        """
        Export all settings for backup/sharing.
        
        Returns:
            Dictionary containing all settings and metadata
        """
        try:
            settings = self.get_all_settings()
            return {
                'settings': settings,
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return {}
    
    def import_settings(self, settings_data: Dict[str, Any], validate: bool = True) -> bool:
        """
        Import settings from backup/sharing.
        
        Args:
            settings_data: Settings data to import
            validate: Whether to validate settings before import
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if 'settings' not in settings_data:
                logger.error("Invalid settings data format")
                return False
            
            settings = settings_data['settings']
            
            if validate:
                if not self._validate_settings_bulk(settings):
                    logger.error("Settings validation failed")
                    return False
            
            return self.update_settings(settings)
            
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False
    
    def _validate_setting(self, category: str, key: str, value: Any) -> bool:
        """Validate a single setting against schema."""
        try:
            schema = self._get_default_settings_schema()
            
            if category not in schema or key not in schema[category]:
                logger.warning(f"Unknown setting: {category}.{key}")
                return True  # Allow unknown settings for flexibility
            
            setting_config = schema[category][key]
            
            # Type validation
            expected_type = setting_config['type']
            if not self._validate_type(value, expected_type):
                logger.error(f"Type validation failed for {category}.{key}: expected {expected_type}, got {type(value).__name__}")
                return False
            
            # Range validation for numbers
            if expected_type == 'number':
                if 'min' in setting_config and value < setting_config['min']:
                    logger.error(f"Value {value} below minimum {setting_config['min']} for {category}.{key}")
                    return False
                if 'max' in setting_config and value > setting_config['max']:
                    logger.error(f"Value {value} above maximum {setting_config['max']} for {category}.{key}")
                    return False
            
            # Enum validation
            if 'enum' in setting_config and value not in setting_config['enum']:
                logger.error(f"Value {value} not in allowed values {setting_config['enum']} for {category}.{key}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating setting {category}.{key}: {e}")
            return False
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'boolean': bool,
            'array': list
        }
        
        if expected_type not in type_map:
            return True  # Unknown type, allow it
        
        expected_python_type = type_map[expected_type]
        return isinstance(value, expected_python_type)
    
    def _validate_settings_bulk(self, settings: Dict[str, Dict[str, Any]]) -> bool:
        """Validate multiple settings."""
        for category, category_settings in settings.items():
            for key, value in category_settings.items():
                if not self._validate_setting(category, key, value):
                    return False
        return True
    
    def _get_data_type(self, value: Any) -> str:
        """Get the data type string for a value."""
        if isinstance(value, str):
            return 'string'
        elif isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, list):
            return 'array'
        else:
            return 'object'
    
    def _broadcast_setting_change(self, category: str, key: str, value: Any):
        """Broadcast a single setting change via WebSocket."""
        if self.websocket_callback:
            try:
                self.websocket_callback('settings:update', {
                    'category': category,
                    'key': key,
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error broadcasting setting change: {e}")
    
    def _broadcast_bulk_update(self, updated_settings: List[tuple]):
        """Broadcast multiple setting changes via WebSocket."""
        if self.websocket_callback:
            try:
                changes = [
                    {'category': category, 'key': key, 'value': value}
                    for category, key, value in updated_settings
                ]
                self.websocket_callback('settings:bulk_update', {
                    'changes': changes,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error broadcasting bulk update: {e}")
    
    def _broadcast_settings_reset(self):
        """Broadcast settings reset event via WebSocket."""
        if self.websocket_callback:
            try:
                self.websocket_callback('settings:reset', {
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error broadcasting settings reset: {e}")