/**
 * Centralized Settings Store for Piano LED Visualizer
 * Provides reactive settings management with WebSocket synchronization
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

// Core settings store
export const settings = writable({});
export const settingsLoading = writable(false);
export const settingsError = writable(null);

// Derived stores for specific categories
export const ledSettings = derived(settings, $settings => $settings.led || {});
export const audioSettings = derived(settings, $settings => $settings.audio || {});
export const systemSettings = derived(settings, $settings => $settings.system || {});
export const userSettings = derived(settings, $settings => $settings.user || {});

// Settings API class
class SettingsAPI {
    constructor() {
        this.baseUrl = '/api/settings';
        this.socket = null;
        
        if (browser) {
            this.initializeWebSocket();
        }
    }

    initializeWebSocket() {
        // Initialize WebSocket connection for real-time updates
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('setting_changed', (data) => {
                this.handleSettingChange(data);
            });
            
            this.socket.on('settings_bulk_update', (data) => {
                this.handleBulkUpdate(data);
            });
            
            this.socket.on('settings_reset', () => {
                this.loadAllSettings();
            });
        }
    }

    handleSettingChange(data) {
        const { category, key, value } = data;
        settings.update(currentSettings => {
            if (!currentSettings[category]) {
                currentSettings[category] = {};
            }
            currentSettings[category][key] = value;
            return currentSettings;
        });
    }

    handleBulkUpdate(data) {
        const { updated_settings } = data;
        settings.update(currentSettings => {
            updated_settings.forEach(([category, key, value]) => {
                if (!currentSettings[category]) {
                    currentSettings[category] = {};
                }
                currentSettings[category][key] = value;
            });
            return currentSettings;
        });
    }

    async loadAllSettings() {
        try {
            settingsLoading.set(true);
            settingsError.set(null);
            
            const response = await fetch(this.baseUrl);
            const data = await response.json();
            
            if (response.ok) {
                settings.set(data.settings || {});
                return data.settings;
            } else {
                throw new Error(data.error || 'Failed to load settings');
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
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
        try {
            const response = await fetch(`${this.baseUrl}/${category}/${key}`, {
                method: 'POST',
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
                return true;
            } else {
                throw new Error(data.error || `Failed to set ${category}.${key}`);
            }
        } catch (error) {
            settingsError.set(error.message);
            throw error;
        }
    }

    async updateSettings(settingsData) {
        try {
            settingsLoading.set(true);
            
            const response = await fetch(`${this.baseUrl}/bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ settings: settingsData })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                settings.set(settingsData);
                return true;
            } else {
                throw new Error(data.error || 'Failed to update settings');
            }
        } catch (error) {
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