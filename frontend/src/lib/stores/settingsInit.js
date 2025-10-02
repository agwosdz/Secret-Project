/**
 * Settings Initialization Module
 * Handles proper initialization of settings store with server synchronization
 */

import { settingsAPI } from './settings.js';
import { browser } from '$app/environment';

let initializationPromise = null;

/**
 * Initialize settings by loading from server
 * This should be called once during app startup
 */
export async function initializeSettings() {
    if (initializationPromise) {
        return initializationPromise;
    }
    
    if (!browser) {
        return Promise.resolve();
    }
    
    initializationPromise = settingsAPI.loadAllSettings()
        .then(() => {
            console.log('Settings initialized successfully');
            return true;
        })
        .catch(error => {
            console.error('Failed to initialize settings:', error);
            // Don't reject - let the app continue with localStorage/defaults
            return false;
        });
    
    return initializationPromise;
}

/**
 * Check if settings have been initialized
 */
export function areSettingsInitialized() {
    return initializationPromise !== null;
}