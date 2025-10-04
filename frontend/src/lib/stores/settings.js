/**
 * Centralized Settings Store for Piano LED Visualizer
 * Provides reactive settings management with WebSocket synchronization
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { 
    validateSetting, 
    validateCategory, 
    validateAllSettings, 
    getCategoryDefaults, 
    getAllDefaults 
} from '../schemas/settingsSchema.js';

// Auto-save mechanism
let autoSaveTimeout = null;
const AUTO_SAVE_DELAY = 2000; // 2 seconds

/**
 * Migrate settings from old structure to new consolidated structure
 */
function migrateSettingsStructure(settings) {
    // Check if this is already the new structure
    if (settings && typeof settings === 'object' && 
        (settings.led || settings.piano || settings.audio || settings.gpio || settings.hardware)) {
        return settings;
    }

    // Legacy field mappings for backward compatibility
    const fieldMappings = {
        // LED settings
        'ledCount': ['led', 'led_count'],
        'brightness': ['led', 'brightness'],
        'colorScheme': ['led', 'colorScheme'],
        'animationSpeed': ['led', 'animationSpeed'],
        'gpioPin': ['led', 'gpioPin'],
        'ledOrientation': ['led', 'ledOrientation'],
        'ledType': ['led', 'ledType'],
        'gammaCorrection': ['led', 'gammaCorrection'],
        
        // Piano settings
        'pianoOctave': ['piano', 'octave'],
        'velocitySensitivity': ['piano', 'velocity_sensitivity'],
        'pianoChannel': ['piano', 'channel'],
        
        // Audio settings
        'audioEnabled': ['audio', 'enabled'],
        'audioVolume': ['audio', 'volume'],
        'audioInputDevice': ['audio', 'inputDevice'],
        'audioGain': ['audio', 'gain'],
        
        // GPIO settings
        'gpioPins': ['gpio', 'pins'],
        'gpioDebounce': ['gpio', 'debounce_time'],
        'gpioDma': ['gpio', 'dma_channel'],
        
        // Hardware settings
        'hardwareType': ['hardware', 'type'],
        'boardRevision': ['hardware', 'board_revision']
    };

    const migratedSettings = {};
    
    // Initialize category objects
    const categories = ['led', 'piano', 'audio', 'gpio', 'hardware'];
    categories.forEach(category => {
        migratedSettings[category] = {};
    });

    // Migrate flat fields to nested structure
    for (const [flatKey, value] of Object.entries(settings)) {
        const mapping = fieldMappings[flatKey];
        if (mapping) {
            const [category, nestedKey] = mapping;
            migratedSettings[category][nestedKey] = value;
        } else {
            // Keep unmapped fields at top level for now
            migratedSettings[flatKey] = value;
        }
    }

    // Fill in defaults for missing required fields
    const defaults = getAllDefaults();
    categories.forEach(category => {
        if (defaults[category]) {
            migratedSettings[category] = {
                ...defaults[category],
                ...migratedSettings[category]
            };
        }
    });

    console.log('Migrated settings from flat to nested structure:', migratedSettings);
    return migratedSettings;
}

/**
 * Consolidate settings from multiple localStorage keys into unified structure
 */
function consolidateStorageData() {
    if (!browser) return {};
    
    const consolidatedSettings = {};
    
    try {
        // Load main settings
        const mainSettings = localStorage.getItem('piano-led-settings');
        if (mainSettings) {
            const parsed = JSON.parse(mainSettings);
            Object.assign(consolidatedSettings, parsed);
        }
        
        // Load preferences
        const preferences = localStorage.getItem('midi-visualizer-preferences');
        if (preferences) {
            const parsed = JSON.parse(preferences);
            
            // Map preferences to new structure
            if (parsed.upload) consolidatedSettings.upload = parsed.upload;
            if (parsed.ui) consolidatedSettings.ui = parsed.ui;
            if (parsed.a11y) consolidatedSettings.a11y = parsed.a11y;
            if (parsed.help) consolidatedSettings.help = parsed.help;
            if (parsed.history) consolidatedSettings.history = parsed.history;
        }
        
        // Load help preferences
        const helpPrefs = localStorage.getItem('help-preferences');
        if (helpPrefs) {
            const parsed = JSON.parse(helpPrefs);
            if (!consolidatedSettings.help) consolidatedSettings.help = {};
            Object.assign(consolidatedSettings.help, parsed);
        }
        
        // Load tour completion state
        const tourCompleted = localStorage.getItem('tour-completed');
        if (tourCompleted === 'true') {
            if (!consolidatedSettings.help) consolidatedSettings.help = {};
            consolidatedSettings.help.tourCompleted = true;
        }
        
        // Load last uploaded file
        const lastFile = localStorage.getItem('lastUploadedFile');
        if (lastFile) {
            if (!consolidatedSettings.upload) consolidatedSettings.upload = {};
            consolidatedSettings.upload.lastUploadedFile = lastFile;
        }
        
        console.log('Consolidated settings from multiple localStorage keys:', consolidatedSettings);
        return consolidatedSettings;
        
    } catch (error) {
        console.error('Error consolidating storage data:', error);
        return {};
    }
}

/**
 * Clean up old localStorage keys after successful consolidation
 */
function cleanupOldStorageKeys() {
    if (!browser) return;
    
    try {
        const keysToRemove = [
            'midi-visualizer-preferences',
            'help-preferences', 
            'tour-completed',
            'lastUploadedFile'
        ];
        
        keysToRemove.forEach(key => {
            if (localStorage.getItem(key)) {
                localStorage.removeItem(key);
                console.log(`Cleaned up old localStorage key: ${key}`);
            }
        });
    } catch (error) {
        console.error('Error cleaning up old storage keys:', error);
    }
}

// Enhanced settings store with persistence
/**
 * Merge settings with defaults to ensure all required fields are present
 */
function mergeWithDefaults(settings, defaults) {
    const merged = {};
    
    // Start with defaults
    for (const [category, categoryDefaults] of Object.entries(defaults)) {
        merged[category] = { ...categoryDefaults };
        
        // Merge in actual settings if they exist
        if (settings[category] && typeof settings[category] === 'object') {
            merged[category] = {
                ...merged[category],
                ...settings[category]
            };
        }
    }
    
    // Add any additional categories from settings that aren't in defaults
    for (const [category, categorySettings] of Object.entries(settings)) {
        if (!merged[category]) {
            merged[category] = categorySettings;
        }
    }
    
    return merged;
}

export const settings = writable({}, (set) => {
    // Load and consolidate settings from multiple sources on initialization
    if (browser) {
        try {
            // First, consolidate data from multiple localStorage keys
            const consolidatedData = consolidateStorageData();
            
            // Then migrate the structure if needed
            const migratedSettings = migrateSettingsStructure(consolidatedData);
            
            // Merge with defaults to ensure completeness
            const defaults = getAllDefaults();
            const finalSettings = mergeWithDefaults(migratedSettings, defaults);
            
            console.log('Initialized settings with consolidated and migrated data:', finalSettings);
            set(finalSettings);
            
            // Save the consolidated settings to the main key
            localStorage.setItem('piano-led-settings', JSON.stringify(finalSettings));
            
            // Clean up old localStorage keys after successful consolidation
            if (Object.keys(consolidatedData).length > 0) {
                cleanupOldStorageKeys();
                console.log('Cleaned up fragmented localStorage keys');
            }
            
        } catch (error) {
            console.error('Failed to load and consolidate settings:', error);
            // Fallback to defaults if consolidation fails
            const defaults = getAllDefaults();
            set(defaults);
        }
    }
    
    return () => {
        // Cleanup function
        if (autoSaveTimeout) {
            clearTimeout(autoSaveTimeout);
        }
    };
});

// Subscribe to settings changes for auto-save
if (browser) {
    settings.subscribe((currentSettings) => {
        // Clear existing timeout
        if (autoSaveTimeout) {
            clearTimeout(autoSaveTimeout);
        }
        
        // Set new timeout for auto-save
        autoSaveTimeout = setTimeout(() => {
            try {
                localStorage.setItem('piano-led-settings', JSON.stringify(currentSettings));
                console.log('Auto-saved settings to localStorage');
            } catch (error) {
                console.error('Failed to auto-save settings to localStorage:', error);
            }
        }, AUTO_SAVE_DELAY);
    });
}
export const settingsLoading = writable(false);
export const settingsError = writable(null);

// Derived stores for specific categories with proper defaults
export const ledSettings = derived(settings, $settings => ({
    enabled: false,
    count: 60,
    brightness: 100,
    color_temperature: 6500,
    gamma_correction: 2.2,
    ...($settings.led || {})
}));

export const audioSettings = derived(settings, $settings => ({
    enabled: true,
    volume: 100,
    ...($settings.audio || {})
}));

export const pianoSettings = derived(settings, $settings => ({
    enabled: true,
    octave: 4,
    ...($settings.piano || {})
}));

export const gpioSettings = derived(settings, $settings => ({
    enabled: false,
    pins: [],
    ...($settings.gpio || {})
}));

export const hardwareSettings = derived(settings, $settings => ({
    auto_detect_midi: true,
    auto_detect_gpio: false,
    auto_detect_led: false,
    ...($settings.hardware || {})
}));

export const systemSettings = derived(settings, $settings => ({
    theme: 'dark',
    debug: false,
    ...($settings.system || {})
}));

export const userSettings = derived(settings, $settings => ({
    name: '',
    preferences: {},
    ...($settings.user || {})
}));

// Settings API class
class SettingsAPI {
    constructor() {
        this.baseUrl = '/api/settings';
        this.socket = null;
        this.initialized = false;
        
        if (browser) {
            this.initializeWebSocket();
        }
    }

    initializeWebSocket() {
        // Initialize WebSocket connection for real-time updates
        if (browser && typeof io !== 'undefined') {
            try {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    console.log('Settings WebSocket connected');
                });
                
                this.socket.on('disconnect', () => {
                    console.log('Settings WebSocket disconnected');
                });
                
                this.socket.on('setting_changed', (data) => {
                    console.log('Received setting change:', data);
                    this.handleSettingChange(data);
                });
                
                this.socket.on('settings_bulk_update', (data) => {
                    console.log('Received bulk settings update:', data);
                    this.handleBulkUpdate(data);
                });
                
                this.socket.on('settings_reset', (data) => {
                    console.log('Received settings reset:', data);
                    if (data && data.category) {
                        this.handleCategoryReset(data.category);
                    } else {
                        this.loadAllSettings();
                    }
                });
                
                this.socket.on('error', (error) => {
                    console.error('Settings WebSocket error:', error);
                    settingsError.set(`WebSocket error: ${error.message || error}`);
                });
                
            } catch (error) {
                console.error('Failed to initialize WebSocket:', error);
            }
        }
    }

    handleSettingChange(data) {
        if (data && data.category && data.key !== undefined && data.value !== undefined) {
            // Validate the incoming setting
            const validationResult = validateSetting(data.category, data.key, data.value);
            if (!validationResult.valid) {
                console.error('Invalid setting received via WebSocket:', validationResult.error);
                return;
            }

            settings.update(currentSettings => {
                const updated = { ...currentSettings };
                if (!updated[data.category]) {
                    updated[data.category] = {};
                }
                updated[data.category][data.key] = data.value;
                console.log(`Updated setting ${data.category}.${data.key} to:`, data.value);
                return updated;
            });
        } else {
            console.warn('Invalid setting change data received:', data);
        }
    }

    handleBulkUpdate(data) {
        if (data && typeof data === 'object') {
            // Validate all settings in the bulk update
            const validationResult = validateAllSettings(data);
            if (!validationResult.valid) {
                console.error('Invalid settings received via WebSocket bulk update:', validationResult.errors);
                return;
            }

            settings.update(currentSettings => {
                const updated = { ...currentSettings, ...data };
                console.log('Applied bulk settings update:', updated);
                return updated;
            });
        } else {
            console.warn('Invalid bulk update data received:', data);
        }
    }

    handleCategoryReset(category) {
        if (category) {
            // Get default values for the category
            const categoryDefaults = getCategoryDefaults(category);
            if (!categoryDefaults || Object.keys(categoryDefaults).length === 0) {
                console.error(`No defaults found for category: ${category}`);
                return;
            }

            settings.update(currentSettings => {
                const updated = { ...currentSettings };
                updated[category] = { ...categoryDefaults };
                console.log(`Reset category ${category} to defaults`);
                return updated;
            });
        }
    }

    async loadAllSettings() {
        try {
            settingsLoading.set(true);
            settingsError.set(null);
            console.log('loadAllSettings: Starting to load settings...');
            
            // Fetch settings from server
            const response = await fetch('/api/settings');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const serverSettings = await response.json();
            console.log('loadAllSettings: Server settings received:', JSON.stringify(serverSettings, null, 2));
            
            // Validate server settings
            const validation = validateAllSettings(serverSettings);
            console.log('loadAllSettings: Server settings validation:', validation);
            
            if (validation.valid) {
                // Merge with defaults to ensure all required fields are present
                const defaultSettings = getAllDefaults();
                console.log('loadAllSettings: Default settings:', JSON.stringify(defaultSettings, null, 2));
                
                const mergedSettings = mergeWithDefaults(serverSettings, defaultSettings);
                console.log('loadAllSettings: Merged settings:', JSON.stringify(mergedSettings, null, 2));
                
                // Update the settings store
                settings.set(mergedSettings);
                
                // Save backup to localStorage
                localStorage.setItem('settings_backup', JSON.stringify(mergedSettings));
                console.log('loadAllSettings: Settings saved to localStorage backup');
                
                return mergedSettings;
            } else {
                console.warn('loadAllSettings: Server settings validation failed:', validation.errors);
                throw new Error('Invalid settings from server: ' + validation.errors.join(', '));
            }
        } catch (error) {
            console.error('loadAllSettings: Error loading from server:', error);
            
            // Try to load from localStorage backup
            try {
                const backup = localStorage.getItem('settings_backup');
                if (backup) {
                    const backupSettings = JSON.parse(backup);
                    console.log('loadAllSettings: Loaded backup settings:', JSON.stringify(backupSettings, null, 2));
                    
                    const validation = validateAllSettings(backupSettings);
                    console.log('loadAllSettings: Backup settings validation:', validation);
                    
                    if (validation.valid) {
                        console.log('loadAllSettings: Using valid backup settings');
                        settings.set(backupSettings);
                        return backupSettings;
                    } else {
                        console.warn('loadAllSettings: Backup settings validation failed:', validation.errors);
                    }
                }
            } catch (backupError) {
                console.error('loadAllSettings: Error loading backup:', backupError);
            }
            
            // Fall back to defaults
            console.log('loadAllSettings: Falling back to default settings');
            const defaultSettings = getAllDefaults();
            console.log('loadAllSettings: Using default settings:', JSON.stringify(defaultSettings, null, 2));
            
            // Update the settings store with defaults
            settings.set(defaultSettings);
            
            // Save defaults as backup
            localStorage.setItem('settings_backup', JSON.stringify(defaultSettings));
            
            return defaultSettings;
        } finally {
            settingsLoading.set(false);
        }
    }

    async getCategorySetting(category) {
        try {
            const response = await fetch(`${this.baseUrl}/${category}`);
            const data = await response.json();
            
            if (response.ok) {
                return data.settings;
            } else {
                throw new Error(data.error || `Failed to load ${category} settings`);
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async getSetting(category, key) {
        try {
            const response = await fetch(`${this.baseUrl}/${category}/${key}`);
            const data = await response.json();
            
            if (response.ok) {
                return data.value;
            } else {
                throw new Error(data.error || `Failed to load ${category}.${key}`);
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async setSetting(category, key, value) {
        // Validate inputs
        if (!category || typeof category !== 'string') {
            throw new Error('Category is required and must be a string');
        }
        if (!key || typeof key !== 'string') {
            throw new Error('Key is required and must be a string');
        }
        if (value === undefined || value === null) {
            throw new Error('Value is required');
        }

        // Validate setting against schema
        const validationResult = validateSetting(category, key, value);
        if (!validationResult.valid) {
            const error = `Validation failed for ${category}.${key}: ${validationResult.error}`;
            settingsError.set(error);
            console.error(error);
            throw new Error(error);
        }

        try {
            const response = await fetch(`${this.baseUrl}/${category}/${key}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ value })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update local store
                settings.update(currentSettings => {
                    if (!currentSettings[category]) {
                        currentSettings[category] = {};
                    }
                    currentSettings[category][key] = value;
                    return currentSettings;
                });
                
                // Clear any previous errors
                settingsError.set(null);
                
                // Emit WebSocket event if available
                if (this.socket && this.socket.connected) {
                    this.socket.emit('setting_changed', { category, key, value });
                }
                
                return true;
            } else {
                throw new Error(data.error || `Failed to set ${category}.${key}`);
            }
        } catch (error) {
            const errorMessage = `Failed to save setting ${category}.${key}: ${error.message}`;
            settingsError.set(errorMessage);
            console.error(errorMessage, error);
            throw error;
        }
    }

    async updateSettings(settingsData) {
        try {
            // Validate input
            if (!settingsData || typeof settingsData !== 'object') {
                throw new Error('Settings data must be a valid object');
            }

            // Validate all settings against schema
            const validationResult = validateAllSettings(settingsData);
            if (!validationResult.valid) {
                const error = `Settings validation failed: ${validationResult.errors.join(', ')}`;
                settingsError.set(error);
                console.error(error);
                throw new Error(error);
            }

            settingsLoading.set(true);
            settingsError.set(null);
            
            const response = await fetch(`${this.baseUrl}/bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settingsData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update local store with validated data
                settings.update(currentSettings => {
                    return { ...currentSettings, ...settingsData };
                });
                
                // Emit WebSocket event if available
                if (this.socket && this.socket.connected) {
                    this.socket.emit('settings_bulk_update', settingsData);
                }
                
                return true;
            } else {
                throw new Error(data.error || 'Failed to update settings');
            }
        } catch (error) {
            console.error('Error updating settings:', error);
            settingsError.set(error.message);
            throw error;
        } finally {
            settingsLoading.set(false);
        }
    }

    async resetCategory(category) {
        try {
            const response = await fetch(`${this.baseUrl}/${category}/reset`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Reload settings to get the reset values
                await this.loadAllSettings();
                return true;
            } else {
                throw new Error(data.error || `Failed to reset ${category} settings`);
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async resetAllSettings() {
        try {
            const response = await fetch(`${this.baseUrl}/reset`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Reload settings to get the reset values
                await this.loadAllSettings();
                return true;
            } else {
                throw new Error(data.error || 'Failed to reset all settings');
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async exportSettings() {
        try {
            const response = await fetch(`${this.baseUrl}/export`);
            const data = await response.json();
            
            if (response.ok) {
                return data;
            } else {
                throw new Error(data.error || 'Failed to export settings');
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async importSettings(settingsData) {
        try {
            const response = await fetch(`${this.baseUrl}/import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settingsData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Reload settings to get the imported values
                await this.loadAllSettings();
                return true;
            } else {
                throw new Error(data.error || 'Failed to import settings');
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async validateSettings(settingsData) {
        try {
            const response = await fetch(`${this.baseUrl}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ settings: settingsData })
            });
            
            const data = await response.json();
            return data;
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async getSchema() {
        try {
            const response = await fetch(`${this.baseUrl}/schema`);
            const data = await response.json();
            
            if (response.ok) {
                return data.schema;
            } else {
                throw new Error(data.error || 'Failed to load settings schema');
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }
}

// Export singleton instance
export const settingsAPI = new SettingsAPI();

// Convenience functions
export const loadSettings = () => settingsAPI.loadAllSettings();
export const getSetting = (category, key) => settingsAPI.getSetting(category, key);
export const setSetting = (category, key, value) => settingsAPI.setSetting(category, key, value);
export const updateSettings = (settingsData) => settingsAPI.updateSettings(settingsData);
export const resetSettings = (category = null) => {
    if (category) {
        return settingsAPI.resetCategory(category);
    } else {
        return settingsAPI.resetAllSettings();
    }
};