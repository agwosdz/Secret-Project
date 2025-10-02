/**
 * Settings Schema Definition and Validation
 * Provides comprehensive validation for all settings categories
 */

// Schema definitions for each settings category
export const settingsSchema = {
    piano: {
        type: 'object',
        required: ['enabled', 'octave'],
        properties: {
            enabled: { type: 'boolean' },
            octave: { type: 'number', minimum: 0, maximum: 8 },
            velocity_sensitivity: { type: 'number', minimum: 0, maximum: 127 },
            channel: { type: 'number', minimum: 1, maximum: 16 }
        }
    },
    
    gpio: {
        type: 'object',
        required: ['enabled', 'pins'],
        properties: {
            enabled: { type: 'boolean' },
            pins: {
                type: 'array',
                items: {
                    type: 'object',
                    required: ['pin', 'mode', 'note'],
                    properties: {
                        pin: { type: 'number', minimum: 1, maximum: 40 },
                        mode: { type: 'string', enum: ['input', 'output'] },
                        note: { type: 'number', minimum: 0, maximum: 127 },
                        pullup: { type: 'boolean' }
                    }
                }
            },
            debounce_time: { type: 'number', minimum: 0, maximum: 1000 }
        }
    },
    
    led: {
        type: 'object',
        required: ['enabled', 'count', 'brightness'],
        properties: {
            enabled: { type: 'boolean' },
            count: { type: 'number', minimum: 1, maximum: 1000 },
            brightness: { type: 'number', minimum: 0, maximum: 100 },
            color_temperature: { type: 'number', minimum: 2000, maximum: 10000 },
            gamma_correction: { type: 'number', minimum: 1.0, maximum: 3.0 },
            strip_type: { type: 'string', enum: ['WS2812B', 'WS2811', 'APA102', 'SK6812'] },
            data_pin: { type: 'number', minimum: 1, maximum: 40 },
            clock_pin: { type: 'number', minimum: 1, maximum: 40 },
            reverse_order: { type: 'boolean' },
            color_mode: { type: 'string', enum: ['rainbow', 'velocity', 'note', 'custom'] }
        }
    },
    
    audio: {
        type: 'object',
        required: ['enabled', 'volume'],
        properties: {
            enabled: { type: 'boolean' },
            volume: { type: 'number', minimum: 0, maximum: 100 },
            sample_rate: { type: 'number', enum: [22050, 44100, 48000, 96000] },
            buffer_size: { type: 'number', enum: [64, 128, 256, 512, 1024] },
            latency: { type: 'number', minimum: 0, maximum: 1000 },
            device_id: { type: 'string' }
        }
    },
    
    hardware: {
        type: 'object',
        required: ['auto_detect_midi', 'auto_detect_gpio', 'auto_detect_led'],
        properties: {
            auto_detect_midi: { type: 'boolean' },
            auto_detect_gpio: { type: 'boolean' },
            auto_detect_led: { type: 'boolean' },
            midi_device_id: { type: 'string' },
            rtpmidi_enabled: { type: 'boolean' },
            rtpmidi_port: { type: 'number', minimum: 1024, maximum: 65535 }
        }
    },
    
    system: {
        type: 'object',
        required: ['theme', 'debug'],
        properties: {
            theme: { type: 'string', enum: ['light', 'dark', 'auto'] },
            debug: { type: 'boolean' },
            log_level: { type: 'string', enum: ['debug', 'info', 'warn', 'error'] },
            auto_save: { type: 'boolean' },
            backup_settings: { type: 'boolean' }
        }
    },
    
    user: {
        type: 'object',
        required: ['name', 'preferences'],
        properties: {
            name: { type: 'string', maxLength: 100 },
            email: { type: 'string', format: 'email' },
            preferences: {
                type: 'object',
                properties: {
                    show_tooltips: { type: 'boolean' },
                    auto_connect: { type: 'boolean' },
                    remember_window_size: { type: 'boolean' }
                }
            }
        }
    }
};

/**
 * Validate a single setting value
 */
export function validateSetting(category, key, value) {
    const categorySchema = settingsSchema[category];
    if (!categorySchema) {
        return { valid: false, error: `Unknown category: ${category}` };
    }
    
    const propertySchema = categorySchema.properties[key];
    if (!propertySchema) {
        return { valid: false, error: `Unknown property: ${category}.${key}` };
    }
    
    return validateValue(value, propertySchema, `${category}.${key}`);
}

/**
 * Validate an entire settings category
 */
export function validateCategory(category, data) {
    const categorySchema = settingsSchema[category];
    if (!categorySchema) {
        return { valid: false, error: `Unknown category: ${category}` };
    }
    
    return validateObject(data, categorySchema, category);
}

/**
 * Validate all settings
 */
export function validateAllSettings(settings) {
    const errors = [];
    
    for (const [category, data] of Object.entries(settings)) {
        const result = validateCategory(category, data);
        if (!result.valid) {
            errors.push(result.error);
        }
    }
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}

/**
 * Get default values for a category
 */
export function getCategoryDefaults(category) {
    const categorySchema = settingsSchema[category];
    if (!categorySchema) {
        return {};
    }
    
    const defaults = {};
    for (const [key, schema] of Object.entries(categorySchema.properties)) {
        defaults[key] = getDefaultValue(schema);
    }
    
    return defaults;
}

/**
 * Get all default settings
 */
export function getAllDefaults() {
    const defaults = {};
    for (const category of Object.keys(settingsSchema)) {
        defaults[category] = getCategoryDefaults(category);
    }
    return defaults;
}

// Helper functions for validation
function validateValue(value, schema, path) {
    if (value === null || value === undefined) {
        return { valid: false, error: `${path} is required` };
    }
    
    // Type validation
    if (schema.type === 'boolean' && typeof value !== 'boolean') {
        return { valid: false, error: `${path} must be a boolean` };
    }
    
    if (schema.type === 'number' && typeof value !== 'number') {
        return { valid: false, error: `${path} must be a number` };
    }
    
    if (schema.type === 'string' && typeof value !== 'string') {
        return { valid: false, error: `${path} must be a string` };
    }
    
    if (schema.type === 'array' && !Array.isArray(value)) {
        return { valid: false, error: `${path} must be an array` };
    }
    
    if (schema.type === 'object' && typeof value !== 'object') {
        return { valid: false, error: `${path} must be an object` };
    }
    
    // Range validation for numbers
    if (schema.type === 'number') {
        if (schema.minimum !== undefined && value < schema.minimum) {
            return { valid: false, error: `${path} must be >= ${schema.minimum}` };
        }
        if (schema.maximum !== undefined && value > schema.maximum) {
            return { valid: false, error: `${path} must be <= ${schema.maximum}` };
        }
    }
    
    // Enum validation
    if (schema.enum && !schema.enum.includes(value)) {
        return { valid: false, error: `${path} must be one of: ${schema.enum.join(', ')}` };
    }
    
    // String length validation
    if (schema.type === 'string') {
        if (schema.maxLength && value.length > schema.maxLength) {
            return { valid: false, error: `${path} must be <= ${schema.maxLength} characters` };
        }
    }
    
    // Array validation
    if (schema.type === 'array' && schema.items) {
        for (let i = 0; i < value.length; i++) {
            const itemResult = validateValue(value[i], schema.items, `${path}[${i}]`);
            if (!itemResult.valid) {
                return itemResult;
            }
        }
    }
    
    // Object validation
    if (schema.type === 'object' && schema.properties) {
        return validateObject(value, schema, path);
    }
    
    return { valid: true };
}

function validateObject(obj, schema, path) {
    // Check required properties
    if (schema.required) {
        for (const requiredProp of schema.required) {
            if (!(requiredProp in obj)) {
                return { valid: false, error: `${path}.${requiredProp} is required` };
            }
        }
    }
    
    // Validate each property
    if (schema.properties) {
        for (const [key, value] of Object.entries(obj)) {
            const propSchema = schema.properties[key];
            if (propSchema) {
                const result = validateValue(value, propSchema, `${path}.${key}`);
                if (!result.valid) {
                    return result;
                }
            }
        }
    }
    
    return { valid: true };
}

function getDefaultValue(schema) {
    if (schema.default !== undefined) {
        return schema.default;
    }
    
    switch (schema.type) {
        case 'boolean':
            return false;
        case 'number':
            return schema.minimum || 0;
        case 'string':
            return schema.enum ? schema.enum[0] : '';
        case 'array':
            return [];
        case 'object':
            return {};
        default:
            return null;
    }
}