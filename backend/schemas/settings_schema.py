"""
Settings Schema Definition and Validation for Backend
Provides comprehensive validation for all settings categories
"""

from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
import re

@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    errors: Optional[List[str]] = None

class SettingsSchema:
    """Settings schema definitions and validation methods"""
    
    SCHEMA = {
        'piano': {
            'type': 'object',
            'required': ['enabled', 'octave'],
            'properties': {
                'enabled': {'type': 'boolean'},
                'octave': {'type': 'number', 'minimum': 0, 'maximum': 8},
                'velocity_sensitivity': {'type': 'number', 'minimum': 0, 'maximum': 127},
                'channel': {'type': 'number', 'minimum': 1, 'maximum': 16}
            }
        },
        
        'gpio': {
            'type': 'object',
            'required': ['enabled', 'pins'],
            'properties': {
                'enabled': {'type': 'boolean'},
                'pins': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'required': ['pin', 'mode', 'note'],
                        'properties': {
                            'pin': {'type': 'number', 'minimum': 1, 'maximum': 40},
                            'mode': {'type': 'string', 'enum': ['input', 'output']},
                            'note': {'type': 'number', 'minimum': 0, 'maximum': 127},
                            'pullup': {'type': 'boolean'}
                        }
                    }
                },
                'debounce_time': {'type': 'number', 'minimum': 0, 'maximum': 1000}
            }
        },
        
        'led': {
            'type': 'object',
            'required': ['enabled', 'count', 'brightness'],
            'properties': {
                'enabled': {'type': 'boolean'},
                'count': {'type': 'number', 'minimum': 1, 'maximum': 1000},
                'brightness': {'type': 'number', 'minimum': 0, 'maximum': 100},
                'color_temperature': {'type': 'number', 'minimum': 2000, 'maximum': 10000},
                'gamma_correction': {'type': 'number', 'minimum': 1.0, 'maximum': 3.0},
                'strip_type': {'type': 'string', 'enum': ['WS2812B', 'WS2811', 'APA102', 'SK6812']},
                'data_pin': {'type': 'number', 'minimum': 1, 'maximum': 40},
                'clock_pin': {'type': 'number', 'minimum': 1, 'maximum': 40},
                'reverse_order': {'type': 'boolean'},
                'color_mode': {'type': 'string', 'enum': ['rainbow', 'velocity', 'note', 'custom']}
            }
        },
        
        'audio': {
            'type': 'object',
            'required': ['enabled', 'volume'],
            'properties': {
                'enabled': {'type': 'boolean'},
                'volume': {'type': 'number', 'minimum': 0, 'maximum': 100},
                'sample_rate': {'type': 'number', 'enum': [22050, 44100, 48000, 96000]},
                'buffer_size': {'type': 'number', 'enum': [64, 128, 256, 512, 1024]},
                'latency': {'type': 'number', 'minimum': 0, 'maximum': 1000},
                'device_id': {'type': 'string'}
            }
        },
        
        'hardware': {
            'type': 'object',
            'required': ['auto_detect_midi', 'auto_detect_gpio', 'auto_detect_led'],
            'properties': {
                'auto_detect_midi': {'type': 'boolean'},
                'auto_detect_gpio': {'type': 'boolean'},
                'auto_detect_led': {'type': 'boolean'},
                'midi_device_id': {'type': 'string'},
                'rtpmidi_enabled': {'type': 'boolean'},
                'rtpmidi_port': {'type': 'number', 'minimum': 1024, 'maximum': 65535}
            }
        },
        
        'system': {
            'type': 'object',
            'required': ['theme', 'debug'],
            'properties': {
                'theme': {'type': 'string', 'enum': ['light', 'dark', 'auto']},
                'debug': {'type': 'boolean'},
                'log_level': {'type': 'string', 'enum': ['debug', 'info', 'warn', 'error']},
                'auto_save': {'type': 'boolean'},
                'backup_settings': {'type': 'boolean'}
            }
        },
        
        'user': {
            'type': 'object',
            'required': ['name', 'preferences'],
            'properties': {
                'name': {'type': 'string', 'maxLength': 100},
                'email': {'type': 'string', 'format': 'email'},
                'preferences': {
                    'type': 'object',
                    'properties': {
                        'show_tooltips': {'type': 'boolean'},
                        'auto_connect': {'type': 'boolean'},
                        'remember_window_size': {'type': 'boolean'}
                    }
                }
            }
        }
    }

    @classmethod
    def validate_setting(cls, category: str, key: str, value: Any) -> ValidationResult:
        """Validate a single setting value"""
        if category not in cls.SCHEMA:
            return ValidationResult(valid=False, error=f"Unknown category: {category}")
        
        category_schema = cls.SCHEMA[category]
        if key not in category_schema.get('properties', {}):
            return ValidationResult(valid=False, error=f"Unknown property: {category}.{key}")
        
        property_schema = category_schema['properties'][key]
        return cls._validate_value(value, property_schema, f"{category}.{key}")

    @classmethod
    def validate_category(cls, category: str, data: Dict[str, Any]) -> ValidationResult:
        """Validate an entire settings category"""
        if category not in cls.SCHEMA:
            return ValidationResult(valid=False, error=f"Unknown category: {category}")
        
        category_schema = cls.SCHEMA[category]
        return cls._validate_object(data, category_schema, category)

    @classmethod
    def validate_all_settings(cls, settings: Dict[str, Any]) -> ValidationResult:
        """Validate all settings"""
        errors = []
        
        for category, data in settings.items():
            result = cls.validate_category(category, data)
            if not result.valid:
                errors.append(result.error)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors if errors else None
        )

    @classmethod
    def get_category_defaults(cls, category: str) -> Dict[str, Any]:
        """Get default values for a category"""
        if category not in cls.SCHEMA:
            return {}
        
        category_schema = cls.SCHEMA[category]
        defaults = {}
        
        for key, schema in category_schema.get('properties', {}).items():
            defaults[key] = cls._get_default_value(schema)
        
        return defaults

    @classmethod
    def get_all_defaults(cls) -> Dict[str, Dict[str, Any]]:
        """Get all default settings"""
        defaults = {}
        for category in cls.SCHEMA.keys():
            defaults[category] = cls.get_category_defaults(category)
        return defaults

    @classmethod
    def _validate_value(cls, value: Any, schema: Dict[str, Any], path: str) -> ValidationResult:
        """Validate a single value against its schema"""
        if value is None:
            return ValidationResult(valid=False, error=f"{path} is required")
        
        # Type validation
        expected_type = schema.get('type')
        if expected_type == 'boolean' and not isinstance(value, bool):
            return ValidationResult(valid=False, error=f"{path} must be a boolean")
        
        if expected_type == 'number' and not isinstance(value, (int, float)):
            return ValidationResult(valid=False, error=f"{path} must be a number")
        
        if expected_type == 'string' and not isinstance(value, str):
            return ValidationResult(valid=False, error=f"{path} must be a string")
        
        if expected_type == 'array' and not isinstance(value, list):
            return ValidationResult(valid=False, error=f"{path} must be an array")
        
        if expected_type == 'object' and not isinstance(value, dict):
            return ValidationResult(valid=False, error=f"{path} must be an object")
        
        # Range validation for numbers
        if expected_type == 'number':
            minimum = schema.get('minimum')
            maximum = schema.get('maximum')
            
            if minimum is not None and value < minimum:
                return ValidationResult(valid=False, error=f"{path} must be >= {minimum}")
            
            if maximum is not None and value > maximum:
                return ValidationResult(valid=False, error=f"{path} must be <= {maximum}")
        
        # Enum validation
        enum_values = schema.get('enum')
        if enum_values and value not in enum_values:
            return ValidationResult(valid=False, error=f"{path} must be one of: {', '.join(map(str, enum_values))}")
        
        # String length validation
        if expected_type == 'string':
            max_length = schema.get('maxLength')
            if max_length and len(value) > max_length:
                return ValidationResult(valid=False, error=f"{path} must be <= {max_length} characters")
            
            # Email format validation
            if schema.get('format') == 'email':
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    return ValidationResult(valid=False, error=f"{path} must be a valid email address")
        
        # Array validation
        if expected_type == 'array':
            items_schema = schema.get('items')
            if items_schema:
                for i, item in enumerate(value):
                    item_result = cls._validate_value(item, items_schema, f"{path}[{i}]")
                    if not item_result.valid:
                        return item_result
        
        # Object validation
        if expected_type == 'object':
            properties = schema.get('properties')
            if properties:
                return cls._validate_object(value, schema, path)
        
        return ValidationResult(valid=True)

    @classmethod
    def _validate_object(cls, obj: Dict[str, Any], schema: Dict[str, Any], path: str) -> ValidationResult:
        """Validate an object against its schema"""
        # Check required properties
        required = schema.get('required', [])
        for required_prop in required:
            if required_prop not in obj:
                return ValidationResult(valid=False, error=f"{path}.{required_prop} is required")
        
        # Validate each property
        properties = schema.get('properties', {})
        for key, value in obj.items():
            if key in properties:
                prop_schema = properties[key]
                result = cls._validate_value(value, prop_schema, f"{path}.{key}")
                if not result.valid:
                    return result
        
        return ValidationResult(valid=True)

    @classmethod
    def _get_default_value(cls, schema: Dict[str, Any]) -> Any:
        """Get default value for a schema property"""
        if 'default' in schema:
            return schema['default']
        
        schema_type = schema.get('type')
        if schema_type == 'boolean':
            return False
        elif schema_type == 'number':
            return schema.get('minimum', 0)
        elif schema_type == 'string':
            enum_values = schema.get('enum')
            return enum_values[0] if enum_values else ''
        elif schema_type == 'array':
            return []
        elif schema_type == 'object':
            return {}
        else:
            return None


# Convenience functions for easy import
def validate_setting(category: str, key: str, value: Any) -> ValidationResult:
    """Validate a single setting"""
    return SettingsSchema.validate_setting(category, key, value)

def validate_category(category: str, data: Dict[str, Any]) -> ValidationResult:
    """Validate a settings category"""
    return SettingsSchema.validate_category(category, data)

def validate_all_settings(settings: Dict[str, Any]) -> ValidationResult:
    """Validate all settings"""
    return SettingsSchema.validate_all_settings(settings)

def get_category_defaults(category: str) -> Dict[str, Any]:
    """Get default values for a category"""
    return SettingsSchema.get_category_defaults(category)

def get_all_defaults() -> Dict[str, Dict[str, Any]]:
    """Get all default settings"""
    return SettingsSchema.get_all_defaults()